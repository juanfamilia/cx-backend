from fastapi import FastAPI
from routes import intelligence_router, evaluation_analysis_router

app = FastAPI(
    title="Siete CX - Analysis Service",
    description="AI/ML Microservice for video analysis, transcription, and intelligence",
    version="0.1.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and monitoring"""
    return {"status": "healthy", "service": "analysis"}

# Include routers
app.include_router(intelligence_router.router, prefix="/api/v1")
app.include_router(evaluation_analysis_router.router, prefix="/api/v1")
