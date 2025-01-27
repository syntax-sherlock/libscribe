# libscribe

libscribe is a tool for ingesting and processing code repositories, primarily from GitHub, and storing them in a vector database.

## Key Features

- Ingests repositories from GitHub.
- Processes the repository content.
- Stores the processed data in a vector database.

## Architecture

```mermaid
graph TD
    %% API Layer
    A[FastAPI Application] --> |POST /ingest| B[Background Task]

    %% Ingestion Layer
    B --> C[GitHub Reader]
    C --> |fetch_repository| D[GitHub API]
    D --> |raw files| C
    C --> |Document objects| E[Processing Pipeline]

    %% Processing Layer
    E --> |enrich_documents| F[Document Enrichment]
    F --> |add metadata| G[Enriched Documents]

    %% Storage Layer
    G --> H[Ingestion Pipeline]
    H --> |SentenceSplitter| I[Text Chunks]
    I --> |VoyageEmbedding| J[Embeddings]
    J --> |store vectors| K[Pinecone DB]

    %% External Services
    D --> |filtered files| C
    subgraph External Services
        D[GitHub API]
        L[Voyage AI API]
        K[Pinecone DB]
    end

    %% Configurations
    M[Environment Config] --> |API keys| A
    M --> |tokens| C
    M --> |credentials| K

    %% Data Flow Notes
    classDef external fill:#f96,stroke:#333
    class D,L,K external
```

The diagram above illustrates the system's architecture and data flow:

1. The FastAPI application receives repository ingestion requests
2. A background task is created to handle the ingestion process
3. The GitHub Reader fetches and filters repository content
4. Documents are enriched with metadata (owner, repo, branch, etc.)
5. The ingestion pipeline:
   - Splits text into chunks
   - Generates embeddings using Voyage AI
   - Stores vectors in Pinecone DB
6. External services (GitHub, Voyage AI, Pinecone) are integrated via API keys

## Usage

To ingest a repository, you can use the `ingest_repository` function in `src/app/main.py`. Provide the repository URL and branch as input.

## File Structure

The `src` directory contains the following subdirectories:

- `app`: Contains the main application logic, including the API endpoints.
- `ingestion`: Contains the logic for ingesting data from GitHub and processing it.
- `storage`: Contains the logic for interacting with the vector database.
- `utils`: Contains utility functions, such as parsing repository URLs.

## Running the Project

1.  Install UV.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2.  Install dependencies using `uv sync`.
3.  Create a `.env` file based on the `.env.example`.
4.  Run the FastAPI application using `uvicorn src.app.main:app --reload`.

## Roadmap

For more details about future plans, please refer to the `ROADMAP.md` file.
