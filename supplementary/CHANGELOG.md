# Changelog / Audit Notes

## v1.0.0 — 2026-04-23

### Initial analysis run

**Pipeline:**
- Search executed: 2026-04-23
- Databases queried: PubMed, bioRxiv, Semantic Scholar, Crossref
- Search queries: 8 structured queries (see src/ingest.py)
- Date range: 2020-01-01 to 2026-04-23

**Record counts:**
- Raw records retrieved: 1,295
- After relevance filter: 1,249
- After deduplication: 1,042

**Deduplication parameters:**
- DOI exact match: applied first
- Title fuzzy similarity threshold: 88 (token_sort_ratio, RapidFuzz)
- Excluded records audit: data/interim/excluded_records.json

**Known issues:**
- bioRxiv API returned 0 matching records for all queries (likely API search limitation)
- Semantic Scholar rate-limited on 6 of 8 queries; partial coverage only (155 records)
- Year field: 2026 counts are inflated due to search-date coincidence with indexing lag

**Figures generated:** 6 (figure1–6, all PNGs in figures/)
**Tables generated:** 4 + 1 supplementary (tables/)

**Tests:** 23 passing, 0 failing

### Data sources
- PubMed: https://pubmed.ncbi.nlm.nih.gov/ (NCBI E-utilities REST API)
- bioRxiv: https://api.biorxiv.org/
- Semantic Scholar: https://api.semanticscholar.org/graph/v1/
- Crossref: https://api.crossref.org/works

### Analysis environment
- Python 3.11.2
- pandas, numpy, scipy, scikit-learn, matplotlib, networkx, rapidfuzz
- See requirements.txt for full dependency list
