from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class EDAVisualizer:

    def __init__(self, dataframe):

        self.df = dataframe

        self.output_dir = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "outputs"
            / "plots"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        sns.set_style("whitegrid")

    def save_plot(self, filename):

        plt.tight_layout()

        plt.savefig(
            self.output_dir / filename,
            dpi=300
        )

        plt.close()

    def age_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.histplot(
            self.df["age"],
            bins=25,
            kde=True
        )

        plt.title("Age Distribution")
        plt.xlabel("Age")
        plt.ylabel("Count")

        self.save_plot("age_distribution.png")

    def income_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.histplot(
            self.df["annual_income"],
            bins=30,
            kde=True
        )

        plt.title("Annual Income Distribution")
        plt.xlabel("Annual Income")
        plt.ylabel("Count")

        self.save_plot("income_distribution.png")

    def credit_score_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.histplot(
            self.df["credit_score"],
            bins=25,
            kde=True
        )

        plt.title("Credit Score Distribution")
        plt.xlabel("Credit Score")
        plt.ylabel("Count")

        self.save_plot("credit_score_distribution.png")

    def balance_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.histplot(
            self.df["account_balance"],
            bins=30,
            kde=True
        )

        plt.title("Account Balance Distribution")
        plt.xlabel("Account Balance")
        plt.ylabel("Count")

        self.save_plot("account_balance_distribution.png")

    def correlation_heatmap(self):

        plt.figure(figsize=(14, 10))

        correlation = self.df.select_dtypes(
            include=["int64", "float64"]
        ).corr()

        sns.heatmap(
            correlation,
            annot=True,
            cmap="coolwarm",
            fmt=".2f"
        )

        plt.title("Correlation Heatmap")

        self.save_plot("correlation_heatmap.png")

    def job_distribution(self):

        plt.figure(figsize=(10, 6))

        self.df["job"].value_counts().plot(
            kind="bar"
        )

        plt.title("Job Distribution")
        plt.xlabel("Job")
        plt.ylabel("Count")

        plt.xticks(rotation=45)

        self.save_plot("job_distribution.png")

    def digital_score_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.histplot(
            self.df["digital_banking_score"],
            bins=20,
            kde=True
        )

        plt.title("Digital Banking Score Distribution")
        plt.xlabel("Digital Banking Score")
        plt.ylabel("Count")

        self.save_plot("digital_score_distribution.png")

    def products_distribution(self):

        plt.figure(figsize=(8, 5))

        sns.countplot(
            x="number_of_products",
            data=self.df
        )

        plt.title("Products per Customer")
        plt.xlabel("Number of Products")
        plt.ylabel("Customers")

        self.save_plot("products_distribution.png")

    def target_distribution(self):

        plt.figure(figsize=(6, 5))

        sns.countplot(
            x="y",
            data=self.df
        )

        plt.title("Term Deposit Subscription")
        plt.xlabel("Subscribed")
        plt.ylabel("Customers")

        self.save_plot("target_distribution.png")

    def boxplots(self):

        columns = [
            "annual_income",
            "credit_score",
            "account_balance",
            "investment_amount"
        ]

        for column in columns:

            plt.figure(figsize=(8, 4))

            sns.boxplot(
                x=self.df[column]
            )

            plt.title(f"{column} Boxplot")

            self.save_plot(f"{column}_boxplot.png")

    