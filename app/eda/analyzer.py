from pathlib import Path

import pandas as pd


class EDAAnalyzer:

    def __init__(self, dataframe):
        self.df = dataframe

    def dataset_info(self):

        print("=" * 60)
        print("DATASET INFORMATION")
        print("=" * 60)

        print(f"\nShape : {self.df.shape}")

        print("\nMissing Values")
        print(self.df.isnull().sum())

        print("\nData Types")
        print(self.df.dtypes)

    def numerical_summary(self):

        print("\n" + "=" * 60)
        print("NUMERICAL SUMMARY")
        print("=" * 60)

        print(self.df.describe())

    def categorical_summary(self):

        print("\n" + "=" * 60)
        print("CATEGORICAL SUMMARY")
        print("=" * 60)

        categorical = self.df.select_dtypes(include="object")

        for column in categorical.columns:

            print(f"\n{column}")

            print(categorical[column].value_counts())

    def correlation_matrix(self):

        print("\n" + "=" * 60)
        print("CORRELATION MATRIX")
        print("=" * 60)

        numeric = self.df.select_dtypes(include=["int64", "float64"])

        print(numeric.corr().round(2))

    def outlier_report(self):

        print("\n" + "=" * 60)
        print("OUTLIER REPORT")
        print("=" * 60)

        numeric = self.df.select_dtypes(include=["int64", "float64"])

        for column in numeric.columns:

            q1 = numeric[column].quantile(0.25)
            q3 = numeric[column].quantile(0.75)

            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outliers = numeric[
                (numeric[column] < lower)
                | (numeric[column] > upper)
            ]

            print(f"{column:<30}{len(outliers)}")