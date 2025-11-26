from fastapi import FastAPI
from analysis.routes import intelligence_router, evaluation_analysis_router

app = FastAPI()
app.include_router(intelligence_router.router)
app.include_router(evaluation_analysis_router.router)
