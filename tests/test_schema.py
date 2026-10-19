"""
Tests for dynamic schema detection and feature metadata.
"""

from app.services.data_manager import data_manager, SYNTHETIC_COLUMNS


def test_schema_introspection_fields():
    schema = data_manager._introspect_schema()
    assert schema is not None
    assert "fields" in schema
    assert len(schema["fields"]) > 0

    field_names = [f["name"] for f in schema["fields"]]
    assert "age" in field_names
    assert "annual_income" in field_names
    assert "credit_score" in field_names
    assert "account_balance" in field_names
    assert "digital_banking_score" in field_names


def test_schema_types_and_defaults():
    schema = data_manager._introspect_schema()
    fields_by_name = {f["name"]: f for f in schema["fields"]}

    # Age should be number with realistic min/max
    age_field = fields_by_name["age"]
    assert age_field["type"] == "number"
    assert age_field["min"] >= 15
    assert age_field["max"] <= 120

    # Job should be select with options
    job_field = fields_by_name["job"]
    assert job_field["type"] == "select"
    assert isinstance(job_field["options"], list)
    assert len(job_field["options"]) > 1

    # Synthetic flag test
    income_field = fields_by_name["annual_income"]
    assert income_field["is_synthetic"] is True
    assert "annual_income" in SYNTHETIC_COLUMNS
