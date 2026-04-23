#!/usr/bin/env python3
"""
Master pipeline script.
Runs: ingest → normalize → bibliometrics → figures → tables

Usage:
    python scripts/run_pipeline.py [--skip-ingest] [--data-dir data]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import run_all_searches
from src.normalize import run_normalization
from src.bibliometrics import run_bibliometrics
from src.figures import generate_all_figures
from src.tables import generate_all_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log"),
    ],
)
logger = logging.getLogger("pipeline")


def main():
    parser = argparse.ArgumentParser(description="sc-foundation-models analysis pipeline")
    parser.add_argument("--skip-ingest", action="store_true",
                        help="Skip literature search if raw data exists")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    parser.add_argument("--fig-dir", default="figures", help="Output figures directory")
    parser.add_argument("--table-dir", default="tables", help="Output tables directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    fig_dir = Path(args.fig_dir)
    table_dir = Path(args.table_dir)
    raw_path = data_dir / "raw" / "raw_combined.json"
    processed_path = data_dir / "processed" / "papers_normalized.csv"

    # Step 1: Ingest
    if not args.skip_ingest or not raw_path.exists():
        logger.info("=== Step 1: Literature ingestion ===")
        records = run_all_searches(data_dir)
        logger.info(f"Ingested {len(records)} raw records")
    else:
        logger.info(f"Skipping ingest; using cached {raw_path}")

    # Step 2: Normalize
    logger.info("=== Step 2: Normalization and deduplication ===")
    df = run_normalization(raw_path, data_dir)
    logger.info(f"Normalized dataset: {len(df)} records")

    # Step 3: Bibliometrics
    logger.info("=== Step 3: Bibliometric analysis ===")
    biblio_results = run_bibliometrics(df, data_dir / "processed")

    # Load scored df
    scored_path = data_dir / "processed" / "papers_scored.csv"
    import pandas as pd
    if scored_path.exists():
        df_scored = pd.read_csv(scored_path)
    else:
        df_scored = df

    # Step 4: Figures
    logger.info("=== Step 4: Figure generation ===")
    stats = {
        "n_identified": len(pd.read_json(raw_path)) if raw_path.exists() else len(df_scored),
        "n_after_dedup": len(df),
        "n_screened": len(df),
        "n_excluded_relevance": 0,
        "n_eligible": len(df_scored),
        "n_included": len(df_scored),
    }
    generate_all_figures(biblio_results, df_scored, stats, fig_dir)

    # Step 5: Tables
    logger.info("=== Step 5: Table generation ===")
    generate_all_tables(df_scored, table_dir)

    logger.info("=== Pipeline complete ===")
    logger.info(f"Figures: {fig_dir}/")
    logger.info(f"Tables: {table_dir}/")
    logger.info(f"Processed data: {data_dir}/processed/")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    main()
