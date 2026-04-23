"""
Generate all manuscript figures from data.

Figure 1: PRISMA-style screening and inclusion flow
Figure 2: Publication timeline
Figure 3: Keyword co-occurrence / topic-cluster map
Figure 4: Model family and task landscape
Figure 5: Benchmark quality score distribution
Figure 6: Reproducibility and limitation heatmap
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

logger = logging.getLogger("figures")

FIG_DIR = Path("figures")
DPI = 150
STYLE = "seaborn-v0_8-whitegrid"


def _save(fig: plt.Figure, name: str, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved {path}")


# ── Figure 1: PRISMA-style flow ───────────────────────────────────────────────

def figure1_prisma(stats: Dict, fig_dir: Path) -> None:
    """Draw a simplified PRISMA screening flow diagram."""
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    n_identified = stats.get("n_identified", 0)
    n_after_dedup = stats.get("n_after_dedup", 0)
    n_screened = stats.get("n_screened", 0)
    n_excluded_relevance = stats.get("n_excluded_relevance", 0)
    n_eligible = stats.get("n_eligible", 0)
    n_included = stats.get("n_included", 0)

    boxes = [
        (1, 10.5, 8, 1.0, f"Records identified via database searching\n(PubMed, bioRxiv, SemanticScholar, Crossref)\nn = {n_identified}", "#AED6F1"),
        (1, 9.0, 8, 1.0, f"Records after deduplication\nn = {n_after_dedup}", "#A9DFBF"),
        (1, 7.5, 8, 1.0, f"Records screened (title + abstract)\nn = {n_screened}", "#F9E79F"),
        (1, 6.0, 8, 1.0, f"Records excluded (off-topic, no data)\nn = {n_excluded_relevance}", "#F1948A"),
        (1, 4.5, 8, 1.0, f"Full-text assessed for eligibility\nn = {n_eligible}", "#D7BDE2"),
        (1, 3.0, 8, 1.0, f"Studies included in final analysis\nn = {n_included}", "#76D7C4"),
    ]

    for x, y, w, h, label, color in boxes:
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            linewidth=1.5,
            edgecolor="#2C3E50",
            facecolor=color,
            alpha=0.85,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=9, wrap=True)

    # Arrows
    arrow_xs = [(5, 5)] * 5
    arrow_ys = [(10.5, 10.1), (9.0, 8.6), (7.5, 7.1), (6.0, 5.6), (4.5, 4.1)]
    for (x1, x2), (y1, y2) in zip(arrow_xs, arrow_ys):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#2C3E50", lw=1.5))

    ax.set_title("Figure 1. Study Screening and Selection (PRISMA-Style)",
                 fontsize=11, fontweight="bold", pad=10)
    _save(fig, "figure1_prisma_flow.png", fig_dir)


# ── Figure 2: Publication timeline ───────────────────────────────────────────

def figure2_timeline(timeline: pd.Series, fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    years = timeline.index.astype(int)
    counts = timeline.values

    bars = ax.bar(years, counts, color="#2980B9", edgecolor="white", linewidth=0.8, alpha=0.85)

    # Trend line
    if len(years) > 2:
        z = np.polyfit(years, counts, 1)
        p = np.poly1d(z)
        ax.plot(years, p(years), "--", color="#E74C3C", linewidth=1.8, label="Linear trend")
        ax.legend(fontsize=9)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(int(count)), ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Year of Publication", fontsize=11)
    ax.set_ylabel("Number of Papers", fontsize=11)
    ax.set_title("Figure 2. Annual Publication Volume: Single-Cell Foundation Models (2020–2026)",
                 fontsize=11, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    _save(fig, "figure2_publication_timeline.png", fig_dir)


# ── Figure 3: Keyword co-occurrence heatmap / cluster map ────────────────────

def figure3_keyword_network(kw_matrix: pd.DataFrame, cluster_terms: Optional[pd.DataFrame], fig_dir: Path) -> None:
    """Draw keyword co-occurrence heatmap and optionally a cluster-term bar chart."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Left: co-occurrence heatmap (top 15 keywords)
    ax = axes[0]
    top_kws = kw_matrix.sum(axis=1).nlargest(15).index
    sub = kw_matrix.loc[top_kws, top_kws]
    vals = sub.values.astype(float)
    norm_vals = vals / (vals.max() + 1e-9)

    im = ax.imshow(norm_vals, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(top_kws)))
    ax.set_yticks(range(len(top_kws)))
    ax.set_xticklabels(top_kws, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(top_kws, fontsize=7)
    plt.colorbar(im, ax=ax, shrink=0.8, label="Normalized co-occurrence")
    ax.set_title("Keyword Co-occurrence (Top 15)", fontsize=10, fontweight="bold")

    # Right: cluster top terms
    ax2 = axes[1]
    if cluster_terms is not None and len(cluster_terms) > 0:
        cluster_terms = cluster_terms.sort_values("n_papers", ascending=True)
        y = range(len(cluster_terms))
        ax2.barh(y, cluster_terms["n_papers"], color="#27AE60", alpha=0.8, edgecolor="white")
        ax2.set_yticks(list(y))
        ax2.set_yticklabels(
            [f"C{i}: {row.top_terms[:35]}..." for i, row in enumerate(cluster_terms.itertuples())],
            fontsize=7,
        )
        ax2.set_xlabel("Number of Papers", fontsize=10)
        ax2.set_title("Topic Clusters (TF-IDF + K-Means)", fontsize=10, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "Cluster data not available", ha="center", va="center", transform=ax2.transAxes)

    plt.suptitle("Figure 3. Keyword Co-occurrence and Topic Clusters", fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    _save(fig, "figure3_keyword_network.png", fig_dir)


# ── Figure 4: Model family and task landscape ─────────────────────────────────

def figure4_model_landscape(model_family: pd.Series, task_dist: pd.Series, fig_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Model families
    ax1 = axes[0]
    if len(model_family) > 0:
        mf = model_family.head(10)
        colors = plt.cm.Set2(np.linspace(0, 1, len(mf)))
        wedges, texts, autotexts = ax1.pie(
            mf.values, labels=None, autopct="%1.1f%%",
            colors=colors, startangle=140, pctdistance=0.8
        )
        ax1.legend(wedges, mf.index, title="Model Family",
                   loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7)
        ax1.set_title("Model Family Distribution", fontsize=10, fontweight="bold")
    else:
        ax1.text(0.5, 0.5, "No data", ha="center", va="center")

    # Task distribution
    ax2 = axes[1]
    if len(task_dist) > 0:
        td = task_dist.head(10)
        y = range(len(td))
        ax2.barh(list(y), td.values, color="#8E44AD", alpha=0.8, edgecolor="white")
        ax2.set_yticks(list(y))
        ax2.set_yticklabels(td.index, fontsize=8)
        ax2.set_xlabel("Number of Papers", fontsize=10)
        ax2.set_title("Task Distribution", fontsize=10, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center")

    plt.suptitle("Figure 4. Model Family and Downstream Task Landscape", fontsize=12, fontweight="bold")
    plt.tight_layout()
    _save(fig, "figure4_model_landscape.png", fig_dir)


# ── Figure 5: Benchmark quality score ────────────────────────────────────────

def figure5_benchmark(df: pd.DataFrame, fig_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Benchmark quality score histogram
    ax1 = axes[0]
    if "benchmark_quality_score" in df.columns:
        scores = pd.to_numeric(df["benchmark_quality_score"], errors="coerce").dropna()
        ax1.hist(scores, bins=[-.5, .5, 1.5, 2.5, 3.5, 4.5],
                 color="#E67E22", edgecolor="white", alpha=0.85)
        ax1.set_xlabel("Benchmark Quality Score (0–4)", fontsize=10)
        ax1.set_ylabel("Number of Papers", fontsize=10)
        ax1.set_xticks([0, 1, 2, 3, 4])
        ax1.set_xticklabels(["0\n(no info)", "1", "2", "3", "4\n(full info)"], fontsize=8)
        ax1.set_title("Benchmark Quality Score Distribution", fontsize=10, fontweight="bold")
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        mean_score = scores.mean()
        ax1.axvline(mean_score, color="#C0392B", linestyle="--", linewidth=1.5,
                    label=f"Mean = {mean_score:.2f}")
        ax1.legend(fontsize=8)
    else:
        ax1.text(0.5, 0.5, "No benchmark data", ha="center", va="center", transform=ax1.transAxes)

    # Baseline presence
    ax2 = axes[1]
    if "bq_baseline" in df.columns:
        has_baseline = int(pd.to_numeric(df["bq_baseline"], errors="coerce").fillna(0).sum())
        no_baseline = len(df) - has_baseline
        ax2.bar(["Baseline\nreported", "No baseline\nreported"],
                [has_baseline, no_baseline],
                color=["#27AE60", "#E74C3C"], alpha=0.8, edgecolor="white")
        ax2.set_ylabel("Number of Papers", fontsize=10)
        ax2.set_title("Baseline Comparison Presence", fontsize=10, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        for bar, val in zip(ax2.patches, [has_baseline, no_baseline]):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(int(val)), ha="center", va="bottom", fontsize=9)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)

    plt.suptitle("Figure 5. Benchmark Design Quality", fontsize=12, fontweight="bold")
    plt.tight_layout()
    _save(fig, "figure5_benchmark_quality.png", fig_dir)


# ── Figure 6: Reproducibility heatmap ────────────────────────────────────────

def figure6_reproducibility(df: pd.DataFrame, fig_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Reproducibility components
    ax1 = axes[0]
    repro_cols = {"Code\nAvailable": "code_flag", "Weights\nAvailable": "weights_flag",
                  "Data\nAvailable": "data_flag"}
    repro_vals = {}
    for label, col in repro_cols.items():
        if col in df.columns:
            repro_vals[label] = df[col].sum()
        else:
            repro_vals[label] = 0

    keys = list(repro_vals.keys())
    vals = list(repro_vals.values())
    total = max(len(df), 1)
    pcts = [v / total * 100 for v in vals]

    bars = ax1.bar(keys, pcts, color=["#2ECC71", "#F39C12", "#3498DB"], alpha=0.85, edgecolor="white")
    ax1.set_ylabel("% of Included Papers", fontsize=10)
    ax1.set_ylim(0, 110)
    ax1.set_title("Reproducibility Components", fontsize=10, fontweight="bold")
    for bar, pct in zip(bars, pcts):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f"{pct:.1f}%", ha="center", va="bottom", fontsize=9)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Reproducibility index distribution
    ax2 = axes[1]
    if "repro_index" in df.columns:
        ri = df["repro_index"].dropna()
        ax2.hist(ri, bins=np.linspace(0, 1.01, 8), color="#9B59B6", edgecolor="white", alpha=0.85)
        ax2.set_xlabel("Reproducibility Index (0–1)", fontsize=10)
        ax2.set_ylabel("Number of Papers", fontsize=10)
        ax2.set_title("Composite Reproducibility Index", fontsize=10, fontweight="bold")
        ax2.axvline(ri.mean(), color="#E74C3C", linestyle="--", linewidth=1.5,
                    label=f"Mean = {ri.mean():.2f}")
        ax2.legend(fontsize=8)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)

    plt.suptitle("Figure 6. Reproducibility and Open-Science Audit", fontsize=12, fontweight="bold")
    plt.tight_layout()
    _save(fig, "figure6_reproducibility.png", fig_dir)


# ── Entry point ───────────────────────────────────────────────────────────────

def generate_all_figures(biblio_results: Dict, df: pd.DataFrame, stats: Dict, fig_dir: Path) -> None:
    logger.info("Generating all figures...")
    figure1_prisma(stats, fig_dir)
    figure2_timeline(biblio_results.get("timeline", pd.Series(dtype=int)), fig_dir)
    figure3_keyword_network(
        biblio_results.get("kw_matrix", pd.DataFrame()),
        biblio_results.get("cluster_terms"),
        fig_dir,
    )
    figure4_model_landscape(
        biblio_results.get("model_family", pd.Series(dtype=int)),
        biblio_results.get("task_dist", pd.Series(dtype=int)),
        fig_dir,
    )
    figure5_benchmark(biblio_results.get("df_scored", df), fig_dir)
    figure6_reproducibility(biblio_results.get("df_repro", df), fig_dir)
    logger.info("All figures generated.")


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/papers_scored.csv")
    parser.add_argument("--biblio", default="data/processed")
    parser.add_argument("--out", default="figures")
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    biblio_dir = Path(args.biblio)

    biblio_results = {}
    for fname, key in [("timeline.csv", "timeline"), ("model_family_dist.csv", "model_family"),
                       ("task_dist.csv", "task_dist"), ("modality_dist.csv", "modality_dist")]:
        p = biblio_dir / fname
        if p.exists():
            s = pd.read_csv(p, index_col=0, header=0).squeeze()
            biblio_results[key] = s

    for fname, key in [("keyword_cooccurrence.csv", "kw_matrix")]:
        p = biblio_dir / fname
        if p.exists():
            biblio_results[key] = pd.read_csv(p, index_col=0)

    cluster_p = biblio_dir / "cluster_terms.csv"
    if cluster_p.exists():
        biblio_results["cluster_terms"] = pd.read_csv(cluster_p)

    biblio_results["df_scored"] = df
    biblio_results["df_repro"] = df

    stats = {
        "n_identified": len(df),
        "n_after_dedup": len(df),
        "n_screened": len(df),
        "n_excluded_relevance": 0,
        "n_eligible": len(df),
        "n_included": len(df),
    }
    generate_all_figures(biblio_results, df, stats, Path(args.out))
