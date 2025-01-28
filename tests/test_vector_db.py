from unittest.mock import Mock, patch

import pytest
from src.storage.vector_db import get_embedding


@pytest.fixture
def mock_litellm_embedding():
    with patch("src.storage.vector_db.embedding") as mock:
        yield mock


def test_get_embedding_response(mock_litellm_embedding):
    """Test get_embedding with LiteLLM EmbeddingResponse."""
    # Create a mock EmbeddingResponse object
    mock_response = Mock()
    mock_response.data = [{"embedding": [0.1, 0.2, 0.3], "index": 0}]
    mock_litellm_embedding.return_value = mock_response

    # Test the function
    result = get_embedding("test text")

    # Verify the result
    assert result == [0.1, 0.2, 0.3]
    mock_litellm_embedding.assert_called_once_with(
        model="voyage/voyage-code-3", dimensions=512, input=["test text"]
    )


def test_get_embedding_invalid_response(mock_litellm_embedding):
    """Test get_embedding with invalid response structure."""
    # Create a mock response with invalid structure
    mock_response = Mock()
    mock_response.data = []  # Empty data list
    mock_litellm_embedding.return_value = mock_response

    # Test the function
    with pytest.raises(ValueError, match="Unexpected embedding response structure"):
        get_embedding("test text")


def test_get_embedding_error(mock_litellm_embedding):
    """Test get_embedding error handling."""
    # Mock an error response
    mock_litellm_embedding.side_effect = Exception("API Error")

    # Test the function
    with pytest.raises(Exception) as exc_info:
        get_embedding("test text")

    assert "API Error" in str(exc_info.value)
    mock_litellm_embedding.assert_called_once()
