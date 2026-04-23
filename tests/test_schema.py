"""Tests for schema validation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schema import PaperRecord


def test_paper_record_defaults():
    r = PaperRecord()
    assert r.paper_id == ""
    assert r.year is None


def test_paper_record_valid():
    r = PaperRecord(paper_id="pmid_12345", title="Test paper", year=2023, doi="10.1234/test")
    assert r.paper_id == "pmid_12345"
    assert r.year == 2023


def test_paper_record_extra_fields():
    r = PaperRecord(paper_id="x", abstract="Some abstract text")
    assert r.paper_id == "x"
