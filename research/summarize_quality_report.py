import argparse
import json
import csv
from pathlib import Path


def pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.0%"
    return f"{(100.0 * numerator / denominator):.1f}%"


def format_failure_counts(failure_counts: dict) -> str:
    if not failure_counts:
        return "none"
    parts = [f"{k}={v}" for k, v in sorted(failure_counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    return ", ".join(parts)


def build_markdown_summary(report: dict) -> str:
    run_config = report.get("run_config", {})
    overall = report.get("overall", {})
    per_variant = report.get("per_variant", {})

    dataset_items_total = int(overall.get("dataset_items_total", 0))
    variants_count = int(overall.get("variants_count", 0))
    overall_status_counts = overall.get("status_counts", {})
    overall_failure_counts = overall.get("failure_reason_counts", {})

    lines = []
    lines.append("# Reliability And Coverage Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append(f"- generated_at_utc: `{report.get('generated_at_utc', 'unknown')}`")
    lines.append(f"- api_base: `{run_config.get('api_base', 'unknown')}`")
    lines.append(f"- dataset: `{run_config.get('dataset', 'unknown')}`")
    lines.append(f"- max_items: `{run_config.get('max_items', 'unknown')}`")
    lines.append(f"- seed: `{run_config.get('seed', 'unknown')}`")
    lines.append(f"- request_retries: `{run_config.get('request_retries', 'unknown')}`")
    lines.append(f"- judge_retries: `{run_config.get('judge_retries', 'unknown')}`")
    lines.append("")

    lines.append("## Overall Reliability")
    lines.append(f"- dataset_items_total: `{dataset_items_total}`")
    lines.append(f"- variants_count: `{variants_count}`")
    lines.append(f"- status_counts: `{overall_status_counts}`")
    lines.append(f"- failure_reason_counts: `{overall_failure_counts}`")
    lines.append("")

    lines.append("## Per-Variant Coverage Table")
    lines.append("")
    lines.append("| Variant | Dataset N | Recorded | Completed (ok) | Coverage | Chat Failed | Judge Failed |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    # Stable sorting A0..A5 style
    for variant_id in sorted(per_variant.keys()):
        stats = per_variant[variant_id]
        dataset_n = int(stats.get("dataset_items_total", 0))
        recorded = int(stats.get("items_with_record", 0))
        completed = int(stats.get("completed_ok", 0))
        chat_failed = int(stats.get("chat_failed", 0))
        judge_failed = int(stats.get("judge_failed", 0))
        lines.append(
            f"| {variant_id} | {dataset_n} | {recorded} | {completed} | {pct(completed, dataset_n)} | {chat_failed} | {judge_failed} |"
        )

    lines.append("")
    lines.append("## Per-Variant Failure Reasons")
    for variant_id in sorted(per_variant.keys()):
        failure_counts = per_variant[variant_id].get("failure_reason_counts", {})
        lines.append(f"- {variant_id}: {format_failure_counts(failure_counts)}")
    lines.append("")

    return "\n".join(lines)


def build_csv_rows(report: dict):
    per_variant = report.get("per_variant", {})
    rows = []
    for variant_id in sorted(per_variant.keys()):
        stats = per_variant[variant_id]
        dataset_n = int(stats.get("dataset_items_total", 0))
        completed = int(stats.get("completed_ok", 0))
        rows.append(
            {
                "variant_id": variant_id,
                "dataset_items_total": dataset_n,
                "items_with_record": int(stats.get("items_with_record", 0)),
                "completed_ok": completed,
                "coverage_ok_ratio": stats.get("coverage_ok_ratio", 0.0),
                "coverage_ok_percent": pct(completed, dataset_n),
                "chat_failed": int(stats.get("chat_failed", 0)),
                "judge_failed": int(stats.get("judge_failed", 0)),
                "failure_reasons": format_failure_counts(stats.get("failure_reason_counts", {})),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Summarize experiment_quality_report.json into a paper-ready markdown table."
    )
    parser.add_argument("--input", required=True, help="Path to quality report JSON.")
    parser.add_argument(
        "--output",
        default="quality_summary.md",
        help="Path to output markdown summary file.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "markdown":
        md = build_markdown_summary(report)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(md)
    else:
        rows = build_csv_rows(report)
        fieldnames = [
            "variant_id",
            "dataset_items_total",
            "items_with_record",
            "completed_ok",
            "coverage_ok_ratio",
            "coverage_ok_percent",
            "chat_failed",
            "judge_failed",
            "failure_reasons",
        ]
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"Wrote quality summary to: {output_path}")


if __name__ == "__main__":
    main()
