import logging

from src.ingestion.github_reader import fetch_github
from src.models.document import Document
from src.storage.vector_db import process_documents
from src.utils.repo_parsing import extract_owner_repo


def create_namespace(owner: str, repo: str) -> str:
    return f"github_{owner}_{repo}".lower().replace("-", "_")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_repository(repo_url: str, branch: str, metadata: dict) -> None:
    owner, repo = extract_owner_repo(repo_url)
    namespace = create_namespace(owner, repo)

    logger.info(f"Fetching documents from {owner}/{repo}")
    documents = fetch_github(repo, owner, branch)

    if not documents:
        logger.warning(
            f"No valid documents found in {owner}/{repo}. "
            "This could be due to unsupported file types or empty files."
        )
        return

    logger.info(f"Enriching {len(documents)} documents with metadata")
    enriched_docs = enrich_documents(
        documents, owner, repo, branch, namespace, metadata
    )

    logger.info(f"Processing documents into vector store namespace: {namespace}")
    process_documents(enriched_docs, namespace)


def enrich_documents(
    docs: list[Document],
    owner: str,
    repo: str,
    branch: str,
    namespace: str,
    metadata: dict,
) -> list[Document]:
    for doc in docs:
        doc.metadata.update(
            {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "namespace": namespace,
                **metadata,
            }
        )
    return docs
