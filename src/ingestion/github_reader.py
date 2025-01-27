"""
GitHub repository reader using llama_index.
"""

import os
from typing import List, Optional
from llama_index.readers.github import GithubClient, GithubRepositoryReader
from llama_index.core import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GithubReaderWrapper:
    """Wrapper for llama_index's GithubRepositoryReader with additional functionality."""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize the GitHub reader with optional token."""
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")

        # Initialize the GitHub client
        self.github_client = GithubClient(github_token=self.github_token, verbose=True)

    def fetch_repository(
        self, owner: str, repo: str, branch: str = "main"
    ) -> List[Document]:
        """
        Fetch repository content from GitHub using llama_index's GithubRepositoryReader.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            List of Document objects containing repository content
        """
        try:
            # Initialize reader with filters to exclude binary and unwanted files
            reader = GithubRepositoryReader(
                github_client=self.github_client,
                owner=owner,
                repo=repo,
                verbose=True,
                use_parser=False,
                # Only include specific file types we want to process
                filter_file_extensions=(
                    [
                        ".py",  # Python files
                        ".md",  # Markdown
                        ".rst",  # ReStructuredText
                        ".txt",  # Text files
                        ".json",  # JSON files
                        ".yaml",  # YAML files
                        ".yml",  # YAML files
                        ".ini",  # Config files
                        ".html",  # HTML files
                    ],
                    GithubRepositoryReader.FilterType.INCLUDE,
                ),
                concurrent_requests=10,
            )

            # Use the public load_data method with proper configuration
            documents = reader.load_data(
                branch=branch,
            )

            # Filter out any empty documents
            documents = [doc for doc in documents if doc.text.strip()]
            return documents

        except Exception as e:
            raise Exception(f"Error fetching repository: {str(e)}")


# Create a global reader instance
github_reader = GithubReaderWrapper()


def fetch_github(repo: str, owner: str, branch: str = "main") -> List[Document]:
    """Fetch GitHub repository content using the global reader instance."""
    return github_reader.fetch_repository(owner, repo, branch)
