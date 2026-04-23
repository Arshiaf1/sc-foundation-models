"""Tests for normalization and deduplication logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalize import (
    normalize_title,
    normalize_author,
    normalize_journal,
    classify_model_family,
    classify_tasks,
    classify_modality,
    is_relevant,
    deduplicate,
)


def test_normalize_title_lowercases():
    assert normalize_title("Single-Cell Foundation Model") == "single cell foundation model"


def test_normalize_title_none():
    assert normalize_title("") == ""


def test_normalize_author():
    assert normalize_author("  Smith  John  ") == "Smith John"


def test_normalize_journal_mapping():
    assert normalize_journal("Nat Methods") == "Nature Methods"


def test_classify_model_family_transformer():
    family = classify_model_family("scBERT for single-cell annotation", "masked language model applied to scRNA-seq")
    assert family == "transformer_masked_lm"


def test_classify_model_family_vae():
    family = classify_model_family("scVI integration", "variational autoencoder for batch correction")
    assert family == "variational_autoencoder"


def test_classify_model_family_unknown():
    family = classify_model_family("A basic method", "We describe a simple method.")
    assert family == "other_or_unclassified"


def test_classify_tasks_perturbation():
    tasks = classify_tasks("perturbation prediction", "CRISPR screen analysis")
    assert "perturbation_prediction" in tasks


def test_classify_modality_scrna():
    modality = classify_modality("scRNA-seq transcriptomics of T cells")
    assert "scRNA-seq" in modality


def test_is_relevant_true():
    rec = {"title": "Single-cell foundation model for transcriptomics", "abstract": ""}
    assert is_relevant(rec) is True


def test_is_relevant_false():
    rec = {"title": "Weather prediction using regression models", "abstract": "climate temperature humidity"}
    assert is_relevant(rec) is False


def test_deduplicate_by_doi():
    records = [
        {"paper_id": "a", "title": "Paper One", "doi": "10.1/x", "abstract": ""},
        {"paper_id": "b", "title": "Paper One duplicate", "doi": "10.1/x", "abstract": ""},
    ]
    kept, excluded = deduplicate(records)
    assert len(kept) == 1
    assert len(excluded) == 1


def test_deduplicate_by_title():
    records = [
        {"paper_id": "a", "title": "Single-Cell Foundation Models for Biology", "doi": "", "abstract": ""},
        {"paper_id": "b", "title": "Single-Cell Foundation Models for Biology.", "doi": "", "abstract": ""},
    ]
    kept, excluded = deduplicate(records)
    assert len(kept) == 1
    assert len(excluded) == 1


def test_deduplicate_keeps_distinct():
    records = [
        {"paper_id": "a", "title": "Foundation models in single cell", "doi": "10.1/a", "abstract": ""},
        {"paper_id": "b", "title": "Spatial transcriptomics methods", "doi": "10.1/b", "abstract": ""},
    ]
    kept, excluded = deduplicate(records)
    assert len(kept) == 2
