from pathlib import Path

import pandas as pd


class ClusterProfiler:

    def __init__(self):

        self.project_root = Path(__file__).resolve().parents[2]

        self.output_dir = (
            self.project_root
            / "data"
            / "processed"
        )

    def profile(self, df):

        print("=" * 60)
        print("CLUSTER PROFILING")
        print("=" * 60)

        summary = (
            df.groupby("cluster")
            .agg(
                customers=("customer_id", "count"),
                average_age=("age", "mean"),
                average_income=("annual_income", "mean"),
                average_balance=("account_balance", "mean"),
                average_credit_score=("credit_score", "mean"),
                average_transactions=("monthly_transactions", "mean"),
                average_investment=("investment_amount", "mean"),
                average_digital_score=("digital_banking_score", "mean"),
                average_products=("number_of_products", "mean"),
            )
            .round(2)
        )

        print(summary)

        output_path = (
            self.output_dir
            / "cluster_summary.csv"
        )

        summary.to_csv(output_path)

        print(f"\nCluster summary saved to:\n{output_path}")

        return summary