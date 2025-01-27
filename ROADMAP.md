# MVP Development Plan: Documentation Ingestion and AI Assistance Tool

## Project Description

A tool for ingesting library documentation and source code to enable AI models to provide context-aware coding assistance, usage examples, and best practices. Users can specify libraries they care about, and the tool will retrieve documentation and source code from GitHub, index the data using LlamaIndex with LiteLLM, and store it in an external vector database. The project includes an API for querying the ingested information.

---

## Features of the MVP

1. **Basic Multi-Library Support**

   - Users can specify one or more libraries to ingest.
   - Ingestion supports public libraries available on GitHub.

2. **Data Sources**

   - Documentation: Extracted from `README.md` and other Markdown files in the repository.
   - Source Code: Extracted from `.py` files in the GitHub repository.

3. **Indexing and Retrieval**

   - Use **LlamaIndex** for building and querying indices.
   - Store indexed data in an external vector database (Pinecone).

4. **API**
   - A simple API for:
     - Ingesting a library.
     - Querying the ingested data for code examples, best practices, or usage instructions.

---

## Development Steps

### Phase 1: Project Setup

1. **Set Up the Project Directory**

   ```bash
   uv init libscript
   cd libscribe
   ```

2. **Install Dependencies**

   Update the `pyproject.toml` file to include the following dependencies:

   ```toml
    dependencies = [
        "fastapi>=0.115.7",
        "llama-index>=0.12.14",
        "llama-index-embeddings-huggingface>=0.5.1",
        "llama-index-llms-litellm>=0.3.0",
        "llama-index-readers-github>=0.5.0",
        "pinecone-client>=5.0.1",
        "pytest>=8.3.4",
        "python-dotenv>=1.0.1",
        "uvicorn>=0.34.0",
    ]
   ```

   Install them:

   ```bash
   uv sync
   ```

3. **Set Up Basic Directory Structure**
   ```bash
   libscribe/
   ├── app/
   │   ├── main.py            # API entry point
   │   ├── routes.py          # API routes
   ├── ingestion/
   │   ├── fetch_github.py    # Fetch GitHub repositories
   ├── storage/
   │   ├── vector_db.py       # Interface for vector database (Pinecone)
   ├── tests/
   ├── pyproject.toml         # Dependency and project configuration
   ├── .env                   # Environment variables (e.g., GitHub token, LLM keys)
   └── README.md
   ```

---

### Phase 2: GitHub Ingestion

1. **Fetch Repository from GitHub**

   - Use the `GithubRepositoryReader` class from `llama_index.readers.github` to fetch repository data.
   - Write a script (`fetch_github.py`) to:
     - Authenticate using a GitHub token from `.env`.
     - Fetch Markdown (`.md`, `.rst`) and Python files (`.py`) from the repository.
     - Handle branch specification and API limits gracefully.

   Example implementation:

   ```python
   import os
   from dotenv import load_dotenv
   from llama_index.readers.github import GithubRepositoryReader, GithubClient

   load_dotenv()

   github_token = os.environ.get("GITHUB_TOKEN")
   github_client = GithubClient(github_token, verbose=True)

   def fetch_github(repo, owner, branch="main"):
       reader = GithubRepositoryReader(
           github_client=github_client,
           owner=owner,
           repo=repo,
           verbose=False,
           use_parser=False,
           filter_file_extensions=([
               ".py", ".txt", ".md", ".rst"
           ], GithubRepositoryReader.FilterType.INCLUDE),
       )
       return reader.load_data(branch=branch)
   ```

   - Test the script by fetching and printing sample data from a public repository (e.g., `psf/requests`).

2. **Indexing the Data**

   - Use the fetched documents directly for indexing without extra pre-processing.
   - Example:

     ```python
     from llama_index.core import VectorStoreIndex, Settings
     from llama_index.embeddings.huggingface import HuggingFaceEmbedding
     from llama_index.llms.litellm import LiteLLM

     Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
     Settings.llm = LiteLLM(model="openrouter/google/gemini-flash-1.5")

     documents = fetch_github("requests", "psf")
     index = VectorStoreIndex.from_documents(documents)
     query_engine = index.as_query_engine()
     response = query_engine.query(
         "What are the parameter options for the requests.get method?"
     )
     print(response)
     ```

---

### Phase 3: Indexing and Storage

1. **Set Up External Vector Database**

   - Use **Pinecone** as the vector database. Create an account on Pinecone and set up an index.
   - Integrate Pinecone into the project.

2. **Integrate LlamaIndex with Pinecone**

   - Use the built-in support of `LlamaIndex` to connect to Pinecone.
   - Test querying to ensure embeddings and metadata are stored correctly.

---

### Phase 4: API Development

1. **Set Up FastAPI**

   - Write `main.py` and `routes.py` to create endpoints.

2. **Endpoints**

   - `POST /ingest`: Ingest a library from GitHub.
     - Input: JSON with `repo_url` and optional metadata.
   - `POST /query`: Query the ingested data.
     - Input: JSON with `library_name` and `query`.
     - Output: Relevant information (usage examples, best practices, etc.).

3. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```

---

### Phase 5: Testing and Validation

1. **Unit Tests**

   - Write tests for:
     - GitHub fetching (`fetch_github.py`).
     - Indexing and querying pipeline.

2. **Integration Test**

   - Test the full pipeline:
     - Ingest a real GitHub repository (e.g., `requests` library).
     - Query the API for examples like: "How do I send a POST request?"

3. **API Testing**
   - Use Postman, curl, or HTTPie to test the API:
     ```bash
     http POST http://127.0.0.1:8000/ingest repo_url=https://github.com/psf/requests
     http POST http://127.0.0.1:8000/query library_name=requests query="How to send POST requests?"
     ```

---

### Phase 6: Polishing and Deployment

1. **Error Handling**

   - Add validation for API inputs and error handling for GitHub fetching.

2. **Environment Management**

   - Use `.env` to store secrets like GitHub tokens and vector database URLs.

3. **Basic Documentation**

   - Write a `README.md` explaining:
     - How to set up the project.
     - API usage examples.

4. **Deployment**
   - Deploy the API on a cloud provider (e.g., Fly.io, Render, or Heroku).
   - Use a managed Pinecone service for vector database hosting.

---

## Task List

### Phase 1: Project Setup

- [x] Set up project structure and virtual environment.
- [x] Install dependencies.
- [x] Configure `.env` for API keys and database credentials.

### Phase 2: GitHub Ingestion

- [x] Finalize and test GitHub fetching logic.
- [x] Use fetched documents for indexing directly.

### Phase 3: Indexing and Storage

- [x] Set up Pinecone account and index.
- [x] Test integration of Pinecone with `LlamaIndex` manually.

### Phase 4: API Development

- [x] Set up FastAPI.
- [x] Implement `POST /ingest` endpoint.
- [ ] Implement `POST /query` endpoint.
- [x] Test API locally.

### Phase 5: Testing

- [ ] Write unit tests for all major components.
- [ ] Perform end-to-end integration testing.

### Phase 6: Polishing and Deployment

- [ ] Add error handling and input validation.
- [ ] Write project documentation.
- [ ] Deploy API and database to a cloud provider.
