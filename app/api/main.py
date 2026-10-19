"""
Customer Segmentation Agent - FastAPI Application Entrypoint.
Configures logging, strict secure CORS with credentials, and mounts the API router.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.api.routes import router
from app.services.data_manager import data_manager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("customer_segmentation.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Customer Segmentation API service...")
    logger.info("Allowed CORS origins: %s", CORS_ORIGINS)
    data_manager.load_active_data()
    logger.info(
        "Active dataset loaded: %s customers in %s segments.",
        len(data_manager.df) if data_manager.df is not None else 0,
        int(data_manager.df["cluster"].nunique()) if data_manager.df is not None and "cluster" in data_manager.df.columns else 0
    )
    yield
    logger.info("Shutting down Customer Segmentation API service...")


app = FastAPI(
    title="Customer Segmentation Intelligence API",
    description="Production-grade retail banking customer segmentation and AI analyst API.",
    version="2.0.0",
    lifespan=lifespan,
)

# Secure CORS: explicit origin list allows credentials safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)