#!/usr/bin/env python3
"""
Push project files to GitHub via the Composio proxy and GitHub Contents API.
Uses the Bud backend proxy route to avoid needing a direct git credential.
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

# Load runtime config
CONFIG_PATH = Path("/root/.skills/runtime/composio-skill-config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

ORCHIDS_API_KEY = config["orchidsApiKey"]
BACKEND_URL = config["backendBaseUrl"]
CONNECTED_ACCOUNT_ID = "ca_OWuTMvIqmUiT"
OWNER = "Arshiaf1"
REPO = "sc-foundation-models"
BASE_BRANCH = "main"


def push_file(file_path: Path, repo_path: str, message: str, existing_sha: str = None) -> dict:
    """Upload a file to GitHub via the proxy."""
    try:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"  SKIP {file_path}: cannot read ({e})")
        return {}

    body = {
        "message": message,
        "content": content,
        "branch": BASE_BRANCH,
    }
    if existing_sha:
        body["sha"] = existing_sha

    resp = requests.post(
        f"{BACKEND_URL}/composio/proxy",
        headers={"x-api-key": ORCHIDS_API_KEY, "Content-Type": "application/json"},
        json={
            "toolkitSlug": "github",
            "connectedAccountId": CONNECTED_ACCOUNT_ID,
            "endpoint": f"/repos/{OWNER}/{REPO}/contents/{repo_path}",
            "method": "PUT",
            "body": body,
        },
        timeout=30,
    )
    return resp.json()


def get_file_sha(repo_path: str) -> str:
    """Get SHA of existing file (needed for updates)."""
    resp = requests.post(
        f"{BACKEND_URL}/composio/proxy",
        headers={"x-api-key": ORCHIDS_API_KEY, "Content-Type": "application/json"},
        json={
            "toolkitSlug": "github",
            "connectedAccountId": CONNECTED_ACCOUNT_ID,
            "endpoint": f"/repos/{OWNER}/{REPO}/contents/{repo_path}",
            "method": "GET",
        },
        timeout=15,
    )
    data = resp.json().get("data", {})
    return data.get("sha", "")


# Files to push: (local path, repo path, commit message)
ROOT = Path(__file__).parent.parent

FILES = [
    (ROOT / "README.md", "README.md", "docs: add README with setup instructions"),
    (ROOT / "LICENSE", "LICENSE", "chore: add MIT license"),
    (ROOT / "CITATION.cff", "CITATION.cff", "docs: add machine-readable citation"),
    (ROOT / "requirements.txt", "requirements.txt", "chore: add pip requirements"),
    (ROOT / "environment.yml", "environment.yml", "chore: add conda environment"),
    (ROOT / "pyproject.toml", "pyproject.toml", "chore: add pyproject.toml"),
    (ROOT / ".gitignore", ".gitignore", "chore: add gitignore"),
    (ROOT / "src/__init__.py", "src/__init__.py", "feat: add src package"),
    (ROOT / "src/schema.py", "src/schema.py", "feat(pipeline): add Pydantic schema"),
    (ROOT / "src/ingest.py", "src/ingest.py", "feat(pipeline): add literature ingestion module"),
    (ROOT / "src/normalize.py", "src/normalize.py", "feat(pipeline): add normalization and deduplication"),
    (ROOT / "src/bibliometrics.py", "src/bibliometrics.py", "feat(bibliometrics): add bibliometric analysis"),
    (ROOT / "src/figures.py", "src/figures.py", "feat(figures): add figure generation code"),
    (ROOT / "src/tables.py", "src/tables.py", "feat(figures): add table generation code"),
    (ROOT / "scripts/run_pipeline.py", "scripts/run_pipeline.py", "feat(pipeline): add master pipeline script"),
    (ROOT / "scripts/push_to_github.py", "scripts/push_to_github.py", "chore: add GitHub push automation script"),
    (ROOT / "tests/__init__.py", "tests/__init__.py", "test: add test package"),
    (ROOT / "tests/test_schema.py", "tests/test_schema.py", "test: add schema tests"),
    (ROOT / "tests/test_normalize.py", "tests/test_normalize.py", "test: add normalize tests"),
    (ROOT / "tests/test_bibliometrics.py", "tests/test_bibliometrics.py", "test: add bibliometrics tests"),
    (ROOT / ".github/workflows/ci.yml", ".github/workflows/ci.yml", "ci: add GitHub Actions CI workflow"),
    (ROOT / "manuscript/manuscript.md", "manuscript/manuscript.md", "feat(manuscript-draft): add full manuscript"),
    (ROOT / "references/references.bib", "references/references.bib", "docs: add BibTeX references"),
    (ROOT / "supplementary/CHANGELOG.md", "supplementary/CHANGELOG.md", "docs: add changelog and audit notes"),
    (ROOT / "data/processed/papers_normalized.csv", "data/processed/papers_normalized.csv",
     "data: add normalized paper database (1042 records)"),
    (ROOT / "data/processed/timeline.csv", "data/processed/timeline.csv", "data: add publication timeline"),
    (ROOT / "data/processed/model_family_dist.csv", "data/processed/model_family_dist.csv", "data: add model family distribution"),
    (ROOT / "data/processed/task_dist.csv", "data/processed/task_dist.csv", "data: add task distribution"),
    (ROOT / "data/processed/modality_dist.csv", "data/processed/modality_dist.csv", "data: add modality distribution"),
    (ROOT / "data/processed/cluster_terms.csv", "data/processed/cluster_terms.csv", "data: add topic cluster terms"),
    (ROOT / "figures/figure1_prisma_flow.png", "figures/figure1_prisma_flow.png", "feat(figures): Figure 1 PRISMA flow"),
    (ROOT / "figures/figure2_publication_timeline.png", "figures/figure2_publication_timeline.png", "feat(figures): Figure 2 publication timeline"),
    (ROOT / "figures/figure3_keyword_network.png", "figures/figure3_keyword_network.png", "feat(figures): Figure 3 keyword network"),
    (ROOT / "figures/figure4_model_landscape.png", "figures/figure4_model_landscape.png", "feat(figures): Figure 4 model landscape"),
    (ROOT / "figures/figure5_benchmark_quality.png", "figures/figure5_benchmark_quality.png", "feat(figures): Figure 5 benchmark quality"),
    (ROOT / "figures/figure6_reproducibility.png", "figures/figure6_reproducibility.png", "feat(figures): Figure 6 reproducibility"),
    (ROOT / "tables/table1_included_studies.csv", "tables/table1_included_studies.csv", "data: Table 1 included studies"),
    (ROOT / "tables/table2_model_taxonomy.csv", "tables/table2_model_taxonomy.csv", "data: Table 2 model taxonomy"),
    (ROOT / "tables/table3_benchmarks.csv", "tables/table3_benchmarks.csv", "data: Table 3 benchmarks"),
    (ROOT / "tables/table4_reproducibility_audit.csv", "tables/table4_reproducibility_audit.csv", "data: Table 4 reproducibility audit"),
    (ROOT / "tables/suppl_table_s1_modality_breakdown.csv", "tables/suppl_table_s1_modality_breakdown.csv", "data: Supplementary Table S1"),
    (ROOT / "logs/query_log.jsonl", "logs/query_log.jsonl", "data: add query audit log"),
]


def main():
    print(f"Pushing {len(FILES)} files to {OWNER}/{REPO}...")
    success, failed = 0, 0

    for local_path, repo_path, commit_msg in FILES:
        if not local_path.exists():
            print(f"  MISSING: {local_path}")
            failed += 1
            continue

        # Get existing SHA if file exists (README.md was already created)
        sha = get_file_sha(repo_path)

        result = push_file(local_path, repo_path, commit_msg, sha if sha else None)
        if result.get("data", {}).get("commit") or result.get("status") == 200:
            print(f"  OK  {repo_path}")
            success += 1
        elif "data" in result and "content" in (result.get("data") or {}):
            print(f"  OK  {repo_path}")
            success += 1
        else:
            print(f"  ERR {repo_path}: {str(result)[:150]}")
            failed += 1

        time.sleep(0.3)  # Rate limiting

    print(f"\nDone: {success} pushed, {failed} failed")
    print(f"Repo: https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
