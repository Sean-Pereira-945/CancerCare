import json
import math
import random
from pathlib import Path

def mcnemar_test(a_scores, b_scores):
    """
    Computes McNemar's test for paired binary data.
    a_scores and b_scores must be lists of 0.0 or 1.0 of the same length.
    """
    if len(a_scores) != len(b_scores):
        raise ValueError("Scores must have the same length")
        
    b = 0  # Variant A failed (0), Variant B passed (1)
    c = 0  # Variant A passed (1), Variant B failed (0)
    
    for score_a, score_b in zip(a_scores, b_scores):
        if score_a == 0.0 and score_b == 1.0:
            b += 1
        elif score_a == 1.0 and score_b == 0.0:
            c += 1
            
    if b + c == 0:
        return 0.0, 1.0  # Exact match, no difference, p=1.0
        
    chi_square = ((abs(b - c) - 1) ** 2) / (b + c)
    
    # Very rough approximation of p-value for 1 degree of freedom
    # For a rigorous paper, use scipy.stats.chi2.sf
    # Critical value for p=0.05 is ~3.84
    # Critical value for p=0.01 is ~6.63
    # Critical value for p=0.001 is ~10.83
    
    if chi_square > 10.83:
        p_val = "< 0.001"
    elif chi_square > 6.63:
        p_val = "< 0.01"
    elif chi_square > 3.84:
        p_val = "< 0.05"
    else:
        p_val = "> 0.05"
        
    return chi_square, p_val

def bootstrap_ci(a_scores, b_scores, iterations=10000, alpha=0.05):
    """
    Computes paired bootstrap confidence intervals for the mean difference.
    """
    diffs = [b - a for a, b in zip(a_scores, b_scores)]
    n = len(diffs)
    if n == 0:
        return 0.0, (0.0, 0.0)
        
    boot_means = []
    for _ in range(iterations):
        sample = [random.choice(diffs) for _ in range(n)]
        boot_means.append(sum(sample) / n)
        
    boot_means.sort()
    lower_idx = int((alpha / 2) * iterations)
    upper_idx = int((1 - alpha / 2) * iterations)
    
    mean_diff = sum(diffs) / n
    return mean_diff, (boot_means[lower_idx], boot_means[upper_idx])

def analyze_results(raw_data_file: str, base_variant="A1", compare_variant="A5"):
    path = Path(raw_data_file)
    if not path.exists():
        print(f"Error: Could not find raw data file at {raw_data_file}")
        print("Please run experiment_runner.py first to generate the data.")
        return

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if base_variant not in data or compare_variant not in data:
        print(f"Error: Missing data for {base_variant} or {compare_variant}")
        return

    base_items = {item["item_id"]: item["metrics"] for item in data[base_variant]}
    compare_items = {item["item_id"]: item["metrics"] for item in data[compare_variant]}

    # Align items
    common_ids = set(base_items.keys()).intersection(set(compare_items.keys()))
    if not common_ids:
        print("No overlapping items found to compare.")
        return
        
    print(f"=== Statistical Analysis: {base_variant} vs {compare_variant} ===")
    print(f"Sample Size (N) = {len(common_ids)}\n")

    metrics = ["faithfulness", "hallucination", "safety_violation", "citation_correctness"]

    for metric in metrics:
        base_scores = [base_items[iid].get(metric, 0.0) for iid in common_ids]
        compare_scores = [compare_items[iid].get(metric, 0.0) for iid in common_ids]
        
        # 1. Calculate basic difference
        base_mean = sum(base_scores) / len(base_scores)
        comp_mean = sum(compare_scores) / len(compare_scores)
        diff = comp_mean - base_mean
        
        print(f"--- Metric: {metric.upper()} ---")
        print(f"  {base_variant} Mean: {base_mean:.4f}")
        print(f"  {compare_variant} Mean: {comp_mean:.4f}")
        print(f"  Absolute Difference: {diff:+.4f}")
        
        # 2. Bootstrap CI
        mean_diff, (ci_low, ci_high) = bootstrap_ci(base_scores, compare_scores)
        print(f"  Bootstrap 95% CI of Difference: [{ci_low:+.4f}, {ci_high:+.4f}]")
        
        # 3. McNemar's Test
        # We assume scores are binary (1.0 or 0.0). If they aren't perfectly binary, 
        # we threshold them at 0.5 to behave like binary errors for McNemar.
        bin_base = [1.0 if s >= 0.5 else 0.0 for s in base_scores]
        bin_comp = [1.0 if s >= 0.5 else 0.0 for s in compare_scores]
        
        chi_sq, p_val = mcnemar_test(bin_base, bin_comp)
        
        print(f"  McNemar Test Chi-Square: {chi_sq:.2f}")
        print(f"  McNemar p-value: {p_val}")
        
        if p_val in ["< 0.05", "< 0.01", "< 0.001"]:
            print("  * Result is STATISTICALLY SIGNIFICANT")
        else:
            print("  * Result is NOT statistically significant")
        print()

if __name__ == "__main__":
    RAW_DATA_FILE = "experiment_raw_data.json"
    
    # Ensure working directory is research folder
    os_path = Path(__file__).parent
    import os
    os.chdir(os_path)
    
    # Typical research ablation: compare Generic RAG (A1) vs Full System (A5)
    analyze_results(RAW_DATA_FILE, base_variant="A1", compare_variant="A5")
    
    # You can also compare Ablations, e.g. A2 vs A4 to isolate the effect of gating
    # analyze_results(RAW_DATA_FILE, base_variant="A2", compare_variant="A4")
