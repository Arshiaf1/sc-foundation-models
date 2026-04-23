"""
Generate manuscript tables from processed data.

Table 1: Included studies and core metadata
Table 2: Model taxonomy and task mapping
Table 3: Benchmark datasets and evaluation metrics
Table 4: Reproducibility and limitation audit
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("tables")


def generate_table1(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Table 1: Included studies – core metadata (title, authors, year, venue, DOI, source)."""
    cols = ["paper_id", "title", "authors", "year", "venue", "doi", "source_database"]
    available = [c for c in cols if c in df.columns]
    t1 = df[available].copy()
    t1 = t1.sort_values("year", ascending=False) if "year" in t1.columns else t1
    t1 = t1.reset_index(drop=True)
    t1.index = t1.index + 1
    out_path = out_dir / "table1_included_studies.csv"
    t1.to_csv(out_path)
    logger.info(f"Table 1: {len(t1)} rows → {out_path}")
    return t1


def generate_table2(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Table 2: Model taxonomy and task mapping."""
    cols = ["title", "model_name", "model_family", "architecture_type",
            "modality_input", "pretraining_objective", "zero_shot_or_finetuned",
            "downstream_application", "omics_modality", "organism"]
    available = [c for c in cols if c in df.columns]
    t2 = df[available].copy()
    t2 = t2.drop_duplicates(subset=["title"] if "title" in t2.columns else None)
    t2 = t2.reset_index(drop=True)
    t2.index = t2.index + 1
    out_path = out_dir / "table2_model_taxonomy.csv"
    t2.to_csv(out_path)
    logger.info(f"Table 2: {len(t2)} rows → {out_path}")
    return t2


def generate_table3(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Table 3: Benchmark datasets and evaluation metrics."""
    cols = ["title", "benchmark_dataset", "benchmark_size", "split_strategy",
            "metric_used", "baseline_compared", "reported_main_result",
            "independent_validation_present", "benchmark_quality_score"]
    available = [c for c in cols if c in df.columns]
    t3 = df[available].copy()
    if "benchmark_dataset" in t3.columns:
        t3 = t3[t3["benchmark_dataset"].notna() & (t3["benchmark_dataset"] != "")]
    t3 = t3.reset_index(drop=True)
    t3.index = t3.index + 1
    out_path = out_dir / "table3_benchmarks.csv"
    t3.to_csv(out_path)
    logger.info(f"Table 3: {len(t3)} rows → {out_path}")
    return t3


def generate_table4(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Table 4: Reproducibility and limitation audit."""
    cols = ["title", "code_available", "weights_available", "data_available",
            "license", "docs_quality_score", "reproducibility_notes",
            "main_limitation", "benchmark_risk", "overclaim_risk",
            "translational_relevance_score", "repro_index"]
    available = [c for c in cols if c in df.columns]
    t4 = df[available].copy()
    t4 = t4.reset_index(drop=True)
    t4.index = t4.index + 1
    out_path = out_dir / "table4_reproducibility_audit.csv"
    t4.to_csv(out_path)
    logger.info(f"Table 4: {len(t4)} rows → {out_path}")
    return t4


def generate_supplementary_modality_table(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Supplementary Table S1: Modality breakdown."""
    if "omics_modality" not in df.columns:
        return pd.DataFrame()
    modality_counts = df["omics_modality"].value_counts().reset_index()
    modality_counts.columns = ["omics_modality", "n_papers"]
    out_path = out_dir / "suppl_table_s1_modality_breakdown.csv"
    modality_counts.to_csv(out_path, index=False)
    logger.info(f"Supplementary Table S1 → {out_path}")
    return modality_counts


def generate_all_tables(df: pd.DataFrame, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    t1 = generate_table1(df, out_dir)
    t2 = generate_table2(df, out_dir)
    t3 = generate_table3(df, out_dir)
    t4 = generate_table4(df, out_dir)
    s1 = generate_supplementary_modality_table(df, out_dir)
    logger.info("All tables generated.")
    return {"table1": t1, "table2": t2, "table3": t3, "table4": t4, "suppl_s1": s1}


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/papers_scored.csv")
    parser.add_argument("--out", default="tables")
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    generate_all_tables(df, Path(args.out))
