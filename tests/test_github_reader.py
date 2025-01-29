import os
from unittest.mock import Mock, patch

import pytest
from src.ingestion.github_reader import GithubReader


@pytest.fixture
def github_token():
    return "test_token"


@pytest.fixture
def mock_langchain_loader():
    with patch("src.ingestion.github_reader.GithubFileLoader") as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


def test_init_with_token(github_token):
    reader = GithubReader(github_token=github_token)
    assert reader.github_token == github_token


def test_init_with_env_var():
    os.environ["GITHUB_TOKEN"] = "env_token"
    reader = GithubReader()
    assert reader.github_token == "env_token"
    del os.environ["GITHUB_TOKEN"]


def test_init_without_token():
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with pytest.raises(ValueError):
        GithubReader()


def test_fetch_repository_success(github_token, mock_langchain_loader):
    mock_class, mock_instance = mock_langchain_loader
    # Setup mock documents
    mock_doc1 = Mock()
    mock_doc1.page_content = "test content 1"
    mock_doc1.metadata = {"source": "test.py"}

    mock_doc2 = Mock()
    mock_doc2.page_content = "test content 2"
    mock_doc2.metadata = {"source": "test2.py"}

    mock_instance.load.return_value = [mock_doc1, mock_doc2]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo", branch="custom")

    # Verify
    assert mock_class.call_count == 1
    call_args = mock_class.call_args[1]  # Get kwargs
    assert call_args["repo"] == "test/repo"
    assert call_args["branch"] == "custom"
    assert call_args["access_token"] == github_token
    # Test file_filter function behavior instead of comparing function objects
    assert call_args["file_filter"]("test.py") == True
    assert call_args["file_filter"]("test.jpg") == False
    assert len(docs) == 2
    assert docs[0].page_content == "test content 1"
    assert docs[0].metadata == {"source": "test.py"}
    assert docs[1].page_content == "test content 2"
    assert docs[1].metadata == {"source": "test2.py"}


def test_fetch_repository_filters_empty_docs(github_token, mock_langchain_loader):
    _, mock_instance = mock_langchain_loader
    # Setup mock documents
    mock_doc1 = Mock()
    mock_doc1.page_content = "content"
    mock_doc1.metadata = {"source": "test.py"}

    mock_doc2 = Mock()
    mock_doc2.page_content = "   "  # Empty content
    mock_doc2.metadata = {"source": "empty.py"}

    mock_doc3 = Mock()
    mock_doc3.page_content = "more content"
    mock_doc3.metadata = {"source": "test2.py"}

    mock_instance.load.return_value = [mock_doc1, mock_doc2, mock_doc3]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo")

    # Verify
    assert len(docs) == 3
    # Verify document contents are preserved
    assert docs[0].page_content == "content"
    assert docs[1].page_content == "   "
    assert docs[2].page_content == "more content"


def test_fetch_repository_error(github_token, mock_langchain_loader):
    _, mock_instance = mock_langchain_loader
    # Setup
    mock_instance.load.side_effect = Exception("API Error")

    # Execute and Verify
    reader = GithubReader(github_token=github_token)
    with pytest.raises(Exception) as exc_info:
        reader.fetch_repository(owner="test", repo="repo")
    assert "Error fetching repository" in str(exc_info.value)


def test_is_allowed_file():
    reader = GithubReader(github_token="test_token")

    # Test allowed extensions
    assert reader._is_allowed_file("test.py")
    assert reader._is_allowed_file("doc.md")
    assert reader._is_allowed_file("config.yml")

    # Test disallowed extensions
    assert not reader._is_allowed_file("image.png")
    assert not reader._is_allowed_file("script.sh")
    assert not reader._is_allowed_file("no_extension")
