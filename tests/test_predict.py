"""
Tests for customer scoring and prediction endpoint logic.
"""

from app.services.data_manager import data_manager


def test_predict_standard_customer():
    profile = {
        "age": 38,
        "job": "technician",
        "marital": "married",
        "education": "university.degree",
        "housing": "yes",
        "loan": "no",
        "annual_income": 85000.0,
        "credit_score": 730.0,
        "account_balance": 48000.0,
        "digital_banking_score": 75.0,
        "monthly_transactions": 30.0,
        "investment_amount": 15000.0,
        "account_tenure": 6.0,
        "number_of_products": 3,
    }

    result = data_manager.predict_customer(profile)
    assert result is not None
    assert "predicted_cluster" in result
    assert isinstance(result["predicted_cluster"], int)
    assert "persona" in result
    assert isinstance(result["persona"], str)

    # Check confidence score bounds
    assert 0.0 <= result["confidence"] <= 1.0

    # Check recommendations and reasons
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0

    assert "reasons" in result
    assert len(result["reasons"]) > 0


def test_predict_student_low_balance_warnings():
    profile = {
        "age": 21,
        "job": "student",
        "marital": "single",
        "education": "high.school",
        "housing": "no",
        "loan": "no",
        "annual_income": 18000.0,
        "credit_score": 610.0,
        "account_balance": 1500.0,
        "digital_banking_score": 85.0,
        "monthly_transactions": 12.0,
        "investment_amount": 0.0,
        "account_tenure": 1.0,
        "number_of_products": 1,
    }

    result = data_manager.predict_customer(profile)
    assert result is not None
    # Low credit score (<650) should trigger warning
    assert len(result["warnings"]) > 0
    # Should recommend student or credit builder products
    rec_titles = [r["title"] for r in result["recommendations"]]
    assert any("Student" in t or "Credit" in t or "Savings" in t for t in rec_titles)
