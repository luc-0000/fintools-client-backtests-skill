#!/usr/bin/env python
# encoding=utf8

"""
FastAPI Application Entry Point

This is a FastAPI version of the Flask application.
It demonstrates how to migrate from Flask to FastAPI using the get_pool endpoint as an example.

To run this application:
    uvicorn end_points.main:app --reload --port 8000

Or:
    python -m uvicorn end_points.main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from end_points.config.global_var import global_var
from end_points.config.routes import register_routes
from end_points.init_global import init_global


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    try:
        init_success = init_global(config_file)
        if not init_success:
            logging.warning("Global initialization completed with warnings")
    except Exception as e:
        logging.error(f"Could not initialize global variables: {e}")
        logging.warning("Some features may not work correctly")

    yield

    # Shutdown
    db = global_var.get("db")
    if db is not None:
        try:
            db.session.close()
            logging.info("Database session closed")
        except Exception as e:
            logging.error(f"Error closing database session: {e}")


# Create FastAPI app
app = FastAPI(
    title="AI Money API (FastAPI Version)",
    description="FastAPI version of the AI Money backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Load configuration
env_dist = os.environ
config_file = env_dist.get('CFG_PATH', '../service.conf')

# Configure logging
LOG_FORMAT = '%(asctime)s %(levelname)s FastAPI %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    log_line = f'request {request.client.host} {request.method} {request.url.scheme} {request.url.path} {response.status_code} {process_time:.3f}s'
    logging.info(log_line)

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "FAILURE",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


# Register all routes
register_routes(app, api_version="api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Money FastAPI Server",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if global_var.get("db") else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "end_points.main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )