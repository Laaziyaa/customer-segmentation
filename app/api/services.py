from pathlib import Path
import pandas as pd
from .recommendation_rules import get_personalized_recommendations

class CustomerService:

    def __init__(self):

        import joblib

        self.project_root = Path(__file__).resolve().parents[2]

        processed_path = (
            self.project_root
            / "data"
            / "processed"
        )

        self.cluster_summary = pd.read_csv(
            processed_path / "cluster_summary.csv"
        )

        self.personas = pd.read_csv(
            processed_path / "customer_personas.csv"
        )

        self.recommendations = pd.read_csv(
            processed_path / "customer_recommendations.csv"
        )

        self.customers = pd.read_csv(
            processed_path / "clustered_customers.csv"
        )

        model_path = (
            self.project_root
            / "data"
            / "models"
        )

        self.preprocessor = joblib.load(
            model_path / "preprocessor.pkl"
        )

        self.kmeans = joblib.load(
            model_path / "kmeans_model.pkl"
        )

    def get_clusters(self):

        return self.cluster_summary.to_dict(
            orient="records"
        )

    def get_personas(self):

        return self.personas.to_dict(
            orient="records"
        )

    def get_recommendations(self):

        return self.recommendations.to_dict(
            orient="records"
        )

    def get_customer(self, customer_id):

        customer_id = int(customer_id)

        customer = self.customers[
            self.customers["customer_id"] == customer_id
        ]

        if customer.empty:
            return None

        customer = customer.iloc[0].to_dict()

        # Convert NaN values to None (valid JSON)
        customer = {
            key: (
                None if pd.isna(value) else value
            )
            for key, value in customer.items()
        }

        cluster = customer["cluster"]

        persona = self.personas[
            self.personas["cluster"] == cluster
        ].iloc[0]["persona"]

        recommendations = self.recommendations[
            self.recommendations["cluster"] == cluster
        ].iloc[0]["recommended_products"]

        return {
            "customer": customer,
            "persona": persona,
            "recommendations": recommendations
        }

    def predict_customer(self, customer_data):

        input_df = pd.DataFrame([customer_data])

        processed_data = self.preprocessor.transform(input_df)

        cluster = int(
            self.kmeans.predict(processed_data)[0]
        )

        persona = self.personas[
            self.personas["cluster"] == cluster
        ].iloc[0]["persona"]

        cluster_products = [
        {
            "title": product.strip(),
            "category": "Cluster Recommendation",
            "reason": f"Recommended because you belong to the '{persona}' customer segment."
        }
        for product in self.recommendations[
            self.recommendations["cluster"] == cluster
        ].iloc[0]["recommended_products"].split(", ")]

        rule_output = get_personalized_recommendations(customer_data)

        all_recommendations = (
            cluster_products +
            rule_output["personalized_recommendations"]
        )

        seen = set()
        final_recommendations = []

        for recommendation in all_recommendations:
            if recommendation["title"] not in seen:
                seen.add(recommendation["title"])
                final_recommendations.append(recommendation)

        return {
        "predicted_cluster": cluster,
        "persona": persona,
        "recommendations": final_recommendations,
        "warnings": rule_output["warnings"]
        }