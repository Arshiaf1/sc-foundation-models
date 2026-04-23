"""
Pydantic schema for paper metadata records.
"""

from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


class PaperRecord(BaseModel):
    # Identity
    paper_id: str = ""
    title: str = ""
    authors: str = ""
    year: Optional[int] = None
    venue: str = ""
    doi: str = ""
    preprint_id: str = ""
    url: str = ""
    source_database: str = ""

    # Methodological
    model_name: str = ""
    model_family: str = ""
    architecture_type: str = ""
    modality_input: str = ""
    pretraining_objective: str = ""
    tokenization_strategy: str = ""
    embedding_type: str = ""
    fine_tuning_type: str = ""
    zero_shot_or_finetuned: str = ""

    # Biology / biotech
    organism: str = ""
    tissue: str = ""
    cell_type_granularity: str = ""
    omics_modality: str = ""
    spatial_component: str = ""
    perturbation_task: str = ""
    biomarker_task: str = ""
    downstream_application: str = ""

    # Benchmark
    benchmark_dataset: str = ""
    benchmark_size: str = ""
    split_strategy: str = ""
    metric_used: str = ""
    baseline_compared: str = ""
    reported_main_result: str = ""
    independent_validation_present: str = ""

    # Reproducibility
    code_available: str = ""
    weights_available: str = ""
    data_available: str = ""
    license: str = ""
    docs_quality_score: str = ""
    reproducibility_notes: str = ""

    # Critical appraisal
    main_limitation: str = ""
    benchmark_risk: str = ""
    overclaim_risk: str = ""
    translational_relevance_score: str = ""

    class Config:
        extra = "allow"
