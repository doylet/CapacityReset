"""
FastAPI Jobs API - Application Entry Point

Single responsibility: Application setup and configuration.
All routing logic separated into api/routes.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import jobs_router, skills_router, lexicon_router, clusters_router


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Responsibilities:
    - Application initialization
    - Middleware configuration
    - Router registration
    - Health check endpoint
    """
    app = FastAPI(
        title="Jobs API",
        version="1.0.0",
        description="Job skills management and ML enrichment API"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to Next.js URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(jobs_router)
    app.include_router(skills_router)
    app.include_router(lexicon_router)
    app.include_router(clusters_router)
    
    # Health check
    @app.get("/")
    async def root():
        return {"message": "Jobs API v1.0.0", "status": "healthy"}
    
    return app


# Create application instance
app = create_app()
