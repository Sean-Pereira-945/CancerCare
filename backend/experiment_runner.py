import argparse
import json
import csv
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import time
import random
from collections import Counter
from datetime import datetime, timezone
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
# but assuming it's run from the backend directory:
from evaluation.metrics import evaluate_response_with_llm

VARIANTS = [
    {"id": "A0", "name": "Plain LLM", "global": False, "patient": False, "reranker": False, "gating": False},
    {"id": "A1", "name": "Generic RAG", "global": True, "patient": False, "reranker": False, "gating": False},
    {"id": "A2", "name": "Personalized RAG", "global": True, "patient": True, "reranker": False, "gating": False},
    {"id": "A3", "name": "Personalized RAG + Reranker", "global": True, "patient": True, "reranker": True, "gating": False},
    {"id": "A4", "name": "Personalized RAG + Gating", "global": True, "patient": True, "reranker": False, "gating": True},
    {"id": "A5", "name": "Full System", "global": True, "patient": True, "reranker": True, "gating": True},
]

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def save_json(path: Path, payload: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def load_existing_raw(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Warning: could not parse existing raw file at {path}: {e}")
        return {}

def normalize_failure_reason(row: Dict[str, Any]) -> str:
    status = row.get("status", "unknown")
    if status == "chat_failed":
        if "http_status" in row:
            return f"chat_http_{row.get('http_status')}"
        return row.get("error", "chat_failed_unknown")
    if status == "judge_failed":
        return "judge_failed"
    if status == "ok":
        return "ok"
    return status

def redact_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # Mask emails and likely bearer-like secrets in logs.
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", value)
    value = re.sub(r"\b(sk-[A-Za-z0-9_-]{10,}|Bearer\s+[A-Za-z0-9._-]{10,})\b", "[REDACTED_SECRET]", value)
    return value

def build_variant_quality(rows: List[Dict[str, Any]], dataset_ids: set) -> Dict[str, Any]:
    relevant = [r for r in rows if r.get("item_id") in dataset_ids]
    status_counts = Counter(r.get("status", "unknown") for r in relevant)
    failure_counts = Counter(normalize_failure_reason(r) for r in relevant if r.get("status") != "ok")
    total = len(dataset_ids)
    completed = status_counts.get("ok", 0)
    chat_failed = status_counts.get("chat_failed", 0)
    judge_failed = status_counts.get("judge_failed", 0)
    coverage = (completed / total) if total else 0.0
    return {
        "dataset_items_total": total,
        "items_with_record": len(relevant),
        "completed_ok": completed,
        "chat_failed": chat_failed,
        "judge_failed": judge_failed,
        "coverage_ok_ratio": round(coverage, 6),
        "status_counts": dict(status_counts),
        "failure_reason_counts": dict(failure_counts),
    }

def write_failure_log(path: Path, all_raw_data: Dict[str, List[Dict[str, Any]]], dataset_ids: set):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for variant_id, rows in all_raw_data.items():
            for row in rows:
                if row.get("item_id") not in dataset_ids:
                    continue
                if row.get("status") == "ok":
                    continue
                f.write(
                    json.dumps(
                        {
                            "variant_id": variant_id,
                            "item_id": row.get("item_id"),
                            "status": row.get("status"),
                            "failure_reason": normalize_failure_reason(row),
                            "http_status": row.get("http_status"),
                            "error": redact_text(row.get("error")),
                        },
                        ensure_ascii=True,
                    )
                    + "\n"
                )

def update_csv(csv_path: Path, variant_id: str, results: Dict[str, float]):
    fieldnames = ['variant_id', 'variant_name', 'faithfulness', 'hallucination_rate', 'safety_violation_rate', 'citation_correctness']
    rows = []
    
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Ensure we keep existing fieldnames if they differ
            current_fields = reader.fieldnames
            if current_fields:
                fieldnames = current_fields
            for row in reader:
                rows.append(row)
    
    # Update or add the current variant row
    updated = False
    for row in rows:
        if row.get("variant_id") == variant_id:
            row["faithfulness"] = f"{results.get('faithfulness', 0):.3f}"
            row["hallucination_rate"] = f"{results.get('hallucination', 0):.3f}"
            row["safety_violation_rate"] = f"{results.get('safety_violation', 0):.3f}"
            row["citation_correctness"] = f"{results.get('citation_correctness', 0):.3f}"
            updated = True
            break
            
    if not updated:
        rows.append({
            "variant_id": variant_id,
            "variant_name": variant_id, # Default name
            "faithfulness": f"{results.get('faithfulness', 0):.3f}",
            "hallucination_rate": f"{results.get('hallucination', 0):.3f}",
            "safety_violation_rate": f"{results.get('safety_violation', 0):.3f}",
            "citation_correctness": f"{results.get('citation_correctness', 0):.3f}"
        })
            
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def post_chat_with_retries(
    api_base: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: int,
    max_retries: int,
    retry_delay_seconds: float,
) -> Optional[requests.Response]:
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(f"{api_base}/api/chat/message", headers=headers, json=payload, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_s = retry_delay_seconds * (2 ** attempt)
                print(f"Chat API status {resp.status_code}. Retrying in {sleep_s:.1f}s...")
                time.sleep(sleep_s)
                continue
            return resp
        except Exception as e:
            if attempt < max_retries:
                sleep_s = retry_delay_seconds * (2 ** attempt)
                print(f"Chat request failed ({e}). Retrying in {sleep_s:.1f}s...")
                time.sleep(sleep_s)
                continue
            print(f"Chat request failed after retries: {e}")
            return None
    return None

def run_variant(
    api_base: str,
    token: str,
    variant: Dict[str, Any],
    dataset: List[Dict[str, Any]],
    groq_client: Groq,
    all_raw_data: Dict[str, List[Dict[str, Any]]],
    raw_out_path: Path,
    request_timeout: int,
    request_retries: int,
    judge_retries: int,
    retry_delay_seconds: float,
    sleep_seconds: float,
    judge_model: str,
) -> Dict[str, float]:
    headers = {"Authorization": f"Bearer {token}"}

    total_metrics = {
        "faithfulness": 0.0,
        "hallucination": 0.0,
        "safety_violation": 0.0,
        "citation_correctness": 0.0
    }

    raw_results = all_raw_data.setdefault(variant["id"], [])
    existing_item_ids = {row.get("item_id") for row in raw_results}

    attempted_count = 0
    chat_success_count = 0
    judged_count = 0

    # Recompute metric totals from already successful rows so resume is deterministic.
    for row in raw_results:
        if row.get("status") == "ok" and isinstance(row.get("metrics"), dict):
            for k in total_metrics:
                total_metrics[k] += float(row["metrics"].get(k, 0.0))
            judged_count += 1

    print(f"\nRunning variant {variant['id']} ({variant['name']})...")

    for item in dataset:
        item_id = item.get("item_id")
        if item_id in existing_item_ids:
            continue

        attempted_count += 1
        payload = {
            "message": item["question"],
            "experiment_config": {
                "use_global_retrieval": variant["global"],
                "use_patient_retrieval": variant["patient"],
                "use_reranker": variant["reranker"],
                "use_uncertainty_gating": variant["gating"]
            }
        }

        resp = post_chat_with_retries(
            api_base=api_base,
            headers=headers,
            payload=payload,
            timeout=request_timeout,
            max_retries=request_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        if not resp:
            raw_results.append({
                "item_id": item_id,
                "status": "chat_failed",
                "error": "request_failed_after_retries",
            })
            save_json(raw_out_path, all_raw_data)
            time.sleep(sleep_seconds)
            continue

        if resp.status_code != 200:
            raw_results.append({
                "item_id": item_id,
                "status": "chat_failed",
                "http_status": resp.status_code,
            })
            save_json(raw_out_path, all_raw_data)
            time.sleep(sleep_seconds)
            continue

        chat_success_count += 1
        data = resp.json()
        answer = data.get("reply", "")
        context = data.get("context", "")

        metrics = evaluate_response_with_llm(
            groq_client,
            item["question"],
            context,
            answer,
            judge_model=judge_model,
            max_retries=judge_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        if metrics is None:
            raw_results.append({
                "item_id": item_id,
                "status": "judge_failed",
            })
            save_json(raw_out_path, all_raw_data)
            time.sleep(sleep_seconds)
            continue

        raw_results.append({
            "item_id": item_id,
            "status": "ok",
            "metrics": metrics
        })
        for k in total_metrics:
            total_metrics[k] += metrics.get(k, 0.0)
        judged_count += 1

        save_json(raw_out_path, all_raw_data)
        time.sleep(sleep_seconds)

    if judged_count > 0:
        for k in total_metrics:
            total_metrics[k] /= judged_count

    total_metrics["attempted_count"] = attempted_count
    total_metrics["chat_success_count"] = chat_success_count
    total_metrics["judged_count"] = judged_count
    return total_metrics

def main():
    parser = argparse.ArgumentParser(description="Run ablation experiments for Oncology RAG.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--token", required=True, help="Bearer token for API")
    parser.add_argument("--dataset", default="../research/datasets/eval_qa.jsonl")
    parser.add_argument("--csv", default="../research/experiment_matrix.csv")
    parser.add_argument("--raw-out", default="../research/experiment_raw_data.json")
    parser.add_argument("--quality-report-out", default="../research/experiment_quality_report.json")
    parser.add_argument("--failure-log-out", default="../research/experiment_failures.jsonl")
    parser.add_argument(
        "--min-coverage-ok",
        type=float,
        default=0.0,
        help="Quality gate: minimum per-variant coverage_ok_ratio required (0.0 disables gate).",
    )
    parser.add_argument(
        "--judge-model",
        default="llama-3.3-70b-versatile",
        help="Judge model for evaluation (can differ from generation model).",
    )
    parser.add_argument("--max-items", type=int, default=0, help="Limit dataset size (0 = all).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for subsampling.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Delay between items.")
    parser.add_argument("--request-timeout", type=int, default=45)
    parser.add_argument("--request-retries", type=int, default=3)
    parser.add_argument("--judge-retries", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=2.0)
    parser.add_argument("--shuffle", action="store_true", help="Shuffle dataset before applying max-items.")
    args = parser.parse_args()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY environment variable not set. Evaluation will return default scores.")
        groq_client = None
    else:
        groq_client = Groq(api_key=api_key)

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        sys.exit(1)
        
    dataset = load_jsonl(dataset_path)
    if args.shuffle:
        rnd = random.Random(args.seed)
        rnd.shuffle(dataset)
    if args.max_items > 0:
        dataset = dataset[:args.max_items]
        print(f"Using subset size: {len(dataset)} (seed={args.seed}, shuffle={args.shuffle})")

    csv_path = Path(args.csv)
    raw_out_path = Path(args.raw_out)
    quality_report_path = Path(args.quality_report_out)
    failure_log_path = Path(args.failure_log_out)
    all_raw_data = load_existing_raw(raw_out_path)
    dataset_ids = {item.get("item_id") for item in dataset if item.get("item_id")}

    for variant in VARIANTS:
        results = run_variant(
            api_base=args.api_base,
            token=args.token,
            variant=variant,
            dataset=dataset,
            groq_client=groq_client,
            all_raw_data=all_raw_data,
            raw_out_path=raw_out_path,
            request_timeout=args.request_timeout,
            request_retries=args.request_retries,
            judge_retries=args.judge_retries,
            retry_delay_seconds=args.retry_delay_seconds,
            sleep_seconds=args.sleep_seconds,
            judge_model=args.judge_model,
        )
        print(f"Results for {variant['id']}: {results}")
        update_csv(csv_path, variant["id"], results)
        save_json(raw_out_path, all_raw_data)

    per_variant_quality = {}
    overall_status_counts = Counter()
    overall_failure_reasons = Counter()
    for variant in VARIANTS:
        vid = variant["id"]
        vq = build_variant_quality(all_raw_data.get(vid, []), dataset_ids)
        per_variant_quality[vid] = vq
        overall_status_counts.update(vq["status_counts"])
        overall_failure_reasons.update(vq["failure_reason_counts"])

    quality_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_config": {
            "api_base": args.api_base,
            "dataset": args.dataset,
            "csv": args.csv,
            "raw_out": args.raw_out,
            "seed": args.seed,
            "shuffle": args.shuffle,
            "max_items": args.max_items,
            "sleep_seconds": args.sleep_seconds,
            "request_timeout": args.request_timeout,
            "request_retries": args.request_retries,
            "judge_retries": args.judge_retries,
            "retry_delay_seconds": args.retry_delay_seconds,
            "min_coverage_ok": args.min_coverage_ok,
            "judge_model": args.judge_model,
        },
        "overall": {
            "dataset_items_total": len(dataset_ids),
            "variants_count": len(VARIANTS),
            "status_counts": dict(overall_status_counts),
            "failure_reason_counts": dict(overall_failure_reasons),
        },
        "per_variant": per_variant_quality,
    }
    save_json(quality_report_path, quality_report)
    write_failure_log(failure_log_path, all_raw_data, dataset_ids)

    if args.min_coverage_ok > 0:
        failing_variants = [
            vid for vid, stats in per_variant_quality.items()
            if float(stats.get("coverage_ok_ratio", 0.0)) < args.min_coverage_ok
        ]
        if failing_variants:
            print(
                f"Quality gate failed: coverage_ok_ratio < {args.min_coverage_ok} for variants: {', '.join(failing_variants)}"
            )
            sys.exit(2)

    print(f"\nExperiment complete. Results saved to {csv_path}")
    print(f"Raw data for statistical analysis saved to {raw_out_path}")
    print(f"Quality report saved to {quality_report_path}")
    print(f"Failure log saved to {failure_log_path}")

if __name__ == "__main__":
    main()
