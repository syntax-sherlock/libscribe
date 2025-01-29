"""
GitHub repository reader using github3.py.
"""

import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from github3 import login
from github3.exceptions import GitHubError
from github3.repos.contents import Contents
from src.config import get_env_var
from src.models.document import Document

ALLOWED_EXTENSIONS = {
    ".py",  # Python files
    ".md",  # Markdown
    ".rst",  # ReStructuredText
    ".txt",  # Text files
    ".json",  # JSON files
    ".yaml",  # YAML files
    ".yml",  # YAML files
    ".ini",  # Config files
    ".html",  # HTML files
}


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GithubReader:
    """GitHub repository reader using github3.py."""

    def __init__(self, github_token: str | None = None):
        """Initialize the GitHub reader with optional token."""
        self.github_token = github_token or get_env_var("GITHUB_TOKEN")
        self.github = login(token=self.github_token)

    def _is_allowed_file(self, path: str) -> bool:
        """Check if file extension is in allowed list."""
        extension = Path(path).suffix
        is_allowed = extension in ALLOWED_EXTENSIONS
        if not is_allowed:
            logger.debug(f"Skipping file with unsupported extension: {path}")
        return is_allowed

    def _process_content(self, content: Contents) -> Document | None:
        """Process a single file content into a Document."""
        try:
            if content.type != "file":
                logger.debug(f"Skipping non-file content: {content.path}")
                return None

            if not self._is_allowed_file(content.path):
                return None

            # Get the actual file content
            try:
                # Refresh content to ensure we have the latest data
                # including the actual file content
                content.refresh()
                if content.content:
                    decoded_content = base64.b64decode(content.content).decode("utf-8")
                    if not decoded_content.strip():
                        logger.debug(f"Skipping empty file: {content.path}")
                        return None
                else:
                    logger.error(f"No content found for {content.path}")
                    return None
            except Exception as e:
                logger.error(f"Failed to decode content for {content.path}: {str(e)}")
                return None

            logger.debug(f"Successfully processed file: {content.path}")
            return Document(
                text=decoded_content,
                metadata={"file_path": content.path},
                id=content.sha,
            )
        except Exception as e:
            logger.error(f"Error processing {content.path}: {str(e)}")
            return None

    def _get_repository_contents(self, repo, path: str = "", ref: str = "main"):
        """Recursively get repository contents."""
        try:
            contents = list(repo.directory_contents(path, ref=ref))
            # Handle tuple responses from github3.py
            processed_contents = []
            for content in contents:
                # If content is a tuple of (name, content_obj), extract content_obj
                if isinstance(content, tuple) and len(content) == 2:
                    _, content_obj = content
                    processed_contents.append(content_obj)
                else:
                    processed_contents.append(content)
            return processed_contents
        except GitHubError:
            return []

    def fetch_repository(
        self, owner: str, repo: str, branch: str = "main"
    ) -> list[Document]:
        logger.info(f"Fetching repository {owner}/{repo} branch {branch}")
        """
        Fetch repository content from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            List of Document objects containing repository content
        """
        try:
            repository = self.github.repository(owner, repo)
            if not repository:
                raise Exception(f"Repository {owner}/{repo} not found")

            # Get all contents recursively
            contents = self._get_repository_contents(repository, ref=branch)
            all_contents = []

            # Process directories recursively
            while contents:
                content = contents.pop()
                # Ensure content is a Contents object
                if not isinstance(content, Contents):
                    continue

                if content.type == "dir":
                    contents.extend(
                        self._get_repository_contents(
                            repository, content.path, ref=branch
                        )
                    )
                else:
                    all_contents.append(content)

            # Log total files found
            logger.info(f"Found {len(all_contents)} total files in repository")

            # Process files concurrently
            documents = []
            processed_count = 0
            skipped_count = 0
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_content = {
                    executor.submit(self._process_content, content): content
                    for content in all_contents
                }
                for future in as_completed(future_to_content):
                    doc = future.result()
                    if doc:
                        documents.append(doc)
                        processed_count += 1
                    else:
                        skipped_count += 1

            logger.info(
                f"Repository processing complete: "
                f"{processed_count} files processed, "
                f"{skipped_count} files skipped"
            )

            # Sort documents by path for consistent ordering
            return sorted(documents, key=lambda x: x.metadata["file_path"])

        except Exception as e:
            raise Exception(f"Error fetching repository: {str(e)}") from e


# Create a global reader instance
github_reader = GithubReader()


def fetch_github(repo: str, owner: str, branch: str = "main") -> list[Document]:
    """Fetch GitHub repository content using the global reader instance."""
    return github_reader.fetch_repository(owner, repo, branch)
