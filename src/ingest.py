"""
Literature ingestion pipeline.

Searches PubMed (via NCBI Entrez), bioRxiv, Semantic Scholar, and Crossref
for papers on single-cell foundation models and related topics.

Usage:
    python -m src.ingest --out data/raw

All queries, date filters, and raw API responses are logged.
"""

from __future__ import annotations

import json
import logging
import os
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Optional: biopython for Entrez
try:
    from Bio import Entrez
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest")

ENTREZ_EMAIL = os.environ.get("ENTREZ_EMAIL", "research@example.com")
SEARCH_QUERIES = [
    "single-cell foundation model",
    "single-cell AI transformer",
    "scRNA-seq transformer",
    "multimodal omics foundation model",
    "spatial transcriptomics foundation model",
    "perturbation prediction single-cell",
    "cell state prediction transformer",
    "biomarker discovery single-cell deep learning",
]
DATE_FILTER_START = "2020/01/01"
DATE_FILTER_END = datetime.today().strftime("%Y/%m/%d")

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
BIORXIV_BASE = "https://api.biorxiv.org/details/biorxiv"
CROSSREF_BASE = "https://api.crossref.org/works"


def _log_query(log_dir: Path, source: str, query: str, params: dict) -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "query": query,
        "params": params,
        "date_filter_start": DATE_FILTER_START,
        "date_filter_end": DATE_FILTER_END,
    }
    log_path = log_dir / "query_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _cache_path(cache_dir: Path, key: str) -> Path:
    h = hashlib.md5(key.encode()).hexdigest()
    return cache_dir / f"{h}.json"


def _load_cache(cache_dir: Path, key: str) -> Optional[Any]:
    p = _cache_path(cache_dir, key)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def _save_cache(cache_dir: Path, key: str, data: Any) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = _cache_path(cache_dir, key)
    with open(p, "w") as f:
        json.dump(data, f)


def search_pubmed(query: str, max_results: int = 200, cache_dir: Optional[Path] = None) -> List[Dict]:
    """Search PubMed via NCBI E-utilities REST API (no biopython required)."""
    if not HAS_BIOPYTHON:
        return _search_pubmed_rest(query, max_results, cache_dir)
    return _search_pubmed_bio(query, max_results, cache_dir)


def _search_pubmed_rest(query: str, max_results: int, cache_dir: Optional[Path]) -> List[Dict]:
    """PubMed search via E-utilities REST (fallback)."""
    cache_key = f"pubmed_rest_{query}_{max_results}"
    if cache_dir:
        cached = _load_cache(cache_dir, cache_key)
        if cached is not None:
            logger.info(f"PubMed cache hit for: {query}")
            return cached

    base_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    base_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params_search = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "mindate": "2020/01/01",
        "maxdate": DATE_FILTER_END,
        "datetype": "pdat",
        "tool": "sc-foundation-review",
        "email": ENTREZ_EMAIL,
    }

    records = []
    try:
        r = requests.get(base_search, params=params_search, timeout=30)
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        logger.info(f"PubMed esearch '{query}': {len(ids)} IDs")

        # Fetch in batches of 20
        for i in range(0, min(len(ids), max_results), 20):
            batch = ids[i: i + 20]
            params_fetch = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "tool": "sc-foundation-review",
                "email": ENTREZ_EMAIL,
            }
            rf = requests.get(base_fetch, params=params_fetch, timeout=30)
            rf.raise_for_status()
            records.extend(_parse_pubmed_xml(rf.text))
            time.sleep(0.4)

    except Exception as e:
        logger.warning(f"PubMed REST error for '{query}': {e}")

    if cache_dir:
        _save_cache(cache_dir, cache_key, records)
    return records


def _parse_pubmed_xml(xml_text: str) -> List[Dict]:
    """Parse PubMed XML response into structured dicts."""
    try:
        import xmltodict
        data = xmltodict.parse(xml_text)
        articles = data.get("PubmedArticleSet", {}).get("PubmedArticle", [])
        if isinstance(articles, dict):
            articles = [articles]
        records = []
        for art in articles:
            try:
                citation = art.get("MedlineCitation", {})
                article = citation.get("Article", {})
                pmid = citation.get("PMID", {})
                if isinstance(pmid, dict):
                    pmid = pmid.get("#text", "")
                title = article.get("ArticleTitle", "")
                if isinstance(title, dict):
                    title = title.get("#text", "")
                # Authors
                author_list = article.get("AuthorList", {}).get("Author", [])
                if isinstance(author_list, dict):
                    author_list = [author_list]
                authors = []
                for a in author_list[:5]:
                    ln = a.get("LastName", "")
                    fn = a.get("ForeName", "")
                    if ln:
                        authors.append(f"{ln} {fn}".strip())
                author_str = "; ".join(authors)
                # Year
                pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
                year_raw = pub_date.get("Year", pub_date.get("MedlineDate", ""))
                year = None
                if year_raw:
                    try:
                        year = int(str(year_raw)[:4])
                    except Exception:
                        pass
                journal = article.get("Journal", {}).get("Title", "")
                # DOI
                doi = ""
                ids_list = article.get("ELocationID", [])
                if isinstance(ids_list, dict):
                    ids_list = [ids_list]
                for eid in ids_list:
                    if isinstance(eid, dict) and eid.get("@EIdType") == "doi":
                        doi = eid.get("#text", "")
                abstract_raw = article.get("Abstract", {}).get("AbstractText", "")
                if isinstance(abstract_raw, list):
                    abstract = " ".join(
                        t.get("#text", t) if isinstance(t, dict) else str(t)
                        for t in abstract_raw
                    )
                elif isinstance(abstract_raw, dict):
                    abstract = abstract_raw.get("#text", "")
                else:
                    abstract = str(abstract_raw) if abstract_raw else ""

                records.append({
                    "paper_id": f"pmid_{pmid}",
                    "title": str(title),
                    "authors": author_str,
                    "year": year,
                    "venue": str(journal),
                    "doi": doi,
                    "preprint_id": "",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "source_database": "PubMed",
                    "abstract": abstract,
                })
            except Exception as e:
                logger.debug(f"Skip article parse error: {e}")
        return records
    except Exception as e:
        logger.warning(f"XML parse error: {e}")
        return []


def _search_pubmed_bio(query: str, max_results: int, cache_dir: Optional[Path]) -> List[Dict]:
    """PubMed search via Biopython Entrez."""
    cache_key = f"pubmed_bio_{query}_{max_results}"
    if cache_dir:
        cached = _load_cache(cache_dir, cache_key)
        if cached is not None:
            logger.info(f"PubMed bio cache hit: {query}")
            return cached

    Entrez.email = ENTREZ_EMAIL
    records = []
    try:
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            mindate=DATE_FILTER_START,
            maxdate=DATE_FILTER_END,
            datetype="pdat",
        )
        search_results = Entrez.read(handle)
        handle.close()
        ids = search_results.get("IdList", [])
        logger.info(f"PubMed bio '{query}': {len(ids)} IDs")
        for i in range(0, len(ids), 20):
            batch = ids[i: i + 20]
            handle = Entrez.efetch(db="pubmed", id=batch, retmode="xml")
            raw = handle.read()
            handle.close()
            records.extend(_parse_pubmed_xml(raw))
            time.sleep(0.4)
    except Exception as e:
        logger.warning(f"PubMed bio error: {e}")

    if cache_dir:
        _save_cache(cache_dir, cache_key, records)
    return records


def search_semantic_scholar(query: str, max_results: int = 100, cache_dir: Optional[Path] = None) -> List[Dict]:
    """Search Semantic Scholar API."""
    cache_key = f"ss_{query}_{max_results}"
    if cache_dir:
        cached = _load_cache(cache_dir, cache_key)
        if cached is not None:
            logger.info(f"SemanticScholar cache hit: {query}")
            return cached

    fields = "title,authors,year,venue,externalIds,abstract,openAccessPdf,publicationDate"
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": fields,
        "publicationDateOrYear": "2020:",
    }
    records = []
    try:
        r = requests.get(SEMANTIC_SCHOLAR_BASE, params=params, timeout=30,
                         headers={"User-Agent": "sc-foundation-review/1.0"})
        r.raise_for_status()
        data = r.json().get("data", [])
        logger.info(f"SemanticScholar '{query}': {len(data)} records")
        for p in data:
            eids = p.get("externalIds") or {}
            doi = eids.get("DOI", "")
            arxiv = eids.get("ArXiv", "")
            pmid = eids.get("PubMed", "")
            authors = "; ".join(
                a.get("name", "") for a in (p.get("authors") or [])[:5]
            )
            year = p.get("year")
            records.append({
                "paper_id": f"ss_{p.get('paperId', '')}",
                "title": p.get("title", ""),
                "authors": authors,
                "year": year,
                "venue": p.get("venue", ""),
                "doi": doi,
                "preprint_id": arxiv,
                "url": f"https://api.semanticscholar.org/graph/v1/paper/{p.get('paperId','')}",
                "source_database": "SemanticScholar",
                "abstract": p.get("abstract", ""),
            })
        time.sleep(1)
    except Exception as e:
        logger.warning(f"SemanticScholar error for '{query}': {e}")

    if cache_dir:
        _save_cache(cache_dir, cache_key, records)
    return records


def search_biorxiv(query: str, max_results: int = 100, cache_dir: Optional[Path] = None) -> List[Dict]:
    """Search bioRxiv via the bioRxiv API (date-range summary endpoint)."""
    cache_key = f"biorxiv_{query}_{max_results}"
    if cache_dir:
        cached = _load_cache(cache_dir, cache_key)
        if cached is not None:
            logger.info(f"bioRxiv cache hit: {query}")
            return cached

    # bioRxiv API: /details/biorxiv/{start_date}/{end_date}/{cursor}
    start_date = "2020-01-01"
    end_date = datetime.today().strftime("%Y-%m-%d")
    records = []
    cursor = 0
    collected = 0
    query_lower = query.lower().replace("-", " ")
    terms = [t.strip() for t in query_lower.split() if len(t.strip()) > 3]

    try:
        while collected < max_results:
            url = f"{BIORXIV_BASE}/{start_date}/{end_date}/{cursor}"
            r = requests.get(url, timeout=30, headers={"User-Agent": "sc-foundation-review/1.0"})
            r.raise_for_status()
            data = r.json()
            collection = data.get("collection", [])
            if not collection:
                break
            for item in collection:
                t = (item.get("title", "") + " " + item.get("abstract", "")).lower()
                if any(term in t for term in terms):
                    doi = item.get("doi", "")
                    records.append({
                        "paper_id": f"biorxiv_{doi.replace('/', '_')}",
                        "title": item.get("title", ""),
                        "authors": item.get("authors", ""),
                        "year": int(item.get("date", "2020")[:4]) if item.get("date") else None,
                        "venue": "bioRxiv",
                        "doi": doi,
                        "preprint_id": doi,
                        "url": f"https://biorxiv.org/abs/{doi}",
                        "source_database": "bioRxiv",
                        "abstract": item.get("abstract", ""),
                    })
                    collected += 1
                    if collected >= max_results:
                        break
            messages = data.get("messages", [{}])
            total = int(messages[0].get("total", 0)) if messages else 0
            cursor += len(collection)
            if cursor >= total or cursor >= 2000:
                break
            time.sleep(0.5)
    except Exception as e:
        logger.warning(f"bioRxiv error for '{query}': {e}")

    logger.info(f"bioRxiv '{query}': {len(records)} matching records")
    if cache_dir:
        _save_cache(cache_dir, cache_key, records)
    return records


def search_crossref(query: str, max_results: int = 100, cache_dir: Optional[Path] = None) -> List[Dict]:
    """Search Crossref works API."""
    cache_key = f"crossref_{query}_{max_results}"
    if cache_dir:
        cached = _load_cache(cache_dir, cache_key)
        if cached is not None:
            logger.info(f"Crossref cache hit: {query}")
            return cached

    params = {
        "query": query,
        "rows": min(max_results, 100),
        "filter": "from-pub-date:2020-01-01",
        "select": "DOI,title,author,published,container-title,abstract,URL",
        "mailto": ENTREZ_EMAIL,
    }
    records = []
    try:
        r = requests.get(CROSSREF_BASE, params=params, timeout=30,
                         headers={"User-Agent": "sc-foundation-review/1.0"})
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        logger.info(f"Crossref '{query}': {len(items)} records")
        for item in items:
            doi = item.get("DOI", "")
            title_list = item.get("title", [""])
            title = title_list[0] if title_list else ""
            authors_list = item.get("author", [])
            authors = "; ".join(
                f"{a.get('family', '')} {a.get('given', '')}".strip()
                for a in authors_list[:5]
            )
            pub = item.get("published", {}).get("date-parts", [[None]])[0]
            year = pub[0] if pub else None
            journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
            records.append({
                "paper_id": f"crossref_{doi.replace('/', '_')}",
                "title": title,
                "authors": authors,
                "year": year,
                "venue": journal,
                "doi": doi,
                "preprint_id": "",
                "url": item.get("URL", ""),
                "source_database": "Crossref",
                "abstract": item.get("abstract", ""),
            })
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Crossref error for '{query}': {e}")

    if cache_dir:
        _save_cache(cache_dir, cache_key, records)
    return records


def run_all_searches(out_dir: Path) -> List[Dict]:
    """Run all search queries across all sources and save raw results."""
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    log_dir = out_dir.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = raw_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    all_records: List[Dict] = []

    for query in SEARCH_QUERIES:
        logger.info(f"=== Query: {query} ===")
        _log_query(log_dir, "all", query, {"date_start": DATE_FILTER_START, "date_end": DATE_FILTER_END})

        r_pm = search_pubmed(query, max_results=100, cache_dir=cache_dir)
        r_ss = search_semantic_scholar(query, max_results=100, cache_dir=cache_dir)
        r_bx = search_biorxiv(query, max_results=50, cache_dir=cache_dir)
        r_cr = search_crossref(query, max_results=50, cache_dir=cache_dir)

        all_records.extend(r_pm)
        all_records.extend(r_ss)
        all_records.extend(r_bx)
        all_records.extend(r_cr)

        logger.info(f"Query '{query}': PubMed={len(r_pm)}, SS={len(r_ss)}, bioRxiv={len(r_bx)}, Crossref={len(r_cr)}")

    # Save raw combined
    raw_path = raw_dir / "raw_combined.json"
    with open(raw_path, "w") as f:
        json.dump(all_records, f, indent=2)
    logger.info(f"Total raw records: {len(all_records)} → {raw_path}")

    return all_records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data")
    args = parser.parse_args()
    run_all_searches(Path(args.out))
