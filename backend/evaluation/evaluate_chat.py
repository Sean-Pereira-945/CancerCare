import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import requests


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def safe_contains(text: str, snippets: List[str]) -> bool:
    lower = (text or "").lower()
    return any((s or "").lower()[:80] in lower for s in snippets)


def run_eval(api_base: str, token: str, dataset: Path, output: Path) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    items = load_jsonl(dataset)

    results = []
    for item in items:
        resp = requests.post(
            f"{api_base}/api/chat/message",
            headers=headers,
            json={
                "message": item["question"],
                "history": [],
                "use_report": True,
            },
            timeout=45,
        )
        row = {
            "item_id": item.get("item_id"),
            "status": resp.status_code,
            "response": "",
            "confidence": None,
            "response_mode": None,
            "sources_used": 0,
            "evidence_overlap": False,
        }

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("reply", "")
            row.update(
                {
                    "response": answer,
                    "confidence": data.get("confidence"),
                    "response_mode": data.get("response_mode"),
                    "sources_used": data.get("sources_used", 0),
                    "evidence_overlap": safe_contains(answer, item.get("gold_evidence", [])),
                }
            )

        results.append(row)

    ok = [r for r in results if r["status"] == 200]
    evidence_hits = [r for r in ok if r["evidence_overlap"]]
    abstains = [r for r in ok if r.get("response_mode") == "abstain"]

    summary = {
        "total": len(results),
        "http_200_rate": round(len(ok) / len(results), 4) if results else 0.0,
        "evidence_overlap_rate": round(len(evidence_hits) / len(ok), 4) if ok else 0.0,
        "abstain_rate": round(len(abstains) / len(ok), 4) if ok else 0.0,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate chat endpoint against JSONL QA set.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--token", required=True, help="Bearer token for authenticated calls")
    parser.add_argument("--dataset", default="research/datasets/eval_qa.jsonl")
    parser.add_argument("--output", default="research/results/eval_run.json")
    args = parser.parse_args()

    summary = run_eval(
        api_base=args.api_base,
        token=args.token,
        dataset=Path(args.dataset),
        output=Path(args.output),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
