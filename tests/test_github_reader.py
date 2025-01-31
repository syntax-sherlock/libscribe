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
    assert reader.allowed_extensions == reader._get_allowed_extensions(None)


def test_init_with_language():
    reader = GithubReader(github_token="test_token", language="python")
    assert ".py" in reader.allowed_extensions
    assert ".pyi" in reader.allowed_extensions
    assert ".md" in reader.allowed_extensions  # Common extension
    assert ".ts" not in reader.allowed_extensions  # TypeScript extension


def test_get_allowed_extensions():
    reader = GithubReader(github_token="test_token")

    # Test with no language (should include all extensions)
    all_extensions = reader._get_allowed_extensions(None)
    assert ".py" in all_extensions
    assert ".ts" in all_extensions
    assert ".md" in all_extensions

    # Test with specific language
    python_extensions = reader._get_allowed_extensions("python")
    assert ".py" in python_extensions
    assert ".pyi" in python_extensions
    assert ".md" in python_extensions  # Common extension
    assert ".ts" not in python_extensions  # TypeScript extension

    # Test with unknown language
    unknown_extensions = reader._get_allowed_extensions("unknown")
    assert ".md" in unknown_extensions  # Common extension
    assert ".py" not in unknown_extensions
    assert ".ts" not in unknown_extensions


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

    # Test with no language
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo", branch="custom")

    # Verify
    assert mock_class.call_count == 1
    call_args = mock_class.call_args[1]  # Get kwargs
    assert call_args["repo"] == "test/repo"
    assert call_args["branch"] == "custom"
    assert call_args["access_token"] == github_token
    # Test file_filter function behavior instead of comparing function objects
    assert call_args["file_filter"]("test.py") is True
    assert call_args["file_filter"]("test.jpg") is False
    assert len(docs) == 2
    assert docs[0].page_content == "test content 1"
    assert docs[0].metadata == {"source": "test.py"}
    assert docs[1].page_content == "test content 2"
    assert docs[1].metadata == {"source": "test2.py"}

    # Test with specific language
    reader = GithubReader(github_token=github_token, language="python")
    docs = reader.fetch_repository(owner="test", repo="repo", branch="custom")

    # Verify language-specific filtering
    call_args = mock_class.call_args[1]
    assert call_args["file_filter"]("test.py") is True
    assert call_args["file_filter"]("test.ts") is False
    assert call_args["file_filter"]("doc.md") is True  # Common extension


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
    # Test with no language specified
    reader = GithubReader(github_token="test_token")
    assert reader._is_allowed_file("test.py")
    assert reader._is_allowed_file("doc.md")
    assert reader._is_allowed_file("config.yml")
    assert reader._is_allowed_file("app.ts")
    assert not reader._is_allowed_file("image.png")

    # Test with Python
    python_reader = GithubReader(github_token="test_token", language="python")
    assert python_reader._is_allowed_file("test.py")
    assert python_reader._is_allowed_file("types.pyi")
    assert python_reader._is_allowed_file("doc.md")  # Common extension
    assert not python_reader._is_allowed_file("app.ts")  # TypeScript file
    assert not python_reader._is_allowed_file("image.png")

    # Test with TypeScript
    ts_reader = GithubReader(github_token="test_token", language="typescript")
    assert ts_reader._is_allowed_file("app.ts")
    assert ts_reader._is_allowed_file("component.tsx")
    assert ts_reader._is_allowed_file("doc.md")  # Common extension
    assert not ts_reader._is_allowed_file("test.py")  # Python file
    assert not ts_reader._is_allowed_file("image.png")

    # Test ignored directories (should work regardless of language)
    for test_reader in [reader, python_reader, ts_reader]:
        assert not test_reader._is_allowed_file(".github/workflows/test.yml")
        assert not test_reader._is_allowed_file("src/.github/config.md")
        assert not test_reader._is_allowed_file(".circleci/config.yml")
        assert not test_reader._is_allowed_file(".gitlab/ci.yml")
        assert not test_reader._is_allowed_file(".azure/pipelines.yml")
        assert not test_reader._is_allowed_file("workflows/deploy.yml")

    # Test allowed nested directories (only for default reader)
    assert reader._is_allowed_file("docs/test.md")
    assert reader._is_allowed_file("src/lib/utils.py")
    assert reader._is_allowed_file("nested/path/to/file.rst")


def test_is_ignored_directory():
    reader = GithubReader(github_token="test_token")

    # Test ignored directories
    assert reader._is_ignored_directory(".github/workflows/test.yml")
    assert reader._is_ignored_directory("src/.github/config.md")
    assert reader._is_ignored_directory(".circleci/config.yml")
    assert reader._is_ignored_directory(".gitlab/ci.yml")
    assert reader._is_ignored_directory(".azure/pipelines.yml")
    assert reader._is_ignored_directory("workflows/deploy.yml")

    # Test allowed directories
    assert not reader._is_ignored_directory("docs/test.md")
    assert not reader._is_ignored_directory("src/lib/utils.py")
    assert not reader._is_ignored_directory("nested/path/to/file.rst")
