"""Document model for storing text content and metadata."""

from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints


class Document(BaseModel):
    """Document class for storing text content and metadata."""

    text: Annotated[str, StringConstraints(min_length=1)]
    metadata: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None
    embedding: list[float] | None = None
