import argparse
import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List
import requests
import time
from groq import Groq
import os

# Import metrics correctly relative to the execution path if needed, 
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

def update_csv(csv_path: Path, variant_id: str, results: Dict[str, float]):
    if not csv_path.exists():
        print(f"Warning: {csv_path} does not exist.")
        return
        
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["variant_id"] == variant_id:
                row["faithfulness"] = f"{results.get('faithfulness', 0):.3f}"
                row["hallucination_rate"] = f"{results.get('hallucination', 0):.3f}"
                row["safety_violation_rate"] = f"{results.get('safety_violation', 0):.3f}"
                row["citation_correctness"] = f"{results.get('citation_correctness', 0):.3f}"
            rows.append(row)
            
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def run_variant(api_base: str, token: str, variant: Dict[str, Any], dataset: List[Dict[str, Any]], groq_client: Groq) -> Dict[str, float]:
    headers = {"Authorization": f"Bearer {token}"}
    
    total_metrics = {
        "faithfulness": 0.0,
        "hallucination": 0.0,
        "safety_violation": 0.0,
        "citation_correctness": 0.0
    }
    
    raw_results = []
    
    valid_count = 0
    
    print(f"\nRunning variant {variant['id']} ({variant['name']})...")
    
    for item in dataset:
        payload = {
            "message": item["question"],
            "experiment_config": {
                "use_global_retrieval": variant["global"],
                "use_patient_retrieval": variant["patient"],
                "use_reranker": variant["reranker"],
                "use_uncertainty_gating": variant["gating"]
            }
        }
        
        try:
            resp = requests.post(f"{api_base}/api/chat/message", headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("reply", "")
                context = data.get("context", "")
                
                # Evaluate with LLM judge
                metrics = evaluate_response_with_llm(groq_client, item["question"], context, answer)
                
                raw_results.append({
                    "item_id": item.get("item_id", f"item_{valid_count}"),
                    "metrics": metrics
                })
                
                for k in total_metrics:
                    total_metrics[k] += metrics.get(k, 0.0)
                valid_count += 1
            else:
                print(f"Error {resp.status_code} on item {item.get('item_id')}")
        except Exception as e:
            print(f"Request failed: {e}")
            
        time.sleep(1) # rate limit mitigation
        
    if valid_count > 0:
        for k in total_metrics:
            total_metrics[k] /= valid_count
            
    return total_metrics, raw_results

def main():
    parser = argparse.ArgumentParser(description="Run ablation experiments for Oncology RAG.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--token", required=True, help="Bearer token for API")
    parser.add_argument("--dataset", default="../research/datasets/eval_qa.jsonl")
    parser.add_argument("--csv", default="../research/experiment_matrix.csv")
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
    csv_path = Path(args.csv)
    
    all_raw_data = {}
    
    for variant in VARIANTS:
        results, raw_results = run_variant(args.api_base, args.token, variant, dataset, groq_client)
        print(f"Results for {variant['id']}: {results}")
        update_csv(csv_path, variant["id"], results)
        all_raw_data[variant["id"]] = raw_results
        
    raw_out_path = Path("../research/experiment_raw_data.json")
    with raw_out_path.open("w", encoding="utf-8") as f:
        json.dump(all_raw_data, f, indent=2)
        
    print(f"\nExperiment complete. Results saved to {csv_path}")
    print(f"Raw data for statistical analysis saved to {raw_out_path}")

if __name__ == "__main__":
    main()
