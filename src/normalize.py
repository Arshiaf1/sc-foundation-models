"""
Metadata normalization and deduplication.

Normalizes author names, titles, journal names, classifies model families,
and deduplicates records by DOI, title similarity, and author overlap.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from rapidfuzz import fuzz, process

logger = logging.getLogger("normalize")

# ── Model-family classification keywords ─────────────────────────────────────

MODEL_FAMILY_RULES = [
    ("transformer_masked_lm", ["bert", "roberta", "geneformer", "scbert", "genept",
                                "masked language", "mlm", "mask", "attention transformer"]),
    ("variational_autoencoder", ["vae", "variational autoencoder", "scvi", "totalvi",
                                  "multivi", "peakvi", "scanvi", "autoencode"]),
    ("graph_neural_network", ["gnn", "graph neural", "graph convolutional", "gcn",
                               "cell graph", "cellphonedb graph"]),
    ("multimodal_fusion", ["multimodal", "multi-modal", "multi-omics", "integration",
                            "fusion", "paired omics", "rna atac", "atac rna"]),
    ("spatial_omics", ["spatial", "spatially", "visium", "slide-seq", "stereo-seq",
                        "squidpy", "spagcn", "graphst", "spatial transcriptomics"]),
    ("perturbation_prediction", ["perturbation", "crispr", "genetic screen", "gears",
                                  "scgen", "chemcpa", "Norman", "drug response"]),
    ("foundation_scale_pretraining", ["foundation model", "large language model",
                                       "pretraining", "pretrain", "universal",
                                       "gpt", "llm", "cell2sentence", "uce",
                                       "scgpt", "scfoundation"]),
    ("hybrid_symbolic_statistical", ["symbolic", "differential equation", "ode",
                                      "mechanistic", "prior knowledge", "pathway"]),
]

TASK_KEYWORDS = {
    "cell_type_annotation": ["cell type", "annotation", "label", "classification"],
    "perturbation_prediction": ["perturbation", "crispr", "knockdown", "overexpression", "drug"],
    "biomarker_discovery": ["biomarker", "marker gene", "differential expression", "signature"],
    "batch_correction": ["batch", "integration", "harmonize", "correct"],
    "generation": ["generate", "generation", "synthetic", "imputation"],
    "spatial_reconstruction": ["spatial", "deconvolution", "spot", "location"],
    "trajectory_inference": ["trajectory", "pseudotime", "velocity", "lineage"],
    "multimodal_integration": ["multimodal", "multi-omics", "atac", "protein", "paired"],
}


def _normalize_unicode(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, normalize unicode for fuzzy matching."""
    if not title:
        return ""
    t = _normalize_unicode(title).lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_author(author: str) -> str:
    """Basic author name normalization."""
    a = _normalize_unicode(author)
    # Remove extra whitespace
    a = re.sub(r"\s+", " ", a).strip()
    return a


def normalize_journal(journal: str) -> str:
    """Normalize common journal abbreviations to canonical names."""
    mappings = {
        "nat methods": "Nature Methods",
        "nat biotechnol": "Nature Biotechnology",
        "nat commun": "Nature Communications",
        "cell syst": "Cell Systems",
        "genome biol": "Genome Biology",
        "nucleic acids res": "Nucleic Acids Research",
        "bioinformatics": "Bioinformatics",
        "plos comput biol": "PLOS Computational Biology",
        "brief bioinform": "Briefings in Bioinformatics",
        "mol syst biol": "Molecular Systems Biology",
    }
    j = journal.lower().strip()
    for abbr, full in mappings.items():
        if abbr in j:
            return full
    return journal.strip()


def classify_model_family(title: str, abstract: str) -> str:
    """Assign a model-family category from title+abstract keywords."""
    text = ((title or "") + " " + (abstract or "")).lower()
    for family, keywords in MODEL_FAMILY_RULES:
        if any(kw in text for kw in keywords):
            return family
    return "other_or_unclassified"


def classify_tasks(title: str, abstract: str) -> str:
    """Return comma-separated task labels from title+abstract."""
    text = ((title or "") + " " + (abstract or "")).lower()
    tasks = []
    for task, keywords in TASK_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            tasks.append(task)
    return ", ".join(tasks) if tasks else "unspecified"


def classify_modality(abstract: str) -> str:
    """Classify primary omics modality."""
    text = (abstract or "").lower()
    modalities = []
    if any(k in text for k in ["scrna", "rna-seq", "transcriptom", "mrna"]):
        modalities.append("scRNA-seq")
    if any(k in text for k in ["atac", "chromatin", "accessibility"]):
        modalities.append("scATAC-seq")
    if any(k in text for k in ["protein", "proteom", "cite-seq"]):
        modalities.append("Protein/CITE-seq")
    if any(k in text for k in ["spatial", "visium", "slide-seq", "stereo"]):
        modalities.append("Spatial")
    if any(k in text for k in ["methylat", "epigenom"]):
        modalities.append("Methylation/Epigenomics")
    return ", ".join(modalities) if modalities else "unspecified"


def is_relevant(record: Dict) -> bool:
    """Quick relevance filter on title+abstract."""
    text = ((record.get("title") or "") + " " + (record.get("abstract") or "")).lower()
    relevance_terms = [
        "single.cell", "scrna", "spatial", "omics", "foundation model",
        "transformer", "perturbation", "cell state", "biomarker", "deep learning",
        "neural network", "gene expression", "transcriptom",
    ]
    return any(re.search(t, text) for t in relevance_terms)


def deduplicate(records: List[Dict], title_threshold: int = 88) -> List[Dict]:
    """
    Deduplicate records by:
    1) Exact DOI match
    2) Fuzzy title similarity (rapidfuzz, threshold=88)
    3) Mark superseded preprints where DOI maps to journal version

    Returns deduplicated list.
    Logs exclusion reasons.
    """
    seen_dois: Set[str] = set()
    seen_norm_titles: List[str] = []
    kept: List[Dict] = []
    excluded: List[Dict] = []

    for rec in records:
        doi = (rec.get("doi") or "").strip().lower()
        title = rec.get("title", "")
        norm_t = normalize_title(title)

        # DOI dedup
        if doi and doi in seen_dois:
            excluded.append({**rec, "_exclusion_reason": "duplicate_doi"})
            continue

        # Title fuzzy dedup
        if norm_t and seen_norm_titles:
            best = process.extractOne(norm_t, seen_norm_titles, scorer=fuzz.token_sort_ratio)
            if best and best[1] >= title_threshold:
                excluded.append({**rec, "_exclusion_reason": f"similar_title:{best[1]}"})
                continue

        if doi:
            seen_dois.add(doi)
        if norm_t:
            seen_norm_titles.append(norm_t)
        kept.append(rec)

    logger.info(f"Dedup: kept={len(kept)}, excluded={len(excluded)}")
    return kept, excluded


def enrich_records(records: List[Dict]) -> List[Dict]:
    """Add inferred fields: model_family, downstream_application, omics_modality."""
    enriched = []
    for rec in records:
        title = rec.get("title", "")
        abstract = rec.get("abstract", "")
        rec["model_family"] = rec.get("model_family") or classify_model_family(title, abstract)
        rec["downstream_application"] = rec.get("downstream_application") or classify_tasks(title, abstract)
        rec["omics_modality"] = rec.get("omics_modality") or classify_modality(abstract)
        rec["venue"] = normalize_journal(rec.get("venue", ""))
        rec["authors"] = normalize_author(rec.get("authors", ""))
        enriched.append(rec)
    return enriched


def run_normalization(raw_path: Path, out_dir: Path) -> pd.DataFrame:
    """Load raw records, normalize, filter, deduplicate, enrich, and save."""
    with open(raw_path) as f:
        records = json.load(f)
    logger.info(f"Loaded {len(records)} raw records from {raw_path}")

    # Relevance filter
    relevant = [r for r in records if is_relevant(r)]
    logger.info(f"Relevance filter: {len(relevant)}/{len(records)} retained")

    # Dedup
    kept, excluded = deduplicate(relevant)

    # Save exclusions
    excl_path = out_dir / "interim" / "excluded_records.json"
    excl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(excl_path, "w") as f:
        json.dump(excluded, f, indent=2)

    # Enrich
    enriched = enrich_records(kept)

    df = pd.DataFrame(enriched)
    # Ensure year is numeric
    df["year"] = pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce")

    out_path = out_dir / "processed" / "papers_normalized.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

    csv_path = out_dir / "processed" / "papers_normalized.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved {len(df)} records → {out_path}")
    return df


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw/raw_combined.json")
    parser.add_argument("--out", default="data")
    args = parser.parse_args()
    run_normalization(Path(args.raw), Path(args.out))
