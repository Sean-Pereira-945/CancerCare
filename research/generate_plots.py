import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import argparse

def generate_plots(csv_path: str, output_dir: str):
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: Could not find {csv_path}")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the CSV
    df = pd.read_csv(path)
    
    # We only want to plot if there is actual data.
    # Convert metric columns to numeric, replacing empty with NaN
    metrics = ['faithfulness', 'hallucination_rate', 'safety_violation_rate', 'citation_correctness']
    for m in metrics:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors='coerce')

    # Drop rows that don't have any metric data yet
    df_plot = df.dropna(subset=metrics, how='all').copy()

    if df_plot.empty:
        print("No numeric data found in the CSV. Run your experiment_runner.py first to populate results!")
        return

    # Set seaborn styling for publication-ready looks
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

    # 1. Main Metrics Comparison Bar Chart (Grouped)
    print("Generating comprehensive metrics plot...")
    plot_data = df_plot.melt(id_vars=['variant_id', 'variant_name'], 
                             value_vars=metrics, 
                             var_name='Metric', 
                             value_name='Score')
    
    # Clean up metric names for display
    plot_data['Metric'] = plot_data['Metric'].str.replace('_', ' ').str.title()
    
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(data=plot_data, x='variant_id', y='Score', hue='Metric', palette='viridis')
    plt.title('Performance Metrics Across System Variants', pad=20, fontsize=16, fontweight='bold')
    plt.xlabel('Variant ID')
    plt.ylabel('Score (0.0 to 1.0)')
    plt.ylim(0, 1.05)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add value annotations
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', padding=3, size=9)
        
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'comprehensive_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Safety vs Hallucination Trade-off Chart
    print("Generating safety vs hallucination plot...")
    plt.figure(figsize=(8, 6))
    
    sns.scatterplot(data=df_plot, 
                    x='hallucination_rate', 
                    y='safety_violation_rate', 
                    hue='variant_name',
                    s=200, 
                    palette='deep')
    
    # Annotate points
    for i in range(df_plot.shape[0]):
        plt.text(df_plot['hallucination_rate'].iloc[i] + 0.02, 
                 df_plot['safety_violation_rate'].iloc[i], 
                 df_plot['variant_id'].iloc[i], 
                 horizontalalignment='left', 
                 size='medium', color='black', weight='semibold')

    plt.title('Safety Violations vs Hallucination Rate (Lower is Better)', pad=15)
    plt.xlabel('Hallucination Rate')
    plt.ylabel('Safety Violation Rate')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'safety_hallucination_tradeoff.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Success! Plots generated in '{output_dir}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate publication plots from experiment CSV.")
    parser.add_argument("--csv", default="experiment_matrix.csv")
    parser.add_argument("--output-dir", default="figures")
    args = parser.parse_args()

    os.chdir(Path(__file__).parent)
    generate_plots(args.csv, args.output_dir)
