"""Tests for the Document model."""

import pytest
from pydantic import ValidationError

from models.document import Document


def test_document_creation():
    """Test creating a Document with basic fields."""
    doc = Document(text="Sample text")
    assert doc.text == "Sample text"
    assert doc.metadata == {}
    assert doc.id is None
    assert doc.embedding is None


def test_document_with_metadata():
    """Test creating a Document with metadata."""
    metadata = {"source": "test", "page": 1}
    doc = Document(text="Sample text", metadata=metadata)
    assert doc.metadata == metadata


def test_document_with_all_fields():
    """Test creating a Document with all fields."""
    metadata = {"source": "test"}
    embedding = [0.1, 0.2, 0.3]
    doc = Document(
        text="Sample text",
        metadata=metadata,
        id="123",
        embedding=embedding,
    )
    assert doc.text == "Sample text"
    assert doc.metadata == metadata
    assert doc.id == "123"
    assert doc.embedding == embedding


def test_document_model_validation():
    """Test document model validation."""
    with pytest.raises(ValidationError):
        Document()  # Should fail because text is required

    with pytest.raises(ValidationError):
        Document(text="")  # Empty string should fail

    # Test with invalid metadata type
    with pytest.raises(ValidationError):
        Document(text="Sample", metadata="invalid")  # type: ignore

    # Test with invalid embedding type
    with pytest.raises(ValidationError):
        Document(text="Sample", embedding="invalid")  # type: ignore
