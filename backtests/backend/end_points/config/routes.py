"""
FastAPI Routes Registration

This module centralizes all route registrations for the FastAPI application.
"""

from fastapi import FastAPI

from end_points.get_pool.get_pool_routes import router as pool_router
from end_points.get_stock.get_stock_routes import router as stock_router
from end_points.get_rule.get_rule_routes import router as rule_router
from end_points.get_simulator.get_simulator_routes import router as simulator_router


def register_routes(app: FastAPI, api_version: str = "api/v1"):
    """
    Register all API routes to the FastAPI application

    Args:
        app: FastAPI application instance
        api_version: API version prefix (default: "api/v1")
    """
    prefix = f"/{api_version}"

    # Register pool routes
    app.include_router(
        pool_router,
        prefix=prefix,
        tags=["pool"]
    )

    # Register stock routes
    app.include_router(
        stock_router,
        prefix=prefix,
        tags=["stock"]
    )

    # Register rule routes
    app.include_router(
        rule_router,
        prefix=prefix,
        tags=["rule"]
    )

    # Register simulator routes
    app.include_router(
        simulator_router,
        prefix=prefix,
        tags=["simulator"]
    )
