# Single-Cell Foundation Models in Biotechnology: A Scoping Review and Bibliometric Analysis

This repository holds the code, data, and outputs from my scoping review and bibliometric analysis of single-cell foundation models in biotechnology. I focused especially on multimodal AI approaches for things like cell-state prediction, perturbation modeling, and biomarker discovery.

I put this together to make the whole analysis as reproducible as possible.

---

## What's in the repo?

```bash
sc-foundation-models/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── environment.yml
├── scripts/
│   └── run_pipeline.py          # main script to run everything
├── src/                         # core code modules
├── data/                        # raw, interim and processed data
├── figures/                     # all the figures for the paper
├── tables/                      # tables for the manuscript
├── manuscript/
│   └── manuscript.md
├── tests/
└── logs/

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

- Search date: April 23, 2026
- Databases: PubMed, bioRxiv, Semantic Scholar, and Crossref
- Time period: papers from 2020 onwards
- I used 8 different search queries
- After cleaning and removing duplicates: around 1,042 unique records
- Deduplication was done with exact DOI match + fuzzy title matching
- Topic clustering with TF-IDF + K-means (I tried k=8 and it looked reasonable)

---

## Reproducibility notes

I fixed random seeds wherever possible so the results should be the same if you re-run it with the cached data. All API responses are saved locally, which makes it faster and more consistent to reproduce the figures and tables.
A few limitations I noticed:

Because a lot of the analysis is based on abstracts only, some things like code and data availability are probably under-reported.
The bioRxiv and Semantic Scholar APIs had some limitations during the search.

---

> ### **Disclosure & Attribution**
> This repository was developed with the assistance of generative AI tools for code structuring and technical implementation. The author provided the conceptual framework, defined the biological parameters, and performed full manual validation of all scripts. The final codebase represents the author's integration of AI-assisted development with human-led scientific oversight to ensure accuracy and reproducibility.

---

## Citation

If you use this dataset or code, please cite:

```
[Citation to be added after preprint submission]
```

See `CITATION.cff` for machine-readable citation.

---

## License

MIT License — feel free to use and modify the code (see the LICENSE file).
