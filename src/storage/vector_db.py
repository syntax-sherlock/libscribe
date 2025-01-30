import logging

from qdrant_client import QdrantClient, models
from langchain_voyageai import VoyageAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDB:
    """Vector database interface for document storage and querying."""

    def __init__(self) -> None:
        """Initialize the vector database client and settings."""
        self.embedding = self._init_embedding()
        self.client = self._init_qdrant_client()
        self.collection_name = "github"
        self._init_collection()

    def _init_embedding(self) -> VoyageAIEmbeddings:
        """Initialize the embedding model."""
        return VoyageAIEmbeddings(
            model="voyage-code-3",
            output_dimension=512,
            api_key=get_env_var("VOYAGE_API_KEY"),
        )

    def _init_qdrant_client(self) -> QdrantClient:
        """Initialize the Qdrant client."""
        return QdrantClient(
            url=get_env_var("QDRANT_URL"),
            api_key=get_env_var("QDRANT_API_KEY"),
        )

    def _init_collection(self) -> None:
        """Initialize the Qdrant collection if it doesn't exist."""
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=512, distance=models.Distance.COSINE
                ),
            )

    def query(self, query: str) -> list[dict]:
        """
        Query the vector database for relevant documents.

        Args:
            query: Search query or prompt

        Returns:
            List of relevant documents
        """
        try:
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name="github",
                embedding=self.embedding,
            )
            return vector_store.similarity_search(query)
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

    def add_documents(self, collection_name: str, documents: list) -> None:
        """
        Add documents to the vector database.

        Args:
            collection_name: Name of the collection to add documents to
            documents: List of documents to add

        Raises:
            ValueError: If documents list is empty
        """
        if not documents:
            logger.warning("No documents provided for processing")
            return

        try:
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name,
                embedding=self.embedding,
            )
            vector_store.add_documents(documents)
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            raise


def process_documents(documents: list) -> None:
    """
    Process documents and store them in Qdrant.

    Args:
        documents: List of documents to process

    Raises:
        ValueError: If documents list is empty
    """
    vector_db = VectorDB()
    vector_db.add_documents("github", documents)
