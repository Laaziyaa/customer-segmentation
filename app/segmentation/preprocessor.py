from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class DataPreprocessor:

    def __init__(self, dataframe):
        self.df = dataframe

    def preprocess(self):

        # Features to be used for clustering
        features = [
            "age",
            "job",
            "marital",
            "education",
            "housing",
            "loan",
            "annual_income",
            "credit_score",
            "account_balance",
            "digital_banking_score",
            "monthly_transactions",
            "investment_amount",
            "account_tenure",
            "number_of_products"
        ]

        X = self.df[features].copy()

        # Fill missing categorical values
        categorical_columns = [
            "job",
            "marital",
            "education",
            "housing",
            "loan"
        ]

        for column in categorical_columns:
            X[column] = X[column].fillna("Unknown")

        # Numerical features
        numerical_features = [
            "age",
            "annual_income",
            "credit_score",
            "account_balance",
            "digital_banking_score",
            "monthly_transactions",
            "investment_amount",
            "account_tenure",
            "number_of_products"
        ]

        # Categorical features
        categorical_features = [
            "job",
            "marital",
            "education",
            "housing",
            "loan"
        ]

        # Numerical preprocessing
        numerical_pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler())
            ]
        )

        # Categorical preprocessing
        categorical_pipeline = Pipeline(
            steps=[
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False
                    )
                )
            ]
        )

        # Combine preprocessing
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "numerical",
                    numerical_pipeline,
                    numerical_features
                ),
                (
                    "categorical",
                    categorical_pipeline,
                    categorical_features
                )
            ]
        )

        # Transform data
        X_processed = preprocessor.fit_transform(X)

        print("\nPreprocessing Complete")
        print(f"Original Features : {X.shape[1]}")
        print(f"Processed Features : {X_processed.shape[1]}")

        return X_processed, preprocessor