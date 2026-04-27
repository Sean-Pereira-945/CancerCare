import argparse
import json
from pathlib import Path
from collections import defaultdict


METRICS = ["faithfulness", "hallucination", "safety_violation", "citation_correctness"]


def load_dataset_index(dataset_path: Path):
    index = {}
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            item_id = item.get("item_id")
            if item_id:
                index[item_id] = item
    return index


def main():
    parser = argparse.ArgumentParser(description="Compute per-question-type slice metrics from raw experiment output.")
    parser.add_argument("--raw-data", required=True, help="Path to experiment_raw_data JSON.")
    parser.add_argument("--dataset", required=True, help="Path to eval dataset JSONL.")
    parser.add_argument("--variant", default="A5", help="Variant ID to analyze.")
    parser.add_argument("--output", default="slice_analysis.json", help="Output JSON file.")
    args = parser.parse_args()

    raw_path = Path(args.raw_data)
    dataset_path = Path(args.dataset)
    if not raw_path.exists():
        raise SystemExit(f"Raw data not found: {raw_path}")
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    with raw_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if args.variant not in raw:
        raise SystemExit(f"Variant {args.variant} not found in raw data.")

    ds_index = load_dataset_index(dataset_path)
    by_slice = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    missing_or_failed = 0

    for row in raw[args.variant]:
        item_id = row.get("item_id")
        ds_item = ds_index.get(item_id)
        if not ds_item or row.get("status", "ok") != "ok":
            missing_or_failed += 1
            continue
        qtype = ds_item.get("question_type", "unknown")
        by_slice[qtype]["count"] += 1
        for m in METRICS:
            by_slice[qtype]["sums"][m] += float(row.get("metrics", {}).get(m, 0.0))

    result = {
        "variant": args.variant,
        "total_rows": len(raw[args.variant]),
        "missing_or_failed_rows": missing_or_failed,
        "slices": {},
    }
    for qtype, vals in sorted(by_slice.items()):
        c = vals["count"]
        result["slices"][qtype] = {
            "count": c,
            "metrics_mean": {m: (vals["sums"][m] / c if c else 0.0) for m in METRICS},
        }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote slice analysis to: {out_path}")


if __name__ == "__main__":
    main()
