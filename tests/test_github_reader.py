import os
from unittest.mock import Mock, patch

import pytest
from github3.repos.contents import Contents
from src.ingestion.github_reader import GithubReader


@pytest.fixture
def github_token():
    return "test_token"


@pytest.fixture
def mock_github():
    with patch("src.ingestion.github_reader.login") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


def test_init_with_token(github_token, mock_github):
    reader = GithubReader(github_token=github_token)
    assert reader.github_token == github_token


def test_init_with_env_var(mock_github):
    os.environ["GITHUB_TOKEN"] = "env_token"
    reader = GithubReader()
    assert reader.github_token == "env_token"
    del os.environ["GITHUB_TOKEN"]


def test_init_without_token():
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with pytest.raises(ValueError):
        GithubReader()


def test_fetch_repository_success(github_token, mock_github):
    # Setup mock repository and contents
    mock_repo = Mock()
    mock_github.repository.return_value = mock_repo

    mock_file1 = Mock(spec=Contents)
    mock_file1.type = "file"
    mock_file1.path = "test.py"
    mock_file1.content = "dGVzdCBjb250ZW50IDE="  # base64 for "test content 1"
    mock_file1.sha = "sha1"

    mock_file2 = Mock(spec=Contents)
    mock_file2.type = "file"
    mock_file2.path = "test2.py"
    mock_file2.content = "dGVzdCBjb250ZW50IDI="  # base64 for "test content 2"
    mock_file2.sha = "sha2"

    mock_repo.directory_contents.return_value = [mock_file1, mock_file2]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo", branch="custom")

    # Verify
    mock_github.repository.assert_called_once_with("test", "repo")
    mock_repo.directory_contents.assert_called_with("", ref="custom")
    assert len(docs) == 2
    assert docs[0].text == "test content 1"
    assert docs[1].text == "test content 2"


def test_fetch_repository_filters_empty_docs(github_token, mock_github):
    # Setup mock repository and contents
    mock_repo = Mock()
    mock_github.repository.return_value = mock_repo

    mock_file1 = Mock(spec=Contents)
    mock_file1.type = "file"
    mock_file1.path = "test.py"
    mock_file1.content = "Y29udGVudA=="  # base64 for "content"
    mock_file1.sha = "sha1"

    mock_file2 = Mock(spec=Contents)
    mock_file2.type = "file"
    mock_file2.path = "empty.py"
    mock_file2.content = "ICAg"  # base64 for "   "
    mock_file2.sha = "sha2"

    mock_file3 = Mock(spec=Contents)
    mock_file3.type = "file"
    mock_file3.path = "test2.py"
    mock_file3.content = "bW9yZSBjb250ZW50"  # base64 for "more content"
    mock_file3.sha = "sha3"

    mock_repo.directory_contents.return_value = [mock_file1, mock_file2, mock_file3]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo")

    # Verify
    assert len(docs) == 2
    assert all(doc.text.strip() for doc in docs)


def test_fetch_repository_handles_none_content(github_token, mock_github):
    # Setup mock repository and contents
    mock_repo = Mock()
    mock_github.repository.return_value = mock_repo

    mock_file = Mock(spec=Contents)
    mock_file.type = "file"
    mock_file.path = "test.py"
    mock_file.content = None
    mock_file.sha = "sha1"

    # Mock the refresh method to simulate content being loaded
    def refresh_content():
        mock_file.content = "dGVzdCBjb250ZW50"  # base64 for "test content"

    mock_file.refresh.side_effect = refresh_content

    mock_repo.directory_contents.return_value = [mock_file]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo")

    # Verify
    assert len(docs) == 1
    assert docs[0].text == "test content"
    mock_file.refresh.assert_called_once()


def test_fetch_repository_handles_failed_refresh(github_token, mock_github):
    # Setup mock repository and contents
    mock_repo = Mock()
    mock_github.repository.return_value = mock_repo

    mock_file = Mock(spec=Contents)
    mock_file.type = "file"
    mock_file.path = "test.py"
    mock_file.content = None
    mock_file.sha = "sha1"

    # Mock the refresh method to simulate a failed refresh
    mock_file.refresh.side_effect = Exception("Failed to refresh content")

    mock_repo.directory_contents.return_value = [mock_file]

    # Execute
    reader = GithubReader(github_token=github_token)
    docs = reader.fetch_repository(owner="test", repo="repo")

    # Verify
    assert len(docs) == 0  # No documents should be returned for failed content
    mock_file.refresh.assert_called_once()


def test_fetch_repository_error(github_token, mock_github):
    # Setup
    mock_github.repository.side_effect = Exception("API Error")

    # Execute and Verify
    reader = GithubReader(github_token=github_token)
    with pytest.raises(Exception) as exc_info:
        reader.fetch_repository(owner="test", repo="repo")
    assert "Error fetching repository" in str(exc_info.value)
