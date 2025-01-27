from typing import List
from llama_index.core import Document
from ..utils.repo_parsing import extract_owner_repo
from .github_reader import fetch_github
from ..storage.vector_db import process_documents


def create_namespace(owner: str, repo: str) -> str:
    return f"github_{owner}_{repo}".lower().replace("-", "_")


def process_repository(repo_url: str, branch: str, metadata: dict) -> None:
    owner, repo = extract_owner_repo(repo_url)
    namespace = create_namespace(owner, repo)
    documents = fetch_github(repo, owner, branch)
    enriched_docs = enrich_documents(
        documents, owner, repo, branch, namespace, metadata
    )
    process_documents(enriched_docs, namespace)


def enrich_documents(
    docs: List[Document],
    owner: str,
    repo: str,
    branch: str,
    namespace: str,
    metadata: dict,
) -> List[Document]:
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
