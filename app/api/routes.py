"""
FastAPI Route Handlers for Customer Segmentation Agent.
Implements unified API contract supporting all 8 frontend pages, backward-compatible aliases,
background pipeline training, and the AI agent chat interface.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStatusResponse,
    CustomerDetailResponse,
    CustomerInput,
    CustomersListResponse,
    DatasetResetResponse,
    DatasetSchemaResponse,
    EDAResponse,
    HealthResponse,
    KeyActionResponse,
    ModelEvaluationResponse,
    PipelineStatusResponse,
    PredictResponse,
    SegmentsResponse,
    SetKeyRequest,
    TrainRequest,
    UploadResponse,
)
from app.groq_service import (
    generate_chat_response,
    is_groq_configured,
    test_and_set_groq_key,
    clear_groq_key,
)
from app.services.data_manager import data_manager

logger = logging.getLogger("customer_segmentation.routes")
router = APIRouter()


# ----------------------------------------------------
# Health Check & Root Ping
# ----------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check & cold start ping"
)
@router.get("/api/health", response_model=HealthResponse, include_in_schema=False)
@router.get("/", response_model=HealthResponse, include_in_schema=False)
def get_health() -> HealthResponse:
    total_customers = len(data_manager.df) if data_manager.df is not None else 0
    total_segments = int(data_manager.df["cluster"].nunique()) if data_manager.df is not None and "cluster" in data_manager.df.columns else 0

    return HealthResponse(
        status="healthy",
        message="Customer Segmentation Agent API is operational.",
        version="2.0.0",
        active_dataset_id=data_manager.active_dataset_id,
        total_customers=total_customers,
        total_segments=total_segments,
        last_updated=data_manager.last_updated,
    )


# ----------------------------------------------------
# Dynamic Schema Introspection
# ----------------------------------------------------

@router.get(
    "/api/schema",
    response_model=DatasetSchemaResponse,
    tags=["Metadata"],
    summary="Get dynamic dataset schema for form building"
)
@router.get("/schema", response_model=DatasetSchemaResponse, include_in_schema=False)
def get_dataset_schema() -> DatasetSchemaResponse:
    schema = data_manager._introspect_schema()
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dataset schema is not ready yet. Server is still initializing."
        )
    return DatasetSchemaResponse(**schema)


# ----------------------------------------------------
# Segments / Clusters
# ----------------------------------------------------

@router.get(
    "/api/segments",
    response_model=SegmentsResponse,
    tags=["Segmentation"],
    summary="Customer segments with sizes, traits and recommendations"
)
@router.get("/segments", response_model=SegmentsResponse, include_in_schema=False)
@router.get("/clusters", response_model=SegmentsResponse, include_in_schema=False)
@router.get("/api/clusters", response_model=SegmentsResponse, include_in_schema=False)
def get_segments() -> SegmentsResponse:
    summary_list = data_manager.get_clusters_summary()
    total_customers = len(data_manager.df) if data_manager.df is not None else 0

    return SegmentsResponse(
        total_customers=total_customers,
        number_of_segments=len(summary_list),
        last_updated=data_manager.last_updated,
        segments=summary_list,
    )


@router.get("/personas", tags=["Compatibility"], include_in_schema=False)
@router.get("/api/personas", tags=["Compatibility"], include_in_schema=False)
def get_personas_compatibility():
    summary_list = data_manager.get_clusters_summary()
    return [{"cluster": s["cluster"], "persona": s["persona"]} for s in summary_list]


@router.get("/recommendations", tags=["Compatibility"], include_in_schema=False)
@router.get("/api/recommendations", tags=["Compatibility"], include_in_schema=False)
def get_recommendations_compatibility():
    summary_list = data_manager.get_clusters_summary()
    return [{"cluster": s["cluster"], "persona": s["persona"], "recommended_products": ", ".join(s["recommended_products"])} for s in summary_list]


# ----------------------------------------------------
# Customers Search, Filtering & Details
# ----------------------------------------------------

@router.get(
    "/api/customers",
    response_model=CustomersListResponse,
    tags=["Customers"],
    summary="Paginated customer directory with search and filters"
)
@router.get("/customers", response_model=CustomersListResponse, include_in_schema=False)
def get_customers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=5, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by ID or keywords"),
    segment: Optional[int] = Query(default=None, description="Filter by segment ID"),
    min_age: Optional[int] = Query(default=None, ge=18, le=100, description="Minimum age"),
    max_age: Optional[int] = Query(default=None, ge=18, le=100, description="Maximum age"),
    min_balance: Optional[float] = Query(default=None, description="Minimum balance"),
    max_balance: Optional[float] = Query(default=None, description="Maximum balance"),
    sort_by: str = Query(default="customer_id", description="Field to sort by"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort direction"),
) -> CustomersListResponse:
    res = data_manager.get_customers(
        page=page,
        page_size=page_size,
        search=search,
        segment=segment,
        min_age=min_age,
        max_age=max_age,
        min_balance=min_balance,
        max_balance=max_balance,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return CustomersListResponse(**res)


@router.get(
    "/api/customers/{customer_id}",
    response_model=CustomerDetailResponse,
    tags=["Customers"],
    summary="Single customer lookup with explainability"
)
@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse, include_in_schema=False)
def get_customer_by_id(customer_id: str) -> CustomerDetailResponse:
    try:
        numeric_id = int(customer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID must be a numeric integer."
        )

    res = data_manager.get_customer_details(numeric_id)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer #{customer_id} does not exist in the active dataset."
        )

    return CustomerDetailResponse(**res)


# ----------------------------------------------------
# Live Scoring / Prediction
# ----------------------------------------------------

@router.post(
    "/api/predict",
    response_model=PredictResponse,
    tags=["Scoring"],
    summary="Score a new customer profile"
)
@router.post("/predict", response_model=PredictResponse, include_in_schema=False)
def predict_new_customer(customer: CustomerInput) -> PredictResponse:
    try:
        res = data_manager.predict_customer(customer.model_dump())
        return PredictResponse(**res)
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model scoring failed: {str(e)}"
        )


# ----------------------------------------------------
# Model Evaluation
# ----------------------------------------------------

@router.get(
    "/api/model/evaluation",
    response_model=ModelEvaluationResponse,
    tags=["Evaluation"],
    summary="Clustering diagnostics (silhouette, Davies-Bouldin, Calinski-Harabasz, elbow curve)"
)
@router.get("/api/evaluation", response_model=ModelEvaluationResponse, include_in_schema=False)
@router.get("/charts", include_in_schema=False)
@router.get("/api/charts", include_in_schema=False)
def get_model_evaluation():
    eval_res = data_manager._compute_or_load_evaluation()
    return ModelEvaluationResponse(**eval_res)


# ----------------------------------------------------
# Data Insights / Request-time EDA
# ----------------------------------------------------

@router.get(
    "/api/eda",
    tags=["EDA"],
    summary="Dynamic EDA stats and distributions generated at request time"
)
def get_eda(
    metric: str = Query(default="distributions", pattern="^(distributions|missing|correlations|overview)$"),
    column: Optional[str] = Query(default=None),
    cluster: Optional[int] = Query(default=None),
):
    res = data_manager.get_eda_metrics(metric=metric, column=column, cluster=cluster)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res["error"])
    return res


# ----------------------------------------------------
# AI Assistant Chat
# ----------------------------------------------------

@router.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["AI Assistant"],
    summary="Ask questions using Groq LLM agent with plan inspection and fallback"
)
@router.post("/chat", response_model=ChatResponse, include_in_schema=False)
async def chat_assistant(request: ChatRequest) -> ChatResponse:
    try:
        chat_result = generate_chat_response(request.query)
        return ChatResponse(**chat_result)
    except Exception as e:
        logger.exception("Chat failed: %s", e)
        return ChatResponse(
            response="I encountered an issue processing your question. Please try rephrasing or check server logs.",
            execution_plan=[f"Error occurred: {str(e)}", "Provided generic fallback response"],
            results={}
        )


@router.get(
    "/api/chat/status",
    response_model=ChatStatusResponse,
    tags=["AI Assistant"],
    summary="Get active LLM status and configuration"
)
def get_chat_status() -> ChatStatusResponse:
    from app.config import GROQ_MODEL_NAME
    configured = is_groq_configured()
    return ChatStatusResponse(
        configured=configured,
        active_mode="groq" if configured else "rule_based",
        provider="Groq",
        model=GROQ_MODEL_NAME,
        message=(
            f"Groq LLM ({GROQ_MODEL_NAME}) is active and powering generative reasoning."
            if configured
            else "Local analytical agent active. Provide a Groq API key to activate generative reasoning."
        )
    )


@router.post(
    "/api/chat/key",
    response_model=KeyActionResponse,
    tags=["AI Assistant"],
    summary="Configure and verify Groq API key"
)
def set_chat_key(request: SetKeyRequest) -> KeyActionResponse:
    result = test_and_set_groq_key(request.api_key)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return KeyActionResponse(**result)


@router.delete(
    "/api/chat/key",
    response_model=KeyActionResponse,
    tags=["AI Assistant"],
    summary="Clear Groq API key and revert to analytical agent"
)
def remove_chat_key() -> KeyActionResponse:
    result = clear_groq_key()
    return KeyActionResponse(**result)


# ----------------------------------------------------
# Dataset Upload & Background Training
# ----------------------------------------------------

@router.post(
    "/api/datasets/upload",
    response_model=UploadResponse,
    tags=["Dataset"],
    status_code=status.HTTP_201_CREATED,
    summary="Upload new customer CSV and inspect schema"
)
@router.post("/api/upload", response_model=UploadResponse, include_in_schema=False)
@router.post("/upload", response_model=UploadResponse, include_in_schema=False)
async def upload_dataset_file(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported."
        )

    try:
        content = await file.read()
        res = data_manager.save_uploaded_csv(file.filename, content)
        return UploadResponse(
            dataset_id=res["dataset_id"],
            filename=res["filename"],
            sample_rows=res["sample_rows"],
            total_columns=res["total_columns"],
            detected_numerical=res["detected_numerical"],
            detected_categorical=res["detected_categorical"],
            suggested_k=res["suggested_k"],
            message="CSV validated successfully. Ready to trigger segmentation pipeline.",
        )
    except Exception as e:
        logger.exception("Upload processing failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process CSV file: {str(e)}"
        )


@router.post(
    "/api/datasets/train",
    response_model=PipelineStatusResponse,
    tags=["Dataset"],
    summary="Trigger clustering pipeline for uploaded dataset"
)
def train_dataset_pipeline(request: TrainRequest) -> PipelineStatusResponse:
    job_id = data_manager.start_pipeline_job(dataset_id=request.dataset_id, k=request.k)
    return PipelineStatusResponse(
        job_id=job_id,
        status="running",
        progress=10,
        message="Segmentation pipeline started in background.",
    )


@router.get(
    "/api/datasets/status/{job_id}",
    response_model=PipelineStatusResponse,
    tags=["Dataset"],
    summary="Poll status of background pipeline training"
)
def get_pipeline_job_status(job_id: str) -> PipelineStatusResponse:
    res = data_manager.get_job_status(job_id)
    if res.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found."
        )
    return PipelineStatusResponse(
        job_id=job_id,
        status=res.get("status", "unknown"),
        progress=res.get("progress", 0),
        message=res.get("message", ""),
        started_at=res.get("started_at"),
    )


@router.post(
    "/api/datasets/reset",
    response_model=DatasetResetResponse,
    tags=["Dataset"],
    summary="Reset active dataset back to the default 41,188 customer portfolio"
)
def reset_default_dataset() -> DatasetResetResponse:
    res = data_manager.reset_to_default_dataset()
    return DatasetResetResponse(**res)