import logging
import time

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import ServerlessSpec
from pinecone.core.openapi.shared.exceptions import PineconeApiException
from pinecone.grpc import PineconeGRPC
from src.config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize embedding model
OUTPUT_DIMENSION = 512
voyage_api_key = get_env_var("VOYAGE_API_KEY")
embed_model = VoyageEmbedding(
    model_name="voyage-code-3",
    output_dimension=OUTPUT_DIMENSION,
    voyage_api_key=voyage_api_key,
)

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

# vector_store = PineconeVectorStore(pinecone_index=index)

# llm = LiteLLM(model="openrouter/anthropic/claude-3.5-haiku")
# idx = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

# query_engine = idx.as_query_engine(llm=llm)
# response = query_engine.query("How to set headers in request?")
# print(response)


def process_documents(documents, namespace: str = None):
    """
    Process documents through the ingestion pipeline.

    Args:
        documents: List of documents to process
        namespace: Optional namespace for vector store
    """
    try:
        logger.info(f"Starting to process {len(documents)} documents")
        for doc in documents:
            logger.info(
                f"Processing document: {doc.metadata.get('file_path', 'unknown')}"
            )
        # Create vector store with namespace
        store = PineconeVectorStore(
            pinecone_index=index, namespace=namespace if namespace else ""
        )

        # Create pipeline with namespaced vector store
        # Use larger chunk size and overlap to reduce fragmentation
        # while preserving context
        ingestion_pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(),
                embed_model,
            ],
            vector_store=store,
        )

        ingestion_pipeline.run(documents=documents, show_progress=True)
        logger.info(f"Successfully processed {len(documents)} documents")

    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise
