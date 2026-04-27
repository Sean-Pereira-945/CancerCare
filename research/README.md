# Research Environment & Paper Generation

This `research` folder is the dedicated environment for running formal, reproducible experiments and generating publication-ready artifacts such as tables, figures, and statistical analyses for the CancerCare AI paper.

## Folder Purpose

The goal of this directory is to evaluate the performance of the Retrieval-Augmented Generation (RAG) system across different ablation variants (`A0`-`A5`), run automated LLM-as-a-judge pipelines, and compile the final data into formats suitable for reports and papers.

## Core Files & Artifacts

### 1. Statistical Analysis & Plotting

- `generate_plots.py`: reads the output CSVs and generates publication-ready graphs into `figures/`
- `statistical_analysis.py`: performs paired statistical comparison such as McNemar-style testing and bootstrap confidence intervals
- `slice_analysis.py`: computes performance metrics segmented by question type
- `summarize_quality_report.py`: turns the quality report JSON into lighter-weight summaries

### 2. Core Datasets & Results

- `datasets/eval_qa.jsonl`: benchmark Q&A dataset used for evaluation
- `experiment_matrix.csv`: aggregated per-variant metric table
- `experiment_raw_data.json`: item-level model outputs and judge scores
- `experiment_raw_data.tiny20.json`: small local-debug subset
- `experiment_quality_report.json`: run coverage, failure counts, and diagnostics

### 3. Documentation

- `annotation_guidelines.md`: instructions for dataset creation and grading

## Experiment Outputs

The main outputs produced by the research workflow are:

- `experiment_matrix.csv`
- `experiment_raw_data.json`
- `experiment_quality_report.json`
- `experiment_failures.jsonl`
- `statistical_results.txt`
- `slice_analysis_A5.json`

## Figures

The `figures/` directory contains publication-ready visualizations generated from the experiment outputs.

### Comprehensive Metrics Across Variants

This plot compares the four evaluation metrics across the ablation variants.

![Comprehensive Metrics](figures/comprehensive_metrics.png)

### Safety vs. Hallucination Tradeoff

This scatter plot highlights the relationship between hallucination rate and safety-violation rate across variants. Lower values on both axes are better.

![Safety vs Hallucination Tradeoff](figures/safety_hallucination_tradeoff.png)

## Evaluation Setup

The experiment runner lives in `backend/experiment_runner.py` and executes the same `/api/chat/message` endpoint used by the product. That means the research pipeline evaluates the real backend behavior rather than a disconnected notebook-only mock.

For each evaluation item:

1. A question is sent to the chat API under one of the configured variants.
2. The response and retrieved context are collected.
3. A judge LLM scores the output on binary metrics.
4. Raw per-item outputs are saved.
5. Aggregated metrics, figures, and statistics are derived from those saved outputs.

## Metrics

The main judged metrics are:

- `faithfulness`
- `hallucination`
- `safety_violation`
- `citation_correctness`

Each metric is scored per item and then averaged by variant. The statistical script compares paired outputs between variants on overlapping items only.

## Getting Started

To reproduce the analysis for the paper:

1. **Run the Full Experiment** (from `../backend/`):
   ```powershell
   python experiment_runner.py --dataset "..\research\datasets\eval_qa.jsonl" ...
   ```
2. **Generate Figures** (from `research/`):
   ```powershell
   ..\backend\.venv\Scripts\python.exe generate_plots.py --csv "experiment_matrix.csv" --output-dir "figures"
   ```
3. **Run Statistical Tests** (from `research/`):
   ```powershell
   ..\backend\.venv\Scripts\python.exe statistical_analysis.py --raw-data "experiment_raw_data.json"
   ```
4. **Optional Slice Analysis** (from `research/`):
   ```powershell
   ..\backend\.venv\Scripts\python.exe slice_analysis.py --raw-data "experiment_raw_data.json" --dataset "datasets/eval_qa.jsonl" --variant "A5" --output "slice_analysis_A5.json"
   ```

## Notes

- Keep this folder focused on reproducible evaluation artifacts rather than app-runtime utilities.
- Non-research scripts such as general ingestion/debug helpers should live under `backend/` or dedicated utility folders instead.
