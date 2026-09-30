from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_indexes
from app.routes.contracts import router as contract_router
from app.routes.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_indexes()
    yield


app = FastAPI(
    title="Document Analyzer AI",
    description="""
    AI-powered document analysis API that allows users to upload,
    process, search, and analyze documents using modern AI and
    natural language processing techniques.
    """,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    return {
        "endpoints": {
            "POST /contracts/upload": "Upload a PDF or TXT contract for analysis",
            "GET /contracts/": "Retrieve a list of all uploaded contracts",
            "GET /contracts/{id}": "Retrieve details of a specific contract by ID",
            "POST /analysis/analyze/{contract_id}": "Analyze a contract using AI and return insights",
            "GET /analysis/{analysis_id}": "Retrieve the results of a specific analysis by ID",
            "GET /analysis/contract/{contract_id}": "Retrieve a list of all analyses performed for a specific contract",
        }
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(contract_router)
app.include_router(analysis_router)