import datetime

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from ..ingestion.processing import process_repository
from ..utils.repo_parsing import extract_owner_repo

app = FastAPI(title="LibScribe API")


@app.get("/health")
async def health_check():
    """
    Healthcheck endpoint to verify service status.
    Returns basic service health information.
    """
    return {
        "status": "healthy",
        "service": "LibScribe API",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


class IngestRequest(BaseModel):
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
