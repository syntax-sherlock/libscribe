"""
GitHub repository reader using LangChain's GitHubFileLoader.
"""

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders.github import GithubFileLoader
from src.config import get_env_var

IGNORED_DIRECTORIES = {
    ".github",  # GitHub specific files and workflows
    ".circleci",  # CircleCI configuration
    ".gitlab",  # GitLab specific files
    ".azure",  # Azure DevOps configurations
    "workflows",  # GitHub Actions workflows
}

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
    ".toml",  # TOML files
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GithubReader:
    """GitHub repository reader using LangChain's GitHubFileLoader."""

    def __init__(self, github_token: str | None = None):
        """Initialize the GitHub reader with optional token."""
        self.github_token = github_token or get_env_var("GITHUB_TOKEN")

    def _is_ignored_directory(self, path: str) -> bool:
        """Check if file path contains an ignored directory."""
        path_parts = Path(path).parts
        return any(ignored_dir in path_parts for ignored_dir in IGNORED_DIRECTORIES)

    def _is_allowed_file(self, path: str) -> bool:
        """Check if file should be included based on directory and extension."""
        # First check if file is in an ignored directory
        if self._is_ignored_directory(path):
            logger.debug(f"Skipping file in ignored directory: {path}")
            return False

        # Then check file extension
        extension = Path(path).suffix
        is_allowed = extension in ALLOWED_EXTENSIONS
        if not is_allowed:
            logger.debug(f"Skipping file with unsupported extension: {path}")
        return is_allowed

    def fetch_repository(
        self, owner: str, repo: str, branch: str = "main"
    ) -> list[Document]:
        """
        Fetch repository content from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            List of Document objects containing repository content
        """
        logger.info(f"Fetching repository {owner}/{repo} branch {branch}")
        try:
            # Use GitHubFileLoader to get repository contents
            loader = GithubFileLoader(
                repo=f"{owner}/{repo}",
                branch=branch,
                access_token=self.github_token,
                file_filter=lambda file_path: self._is_allowed_file(file_path),
            )

            return loader.load()

        except Exception as e:
            raise Exception(f"Error fetching repository: {str(e)}") from e


# Create a global reader instance
github_reader = GithubReader()


def fetch_github(repo: str, owner: str, branch: str = "main") -> list[Document]:
    """Fetch GitHub repository content using the global reader instance."""
    return github_reader.fetch_repository(owner, repo, branch)
