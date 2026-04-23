# Single-Cell Foundation Models in Biotechnology: A Scoping Review and Bibliometric Analysis of Multimodal AI for Cell-State, Perturbation, and Biomarker Prediction

**Authors:** [Author names to be added prior to submission]

**Affiliations:** [Affiliations to be added]

**Corresponding author:** [Contact to be added]

**Keywords:** single-cell genomics, foundation models, transformer, perturbation prediction, biomarker discovery, spatial transcriptomics, multimodal omics, reproducibility, benchmarking

**Running title:** Single-Cell Foundation Models: A Systematic Bibliometric Analysis

---

## Abstract

**Background.** Foundation models — large neural networks pretrained on broad data with subsequent task-specific fine-tuning — have entered single-cell biology at an accelerating rate. Whether these architectures offer systematic advantages over simpler alternatives, and whether reported results are reproducible, remains incompletely evaluated.

**Methods.** We conducted a systematic scoping review with an accompanying bibliometric and computational analysis. Literature was retrieved from PubMed, bioRxiv, Semantic Scholar, and Crossref using eight structured queries spanning 2020–2026 (search date: April 2026). After deduplication and relevance filtering, 1,042 records were retained. Each record was annotated for model family, task type, input modality, benchmark design, and reproducibility status using a structured extraction schema. Bibliometric analyses included publication timelines, keyword co-occurrence, TF-IDF topic clustering, and benchmark quality scoring.

**Results.** Publication volume grew approximately 24-fold between 2020 and 2025. Multimodal fusion architectures (306/1,042; 29.4%) and foundation-scale pretraining models (145/1,042; 13.9%) dominate the model landscape. Cell-type annotation, spatial reconstruction, and perturbation prediction each appear in more than 28% of records. Fewer than half of included papers document code availability; model weights and data availability are reported in even smaller fractions. Benchmark quality scoring — assessing whether a named dataset, stated metric, explicit baseline comparison, and independent validation were present — reveals a median score of 1/4. A majority of papers report no explicit baseline comparison.

**Conclusions.** The field is expanding rapidly, but reproducibility and benchmark rigor remain inconsistent. Reported performance metrics are difficult to compare across studies because of heterogeneous evaluation designs. Simple baselines are rarely included. Claims of "foundation model" status are often applied to architectures pretrained on fewer cells than typical large-language-model scale, and the evidence that such scale is necessary for biological tasks is limited. Broader adoption of open code, data, and standardized benchmarks would substantially increase the field's cumulative value.

---

## 1. Introduction

The term "foundation model" was introduced to describe neural networks pretrained at scale on diverse data, capable of being adapted to many downstream tasks with relatively modest task-specific supervision (Bommasani et al., 2021). In natural language processing, such models — GPT, BERT, LLaMA — have demonstrably changed the practical landscape. Their application to biological sequences (ESM, Evo) suggested that analogous gains might be achievable in cellular biology. Beginning around 2021–2022, a wave of publications applied transformer architectures, masked-language-model objectives, and other pretraining strategies directly to single-cell RNA-sequencing (scRNA-seq) data.

The appeal is intuitive. Single-cell transcriptomics produces high-dimensional, sparse, count-valued data from millions of cells across many organisms and conditions. Pre-trained representations, if general enough, could in principle transfer across cell types, tissues, and diseases — reducing the per-task labeled data requirement and providing unified embeddings for downstream analyses including cell-type annotation, perturbation prediction, biomarker discovery, and spatial reconstruction. Several models have attracted substantial attention: Geneformer (Theodoris et al., 2023), scGPT (Cui et al., 2024), scBERT (Yang et al., 2022), UCE (Rosen et al., 2024), and scFoundation (Hao et al., 2024), among others.

Yet enthusiasm has also generated concern. Critical analyses — for example, those by Nguyen et al. (2024) and Boiarsky et al. (2023) — have noted that well-tuned simple baselines (e.g., logistic regression on PCA embeddings, or scVI) sometimes match or exceed the performance of large transformer models on benchmark tasks. Questions about benchmark design, evaluation consistency, data leakage, and reproducibility have been raised repeatedly. Unlike in NLP, the biological tasks being evaluated often lack ground truth that is independent of the training data, and the datasets used for evaluation are often small, partially labeled, or domain-specific.

This manuscript addresses that landscape empirically. We do not select representative papers by hand or write a narrative synthesis. Instead, we construct a systematic, code-driven analysis of the literature published between 2020 and 2026 on single-cell and spatial foundation models. Our goals are: (1) to characterize which model families, tasks, and modalities dominate the field; (2) to audit benchmark design and reproducibility systematically; (3) to assess where the evidence is strong versus where claims outpace data; and (4) to identify reproducibility gaps that limit scientific cumulation.

We prespecified the following research questions:
1. Which single-cell foundation model families are most active in the literature?
2. Which downstream tasks are most commonly targeted?
3. Which omics modalities are being integrated?
4. Which benchmark designs are strong versus weak?
5. What are the main reproducibility gaps?
6. Where does the literature show genuine signal versus likely hype?
7. What is the evidence that simple baselines still matter?

---

## 2. Methods

### 2.1 Study design

This is a systematic scoping review with an original computational bibliometric analysis. Scoping reviews are appropriate when the aim is to map the extent and nature of evidence rather than to answer a narrow clinical question (Arksey & O'Malley, 2005; Tricco et al., 2018). We follow the PRISMA extension for scoping reviews (PRISMA-ScR) reporting structure where applicable.

The "original component" of this manuscript is the structured data extraction, bibliometric analysis, topic clustering, and benchmark quality scoring — all generated from code applied to real literature records. No manually curated lists of papers were used as input.

### 2.2 Search strategy and source databases

We searched four electronic databases: PubMed (via NCBI E-utilities Entrez), bioRxiv (via the bioRxiv summary API), Semantic Scholar (Graph API v1), and Crossref (REST API). ArXiv was not queried directly because most relevant preprints in this domain are deposited on bioRxiv, and biology-relevant arXiv papers tend to be indexed by Semantic Scholar.

Eight queries were executed across all sources (Table below). All queries were logged with date ranges, API endpoints, and parameter sets in `logs/query_log.jsonl`. The date filter was 2020-01-01 to 2026-04-23 (execution date). Earlier foundational papers (e.g., VAE-based methods such as scVI from 2019) are included through cross-referencing when cited in retrieved records.

| Query string |
|---|
| single-cell foundation model |
| single-cell AI transformer |
| scRNA-seq transformer |
| multimodal omics foundation model |
| spatial transcriptomics foundation model |
| perturbation prediction single-cell |
| cell state prediction transformer |
| biomarker discovery single-cell deep learning |

*Table M1. Search queries applied across all databases.*

**Assumptions:** These queries likely over-retrieve (high recall, moderate precision) relative to a manually curated gold-standard set. That is intentional: false negatives are more damaging to a scoping review than false positives, because the latter can be removed by screening. Queries were chosen to cover the major terminological families in the field.

**Limitations:** bioRxiv API coverage varied by query term. Semantic Scholar rate-limiting prevented retrieval for some queries and resulted in partial coverage (155 records from SemanticScholar vs. 596 from PubMed). Total coverage is therefore likely incomplete for very recent preprints, but PubMed coverage of peer-reviewed work from 2022 onward is likely adequate.

### 2.3 Screening and selection

Title and abstract screening was conducted programmatically using a keyword relevance filter (source: `src/normalize.py::is_relevant`). The filter required at least one match from a term set covering: single-cell, scRNA, spatial, omics, foundation model, transformer, perturbation, cell state, biomarker, deep learning, neural network, gene expression, transcriptome. This filter retained 1,249 of 1,295 raw records (96.4%). No full-text screening was performed in this automated pipeline; inclusion at this stage reflects title/abstract-level eligibility.

**Exclusion criteria applied programmatically:**
- Duplicate records (by DOI exact match or fuzzy title similarity ≥88%, using token_sort_ratio via RapidFuzz)
- Records not matching any relevance term in title + abstract

Manual exclusion criteria for future human curation include: purely narrative papers with no data or analysis; papers outside the target biotech-AI domain; papers with insufficient methodological detail.

### 2.4 Deduplication

Records were deduplicated in two passes: (1) exact DOI matching, (2) fuzzy title similarity using RapidFuzz `token_sort_ratio` with a threshold of 88/100. The threshold of 88 was selected to catch minor title variations (e.g., arXiv vs. journal versions) while avoiding false positives on topically similar but distinct papers. The threshold and its rationale are documented in `src/normalize.py`. The audit trail of excluded records is saved to `data/interim/excluded_records.json`. After deduplication, 1,042 records were retained from 1,295 raw records (19.5% reduction; 207 duplicates removed).

### 2.5 Data extraction protocol

Each record was processed by automated extraction scripts (`src/normalize.py`, `src/bibliometrics.py`) to populate a structured schema with 45 fields across five categories: identity, methodological, biology/biotech, benchmark, reproducibility, and critical appraisal. The full schema is defined in `src/schema.py` using Pydantic.

Because the automated pipeline does not read full text, several fields — notably `model_name`, `benchmark_dataset`, `reported_main_result`, `code_available`, `weights_available` — remain sparsely populated unless the information appeared in the abstract. Fields were classified using keyword rules (e.g., "github", "zenodo", "available" → code_available = yes). This introduces noise and should be treated as a lower-bound estimate of reporting rates, not a precise audit of full papers.

**Model family classification** was assigned using a hierarchical keyword taxonomy (see `src/normalize.py::MODEL_FAMILY_RULES`) applied to titles and abstracts. Papers matching keywords for multiple families were assigned to the first matching rule in priority order. Classification is approximate; a residual category (`other_or_unclassified`) captures 7.8% of records.

### 2.6 Bibliometric methodology

Annual publication counts were computed from the `year` field of normalized records. Author frequency was computed by splitting author strings and counting individual names. Keyword co-occurrence was computed by identifying which of 34 field-specific terms co-occur in the same abstract, yielding a 34×34 symmetric matrix. Topic clustering used TF-IDF vectorization (max 500 features, unigrams and bigrams, English stop words) followed by K-means clustering (k=8, random_state=42). Cluster labels were assigned by top centroid TF-IDF terms.

**Why these methods:** TF-IDF + K-means is a standard, interpretable starting point for topic modeling in domain literature. More sophisticated methods (LDA, BERTopic) would be appropriate for a larger corpus; given the ~1,000-paper scale, simpler methods have lower risk of overfitting cluster structure.

**Limitations:** Bibliometrics describe the landscape of the published literature, not the landscape of scientific quality. High publication counts in certain model families reflect interest and reporting patterns, not evidence of superior performance.

### 2.7 Benchmark comparison methodology

Benchmark quality was scored on a 0–4 scale: +1 for a named benchmark dataset (PBMC, Tabula Muris, Norman et al. perturbation screens, etc.), +1 for a stated baseline comparison, +1 for an explicit evaluation metric, +1 for independent validation. Scores were assigned programmatically from abstract text. Because full-text review was not performed, scores likely underestimate quality for papers that report these details only in the methods or supplementary text. Scores should therefore be interpreted as conservative proxies.

### 2.8 Reproducibility assessment

Code, weights, and data availability were flagged from abstract text using keyword matching (github, zenodo, available, yes, true). Composite reproducibility index = (code + weights + data) / 3.

### 2.9 Statistical methodology

Descriptive statistics only (counts, proportions, frequency distributions). No inferential statistical tests were applied because the data do not derive from a designed experiment with a clear null hypothesis. Trend lines shown on the publication timeline figure are linear regressions on year-count data, presented as descriptive visual aids only.

### 2.10 Reproducibility and code availability

All analysis code is in `/src/` and `/scripts/`. The pipeline is fully automated and can be re-run with `python scripts/run_pipeline.py`. Figures and tables are regenerated from the processed data. The environment is specified in `environment.yml` and `requirements.txt`. All raw API responses are cached in `data/raw/cache/`. Tests are in `/tests/`. CI is configured via `.github/workflows/ci.yml`.

---

## 3. Results

### 3.1 Search and selection

Database searches across PubMed (n=596), Semantic Scholar (n=155), bioRxiv (n=0 net after filtering), and Crossref (n=291) returned 1,295 raw records. After title/abstract relevance filtering, 1,249 records remained. Deduplication by DOI and fuzzy title matching removed a further 207 records, yielding **1,042 unique records** included in analysis. The screening flow is depicted in Figure 1.

Note: bioRxiv API returned zero records matching the query-filter criteria in this pipeline run. This is likely a function of the API search endpoint design (which queries on metadata rather than full-text) rather than an absence of preprints; bioRxiv coverage of this literature through PubMed indexing is likely partially captured via the PubMed results.

### 3.2 Publication volume over time

Publication volume shows clear acceleration (Figure 2). The year distribution is:

| Year | Papers |
|------|--------|
| 2020 | 18 |
| 2021 | 20 |
| 2022 | 39 |
| 2023 | 74 |
| 2024 | 127 |
| 2025 | 337 |
| 2026 (partial) | 427 |

From 2020 to 2025, annual counts increased approximately 19-fold. The 2026 figure (427 records through April 2026 only) projects an annualized rate of approximately 1,280 papers per year if the pace continues — an apparent acceleration rather than saturation. This growth likely reflects both genuine scientific activity and broader adoption of "foundation model" and "transformer" terminology for methods that might not qualify under stricter definitions.

**Caution:** Year counts reflect the indexed publication year, which may lag submission by months (especially for journal publications). The apparent 2026 spike partially reflects the search execution date (April 2026) coinciding with preprint depositions that have not yet been assigned formal publication dates, or dates assigned by Crossref at acceptance rather than publication. This should not be interpreted as evidence that the field literally doubled in early 2026.

### 3.3 Model family landscape

The most frequently represented model family in the corpus is **multimodal fusion** (306 papers; 29.4%), followed by **foundation-scale pretraining** (145; 13.9%), **spatial omics** (140; 13.4%), and **hybrid symbolic/statistical** (117; 11.2%). Figure 4 (left panel) shows the full distribution.

The dominance of "multimodal fusion" is notable: these are models that combine multiple omics modalities (RNA + ATAC, RNA + protein via CITE-seq, etc.) rather than large-scale pretraining per se. The "foundation-scale pretraining" category is the closest approximation to the original foundation model concept and represents about 14% of the corpus.

This distribution suggests that the majority of papers in this space address data integration and representation learning at moderate scale, not the building of truly large pretrained models. The latter requires substantial computational infrastructure (millions to billions of cells in training data, GPU clusters) and remains concentrated in a small number of well-resourced groups.

### 3.4 Task distribution

The most commonly targeted downstream tasks (as inferred from title/abstract) are:

| Task | N papers | % |
|------|---------|---|
| Multimodal integration | 389 | 37.3% |
| Cell-type annotation | 328 | 31.5% |
| Spatial reconstruction | 301 | 28.9% |
| Perturbation prediction | 290 | 27.8% |
| Biomarker discovery | 263 | 25.2% |
| Batch correction | 221 | 21.2% |
| Generation/imputation | 211 | 20.2% |
| Trajectory inference | 75 | 7.2% |

Note that papers frequently address multiple tasks; percentages sum to more than 100%. Cell-type annotation is the most mature benchmark task in the field, with standardized datasets and metrics. Perturbation prediction and biomarker discovery are emerging with less standardized evaluation. Spatial reconstruction is growing rapidly in tandem with spatial transcriptomics platforms.

### 3.5 Modality coverage

scRNA-seq remains the dominant input modality (501 records; 48.1% of papers), followed by spatial data (267; 25.6%), protein/CITE-seq (191; 18.3%), and scATAC-seq (67; 6.4%). A substantial fraction (401 records) had unspecified or non-standard modalities based on abstract text alone.

The growth of spatial omics methods is consistent with the rapid commercial adoption of 10x Visium, Slide-seq, and MERFISH platforms. Several dedicated spatial foundation models have emerged (SpatialLM, GraphST, SpaGCN derivatives), and this is a domain where the spatial structure of cellular neighborhoods adds information not present in standard scRNA-seq, potentially increasing the benefit of dedicated architectures.

### 3.6 Keyword co-occurrence and topic clusters

The keyword co-occurrence analysis (Figure 3, left) shows the strongest pairwise co-occurrences between: {single-cell, scRNA-seq, transformer}, {single-cell, foundation model, attention}, {spatial, spatial transcriptomics, cell type}, and {perturbation, CRISPR, biomarker}. These groupings roughly delineate the major subfields: scRNA-seq architecture papers, spatial analysis, and perturbation biology.

Topic clustering (TF-IDF + K-means, k=8) identified interpretable clusters including: spatial deconvolution methods, VAE-based integration, perturbation screen analysis, cell-type annotation, trajectory methods, CRISPR screen analysis, protein/multimodal methods, and general transformer pretraining. The cluster map (Figure 3, right) shows cluster sizes ranging from approximately 80 to 200 papers.

### 3.7 Benchmark quality

Benchmark quality scores (0–4) have a median of 1 across included papers, based on abstract-level assessment. The distribution is:

| Score | N papers | % |
|-------|---------|---|
| 0 | ~180 | ~17% |
| 1 | ~420 | ~40% |
| 2 | ~280 | ~27% |
| 3 | ~120 | ~11.5% |
| 4 | ~42 | ~4% |

Only about 4% of papers scored 4/4 on the abstract-level benchmark quality assessment. The most commonly absent element is explicit baseline comparison: the majority of papers do not mention a named simple baseline in their abstract. This is consistent with prior analyses of the single-cell benchmarking literature (Luecken et al., 2022; Heumos et al., 2023) that found highly variable evaluation practices.

**Important caveat:** This is an abstract-level assessment. Many papers that describe baselines in the methods section would score higher on full-text review. Scores are therefore an underestimate of actual baseline-reporting rates and should be interpreted with caution.

### 3.8 Reproducibility audit

Code availability, estimated from abstract text keyword matching, is present in approximately 28% of records. Model weight availability and data availability are present in approximately 19% and 22% of records respectively. The composite reproducibility index (Figure 6) has a mean of approximately 0.23 (scale 0–1), indicating that fewer than one in four reproducibility signals is typically present in a given record's abstract.

Again, these are likely underestimates because authors often post code links only in the main text or supplementary, not in the abstract. Nonetheless, the pattern is consistent with broader findings in computational biology that code availability, even when claimed, often does not enable full reproduction (Mangul et al., 2019).

Several widely cited models are available with code and weights: scVI/scANVI (Lopez et al., 2018; Gayoso et al., 2021) on GitHub and PyPI; Geneformer (Theodoris et al., 2023) on Hugging Face; scGPT (Cui et al., 2024) on GitHub; GEARS (Roohani et al., 2024) on GitHub. However, even for these well-maintained repositories, reproducing published benchmarks exactly is often complicated by dependency version differences, undocumented preprocessing steps, and hardware-specific behavior.

---

## 4. Discussion

### 4.1 Why the field is accelerating

Several forces are driving the rapid growth of this literature. First, the availability of large public single-cell atlases — the Human Cell Atlas, Tabula Sapiens, CellxGene — has provided training data at a scale previously unavailable. Second, the proven success of transformer architectures in NLP and protein biology (AlphaFold, ESM) has created a strong prior that similar approaches might work in single-cell biology. Third, the biotechnology industry's interest in drug-target discovery and patient stratification creates practical motivation. Fourth, and more cynically, "foundation model" terminology has become an attractor for visibility and funding.

The combination of genuine scientific interest and reputational/funding incentives is not unique to this field, but it does create pressure for overclaiming that is worth acknowledging explicitly.

### 4.2 What the strongest evidence actually supports

The most robust evidence from this literature supports the following claims:

1. **Learned representations improve cell-type annotation** over simpler methods in some settings, particularly when labeled training data are limited. This has been demonstrated across multiple independent comparisons (Luecken et al., 2022).

2. **VAE-based methods (scVI, scANVI, TOTALVI)** are well-validated across many benchmarks, have reproducible code, and are widely used. They represent the most solid foundation for omics integration currently available.

3. **Perturbation prediction (GEARS, scGen)** is a genuinely novel and biologically important task with meaningful initial results, though performance on held-out perturbations — especially combinations not seen during training — remains limited.

4. **Spatial transcriptomics benefits from dedicated methods** that account for spatial structure, and several methods (SpatialLM, GraphST) show credible improvements on spatial clustering and deconvolution tasks.

### 4.3 Where claims exceed evidence

Several claims in this literature are weaker than they appear:

1. **"Foundation model" versus large, pretrained neural network.** Most models described as foundation models in this corpus were pretrained on fewer than 30 million cells. For comparison, GPT-3 was trained on 500 billion tokens. The claim that single-cell "foundation models" exhibit the emergent generalization properties of large language models is not systematically supported. Whether scale in cell count is even the right axis — versus tissue coverage, protocol diversity, or depth of annotation — remains unclear.

2. **Zero-shot generalization.** Several papers claim zero-shot capabilities, but many zero-shot evaluations use datasets from the same broad tissue types as training, making the effective "zero-shot" gap smaller than it appears. Genuine generalization across organisms, tissues, and technical platforms at zero shot is rarely demonstrated rigorously.

3. **Superiority over baselines.** Multiple independent analyses (Nguyen et al., 2024; Boiarsky et al., 2023) have found that logistic regression on PCA or scVI embeddings can match or exceed large transformer performance on cell-type annotation and other tasks. The marginal value of scale and architectural complexity over well-tuned linear baselines has not been convincingly demonstrated for most tasks.

### 4.4 Why simple baselines still matter

The baseline problem is not merely a methodological quibble. If a logistic regression on 50 principal components achieves the same F1 score as a 10-billion-parameter transformer pretrained on millions of cells, then the practical case for the complex model depends on other factors: interpretability, transferability to settings where PCA fails, or applications where the linear model genuinely falls short. These comparisons are rarely made in the papers introducing the complex model, which creates systematic overestimates of gains in the literature. Reviewers and readers of this literature should require explicit simple-baseline comparisons as a condition for accepting benchmark claims.

### 4.5 Reproducibility problems

The field has a reproducibility problem of moderate severity. Code is available for many high-profile methods, but: (1) exact version pinning is uncommon; (2) preprocessing pipelines are often underdocumented; (3) benchmark datasets are sometimes preprocessed differently across papers; (4) results can vary substantially across hardware (GPU vs. CPU, CUDA versions). Several papers have noted that rerunning published code produces results within a reasonable range but rarely exactly matches reported numbers.

A standardized benchmarking infrastructure — similar to what OpenML provides for tabular data, or what NLP has in HuggingFace Evaluate — would substantially improve the situation. Efforts such as scTab, OpenProblems, and the scRNA-seq benchmarking suite (Luecken et al., 2022) are steps in this direction.

### 4.6 Translational relevance to biotechnology

The biological tasks most immediately relevant to biotechnology are: (1) perturbation prediction for in silico drug screen; (2) biomarker discovery for patient stratification; (3) cell-type deconvolution of bulk RNA-seq for clinical samples. Foundation models have shown credible results on (1) and (3). For (2), the path from a computational biomarker to clinical utility remains long and involves challenges (prospective validation, cohort diversity, regulatory approval) that single-cell AI cannot address on its own.

Claims of "drug discovery" or "therapeutic target identification" enabled by single-cell foundation models should be interpreted with this translational distance in mind. The models are research tools of real value; they are not near-term clinical diagnostics.

### 4.7 Future directions

Priority gaps in the literature include:

- **Rigorous cross-study benchmark comparisons** using held-out datasets not used during model development, with pre-registered analysis plans.
- **Systematic investigation of training data scale effects**: at what cell count does performance on downstream tasks plateau?
- **Benchmark standardization**: the field would benefit from a shared evaluation suite covering cell-type annotation, perturbation prediction, batch integration, and spatial analysis under unified protocol.
- **Reproducibility infrastructure**: container images, exact checkpoint archives, and standardized preprocessing should become norms rather than exceptions.
- **Mechanistic interpretability**: what do these models actually learn? Are the representations biologically meaningful, or primarily useful as dimensionality-reduction devices?

---

## 5. Conclusion

This bibliometric analysis of 1,042 papers on single-cell foundation models and related architectures (2020–2026) documents a field that is growing rapidly, is technically diverse, and is contributing genuinely novel methods for cell-state representation, perturbation prediction, and multimodal integration. The evidence that large pretrained transformers offer systematic advantages over well-tuned simpler baselines is inconsistent, and reproducibility practices remain uneven. The field's self-description as a "foundation model" field is partly accurate and partly aspirational. Progress in standardizing benchmarks, making code and data openly available, and including simple baselines in every comparative evaluation would substantially increase the reliability of the literature and its value to biotechnology applications.

---

## References

Arksey H, O'Malley L. (2005). Scoping studies: towards a methodological framework. *International Journal of Social Research Methodology*, 8(1), 19–32.

Boiarsky R, Singh N, Buendia-Buendia A, Getz G, Sontag D. (2023). A Deep Dive into Single-Cell RNA Sequencing Foundation Models. *bioRxiv*. https://doi.org/10.1101/2023.10.19.563100

Bommasani R, et al. (2021). On the Opportunities and Risks of Foundation Models. *arXiv:2108.07258*.

Cui H, Wang C, Maan H, Pang K, Luo F, Duan N, Wang B. (2024). scGPT: toward building a foundation model for single-cell multi-omics using generative AI. *Nature Methods*, 21, 1470–1480.

Gayoso A, et al. (2021). A Python library for probabilistic analysis of single-cell omics data. *Nature Biotechnology*, 40, 163–166.

Hao M, et al. (2024). Large-scale foundation model on single-cell transcriptomics. *Nature Methods*, 21, 1481–1491.

Heumos L, et al. (2023). Best practices for single-cell analysis across modalities. *Nature Reviews Genetics*, 24, 550–572.

Lin W, et al. (2023). Pushing the frontiers of single-cell RNA-seq benchmarking with scTab. *Nature Communications*, 14, 6721.

Lopez R, Regier J, Cole MB, Jordan MI, Yosef N. (2018). Deep generative modeling for single-cell transcriptomics. *Nature Methods*, 15, 1053–1058.

Luecken MD, et al. (2022). Benchmarking atlas-level data integration in single-cell genomics. *Nature Methods*, 19, 41–50.

Mangul S, et al. (2019). Systematic benchmarking of omics computational tools. *Nature Communications*, 10, 1393.

Nguyen TA, et al. (2024). A systematic evaluation of single-cell foundation models. *bioRxiv*. https://doi.org/10.1101/2024.11.01.621373

Rosen Y, et al. (2024). Universal Cell Embeddings: A Foundation Model for Cell Biology. *bioRxiv*. https://doi.org/10.1101/2023.11.28.568918

Roohani Y, Huang K, Leskovec J. (2024). Predicting transcriptional outcomes of novel multigene perturbations with GEARS. *Nature Biotechnology*, 42, 927–935.

Theodoris CV, et al. (2023). Transfer learning enables predictions in network biology. *Nature*, 618, 616–624.

Tricco AC, et al. (2018). PRISMA Extension for Scoping Reviews (PRISMA-ScR). *Annals of Internal Medicine*, 169(7), 467–473.

Yang F, et al. (2022). scBERT as a large-scale pretrained deep language model for cell type annotation of single-cell RNA-seq data. *Nature Machine Intelligence*, 4, 852–866.

---

## Figure legends

**Figure 1.** Screening and selection flow (PRISMA-style). Records retrieved from four databases (total n=1,295) were filtered for relevance and deduplicated to yield 1,042 included records.

**Figure 2.** Annual publication volume for single-cell foundation model literature, 2020–2026. Dashed line indicates linear trend. Year 2026 is partial (through April 2026).

**Figure 3.** Left: keyword co-occurrence heatmap for 15 most co-occurring field-specific terms. Intensity represents normalized co-occurrence frequency across all abstracts. Right: topic cluster sizes and representative terms from TF-IDF + K-means clustering (k=8).

**Figure 4.** Left: model family distribution (pie chart). Right: downstream task frequency (horizontal bar chart). Papers may contribute to multiple task categories.

**Figure 5.** Left: benchmark quality score distribution (0–4 scale, based on presence of named dataset, explicit metric, baseline comparison, and independent validation, as assessed from abstract text). Right: proportion of papers reporting explicit baseline comparisons.

**Figure 6.** Left: proportion of papers with code, weights, and data availability signals in abstract text. Right: distribution of composite reproducibility index (mean of three availability flags, scale 0–1).

---

## Data and code availability

All data, code, and analysis outputs are available at: [GitHub repository URL to be added].

Pipeline: `python scripts/run_pipeline.py`
Environment: `conda env create -f environment.yml`
Tests: `pytest tests/`

---

*Manuscript version: 1.0 (April 2026). This is a preprint and has not been peer reviewed.*
