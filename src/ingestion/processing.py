import logging

from langchain.schema import Document
from src.ingestion.github_reader import fetch_github

from src.storage.vector_db import process_documents
from src.utils.repo_parsing import extract_owner_repo


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_repository(repo_url: str, branch: str):
    owner, repo = extract_owner_repo(repo_url)

    logger.info(f"Fetching documents from {owner}/{repo}")
    documents = fetch_github(repo, owner, branch)

    if not documents:
        logger.warning(
            f"No valid documents found in {owner}/{repo}. "
            "This could be due to unsupported file types or empty files."
        )
        return

    logger.info(f"Enriching {len(documents)} documents with metadata")
    enriched_docs = enrich_documents(documents, owner, repo, branch)

    logger.info(f"Processing documents into vector store: {owner}/{repo}")
    process_documents(enriched_docs)


def enrich_documents(
    docs: list[Document],
    owner: str,
    repo: str,
    branch: str,
) -> list[Document]:

    return [
        Document(
            page_content=doc.page_content,
            metadata={
                "path": doc.metadata.get("path"),
                "repo": repo,
                "owner": owner,
                "branch": branch,
            },
        )
        for doc in docs
    ]
