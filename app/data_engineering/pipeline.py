from pathlib import Path

from .loader import DataLoader
from .validator import DataValidator
from .cleaner import DataCleaner
from .synthetic_features import SyntheticFeatureGenerator


def run_data_pipeline(raw_csv_path):
    """
    Runs the complete data engineering pipeline.

    Parameters:
        raw_csv_path (str | Path): Path to the raw CSV file.

    Returns:
        pandas.DataFrame: Processed dataframe.
    """

    print("=" * 60)
    print("CUSTOMER SEGMENTATION DATA PIPELINE")
    print("=" * 60)

    raw_csv_path = Path(raw_csv_path)

    # Initialize modules
    loader = DataLoader()
    validator = DataValidator()
    cleaner = DataCleaner()
    generator = SyntheticFeatureGenerator()

    # Step 1: Load dataset
    print("\n[1] Loading dataset...")
    df = loader.load_dataset(raw_csv_path)

    # Step 2: Validate dataset
    print("[2] Validating dataset...")
    validator.validate_columns(df)

    # Step 3: Clean dataset
    print("[3] Cleaning dataset...")
    df = cleaner.clean(df)

    # Step 4: Generate synthetic features
    print("[4] Generating synthetic banking features...")
    df = generator.generate(df)

    # Step 5: Dataset summary
    print("[5] Dataset Summary")

    cleaner.dataset_summary(df)

    numerical, categorical = cleaner.split_columns(df)

    print("\nNumerical Columns")
    print(numerical)

    print("\nCategorical Columns")
    print(categorical)

    from app.config import PROCESSED_DATA_DIR
    output_path = PROCESSED_DATA_DIR / "enhanced_bank_dataset.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print("\nEnhanced dataset saved successfully!")
    print(f"Location: {output_path}")

    print("\nPreview of Enhanced Dataset:")
    print(df.head())

    print("\n========== SYNTHETIC FEATURE SUMMARY ==========\n")

    print(df["annual_income"].describe())
    print()
    print(df["credit_score"].describe())
    print()
    print(df["account_balance"].describe())
    print()
    print(df["digital_banking_score"].describe())

    print("\nProducts Distribution")
    print(df["number_of_products"].value_counts().sort_index())

    print("\nTransactions Distribution")
    print(df["monthly_transactions"].describe())

    print("\nPipeline completed successfully.")
    print("=" * 60)

    return df


def main():
    from app.config import RAW_DATA_PATH
    run_data_pipeline(RAW_DATA_PATH)


if __name__ == "__main__":
    main()