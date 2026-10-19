"""
Pydantic schemas defining the API contract for all endpoints.
Provides strong validation and clear serialization types.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ----------------------------------------------------
# Health & Status
# ----------------------------------------------------

class HealthResponse(BaseModel):
    status: str = Field(..., description="Server status, e.g. healthy")
    message: str = Field(..., description="Human-readable status notice")
    version: str = Field(default="2.0.0", description="API version")
    active_dataset_id: str = Field(..., description="Currently active dataset ID")
    total_customers: int = Field(default=0, description="Total customers in active dataset")
    total_segments: int = Field(default=0, description="Total active segments")
    last_updated: str = Field(..., description="ISO 8601 timestamp of last dataset refresh")


# ----------------------------------------------------
# Dynamic Schema Introspection
# ----------------------------------------------------

class SchemaField(BaseModel):
    name: str = Field(..., description="Technical feature name")
    label: str = Field(..., description="User-friendly display label")
    type: str = Field(..., description="'number' or 'select'")
    min: Optional[float] = Field(None, description="Minimum numeric value if applicable")
    max: Optional[float] = Field(None, description="Maximum numeric value if applicable")
    default: Union[float, str] = Field(..., description="Suggested default value (median/mode)")
    options: Optional[List[str]] = Field(None, description="Categorical options if type is select")
    mean: Optional[float] = Field(None, description="Population mean")
    std: Optional[float] = Field(None, description="Population standard deviation")
    is_synthetic: bool = Field(default=False, description="True if feature is synthetically augmented")


class DatasetSchemaResponse(BaseModel):
    dataset_id: str
    total_rows: int
    total_features: int
    fields: List[SchemaField]
    categorical_options: Dict[str, List[str]]
    synthetic_columns: List[str]


# ----------------------------------------------------
# Segments / Clusters
# ----------------------------------------------------

class SegmentItem(BaseModel):
    cluster: int
    persona: str
    customers: int
    percentage: float
    summary: str
    average_income: float
    average_balance: float
    average_credit_score: float
    average_digital_score: float
    average_transactions: float
    average_investment: float
    average_products: float
    recommended_products: List[str]


class SegmentsResponse(BaseModel):
    total_customers: int
    number_of_segments: int
    last_updated: str
    segments: List[SegmentItem]


# ----------------------------------------------------
# Customers Search, Filtering & Details
# ----------------------------------------------------

class CustomerListItem(BaseModel):
    customer_id: int
    cluster: int
    persona: Optional[str] = None
    age: int
    job: Optional[str] = None
    marital: Optional[str] = None
    education: Optional[str] = None
    housing: Optional[str] = None
    loan: Optional[str] = None
    annual_income: Optional[float] = None
    credit_score: Optional[float] = None
    account_balance: Optional[float] = None
    digital_banking_score: Optional[float] = None
    monthly_transactions: Optional[float] = None
    investment_amount: Optional[float] = None
    account_tenure: Optional[float] = None
    number_of_products: Optional[int] = None


class CustomersListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class FeatureComparison(BaseModel):
    feature: str
    label: str
    customer_value: str
    cluster_average: str
    direction: str
    diff_pct: float
    sentence: str


class CustomerDetailResponse(BaseModel):
    customer: Dict[str, Any]
    cluster: int
    persona: str
    recommendations: List[str]
    explanation: List[FeatureComparison]


# ----------------------------------------------------
# Live Scoring / Prediction
# ----------------------------------------------------

class CustomerInput(BaseModel):
    age: int = Field(default=35, ge=18, le=100)
    job: str = Field(default="admin.")
    marital: str = Field(default="married")
    education: str = Field(default="university.degree")
    housing: str = Field(default="yes")
    loan: str = Field(default="no")
    annual_income: float = Field(default=65000.0, ge=0)
    credit_score: float = Field(default=700.0, ge=300, le=850)
    account_balance: float = Field(default=25000.0, ge=0)
    digital_banking_score: float = Field(default=60.0, ge=0, le=100)
    monthly_transactions: float = Field(default=20.0, ge=0)
    investment_amount: float = Field(default=5000.0, ge=0)
    account_tenure: float = Field(default=5.0, ge=0)
    number_of_products: int = Field(default=2, ge=1, le=10)


class RecommendationItem(BaseModel):
    title: str
    category: str
    reason: str


class PredictResponse(BaseModel):
    predicted_cluster: int
    persona: str
    confidence: float
    reasons: List[str]
    recommendations: List[RecommendationItem]
    warnings: List[str]
    input_values: Dict[str, Any]


# ----------------------------------------------------
# Model Evaluation
# ----------------------------------------------------

class CurvePoint(BaseModel):
    k: int
    inertia: Optional[float] = None
    score: Optional[float] = None


class ModelEvaluationResponse(BaseModel):
    silhouette: float
    davies_bouldin: float
    calinski_harabasz: float
    optimal_k: int
    stability_score: float
    elbow_curve: List[Dict[str, Any]]
    silhouette_curve: List[Dict[str, Any]]
    metrics_explanation: Dict[str, str]


# ----------------------------------------------------
# EDA Metrics
# ----------------------------------------------------

class EDAResponse(BaseModel):
    metric: str
    data: Dict[str, Any]


# ----------------------------------------------------
# AI Assistant Chat
# ----------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    response: str
    execution_plan: List[str]
    results: Union[Dict[str, Any], List[Dict[str, Any]], List[Any]]


class ChatStatusResponse(BaseModel):
    configured: bool
    active_mode: str
    provider: str
    model: str
    message: str


class SetKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1)


class KeyActionResponse(BaseModel):
    success: bool
    message: str


class DatasetResetResponse(BaseModel):
    success: bool
    message: str
    total_rows: int


# ----------------------------------------------------
# Dataset Upload & Background Pipeline
# ----------------------------------------------------

class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    sample_rows: int
    total_columns: int
    detected_numerical: List[str]
    detected_categorical: List[str]
    suggested_k: int
    message: str


class TrainRequest(BaseModel):
    dataset_id: str
    k: Optional[int] = Field(default=None, ge=2, le=12)


class PipelineStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    started_at: Optional[str] = None