"""
Agent tools interacting with the central DataManager.
Provides business-friendly analysis, segmentation summaries, customer lookups,
explainability, and retention strategies.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from app.services.data_manager import data_manager


def _get_df() -> pd.DataFrame:
    if data_manager.df is not None:
        return data_manager.df
    data_manager.load_active_data()
    return data_manager.df if data_manager.df is not None else pd.DataFrame()


def _get_summary() -> pd.DataFrame:
    if data_manager.cluster_summary is not None:
        return data_manager.cluster_summary
    return pd.DataFrame()


def _get_personas() -> pd.DataFrame:
    if data_manager.personas is not None:
        return data_manager.personas
    return pd.DataFrame()


def _get_recommendations() -> pd.DataFrame:
    if data_manager.recommendations is not None:
        return data_manager.recommendations
    return pd.DataFrame()


# ---------- EDA Tool ----------

def eda_tool(cluster: Optional[int] = None) -> Dict[str, Any]:
    """
    Performs exploratory data analysis.
    If cluster is provided, scopes the EDA to that cluster only.
    """
    df = _get_df()
    if df.empty:
        return {"error": "Dataset is not loaded."}

    if cluster is not None:
        df = df[df["cluster"] == cluster]

    numeric_cols = [
        c for c in [
            "age", "annual_income", "credit_score", "account_balance",
            "digital_banking_score", "monthly_transactions", "investment_amount",
            "account_tenure", "number_of_products"
        ] if c in df.columns
    ]

    return {
        "scope": "all_customers" if cluster is None else f"cluster_{cluster}",
        "row_count": len(df),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_stats": df[numeric_cols].describe().round(2).to_dict() if numeric_cols else {},
        "correlations": df[numeric_cols].corr().round(2).to_dict() if numeric_cols else {}
    }


# ---------- Segmentation Tool ----------

def segmentation_tool() -> Dict[str, Any]:
    """
    Returns business-friendly customer segment summaries by combining
    cluster statistics, persona names, customer counts, characteristics,
    and recommended banking products.
    """
    clusters = data_manager.get_clusters_summary()
    return {
        "number_of_segments": len(clusters),
        "segments": clusters
    }


# ---------- Customer Lookup Tool ----------

def get_customer_segment(customer_id: int) -> Dict[str, Any]:
    """
    Looks up a single customer's cluster, persona and profile.
    """
    res = data_manager.get_customer_details(customer_id)
    if res is None:
        return {"error": f"Customer {customer_id} not found."}
    return {
        "customer_id": customer_id,
        "cluster": res["cluster"],
        "persona": res["persona"],
        "profile": res["customer"],
        "recommendations": res["recommendations"],
    }


# ---------- Explainability Tool ----------

def explainability_tool(customer_id: int) -> Dict[str, Any]:
    """
    Explains why a customer belongs to their assigned cluster by comparing
    their key features against the cluster average.
    """
    res = data_manager.get_customer_details(customer_id)
    if res is None:
        return {"error": f"Customer {customer_id} not found."}

    sentences = [item["sentence"] for item in res.get("explanation", [])]
    return {
        "customer_id": customer_id,
        "cluster": res["cluster"],
        "persona": res["persona"],
        "explanation": sentences if sentences else ["Customer attributes align with segment centroid."]
    }


# ---------- Retention & Strategy Tool ----------

def retention_tool(cluster: Optional[int] = None) -> Dict[str, Any]:
    """
    Customer Strategy Tool.
    Identifies customers requiring retention efforts while recommending
    next-best banking actions such as upgrades and personalized engagement.
    """
    df = _get_df()
    if df.empty:
        return {"error": "Dataset is not loaded."}

    if cluster is not None:
        df = df[df["cluster"] == cluster]

    sample_size = min(len(df), 200)
    sample_df = df.sample(sample_size, random_state=42) if len(df) > sample_size else df

    strategies = []
    for _, row in sample_df.iterrows():
        c_id = int(row.get("customer_id", row.name))
        c_cluster = int(row.get("cluster", 0))

        risk_level = "Low"
        reasons = []
        next_actions = []

        if row.get("digital_banking_score", 50) < 40:
            risk_level = "High"
            reasons.append("Low digital banking engagement.")
            next_actions.append("Promote mobile banking onboarding incentives.")

        if row.get("monthly_transactions", 20) < 10:
            risk_level = "Medium"
            reasons.append("Infrequent monthly transaction activity.")
            next_actions.append("Offer cashback reward program.")

        if row.get("annual_income", 0) > 100000 and row.get("credit_score", 0) >= 740:
            next_actions.append("Eligible for Premium Wealth Management package.")

        strategies.append({
            "customer_id": c_id,
            "cluster": c_cluster,
            "risk_level": risk_level,
            "reasons": reasons if reasons else ["Customer demonstrates stable banking behavior."],
            "next_best_actions": next_actions if next_actions else ["Standard quarterly relationship check-in."]
        })

    high_risk_count = sum(1 for s in strategies if s["risk_level"] == "High")
    return {
        "strategy_type": "Customer Strategy",
        "scope": "all_customers" if cluster is None else f"cluster_{cluster}",
        "customers_analyzed": len(strategies),
        "high_risk_customers": high_risk_count,
        "customer_strategies": strategies[:50]
    }


# ---------- Feature Engineering Pipeline Tool ----------

def feature_engineering_tool() -> Dict[str, Any]:
    """
    Explains the feature engineering pipeline used before K-Means clustering.
    """
    return {
        "title": "Feature Engineering Pipeline",
        "input_features": [
            "Age", "Annual Income", "Credit Score", "Account Balance",
            "Digital Banking Score", "Monthly Transactions", "Investment Amount",
            "Account Tenure", "Number of Products"
        ],
        "transformations": [
            "Handled missing values with median imputation and categorical filling",
            "Extracted financial attributes and behavioral scores",
            "Scaled numerical features using StandardScaler",
            "One-hot encoded categorical attributes (job, marital, education, housing, loan)",
            "Trained K-Means / MiniBatchKMeans cluster model"
        ],
        "output": "K-Means cluster assignments with statistical persona profiling",
        "purpose": "Groups bank customers by transaction behavior, financial health, and digital adoption."
    }


def personas_tool() -> List[Dict[str, Any]]:
    """Returns personas for API response compatibility."""
    return data_manager.get_clusters_summary()


def recommendations_tool() -> List[Dict[str, Any]]:
    """Returns recommendations for API response compatibility."""
    personas = data_manager.get_clusters_summary()
    return [{"cluster": p["cluster"], "persona": p["persona"], "recommended_products": ", ".join(p["recommended_products"])} for p in personas]


def charts_tool() -> Dict[str, Any]:
    """Returns chart data for API response compatibility."""
    return {
        "clusters": data_manager.get_clusters_summary(),
        "evaluation": data_manager._compute_or_load_evaluation()
    }