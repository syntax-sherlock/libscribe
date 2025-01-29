import logging

from qdrant_client import QdrantClient, models
from langchain_voyageai import VoyageAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize embedding model settings
OUTPUT_DIMENSION = 512
EMBEDDING_MODEL = "voyage-code-3"

embedding = VoyageAIEmbeddings(
    model=EMBEDDING_MODEL,
    output_dimension=OUTPUT_DIMENSION,
    api_key=get_env_var("VOYAGE_API_KEY"),
)

qdrant_url = get_env_var("QDRANT_URL")
qdant_api_key = get_env_var("QDRANT_API_KEY")
qdrant_collection = "github"
qdrant = QdrantClient(url=qdrant_url, api_key=qdant_api_key)

if not qdrant.collection_exists(collection_name=qdrant_collection):
    qdrant.create_collection(
        collection_name=qdrant_collection,
        vectors_config=models.VectorParams(
            size=OUTPUT_DIMENSION, distance=models.Distance.COSINE
        ),
    )


def process_documents(documents: list) -> None:
    """
    Process documents and store them in Qdrant.

    Args:
        documents: List of documents to process

    Raises:
        ValueError: If documents list is empty
    """
    if not documents:
        logger.warning("No documents provided for processing")
        return

    try:
        vector_store = QdrantVectorStore(
            client=qdrant, collection_name="github", embedding=embedding
        )
        vector_store.add_documents(documents)

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise
