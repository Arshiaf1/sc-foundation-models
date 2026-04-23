"""
Bibliometric analysis and evidence mapping.

Computes:
- Publication counts by year
- Author/institution frequency
- Keyword co-occurrence
- Topic clustering (TF-IDF + k-means)
- Task, modality, benchmark, reproducibility distributions
- Benchmark quality scoring
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger("bibliometrics")


# ── Keyword co-occurrence ─────────────────────────────────────────────────────

FIELD_KEYWORDS = [
    "single-cell", "foundation model", "transformer", "scRNA-seq",
    "perturbation", "spatial", "multimodal", "VAE", "GNN", "attention",
    "biomarker", "cell type", "batch correction", "pretraining",
    "CRISPR", "scGPT", "Geneformer", "scBERT", "scVI", "scANVI",
    "CellLM", "UCE", "scFoundation", "GEARS", "scGen", "ChemCPA",
    "benchmark", "reproducibility", "zero-shot", "fine-tuning",
    "cell atlas", "trajectory", "gene expression", "embeddings",
]


def extract_keywords(text: str, keyword_list: List[str]) -> List[str]:
    found = []
    text_lower = text.lower()
    for kw in keyword_list:
        if kw.lower() in text_lower:
            found.append(kw)
    return found


def keyword_cooccurrence_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build keyword co-occurrence matrix from titles+abstracts."""
    corpus = (df.get("title", pd.Series(dtype=str)).fillna("") + " " +
              df.get("abstract", pd.Series(dtype=str)).fillna(""))

    counts = np.zeros((len(FIELD_KEYWORDS), len(FIELD_KEYWORDS)), dtype=int)
    for text in corpus:
        present = [i for i, kw in enumerate(FIELD_KEYWORDS) if kw.lower() in text.lower()]
        for i in present:
            for j in present:
                if i != j:
                    counts[i, j] += 1
    kw_df = pd.DataFrame(counts, index=FIELD_KEYWORDS, columns=FIELD_KEYWORDS)
    return kw_df


# ── Topic clustering ──────────────────────────────────────────────────────────

def topic_clustering(df: pd.DataFrame, n_clusters: int = 8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """TF-IDF topic clustering. Returns df with cluster labels and top-term table."""
    corpus = (df.get("title", pd.Series(dtype=str)).fillna("") + " " +
              df.get("abstract", pd.Series(dtype=str)).fillna("")).tolist()

    valid_idx = [i for i, c in enumerate(corpus) if len(c.strip()) > 20]
    valid_corpus = [corpus[i] for i in valid_idx]

    if len(valid_corpus) < n_clusters:
        n_clusters = max(2, len(valid_corpus))

    vec = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
    X = vec.fit_transform(valid_corpus)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    label_col = [""] * len(df)
    for rank, orig_idx in enumerate(valid_idx):
        label_col[orig_idx] = f"cluster_{labels[rank]}"

    df = df.copy()
    df["topic_cluster"] = label_col

    # Top terms per cluster
    terms = vec.get_feature_names_out()
    cluster_terms = []
    for ci in range(n_clusters):
        centroid = km.cluster_centers_[ci]
        top_idx = centroid.argsort()[::-1][:10]
        cluster_terms.append({
            "cluster": f"cluster_{ci}",
            "n_papers": int((np.array(labels) == ci).sum()),
            "top_terms": ", ".join(terms[top_idx]),
        })
    terms_df = pd.DataFrame(cluster_terms)
    return df, terms_df


# ── Evidence mapping ──────────────────────────────────────────────────────────

def task_distribution(df: pd.DataFrame) -> pd.Series:
    if "downstream_application" not in df.columns:
        return pd.Series(dtype=int)
    tasks = []
    for v in df["downstream_application"].dropna():
        tasks.extend([t.strip() for t in str(v).split(",") if t.strip()])
    return pd.Series(Counter(tasks)).sort_values(ascending=False)


def modality_distribution(df: pd.DataFrame) -> pd.Series:
    if "omics_modality" not in df.columns:
        return pd.Series(dtype=int)
    modalities = []
    for v in df["omics_modality"].dropna():
        modalities.extend([m.strip() for m in str(v).split(",") if m.strip()])
    return pd.Series(Counter(modalities)).sort_values(ascending=False)


def model_family_distribution(df: pd.DataFrame) -> pd.Series:
    if "model_family" not in df.columns:
        return pd.Series(dtype=int)
    return df["model_family"].value_counts()


def reproducibility_score(df: pd.DataFrame) -> pd.DataFrame:
    """Assign 0/1 flags and compute a composite reproducibility index."""
    repro_df = df.copy()

    def to_flag(col: str) -> pd.Series:
        s = repro_df.get(col, pd.Series(dtype=str)).fillna("").str.lower()
        return s.apply(lambda x: 1 if any(t in x for t in ["yes", "available", "github", "zenodo", "true"]) else 0)

    repro_df["code_flag"] = to_flag("code_available").astype(int)
    repro_df["weights_flag"] = to_flag("weights_available").astype(int)
    repro_df["data_flag"] = to_flag("data_available").astype(int)
    repro_df["repro_index"] = (repro_df["code_flag"].astype(float) + repro_df["weights_flag"].astype(float) + repro_df["data_flag"].astype(float)) / 3
    return repro_df


def benchmark_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    """Score benchmark quality: dataset named, baseline present, metric stated, independent validation."""
    bq = df.copy()

    def flag(col: str, terms: List[str]) -> pd.Series:
        s = bq.get(col, pd.Series(dtype=str)).fillna("").str.lower()
        return s.apply(lambda x: 1 if any(t in x for t in terms) else 0)

    bq["bq_dataset"] = flag("benchmark_dataset", ["pbmc", "tabula", "perturbseq", "norman", "dixit", "10x", "atlas"])
    bq["bq_baseline"] = flag("baseline_compared", ["logistic", "pca", "random", "scvi", "seurat", "baseline"])
    bq["bq_metric"] = flag("metric_used", ["auroc", "f1", "pearson", "mse", "accuracy", "balanced"])
    bq["bq_independent"] = flag("independent_validation_present", ["yes", "independent", "held-out", "external"])
    bq["benchmark_quality_score"] = bq[["bq_dataset", "bq_baseline", "bq_metric", "bq_independent"]].sum(axis=1)
    return bq


# ── Year counts ───────────────────────────────────────────────────────────────

def publication_timeline(df: pd.DataFrame) -> pd.Series:
    year_col = pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce")
    valid = year_col[(year_col >= 2018) & (year_col <= 2026)]
    return valid.value_counts().sort_index()


# ── Top authors ───────────────────────────────────────────────────────────────

def top_authors(df: pd.DataFrame, n: int = 20) -> pd.Series:
    all_authors = []
    for auth_str in df.get("authors", pd.Series(dtype=str)).dropna():
        for a in str(auth_str).split(";"):
            a = a.strip()
            if a and len(a) > 2:
                all_authors.append(a)
    return pd.Series(Counter(all_authors)).sort_values(ascending=False).head(n)


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_bibliometrics(df: pd.DataFrame, out_dir: Path) -> Dict:
    """Run all bibliometric analyses and save outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # Timeline
    timeline = publication_timeline(df)
    timeline.to_csv(out_dir / "timeline.csv", header=["count"])
    results["timeline"] = timeline
    logger.info(f"Timeline: {dict(timeline)}")

    # Model family
    mf = model_family_distribution(df)
    mf.to_csv(out_dir / "model_family_dist.csv", header=["count"])
    results["model_family"] = mf

    # Task distribution
    td = task_distribution(df)
    td.to_csv(out_dir / "task_dist.csv", header=["count"])
    results["task_dist"] = td

    # Modality distribution
    md = modality_distribution(df)
    md.to_csv(out_dir / "modality_dist.csv", header=["count"])
    results["modality_dist"] = md

    # Top authors
    ta = top_authors(df)
    ta.to_csv(out_dir / "top_authors.csv", header=["n_papers"])
    results["top_authors"] = ta

    # Keyword co-occurrence
    kw_matrix = keyword_cooccurrence_matrix(df)
    kw_matrix.to_csv(out_dir / "keyword_cooccurrence.csv")
    results["kw_matrix"] = kw_matrix

    # Topic clustering
    df_clust, terms_df = topic_clustering(df)
    df_clust.to_csv(out_dir / "papers_clustered.csv", index=False)
    terms_df.to_csv(out_dir / "cluster_terms.csv", index=False)
    results["df_clustered"] = df_clust
    results["cluster_terms"] = terms_df

    # Reproducibility
    df_repro = reproducibility_score(df_clust)
    results["df_repro"] = df_repro

    # Benchmark quality
    df_bq = benchmark_quality_score(df_repro)
    df_bq.to_csv(out_dir / "papers_scored.csv", index=False)
    results["df_scored"] = df_bq

    logger.info("Bibliometric analysis complete.")
    return results


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/papers_normalized.csv")
    parser.add_argument("--out", default="data/processed")
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    run_bibliometrics(df, Path(args.out))
