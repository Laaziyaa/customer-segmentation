from typing import Tuple

import numpy as np
import pandas as pd


class DataCleaner:

    def clean(self, dataframe: pd.DataFrame) -> pd.DataFrame:

        df = dataframe.copy()

        print("\nCleaning dataset...")

        # Replace "unknown" with NaN
        df.replace("unknown", np.nan, inplace=True)

        # Remove duration (data leakage)
        if "duration" in df.columns:
            df.drop(columns=["duration"], inplace=True)

        # Remove duplicate rows
        duplicates = df.duplicated().sum()

        print(f"Potential duplicate rows: {duplicates}")
        print("Keeping duplicates because the dataset has no customer ID.")

        print("Cleaning complete.")

        return df

    def split_columns(
        self,
        dataframe: pd.DataFrame
    ) -> Tuple[list, list]:

        numerical = dataframe.select_dtypes(
            include=["int64", "float64"]
        ).columns.tolist()

        categorical = dataframe.select_dtypes(
            include=["object"]
        ).columns.tolist()

        return numerical, categorical

    def dataset_summary(
        self,
        dataframe: pd.DataFrame
    ):

        print("\nDataset Shape")
        print(dataframe.shape)

        print("\nMissing Values")

        print(dataframe.isnull().sum())

        print("\nData Types")

        print(dataframe.dtypes)