import logging
import time

from litellm import embedding
from pinecone import ServerlessSpec
from pinecone.core.openapi.shared.exceptions import PineconeApiException
from pinecone.grpc import PineconeGRPC
from src.config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize embedding model settings
OUTPUT_DIMENSION = 512
EMBEDDING_MODEL = "voyage/voyage-code-3"


def get_embedding(text: str) -> list[float]:
    """Get embedding for text using LiteLLM."""
    try:
        response = embedding(
            model=EMBEDDING_MODEL,
            dimensions=OUTPUT_DIMENSION,
            input=[text],
        )
        # The response is a LiteLLM EmbeddingResponse object
        # response.data is a list of dictionaries, each with an 'embedding' key
        if (
            hasattr(response, "data")
            and isinstance(response.data, list)
            and response.data
            and isinstance(response.data[0], dict)
        ):
            return response.data[0]["embedding"]

        # If we get here, the response structure is not what we expect
        logger.error(f"Unexpected response structure: {response}")
        raise ValueError("Unexpected embedding response structure")
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        raise


# Initialize Pinecone client
index_name = "github-repos"
pinecone_api_key = get_env_var("PINECONE_API_KEY")
pinecone_client = PineconeGRPC(api_key=pinecone_api_key)


def create_index_if_not_exists(index_name: str) -> str | None:
    try:
        # Check if index already exists
        existing_indexes = pinecone_client.list_indexes().names()
        if index_name in existing_indexes:
            logger.info(f"Index '{index_name}' already exists")
            return index_name

        logger.info(f"Creating index '{index_name}'...")
        pinecone_client.create_index(
            index_name,
            dimension=OUTPUT_DIMENSION,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

        # Wait for index to be ready
        time.sleep(5)
        logger.info(f"Index '{index_name}' created successfully")
        return index_name

    except PineconeApiException as e:
        if "already exists" in str(e):
            logger.info(f"Index '{index_name}' already exists (caught from API)")
            return index_name
        logger.error(f"Failed to create index: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating index: {str(e)}")
        raise


# Create index and initialize client
create_index_if_not_exists(index_name)
index = pinecone_client.Index(index_name)


def process_documents(documents: list, namespace: str | None = None) -> None:
    """
    Process documents and store them in Pinecone.

    Args:
        documents: List of documents to process
        namespace: Optional namespace for vector store

    Raises:
        ValueError: If documents list is empty
    """
    if not documents:
        logger.warning("No documents provided for processing")
        return

    try:
        logger.info(f"Processing {len(documents)} documents")
        logger.debug("Document paths:")
        for doc in documents:
            logger.debug(f"- {doc.metadata.get('file_path', 'unknown')}")

        # Process documents and generate embeddings if needed
        vectors = []
        for doc in documents:
            if doc.embedding is None:
                logger.debug(
                    "Generating embedding for: "
                    f"{doc.metadata.get('file_path', 'unknown')}"
                )
                doc.embedding = get_embedding(doc.text)
            vectors.append((doc.id, doc.embedding, doc.metadata))

        if not vectors:
            logger.warning("No vectors generated from documents")
            return

        # Use Pinecone's built-in methods for simplicity
        logger.info(f"Upserting {len(vectors)} vectors to Pinecone")
        index.upsert(
            vectors=vectors,
            namespace=namespace or "",
        )

        logger.info(f"Successfully processed {len(documents)} documents")

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise
