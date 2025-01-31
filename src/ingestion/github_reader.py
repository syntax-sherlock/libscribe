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
    "node_modules",  # Node.js dependencies
    "CONTRIBUTING",  # Contribution guidelines
    ".vscode",  # Visual Studio Code settings
    ".idea",  # IntelliJ IDEA settings
    ".yarn",  # Yarn package manager
}

# Common extensions that are always included (documentation, configuration, etc.)
COMMON_EXTENSIONS = {
    ".md",  # Markdown
    ".mdx",  # Markdown with JSX
    ".rst",  # ReStructuredText
    ".txt",  # Text files
    ".json",  # JSON files
    ".yaml",  # YAML files
    ".yml",  # YAML files
    ".ini",  # Config files
    ".toml",  # TOML files
}

# Language-specific file extensions
LANGUAGE_EXTENSIONS = {
    "python": {
        ".py",  # Python source
        ".pyi",  # Python interface
        ".pyx",  # Cython source
        ".ipynb",  # Jupyter notebooks
    },
    "typescript": {
        ".ts",  # TypeScript source
        ".tsx",  # TypeScript React
        ".d.ts",  # TypeScript declarations
    },
    "javascript": {
        ".js",  # JavaScript source
        ".jsx",  # JavaScript React
        ".mjs",  # ES modules
    },
    "java": {
        ".java",  # Java source
        ".jar",  # Java archive
    },
    "go": {
        ".go",  # Go source
    },
    "rust": {
        ".rs",  # Rust source
    },
    "c": {
        ".c",  # C source
        ".h",  # C header
    },
    "cpp": {
        ".cpp",  # C++ source
        ".hpp",  # C++ header
        ".cc",  # C++ source
        ".hh",  # C++ header
    },
}

# Convert nested dictionaries to sets
LANGUAGE_EXTENSIONS = {lang: set(exts) for lang, exts in LANGUAGE_EXTENSIONS.items()}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GithubReader:
    """GitHub repository reader using LangChain's GitHubFileLoader."""

    def __init__(self, github_token: str | None = None, language: str | None = None):
        """
        Initialize the GitHub reader.

        Args:
            github_token: Optional GitHub API token
            language: Optional programming language to filter files by
        """
        self.github_token = github_token or get_env_var("GITHUB_TOKEN")
        self.allowed_extensions = self._get_allowed_extensions(language)

    def _is_ignored_directory(self, path: str) -> bool:
        """Check if file path contains an ignored directory."""
        path_parts = Path(path).parts
        return any(ignored_dir in path_parts for ignored_dir in IGNORED_DIRECTORIES)

    def _get_allowed_extensions(self, language: str | None) -> set[str]:
        """
        Get the set of allowed file extensions based on language.

        Args:
            language: Programming language to filter by, or None for all extensions

        Returns:
            Set of allowed file extensions
        """
        if language is None:
            # If no language specified, include all language extensions
            all_extensions = set()
            for lang_extensions in LANGUAGE_EXTENSIONS.values():
                all_extensions.update(lang_extensions)
            return all_extensions.union(COMMON_EXTENSIONS)

        if language.lower() not in LANGUAGE_EXTENSIONS:
            logger.warning(
                f"Unknown language: {language}, defaulting to common extensions only"
            )
            return COMMON_EXTENSIONS.copy()

        # Combine language-specific extensions with common extensions
        return LANGUAGE_EXTENSIONS[language.lower()].union(COMMON_EXTENSIONS)

    def _is_allowed_file(self, path: str) -> bool:
        """Check if file should be included based on directory and extension."""
        # First check if file is in an ignored directory
        if self._is_ignored_directory(path):
            logger.debug(f"Skipping file in ignored directory: {path}")
            return False

        # Then check file extension
        extension = Path(path).suffix
        return extension in self.allowed_extensions

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


def fetch_github(
    repo: str, owner: str, branch: str = "main", language: str | None = None
) -> list[Document]:
    """
    Fetch GitHub repository content.

    Args:
        repo: Repository name
        owner: Repository owner
        branch: Branch name (default: main)
        language: Programming language to filter by (default: None)

    Returns:
        List of Document objects containing repository content
    """
    reader = GithubReader(language=language)
    return reader.fetch_repository(owner, repo, branch)
