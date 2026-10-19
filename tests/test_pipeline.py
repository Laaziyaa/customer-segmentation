"""
Tests for clustering evaluation metrics, data filtering, and customer lookups.
"""

from app.services.data_manager import data_manager


def test_evaluation_metrics():
    eval_res = data_manager._compute_or_load_evaluation()
    assert eval_res is not None
    assert "silhouette" in eval_res
    assert "davies_bouldin" in eval_res
    assert "calinski_harabasz" in eval_res
    assert "elbow_curve" in eval_res

    assert -1.0 <= eval_res["silhouette"] <= 1.0
    assert eval_res["davies_bouldin"] >= 0.0
    assert eval_res["calinski_harabasz"] > 0.0
    assert len(eval_res["elbow_curve"]) >= 4


def test_customer_filtering_and_pagination():
    res = data_manager.get_customers(page=1, page_size=10, min_age=30, max_age=40)
    assert res is not None
    assert "items" in res
    assert "total" in res
    assert len(res["items"]) <= 10

    for customer in res["items"]:
        assert 30 <= customer["age"] <= 40


def test_customer_details_lookup():
    first_customer = data_manager.df.iloc[0]
    c_id = int(first_customer["customer_id"])

    detail = data_manager.get_customer_details(c_id)
    assert detail is not None
    assert detail["cluster"] == int(first_customer["cluster"])
    assert "persona" in detail
    assert "explanation" in detail
    assert len(detail["explanation"]) > 0
