"""Tests for bibliometric analysis functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.bibliometrics import (
    publication_timeline,
    task_distribution,
    model_family_distribution,
    benchmark_quality_score,
    reproducibility_score,
)


def _make_df():
    return pd.DataFrame([
        {
            "year": 2022,
            "model_family": "transformer_masked_lm",
            "downstream_application": "cell_type_annotation, biomarker_discovery",
            "benchmark_dataset": "PBMC3k",
            "baseline_compared": "logistic regression",
            "metric_used": "accuracy",
            "independent_validation_present": "yes",
            "code_available": "github",
            "weights_available": "",
            "data_available": "zenodo",
        },
        {
            "year": 2023,
            "model_family": "variational_autoencoder",
            "downstream_application": "batch_correction",
            "benchmark_dataset": "",
            "baseline_compared": "",
            "metric_used": "auroc",
            "independent_validation_present": "",
            "code_available": "",
            "weights_available": "",
            "data_available": "",
        },
    ])


def test_publication_timeline():
    df = _make_df()
    timeline = publication_timeline(df)
    assert 2022 in timeline.index
    assert timeline[2022] == 1


def test_task_distribution():
    df = _make_df()
    td = task_distribution(df)
    assert "cell_type_annotation" in td.index
    assert td["cell_type_annotation"] >= 1


def test_model_family_distribution():
    df = _make_df()
    mf = model_family_distribution(df)
    assert "transformer_masked_lm" in mf.index


def test_benchmark_quality_score_columns():
    df = _make_df()
    bq = benchmark_quality_score(df)
    assert "benchmark_quality_score" in bq.columns
    assert bq["benchmark_quality_score"].max() <= 4


def test_benchmark_quality_score_first_row():
    df = _make_df()
    bq = benchmark_quality_score(df)
    # First row has dataset, baseline, metric, independent validation
    assert bq.iloc[0]["benchmark_quality_score"] == 4


def test_reproducibility_score():
    df = _make_df()
    rs = reproducibility_score(df)
    assert "repro_index" in rs.columns
    # First row has code + data but not weights → 2/3
    assert abs(rs.iloc[0]["repro_index"] - 2/3) < 0.01
