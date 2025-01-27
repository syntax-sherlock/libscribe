import os
from unittest.mock import Mock, patch

import pytest
from llama_index.core import Document
from src.ingestion.github_reader import GithubReaderWrapper


@pytest.fixture
def github_token():
    return "test_token"


@pytest.fixture
def mock_github_client():
    with patch("src.ingestion.github_reader.GithubClient") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_repo_reader():
    with patch("src.ingestion.github_reader.GithubRepositoryReader") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


def test_init_with_token(github_token, mock_github_client):
    reader = GithubReaderWrapper(github_token=github_token)
    assert reader.github_token == github_token


def test_init_with_env_var(mock_github_client):
    os.environ["GITHUB_TOKEN"] = "env_token"
    reader = GithubReaderWrapper()
    assert reader.github_token == "env_token"
    del os.environ["GITHUB_TOKEN"]


def test_init_without_token():
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with pytest.raises(ValueError):
        GithubReaderWrapper()


def test_fetch_repository_success(github_token, mock_github_client, mock_repo_reader):
    # Setup
    test_docs = [Document(text="test content 1"), Document(text="test content 2")]
    mock_repo_reader.load_data.return_value = test_docs

    # Execute
    reader = GithubReaderWrapper(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo", branch="custom")

    # Verify
    mock_repo_reader.load_data.assert_called_once_with(branch="custom")
    assert docs == test_docs


def test_fetch_repository_filters_empty_docs(
    github_token, mock_github_client, mock_repo_reader
):
    # Setup
    test_docs = [
        Document(text="content"),
        Document(text="  "),  # Empty after strip
        Document(text="more content"),
    ]
    mock_repo_reader.load_data.return_value = test_docs

    # Execute
    reader = GithubReaderWrapper(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo")

    # Verify
    assert len(docs) == 2
    assert all(doc.text.strip() for doc in docs)


def test_fetch_repository_error(github_token, mock_github_client, mock_repo_reader):
    # Setup
    mock_repo_reader.load_data.side_effect = Exception("API Error")

    # Execute and Verify
    reader = GithubReaderWrapper(github_token=github_token)
    with pytest.raises(Exception) as exc_info:
        reader.fetch_repository(owner="test", repo="repo")
    assert "Error fetching repository" in str(exc_info.value)
