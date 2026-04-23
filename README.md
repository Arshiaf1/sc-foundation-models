# Single-Cell Foundation Models in Biotechnology: Scoping Review and Bibliometric Analysis

[![CI](https://github.com/[owner]/sc-foundation-models/actions/workflows/ci.yml/badge.svg)](https://github.com/[owner]/sc-foundation-models/actions/workflows/ci.yml)

This repository contains the complete reproducible analysis package for:

> **Single-Cell Foundation Models in Biotechnology: A Scoping Review and Bibliometric Analysis of Multimodal AI for Cell-State, Perturbation, and Biomarker Prediction**

---

## Contents

```
sc-foundation-models/
  README.md              ← This file
  LICENSE                ← MIT
  CITATION.cff           ← Machine-readable citation
  requirements.txt       ← Python dependencies (pip)
  environment.yml        ← Conda environment
  .gitignore
  .github/workflows/ci.yml  ← CI: tests + artifact regeneration
  data/
    raw/                 ← Raw API responses (cached)
    interim/             ← Excluded records, intermediate files
    processed/           ← Normalized and scored paper dataset (CSV/Parquet)
  figures/               ← All 6 manuscript figures (PNG)
  tables/                ← All 4 manuscript tables + supplementary (CSV)
  manuscript/            ← Manuscript source (manuscript.md)
  scripts/
    run_pipeline.py      ← Master pipeline: ingest → normalize → analyze → figures → tables
  src/
    schema.py            ← Pydantic schema for paper records
    ingest.py            ← Literature search (PubMed, bioRxiv, Semantic Scholar, Crossref)
    normalize.py         ← Normalization, deduplication, enrichment
    bibliometrics.py     ← Bibliometric analysis, topic clustering, scoring
    figures.py           ← All figure generation code
    tables.py            ← All table generation code
  tests/
    test_schema.py
    test_normalize.py
    test_bibliometrics.py
  supplementary/         ← Supplementary files
  references/            ← BibTeX reference database
  logs/                  ← Pipeline logs, query audit trail
```

---

## Quick start

### 1. Set up environment

```bash
conda env create -f environment.yml
conda activate sc-foundation-models
```

Or with pip:
```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
python scripts/run_pipeline.py
```

This will:
1. Search PubMed, bioRxiv, Semantic Scholar, and Crossref
2. Normalize and deduplicate records
3. Run bibliometric analysis and topic clustering
4. Generate all 6 figures to `figures/`
5. Generate all 4 tables to `tables/`

API responses are cached in `data/raw/cache/`. To re-run analysis without re-querying APIs:
```bash
python scripts/run_pipeline.py --skip-ingest
```

### 3. Run tests

```bash
pytest tests/ -v
```

### 4. Generate only figures from existing data

```bash
python src/figures.py --data data/processed/papers_scored.csv --biblio data/processed --out figures
```

---

## Outputs

| File | Description |
|------|-------------|
| `figures/figure1_prisma_flow.png` | PRISMA screening flow |
| `figures/figure2_publication_timeline.png` | Annual publication counts |
| `figures/figure3_keyword_network.png` | Keyword co-occurrence + topic clusters |
| `figures/figure4_model_landscape.png` | Model family + task distribution |
| `figures/figure5_benchmark_quality.png` | Benchmark quality scores |
| `figures/figure6_reproducibility.png` | Reproducibility audit |
| `tables/table1_included_studies.csv` | All included papers with core metadata |
| `tables/table2_model_taxonomy.csv` | Model taxonomy and task mapping |
| `tables/table3_benchmarks.csv` | Benchmark dataset and metric information |
| `tables/table4_reproducibility_audit.csv` | Reproducibility and limitation flags |
| `data/processed/papers_normalized.csv` | Normalized paper dataset |
| `data/processed/papers_scored.csv` | Dataset with benchmark + reproducibility scores |
| `logs/query_log.jsonl` | Audit trail of all API queries |

---

## Methods summary

- **Search date:** April 23, 2026
- **Databases:** PubMed, bioRxiv, Semantic Scholar, Crossref
- **Queries:** 8 structured queries (see `src/ingest.py::SEARCH_QUERIES`)
- **Date filter:** 2020-01-01 to search date
- **Raw records:** 1,295
- **After deduplication:** 1,042
- **Deduplication:** DOI exact match + fuzzy title similarity (RapidFuzz, threshold 88)
- **Classification:** Keyword-rule taxonomy (model family, tasks, modalities)
- **Topic modeling:** TF-IDF + K-means (k=8)
- **Benchmark scoring:** 0–4 scale from abstract-level keyword presence

---

## Reproducibility notes

All figures and tables are fully reproducible from source code and cached data. Random seeds are fixed (`random_state=42` in all scikit-learn calls). The pipeline is deterministic given the same input data.

API responses are cached locally. Re-running `--skip-ingest` regenerates all analysis outputs identically.

**Known limitations:**
- Abstract-level extraction underestimates code/data availability reporting rates
- bioRxiv API returned limited results for some queries
- Semantic Scholar was rate-limited for several queries

---

## Citation

If you use this dataset or code, please cite:

```
[Citation to be added after preprint submission]
```

See `CITATION.cff` for machine-readable citation.

---

## License

MIT License — see `LICENSE`.
