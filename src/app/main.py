from datetime import UTC, datetime
from typing import Literal

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from langchain.schema import Document
from pydantic import BaseModel, ConfigDict, HttpUrl
from src.ingestion.processing import process_repository
from src.storage.vector_db import VectorDB
from src.utils.repo_parsing import extract_owner_repo

app = FastAPI(title="LibScribe API")


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    model_config = ConfigDict(extra="forbid")

    query: str


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error"] = "success"
    results: list[Document] = []
    message: str | None = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy"] = "healthy"
    service: Literal["LibScribe API"] = "LibScribe API"
    timestamp: str
    version: str = "1.0.0"  # Consider moving to config


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Healthcheck endpoint to verify service status.
    Returns basic service health information including service name, status,
    and timestamp.
    """
    return HealthResponse(timestamp=datetime.now(UTC).isoformat())


@app.post("/query")
def query_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Query the ingested data for relevant information.

    Parameters:
    - query: Search query or prompt

    Returns:
    - JSON response with query results
    """
    try:
        # Initialize vector database
        vector_db = VectorDB()

        # Perform the query
        results = vector_db.query(query=request.query)

        return QueryResponse(
            status="success", results=results, message="Query completed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}") from e


class IngestRequest(BaseModel):
    """Request model for repository ingestion."""

    model_config = ConfigDict(extra="forbid")

    repo_url: HttpUrl
    branch: str = "main"
    language: str | None = None


@app.post("/ingest")
def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a GitHub repository into the vector database.

    Parameters:
    - repo_url: Full GitHub repository URL (e.g., https://github.com/owner/repo)
    - branch: Repository branch to ingest (default: "main")

    Returns:
    - JSON response with status and job information
    """
    try:
        # Extract owner/repo for validation
        owner, repo = extract_owner_repo(str(request.repo_url))

        # Start background processing
        background_tasks.add_task(
            process_repository, str(request.repo_url), request.branch, request.language
        )

        return {
            "status": "accepted",
            "message": "Repository ingestion started",
            "repository": {"owner": owner, "repo": repo, "branch": request.branch},
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
