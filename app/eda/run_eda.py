from pathlib import Path

import pandas as pd

from .analyzer import EDAAnalyzer
from .visualizer import EDAVisualizer


def main():

    project_root = Path(__file__).resolve().parents[2]

    dataset = (
        project_root
        / "data"
        / "processed"
        / "enhanced_bank_dataset.csv"
    )

    df = pd.read_csv(dataset)

    analyzer = EDAAnalyzer(df)

    analyzer.dataset_info()

    analyzer.numerical_summary()

    analyzer.categorical_summary()

    analyzer.correlation_matrix()

    analyzer.outlier_report()

    print("\nGenerating visualizations...")

    visualizer = EDAVisualizer(df)

    visualizer.age_distribution()

    visualizer.income_distribution()

    visualizer.credit_score_distribution()

    visualizer.balance_distribution()

    visualizer.digital_score_distribution()

    visualizer.products_distribution()

    visualizer.job_distribution()

    visualizer.target_distribution()

    visualizer.correlation_heatmap()

    visualizer.boxplots()

    print("Visualizations saved successfully.")


if __name__ == "__main__":
    main()