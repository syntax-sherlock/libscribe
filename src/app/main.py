# ruff: noqa: E402
import warnings
from datetime import UTC, datetime
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, HttpUrl

# TODO: Remove after https://github.com/BerriAI/litellm/issues/7560 is fixed
warnings.filterwarnings(
    "ignore", category=UserWarning, module="pydantic._internal._config"
)

from src.ingestion.processing import process_repository
from src.utils.repo_parsing import extract_owner_repo

app = FastAPI(title="LibScribe API")


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


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo_url: HttpUrl
    branch: str = "main"
    metadata: dict | None = {}


@app.post("/ingest")
def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a GitHub repository into the vector database.

    Parameters:
    - repo_url: Full GitHub repository URL (e.g., https://github.com/owner/repo)
    - branch: Repository branch to ingest (default: "main")
    - metadata: Optional metadata to attach to the documents

    Returns:
    - JSON response with status and job information
    """
    try:
        # Extract owner/repo for validation
        owner, repo = extract_owner_repo(str(request.repo_url))

        # Start background processing
        background_tasks.add_task(
            process_repository, str(request.repo_url), request.branch, request.metadata
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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
