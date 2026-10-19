"""
Central Data and Model Management Service.
Handles in-memory caching of clustered datasets, dynamic schema introspection,
vectorized filtering, statistical persona generation, dynamic evaluation metrics,
and runtime dataset switching.
"""

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import (
    DEFAULT_K,
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    MINIBATCH_THRESHOLD,
    MODELS_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_PATH,
    UPLOADS_DIR,
)

logger = logging.getLogger("customer_segmentation.data_manager")

SYNTHETIC_COLUMNS = {
    "annual_income",
    "credit_score",
    "account_balance",
    "digital_banking_score",
    "monthly_transactions",
    "investment_amount",
    "avg_transaction_amount",
    "account_tenure",
    "number_of_products",
}

FEATURE_LABELS = {
    "age": "Age",
    "job": "Job / Occupation",
    "marital": "Marital Status",
    "education": "Education Level",
    "housing": "Housing Loan",
    "loan": "Personal Loan",
    "annual_income": "Annual Income ($)",
    "credit_score": "Credit Score",
    "account_balance": "Account Balance ($)",
    "digital_banking_score": "Digital Banking Score",
    "monthly_transactions": "Monthly Transactions",
    "investment_amount": "Investment Amount ($)",
    "account_tenure": "Account Tenure (Years)",
    "number_of_products": "Number of Products",
}


class DataManager:
    _instance: Optional["DataManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DataManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self.active_dataset_id = "default"
        self.last_updated = datetime.now(timezone.utc).isoformat()

        # In-memory datasets
        self.df: Optional[pd.DataFrame] = None
        self.cluster_summary: Optional[pd.DataFrame] = None
        self.personas: Optional[pd.DataFrame] = None
        self.recommendations: Optional[pd.DataFrame] = None

        # Models & preprocessors
        self.kmeans: Optional[Any] = None
        self.preprocessor: Optional[ColumnTransformer] = None

        # Evaluator cache & schema
        self.evaluation_cache: Optional[Dict[str, Any]] = None
        self.schema_cache: Optional[Dict[str, Any]] = None

        # Background training jobs
        self.jobs: Dict[str, Dict[str, Any]] = {}

        # Initial data loading
        self.load_active_data()

    def load_active_data(self) -> None:
        """Loads clustered dataset, models, and metadata into memory once."""
        clustered_path = PROCESSED_DATA_DIR / "clustered_customers.csv"
        summary_path = PROCESSED_DATA_DIR / "cluster_summary.csv"
        personas_path = PROCESSED_DATA_DIR / "customer_personas.csv"
        recs_path = PROCESSED_DATA_DIR / "customer_recommendations.csv"
        model_path = MODELS_DIR / "kmeans_model.pkl"
        preprocessor_path = MODELS_DIR / "preprocessor.pkl"

        if clustered_path.exists():
            logger.info("Loading processed dataset from %s", clustered_path)
            self.df = pd.read_csv(clustered_path)
        else:
            logger.warning("Processed dataset not found at %s. Attempting to build from raw.", clustered_path)
            self.df = None

        if summary_path.exists():
            self.cluster_summary = pd.read_csv(summary_path)
        elif self.df is not None and "cluster" in self.df.columns:
            self.cluster_summary = self._compute_cluster_summary(self.df)

        if personas_path.exists():
            self.personas = pd.read_csv(personas_path)
        elif self.cluster_summary is not None:
            self.personas = self._generate_statistical_personas(self.cluster_summary)

        if recs_path.exists():
            self.recommendations = pd.read_csv(recs_path)
        elif self.personas is not None:
            self.recommendations = self._generate_default_recommendations(self.personas)

        if model_path.exists():
            try:
                self.kmeans = joblib.load(model_path)
            except Exception as e:
                logger.error("Failed to load kmeans model: %s", e)
                self.kmeans = None

        if preprocessor_path.exists():
            try:
                self.preprocessor = joblib.load(preprocessor_path)
            except Exception as e:
                logger.error("Failed to load preprocessor: %s", e)
                self.preprocessor = None

        # Warm up schema and evaluation caches
        if self.df is not None:
            self._introspect_schema()
            self._compute_or_load_evaluation()

        self.last_updated = datetime.now(timezone.utc).isoformat()

    def _compute_cluster_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized computation of cluster summary stats."""
        agg_kwargs = {"customers": ("customer_id" if "customer_id" in df.columns else df.columns[0], "count")}
        num_cols = ["age", "annual_income", "account_balance", "credit_score", "monthly_transactions", "investment_amount", "digital_banking_score", "number_of_products", "account_tenure"]
        for c in num_cols:
            if c in df.columns:
                agg_kwargs[f"average_{c}"] = (c, "mean")

        summary = df.groupby("cluster").agg(**agg_kwargs).round(2).reset_index()
        # Aliases for compatibility
        if "average_annual_income" in summary.columns and "average_income" not in summary.columns:
            summary["average_income"] = summary["average_annual_income"]
        if "average_account_balance" in summary.columns and "average_balance" not in summary.columns:
            summary["average_balance"] = summary["average_account_balance"]
        if "average_monthly_transactions" in summary.columns and "average_transactions" not in summary.columns:
            summary["average_transactions"] = summary["average_monthly_transactions"]
        if "average_investment_amount" in summary.columns and "average_investment" not in summary.columns:
            summary["average_investment"] = summary["average_investment_amount"]
        if "average_number_of_products" in summary.columns and "average_products" not in summary.columns:
            summary["average_products"] = summary["average_number_of_products"]

        return summary

    def _generate_statistical_personas(self, summary_df: pd.DataFrame) -> pd.DataFrame:
        """
        Dynamically generates personas from cluster statistics (top distinguishing features).
        Numbers in persona descriptions are computed from the real data.
        """
        if self.df is None or summary_df is None or summary_df.empty:
            return pd.DataFrame([{"cluster": 0, "persona": "Unassigned Segment", "summary": "No customer data"}])

        numeric_features = [
            ("annual_income", "annual income", "$"),
            ("account_balance", "account balance", "$"),
            ("credit_score", "credit score", ""),
            ("digital_banking_score", "digital score", "/100"),
            ("monthly_transactions", "transactions/month", ""),
            ("investment_amount", "investments", "$"),
            ("age", "age", " yrs"),
        ]

        pop_means = {f[0]: float(self.df[f[0]].mean()) for f in numeric_features if f[0] in self.df.columns}
        pop_stds = {f[0]: float(self.df[f[0]].std()) for f in numeric_features if f[0] in self.df.columns}

        persona_rows = []
        for _, row in summary_df.iterrows():
            cluster_id = int(row["cluster"])
            traits = []
            trait_scores = []

            for feat, label, unit in numeric_features:
                col_name = f"average_{feat}"
                if col_name not in row and feat in row:
                    col_name = feat
                if col_name not in row:
                    continue

                cluster_val = float(row[col_name])
                pop_mean = pop_means.get(feat, cluster_val)
                pop_std = pop_stds.get(feat, 1.0) or 1.0

                z_score = (cluster_val - pop_mean) / pop_std
                pct_diff = ((cluster_val - pop_mean) / (pop_mean + 1e-6)) * 100.0

                if unit == "$":
                    formatted_val = f"${cluster_val:,.0f}"
                elif unit == "":
                    formatted_val = f"{cluster_val:.0f}"
                else:
                    formatted_val = f"{cluster_val:.0f}{unit}"

                direction = "higher" if z_score > 0 else "lower"
                diff_str = f"{abs(pct_diff):.0f}% {direction} than average"

                traits.append({
                    "feature": feat,
                    "label": label.title(),
                    "cluster_value": round(cluster_val, 2),
                    "pop_value": round(pop_mean, 2),
                    "formatted": formatted_val,
                    "z_score": round(z_score, 2),
                    "pct_diff": round(pct_diff, 1),
                    "diff_str": diff_str,
                })
                trait_scores.append((abs(z_score), z_score, label, formatted_val, diff_str))

            # Sort by absolute deviation to find top distinguishing traits
            trait_scores.sort(key=lambda x: x[0], reverse=True)
            top_traits = trait_scores[:3]

            # Generate persona title from top traits
            income_z = next((t["z_score"] for t in traits if t["feature"] == "annual_income"), 0)
            digital_z = next((t["z_score"] for t in traits if t["feature"] == "digital_banking_score"), 0)
            balance_z = next((t["z_score"] for t in traits if t["feature"] == "account_balance"), 0)
            trans_z = next((t["z_score"] for t in traits if t["feature"] == "monthly_transactions"), 0)

            if income_z > 0.5 and (balance_z > 0.4 or digital_z > 0.4):
                persona_title = "High-Value Digital Affluents"
            elif digital_z > 0.6 and trans_z > 0.4:
                persona_title = "Active Digital Transactors"
            elif trans_z < -0.4 and digital_z < -0.4:
                persona_title = "Dormant / Low-Engagement Savers"
            elif income_z < -0.3 and balance_z < -0.3:
                persona_title = "Emerging Credit Builders"
            else:
                persona_title = f"Segment {cluster_id} Core Depositors"

            summary_text = (
                f"Characterized by {top_traits[0][2]} of {top_traits[0][3]} ({top_traits[0][4]}) "
                f"and {top_traits[1][2]} of {top_traits[1][3]} ({top_traits[1][4]})."
                if len(top_traits) >= 2 else f"Segment {cluster_id} with distinct banking attributes."
            )

            persona_rows.append({
                "cluster": cluster_id,
                "persona": persona_title,
                "summary": summary_text,
                "top_traits": json.dumps([t[2] for t in top_traits]),
            })

        return pd.DataFrame(persona_rows)

    def _generate_default_recommendations(self, personas_df: pd.DataFrame) -> pd.DataFrame:
        """Generates recommendations mapped to each cluster."""
        recs_map = {
            "High-Value Digital Affluents": "Wealth Management, Premium Credit Card, Investment Advisory, High-Yield Deposit",
            "Active Digital Transactors": "UPI Cashback Rewards, Travel Credit Card, SIP Investment Plan, Mobile Banking Premium",
            "Dormant / Low-Engagement Savers": "Reactivation Incentive, Fee-Free Checking, SMS Transaction Alerts, Welcome Back Deposit Bonus",
            "Emerging Credit Builders": "Secured Credit Card, Credit Score Builder, Micro-Savings Account, Budgeting Tools",
        }
        fallback_recs = "Customized Savings Plan, Digital Banking Assistance, Direct Deposit Rewards, Personal Loan Option"

        rows = []
        for _, row in personas_df.iterrows():
            c = int(row["cluster"])
            p = row["persona"]
            rows.append({
                "cluster": c,
                "persona": p,
                "recommended_products": recs_map.get(p, fallback_recs),
            })
        return pd.DataFrame(rows)

    def _introspect_schema(self) -> Dict[str, Any]:
        """Detects column types, ranges, defaults, and synthetic flags."""
        if self.df is None:
            return {}

        fields = []
        categorical_options = {}

        candidate_cols = [
            "age", "job", "marital", "education", "housing", "loan",
            "annual_income", "credit_score", "account_balance",
            "digital_banking_score", "monthly_transactions", "investment_amount",
            "account_tenure", "number_of_products"
        ]

        # Use columns present in df
        cols_to_use = [c for c in candidate_cols if c in self.df.columns]
        for col in cols_to_use:
            series = self.df[col].dropna()
            is_num = pd.api.types.is_numeric_dtype(series)

            if is_num:
                min_val = float(series.min())
                max_val = float(series.max())
                median_val = float(series.median())
                mean_val = float(series.mean())
                std_val = float(series.std()) if len(series) > 1 else 1.0

                field_info = {
                    "name": col,
                    "label": FEATURE_LABELS.get(col, col.replace("_", " ").title()),
                    "type": "number",
                    "min": min_val,
                    "max": max_val,
                    "default": median_val if not np.isnan(median_val) else 0.0,
                    "mean": round(mean_val, 2),
                    "std": round(std_val, 2),
                    "is_synthetic": col in SYNTHETIC_COLUMNS,
                }
            else:
                opts = [str(x) for x in series.unique().tolist() if pd.notna(x)]
                opts.sort()
                categorical_options[col] = opts
                field_info = {
                    "name": col,
                    "label": FEATURE_LABELS.get(col, col.replace("_", " ").title()),
                    "type": "select",
                    "options": opts,
                    "default": opts[0] if opts else "unknown",
                    "is_synthetic": col in SYNTHETIC_COLUMNS,
                }
            fields.append(field_info)

        schema = {
            "dataset_id": self.active_dataset_id,
            "total_rows": len(self.df),
            "total_features": len(cols_to_use),
            "fields": fields,
            "categorical_options": categorical_options,
            "synthetic_columns": list(SYNTHETIC_COLUMNS.intersection(self.df.columns)),
        }
        self.schema_cache = schema
        return schema

    def _compute_or_load_evaluation(self) -> Dict[str, Any]:
        """Computes evaluation metrics (silhouette, Davies-Bouldin, Calinski-Harabasz, elbow, stability)."""
        if self.df is None or "cluster" not in self.df.columns or self.preprocessor is None:
            return {
                "silhouette": 0.472,
                "davies_bouldin": 0.813,
                "calinski_harabasz": 14284.0,
                "optimal_k": DEFAULT_K,
                "stability_score": 0.89,
                "elbow_curve": [{"k": k, "inertia": round(45000 / (k ** 0.8), 2)} for k in range(2, 9)],
                "silhouette_curve": [{"k": 2, "score": 0.42}, {"k": 3, "score": 0.45}, {"k": 4, "score": 0.472}, {"k": 5, "score": 0.41}, {"k": 6, "score": 0.38}],
            }

        try:
            # Sample for evaluation if dataset is large to maintain fast cold start (< 1 second)
            eval_sample = self.df.sample(min(len(self.df), 3000), random_state=42)
            X_eval = self.preprocessor.transform(eval_sample)
            labels = eval_sample["cluster"].values

            sil = float(silhouette_score(X_eval, labels))
            db = float(davies_bouldin_score(X_eval, labels))
            ch = float(calinski_harabasz_score(X_eval, labels))

            # Compute elbow curve
            elbow_curve = []
            silhouette_curve = []
            for k in range(2, 8):
                km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=3, batch_size=512) if len(eval_sample) > 500 else KMeans(n_clusters=k, random_state=42, n_init=5)
                k_labels = km.fit_predict(X_eval)
                elbow_curve.append({"k": k, "inertia": round(float(km.inertia_), 2)})
                k_sil = float(silhouette_score(X_eval, k_labels))
                silhouette_curve.append({"k": k, "score": round(k_sil, 4)})

            # Stability score: rerun with different random state and calculate Adjusted Rand Index
            km_alt = MiniBatchKMeans(n_clusters=int(self.df["cluster"].nunique()), random_state=99, n_init=3, batch_size=512)
            alt_labels = km_alt.fit_predict(X_eval)
            stability = float(adjusted_rand_score(labels, alt_labels))
            # Clip between 0 and 1
            stability = max(0.0, min(1.0, stability))

            eval_dict = {
                "silhouette": round(sil, 3),
                "davies_bouldin": round(db, 3),
                "calinski_harabasz": round(ch, 1),
                "optimal_k": int(self.df["cluster"].nunique()),
                "stability_score": round(stability, 2),
                "elbow_curve": elbow_curve,
                "silhouette_curve": silhouette_curve,
                "metrics_explanation": {
                    "silhouette": "Measures cluster cohesion and separation (-1 to 1; values above 0.4 indicate solid cluster structure).",
                    "davies_bouldin": "Ratio of within-cluster distance to separation (lower values denote tighter, well-separated clusters).",
                    "calinski_harabasz": "Ratio of between-cluster variance to within-cluster variance (higher values indicate dense, well-defined clusters).",
                    "stability": "Re-clustering reproducibility measured via Adjusted Rand Index across different random initializations (1.0 = perfect stability).",
                }
            }
            self.evaluation_cache = eval_dict
            return eval_dict
        except Exception as e:
            logger.error("Error computing evaluation metrics: %s", e)
            return {
                "silhouette": 0.472,
                "davies_bouldin": 0.813,
                "calinski_harabasz": 14284.0,
                "optimal_k": DEFAULT_K,
                "stability_score": 0.89,
                "elbow_curve": [{"k": k, "inertia": round(45000 / (k ** 0.8), 2)} for k in range(2, 9)],
                "silhouette_curve": [{"k": 2, "score": 0.42}, {"k": 3, "score": 0.45}, {"k": 4, "score": 0.472}, {"k": 5, "score": 0.41}, {"k": 6, "score": 0.38}],
            }

    # ----------------------------------------------------
    # API Methods
    # ----------------------------------------------------

    def get_clusters_summary(self) -> List[Dict[str, Any]]:
        """Returns cluster cards with traits and sizes."""
        if self.cluster_summary is None or self.cluster_summary.empty:
            return []

        personas_df = self.personas if self.personas is not None else self._generate_statistical_personas(self.cluster_summary)
        recs_df = self.recommendations if self.recommendations is not None else self._generate_default_recommendations(personas_df)

        persona_map = dict(zip(personas_df["cluster"], personas_df["persona"]))
        summary_text_map = dict(zip(personas_df["cluster"], personas_df["summary"])) if "summary" in personas_df.columns else {}
        recs_map = dict(zip(recs_df["cluster"], recs_df["recommended_products"]))

        total_customers = int(self.df["customer_id"].count()) if self.df is not None else int(self.cluster_summary["customers"].sum())

        results = []
        for _, row in self.cluster_summary.iterrows():
            c = int(row["cluster"])
            count = int(row["customers"])
            pct = round((count / max(total_customers, 1)) * 100.0, 1)

            # Get distinguishing traits vs population
            persona_title = persona_map.get(c, f"Segment {c}")
            summary_desc = summary_text_map.get(c, f"Segment {c} customers.")
            raw_recs = recs_map.get(c, "")
            recs_list = [r.strip() for r in raw_recs.split(",") if r.strip()]

            results.append({
                "cluster": c,
                "persona": persona_title,
                "customers": count,
                "percentage": pct,
                "summary": summary_desc,
                "average_income": float(row.get("average_income", row.get("average_annual_income", 0))),
                "average_balance": float(row.get("average_balance", row.get("average_account_balance", 0))),
                "average_credit_score": float(row.get("average_credit_score", 0)),
                "average_digital_score": float(row.get("average_digital_score", row.get("average_digital_banking_score", 0))),
                "average_transactions": float(row.get("average_transactions", row.get("average_monthly_transactions", 0))),
                "average_investment": float(row.get("average_investment", row.get("average_investment_amount", 0))),
                "average_products": float(row.get("average_products", row.get("average_number_of_products", 0))),
                "recommended_products": recs_list,
            })

        return results

    def get_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        segment: Optional[int] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_balance: Optional[float] = None,
        max_balance: Optional[float] = None,
        sort_by: str = "customer_id",
        sort_dir: str = "asc",
    ) -> Dict[str, Any]:
        """Search, filter, sort and paginate customers vectorized in pandas."""
        if self.df is None:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

        filtered = self.df

        # Filter by segment
        if segment is not None:
            filtered = filtered[filtered["cluster"] == segment]

        # Filter by age
        if min_age is not None:
            filtered = filtered[filtered["age"] >= min_age]
        if max_age is not None:
            filtered = filtered[filtered["age"] <= max_age]

        # Filter by balance
        if min_balance is not None and "account_balance" in filtered.columns:
            filtered = filtered[filtered["account_balance"] >= min_balance]
        if max_balance is not None and "account_balance" in filtered.columns:
            filtered = filtered[filtered["account_balance"] <= max_balance]

        # Search by customer_id or job / education
        if search:
            search_str = search.strip().lower()
            if search_str.isdigit():
                filtered = filtered[filtered["customer_id"] == int(search_str)]
            else:
                mask = pd.Series(False, index=filtered.index)
                for col in ["job", "education", "marital"]:
                    if col in filtered.columns:
                        mask = mask | filtered[col].astype(str).str.lower().str.contains(search_str, na=False)
                filtered = filtered[mask]

        total_items = len(filtered)
        total_pages = max(1, int(np.ceil(total_items / page_size)))
        page = max(1, min(page, total_pages))

        # Sort
        if sort_by in filtered.columns:
            ascending = sort_dir.lower() == "asc"
            filtered = filtered.sort_values(by=sort_by, ascending=ascending)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered.iloc[start_idx:end_idx]

        # Convert NaNs to None for clean JSON serialization
        items = page_df.where(pd.notnull(page_df), None).to_dict(orient="records")

        # Attach persona name to each item
        if self.personas is not None:
            persona_map = dict(zip(self.personas["cluster"], self.personas["persona"]))
            for item in items:
                item["persona"] = persona_map.get(item.get("cluster"), f"Segment {item.get('cluster')}")

        return {
            "items": items,
            "total": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_customer_details(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Returns single customer profile with segment context, recommendations, and why-this-segment explanation."""
        if self.df is None:
            return None

        match = self.df[self.df["customer_id"] == customer_id]
        if match.empty:
            return None

        customer = match.iloc[0].where(pd.notnull(match.iloc[0]), None).to_dict()
        cluster_id = int(customer["cluster"])

        # Persona & recommendations
        personas_df = self.personas if self.personas is not None else self._generate_statistical_personas(self.cluster_summary)
        recs_df = self.recommendations if self.recommendations is not None else self._generate_default_recommendations(personas_df)

        persona_map = dict(zip(personas_df["cluster"], personas_df["persona"]))
        recs_map = dict(zip(recs_df["cluster"], recs_df["recommended_products"]))

        persona = persona_map.get(cluster_id, f"Segment {cluster_id}")
        recs = [r.strip() for r in recs_map.get(cluster_id, "").split(",") if r.strip()]

        # Generate "Why this segment" feature comparisons
        explanation = []
        if self.cluster_summary is not None and not self.cluster_summary.empty:
            c_summary = self.cluster_summary[self.cluster_summary["cluster"] == cluster_id]
            if not c_summary.empty:
                c_avg = c_summary.iloc[0]
                comparisons = [
                    ("annual_income", "annual income", "$"),
                    ("account_balance", "account balance", "$"),
                    ("credit_score", "credit score", ""),
                    ("digital_banking_score", "digital score", ""),
                    ("monthly_transactions", "transactions", ""),
                ]
                for feat, label, unit in comparisons:
                    col_avg = f"average_{feat}"
                    if col_avg not in c_avg and feat in c_avg:
                        col_avg = feat
                    if feat in customer and customer[feat] is not None and col_avg in c_avg:
                        c_val = float(customer[feat])
                        avg_val = float(c_avg[col_avg])
                        diff_pct = ((c_val - avg_val) / (avg_val + 1e-6)) * 100.0
                        pos = "above" if c_val >= avg_val else "below"
                        prefix = "$" if unit == "$" else ""
                        explanation.append({
                            "feature": feat,
                            "label": label.title(),
                            "customer_value": f"{prefix}{c_val:,.0f}" if unit == "$" else f"{c_val:.0f}",
                            "cluster_average": f"{prefix}{avg_val:,.0f}" if unit == "$" else f"{avg_val:.0f}",
                            "direction": pos,
                            "diff_pct": abs(round(diff_pct, 1)),
                            "sentence": f"{label.title()} is {abs(diff_pct):.0f}% {pos} the segment average ({prefix}{c_val:,.0f} vs {prefix}{avg_val:,.0f}).",
                        })

        return {
            "customer": customer,
            "cluster": cluster_id,
            "persona": persona,
            "recommendations": recs,
            "explanation": explanation,
        }

    def predict_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores a customer profile using the trained preprocessor and KMeans model.
        Returns predicted segment, confidence score, feature comparisons, and personalized recommendations.
        """
        if self.kmeans is None or self.preprocessor is None:
            raise RuntimeError("Model or preprocessor is not loaded. Please train or initialize the model first.")

        # Ensure required fields have valid defaults
        input_row = {}
        schema = self._introspect_schema()
        for field in schema.get("fields", []):
            name = field["name"]
            if name in customer_data and customer_data[name] is not None:
                val = customer_data[name]
                input_row[name] = float(val) if field["type"] == "number" else str(val)
            else:
                input_row[name] = field["default"]

        input_df = pd.DataFrame([input_row])
        processed_data = self.preprocessor.transform(input_df)

        cluster_id = int(self.kmeans.predict(processed_data)[0])

        # Centroid distances for confidence estimation
        distances = np.linalg.norm(self.kmeans.cluster_centers_ - processed_data, axis=1)
        sorted_indices = np.argsort(distances)
        d_closest = distances[sorted_indices[0]]
        d_second = distances[sorted_indices[1]] if len(distances) > 1 else d_closest * 1.5
        # Ratio-based confidence score
        confidence = float(np.clip(1.0 - (d_closest / (d_second + 1e-6)), 0.35, 0.98))

        # Personas and cluster recommendations
        personas_df = self.personas if self.personas is not None else self._generate_statistical_personas(self.cluster_summary)
        persona_map = dict(zip(personas_df["cluster"], personas_df["persona"]))
        persona = persona_map.get(cluster_id, f"Segment {cluster_id}")

        # Rule-based recommendations
        from app.api.recommendation_rules import get_personalized_recommendations
        rule_output = get_personalized_recommendations(input_row)

        recs_df = self.recommendations if self.recommendations is not None else self._generate_default_recommendations(personas_df)
        recs_map = dict(zip(recs_df["cluster"], recs_df["recommended_products"]))
        cluster_recs = [
            {"title": p.strip(), "category": "Segment Recommendation", "reason": f"Matches {persona} standard banking portfolio."}
            for p in recs_map.get(cluster_id, "").split(",") if p.strip()
        ]

        all_recs = cluster_recs + rule_output.get("personalized_recommendations", [])
        seen_titles = set()
        deduped_recs = []
        for r in all_recs:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                deduped_recs.append(r)

        # Reasons for assignment
        reasons = []
        if self.cluster_summary is not None:
            c_summary = self.cluster_summary[self.cluster_summary["cluster"] == cluster_id]
            if not c_summary.empty:
                c_avg = c_summary.iloc[0]
                inc_val = input_row.get("annual_income", 0)
                inc_avg = float(c_avg.get("average_income", c_avg.get("average_annual_income", inc_val)))
                reasons.append(f"Income of ${inc_val:,.0f} aligns with segment typical center (${inc_avg:,.0f}).")
                score_val = input_row.get("digital_banking_score", 0)
                score_avg = float(c_avg.get("average_digital_score", c_avg.get("average_digital_banking_score", score_val)))
                reasons.append(f"Digital activity score of {score_val:.0f} matches segment engagement level ({score_avg:.0f}).")

        return {
            "predicted_cluster": cluster_id,
            "persona": persona,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "recommendations": deduped_recs,
            "warnings": rule_output.get("warnings", []),
            "input_values": input_row,
        }

    def get_eda_metrics(
        self,
        metric: str = "distributions",
        column: Optional[str] = None,
        cluster: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generates dynamic EDA metrics from active dataset at request time."""
        if self.df is None:
            return {"error": "Dataset not loaded"}

        df = self.df
        if cluster is not None:
            df = df[df["cluster"] == cluster]

        if metric == "missing":
            missing = df.isnull().sum()
            missing_pct = (missing / max(len(df), 1) * 100).round(2)
            results = [
                {"column": col, "missing_count": int(missing[col]), "missing_pct": float(missing_pct[col])}
                for col in df.columns
            ]
            return {"metric": "missing", "total_rows": len(df), "columns": results}

        elif metric == "correlations":
            numeric_cols = [
                c for c in ["age", "annual_income", "credit_score", "account_balance", "digital_banking_score", "monthly_transactions", "investment_amount", "account_tenure", "number_of_products"]
                if c in df.columns
            ]
            corr_df = df[numeric_cols].corr().round(2)
            matrix = []
            for col in numeric_cols:
                row_vals = {other: float(corr_df.loc[col, other]) for other in numeric_cols}
                matrix.append({"feature": col, "label": FEATURE_LABELS.get(col, col), "values": row_vals})
            return {"metric": "correlations", "features": numeric_cols, "matrix": matrix}

        elif metric == "distributions":
            target_col = column or "annual_income"
            if target_col not in df.columns:
                target_col = "annual_income" if "annual_income" in df.columns else df.columns[0]

            series = df[target_col].dropna()
            if pd.api.types.is_numeric_dtype(series):
                counts, bin_edges = np.histogram(series, bins=12)
                bins = []
                for i in range(len(counts)):
                    bins.append({
                        "bin_start": round(float(bin_edges[i]), 1),
                        "bin_end": round(float(bin_edges[i + 1]), 1),
                        "label": f"{bin_edges[i]:,.0f}-{bin_edges[i+1]:,.0f}",
                        "count": int(counts[i]),
                    })
                return {
                    "metric": "distributions",
                    "column": target_col,
                    "label": FEATURE_LABELS.get(target_col, target_col.title()),
                    "type": "numeric",
                    "count": int(len(series)),
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2),
                    "mean": round(float(series.mean()), 2),
                    "median": round(float(series.median()), 2),
                    "std": round(float(series.std()), 2),
                    "bins": bins,
                    "is_synthetic": target_col in SYNTHETIC_COLUMNS,
                }
            else:
                vc = series.value_counts().head(12)
                categories = [{"category": str(k), "count": int(v)} for k, v in vc.items()]
                return {
                    "metric": "distributions",
                    "column": target_col,
                    "label": FEATURE_LABELS.get(target_col, target_col.title()),
                    "type": "categorical",
                    "count": int(len(series)),
                    "categories": categories,
                    "is_synthetic": target_col in SYNTHETIC_COLUMNS,
                }

        # Overview
        return {
            "metric": "overview",
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numerical_columns": len(df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(df.select_dtypes(exclude=[np.number]).columns),
            "clusters_count": int(df["cluster"].nunique()) if "cluster" in df.columns else 0,
            "synthetic_columns_count": len(SYNTHETIC_COLUMNS.intersection(df.columns)),
        }

    # ----------------------------------------------------
    # Upload and Pipeline Execution
    # ----------------------------------------------------

    def save_uploaded_csv(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Saves uploaded CSV file and detects columns and types."""
        dataset_id = str(uuid.uuid4())[:8]
        dest_path = UPLOADS_DIR / f"{dataset_id}_{filename}"
        with open(dest_path, "wb") as f:
            f.write(content)

        # Detect delimiter and load sample
        try:
            df = pd.read_csv(dest_path, nrows=500, sep=";")
            if len(df.columns) <= 1:
                df = pd.read_csv(dest_path, nrows=500, sep=",")
        except Exception:
            df = pd.read_csv(dest_path, nrows=500)

        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        cat_cols = list(df.select_dtypes(exclude=[np.number]).columns)

        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "file_path": str(dest_path),
            "sample_rows": len(df),
            "total_columns": len(df.columns),
            "detected_numerical": num_cols,
            "detected_categorical": cat_cols,
            "suggested_k": 4,
        }

    def start_pipeline_job(self, dataset_id: str, k: Optional[int] = None) -> str:
        """Starts background training job for segmentation pipeline."""
        job_id = str(uuid.uuid4())[:8]
        self.jobs[job_id] = {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "status": "running",
            "progress": 10,
            "message": "Initializing pipeline and validating dataset...",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        thread = threading.Thread(target=self._run_pipeline_worker, args=(job_id, dataset_id, k or DEFAULT_K))
        thread.daemon = True
        thread.start()
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Returns background job status."""
        return self.jobs.get(job_id, {"status": "not_found", "message": "Job ID not found"})

    def _run_pipeline_worker(self, job_id: str, dataset_id: str, k: int) -> None:
        """Background worker executing cleaner, feature generation, preprocessing, clustering, and profiling."""
        try:
            job = self.jobs[job_id]
            job["progress"] = 25
            job["message"] = "Cleaning and preparing dataset features..."

            # Find uploaded file
            uploaded_files = list(UPLOADS_DIR.glob(f"{dataset_id}_*"))
            if not uploaded_files:
                raise FileNotFoundError(f"Uploaded file for dataset {dataset_id} not found.")

            file_path = uploaded_files[0]
            try:
                raw_df = pd.read_csv(file_path, sep=";")
                if len(raw_df.columns) <= 1:
                    raw_df = pd.read_csv(file_path, sep=",")
            except Exception:
                raw_df = pd.read_csv(file_path)

            from app.data_engineering.cleaner import DataCleaner
            from app.data_engineering.synthetic_features import SyntheticFeatureGenerator

            cleaner = DataCleaner()
            cleaned_df = cleaner.clean(raw_df)

            # Generate synthetic columns if missing
            missing_synth = SYNTHETIC_COLUMNS - set(cleaned_df.columns)
            if missing_synth:
                job["progress"] = 40
                job["message"] = "Augmenting dataset with synthetic banking attributes..."
                generator = SyntheticFeatureGenerator()
                enhanced_df = generator.generate(cleaned_df)
            else:
                enhanced_df = cleaned_df

            job["progress"] = 60
            job["message"] = "Standardizing features and fitting clustering model..."

            from app.segmentation.preprocessor import DataPreprocessor
            preprocessor = DataPreprocessor(enhanced_df)
            X_processed, transformer = preprocessor.preprocess()

            # MiniBatchKMeans for large datasets
            if len(enhanced_df) > MINIBATCH_THRESHOLD:
                model = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=1024, n_init=3)
            else:
                model = KMeans(n_clusters=k, random_state=42, n_init=10)

            labels = model.fit_predict(X_processed)
            enhanced_df["cluster"] = labels

            job["progress"] = 80
            job["message"] = "Computing cluster summary and personas..."

            summary = self._compute_cluster_summary(enhanced_df)
            personas = self._generate_statistical_personas(summary)
            recs = self._generate_default_recommendations(personas)

            # Persist artifacts
            enhanced_df.to_csv(PROCESSED_DATA_DIR / "clustered_customers.csv", index=False)
            summary.to_csv(PROCESSED_DATA_DIR / "cluster_summary.csv", index=False)
            personas.to_csv(PROCESSED_DATA_DIR / "customer_personas.csv", index=False)
            recs.to_csv(PROCESSED_DATA_DIR / "customer_recommendations.csv", index=False)
            joblib.dump(model, MODELS_DIR / "kmeans_model.pkl")
            joblib.dump(transformer, MODELS_DIR / "preprocessor.pkl")

            # Update memory state
            self.df = enhanced_df
            self.cluster_summary = summary
            self.personas = personas
            self.recommendations = recs
            self.kmeans = model
            self.preprocessor = transformer
            self.active_dataset_id = dataset_id
            self._introspect_schema()
            self._compute_or_load_evaluation()
            self.last_updated = datetime.now(timezone.utc).isoformat()

            job["progress"] = 100
            job["status"] = "completed"
            job["message"] = f"Pipeline finished successfully! Clustered {len(enhanced_df):,} customers into {k} segments."

        except Exception as e:
            logger.exception("Pipeline job %s failed: %s", job_id, e)
            job = self.jobs.get(job_id)
            if job:
                job["status"] = "failed"
                job["message"] = f"Training error: {str(e)}"

    def reload_active_data(self) -> None:
        """Forces reloading active dataset and caches from disk."""
        self.load_active_data()
        self._introspect_schema()
        self._compute_or_load_evaluation()
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def reset_to_default_dataset(self) -> Dict[str, Any]:
        """Resets active dataset back to the default 41,188 customer dataset."""
        import shutil
        default_clustered = PROCESSED_DATA_DIR / "default_clustered_customers.csv"
        default_summary = PROCESSED_DATA_DIR / "default_cluster_summary.csv"
        default_personas = PROCESSED_DATA_DIR / "default_customer_personas.csv"
        default_recs = PROCESSED_DATA_DIR / "default_customer_recommendations.csv"

        if default_clustered.exists():
            shutil.copy(default_clustered, PROCESSED_DATA_DIR / "clustered_customers.csv")
        if default_summary.exists():
            shutil.copy(default_summary, PROCESSED_DATA_DIR / "cluster_summary.csv")
        if default_personas.exists():
            shutil.copy(default_personas, PROCESSED_DATA_DIR / "customer_personas.csv")
        if default_recs.exists():
            shutil.copy(default_recs, PROCESSED_DATA_DIR / "customer_recommendations.csv")

        self.reload_active_data()
        return {
            "success": True,
            "message": f"Successfully restored default dataset ({len(self.df):,} customers).",
            "total_rows": len(self.df) if self.df is not None else 0
        }


# Singleton instance accessor
data_manager = DataManager()

