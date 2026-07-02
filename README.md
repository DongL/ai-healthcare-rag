# MediRAG: Healthcare Document Retrieval System

A production-ready Retrieval-Augmented Generation (RAG) system for healthcare document retrieval, built with FastAPI, ChromaDB, and OpenAI integration.

## Overview

This project demonstrates a scalable RAG pipeline designed for healthcare applications. It combines semantic search using sentence transformers with LLM-based answer generation to provide accurate, context-aware responses to medical queries.

### Key Features

- **Dual Vector Store Support**: ChromaDB (primary) with FAISS fallback for high availability
- **Production-Grade Architecture**: FastAPI with async support, structured logging, health checks, and monitoring
- **LLM Integration**: OpenAI GPT-4o-mini for context-aware answer generation
- **Containerized Deployment**: Docker + Docker Compose with multi-stage builds
- **Enterprise Configuration**: Environment-based settings with Pydantic validation
- **Performance Optimized**: Response time tracking, efficient embeddings, automatic retries

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Stores**: ChromaDB 0.4.24, FAISS 1.9.0
- **LLM**: OpenAI GPT-4o-mini
- **Server**: Uvicorn with uvloop
- **Containerization**: Docker, Docker Compose

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│      FastAPI Server             │
│  ┌──────────────────────────┐   │
│  │  Middleware & Logging    │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │   RAG Endpoint           │   │
│  │  - Query validation      │   │
│  │  - Embedding generation  │   │
│  └──────────────────────────┘   │
└────────┬────────────────┬───────┘
         │                │
         ▼                ▼
   ┌─────────┐      ┌─────────┐
   │ChromaDB │      │  FAISS  │
   │(Primary)│      │(Fallback)│
   └─────────┘      └─────────┘
         │                │
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │  OpenAI API    │
         │  (GPT-4o-mini) │
         └────────────────┘
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)
- OpenAI API key (optional, for answer generation)

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd RAG_healthcare
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Launch services**
```bash
docker-compose up --build
```

4. **Test the API**
```bash
curl -X POST "http://localhost:8000/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is metformin used for?", "k": 2}'
```

### Local Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn rag_app:app --reload --port 8000
```

## API Documentation

### Endpoints

#### `POST /rag`
Retrieve relevant documents and generate an answer.

**Request:**
```json
{
  "query": "What is metformin used for?",
  "k": 2
}
```

**Response:**
```json
{
  "query": "What is metformin used for?",
  "retrieved_contexts": [
    "Metformin is commonly prescribed as a first-line therapy for type 2 diabetes."
  ],
  "num_results": 1,
  "answer": "Metformin is commonly prescribed as a first-line therapy for type 2 diabetes. It helps control blood sugar levels in patients with this condition.",
  "processing_time_ms": 245.32,
  "timestamp": "2025-10-26T10:30:45.123456"
}
```

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-26T10:30:45.123456",
  "index_size": 250
}
```

#### `GET /docs`
Interactive API documentation (Swagger UI).

#### `GET /redoc`
Alternative API documentation (ReDoc).

## Configuration

Environment variables are managed via [.env](.env) and validated through [config.py](config.py):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for answer generation |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence transformer model |
| `OPENAI_MODEL` | gpt-4o-mini | OpenAI model for answers |
| `DATA_DIR` | seed_corpus | Directory scanned for source documents (.txt, .md, .pdf) |
| `CHUNK_SIZE` | 512 | Target chunk size in characters |
| `CHUNK_OVERLAP` | 64 | Character overlap between consecutive chunks |
| `REINDEX_ON_CORPUS_CHANGE` | true | Rebuild the index when the corpus changes |
| `USE_CHROMADB` | true | Use ChromaDB (falls back to FAISS) |
| `CHROMA_HOST` | chromadb | ChromaDB service hostname |
| `CHROMA_PORT` | 8000 | ChromaDB service port |
| `DEBUG` | false | Enable debug mode |
| `LOG_LEVEL` | INFO | Logging level |

## Project Structure

```
RAG_healthcare/
├── rag_app.py                    # Main FastAPI application
├── ingest.py                     # Document ingestion pipeline (discover → parse → chunk)
├── config.py                     # Configuration management
├── scripts/
│   └── generate_seed_corpus.py   # Regenerates the synthetic corpus
├── seed_corpus/                  # Shipped synthetic corpus (default DATA_DIR)
├── data/                         # Real documents (git-ignored; mount for production)
├── tests/                        # Unit tests (pytest)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Multi-stage production build
├── docker-compose.yml            # Service orchestration
├── .env                          # Environment variables
└── README.md                     # This file
```

## Key Implementation Details

### Document Ingestion

Documents are loaded from a directory at startup by the pipeline in [`ingest.py`](ingest.py):

1. **Discover** — recursively find `.txt`, `.md`, and `.pdf` files under `DATA_DIR`.
2. **Parse** — read text/markdown directly; extract PDF text via `pypdf` (best-effort — a PDF is skipped with a warning if `pypdf` is unavailable).
3. **Chunk** — deterministic recursive-character splitting (`CHUNK_SIZE` characters with `CHUNK_OVERLAP` overlap), preserving character offsets so every chunk is traceable back to its source document.
4. **Index** — embed and load into ChromaDB/FAISS. A corpus fingerprint is stored with the collection so a changed corpus is automatically re-indexed on restart.

Two document locations are supported:

- **`seed_corpus/`** — a shipped, clearly-synthetic, de-identified corpus. It is the default `DATA_DIR`, so the app runs out of the box. Regenerate it with:
  ```bash
  python scripts/generate_seed_corpus.py
  ```
- **`data/`** — for real documents. It is **git-ignored** (real healthcare data must never be committed) and mounted read-only in `docker-compose.yml`. Point the app at it with `DATA_DIR=data`.

### Vector Store Selection
- **ChromaDB**: Primary choice for persistent, production-grade vector storage with HTTP client support
- **FAISS**: In-memory fallback for development and high-availability scenarios
- Automatic failover with retry logic ensures continuous operation

### Embedding Strategy
- Sentence transformers (all-MiniLM-L6-v2) for efficient, high-quality embeddings
- 384-dimensional vectors balance performance and accuracy
- Batch processing support for scaling to larger document sets

### Answer Generation
- Context-aware prompts with retrieved documents
- Temperature-controlled generation (0.7) for balanced creativity
- Graceful degradation: returns retrieval results even if LLM fails

### Production Features
- Request/response timing middleware with `X-Process-Time` headers
- Global exception handling with debug-aware error messages
- Structured logging with timestamp, severity, and context
- Health checks compatible with Kubernetes/Docker Swarm
- Non-root container user for security
- Multi-stage Docker builds for minimal image size

## Performance

- **Embedding Generation**: ~50-100ms (sentence-transformers)
- **Vector Search**: ~5-20ms (ChromaDB/FAISS)
- **LLM Generation**: ~200-500ms (OpenAI API)
- **Total Response Time**: ~250-600ms end-to-end

## Security Considerations

- API keys loaded from environment (never committed)
- Non-root container execution
- CORS middleware with configurable origins
- Input validation with Pydantic
- Request size limits and query length constraints
- Health check endpoints don't expose sensitive data

## Scaling Strategies

### Horizontal Scaling
- Stateless API design allows multiple replicas
- ChromaDB supports distributed deployment
- Load balancer (Nginx/Traefik) for traffic distribution

### Vertical Scaling
- Increase uvicorn workers (CPU-bound)
- Optimize embedding model size vs. accuracy
- Batch processing for bulk queries

### Future Enhancements
- Add Pinecone/Milvus for cloud-native vector storage
- Implement caching layer (Redis) for frequent queries
- Add BM25 hybrid search for keyword matching
- Integrate reranking models for improved relevance
- Implement rate limiting and API key authentication

## Development Roadmap

- [ ] Add unit tests (pytest + pytest-asyncio)
- [ ] Implement query caching
- [ ] Add document upload endpoint
- [ ] Support multiple document formats (PDF, DOCX)
- [ ] Implement user authentication
- [ ] Add metrics and monitoring (Prometheus)
- [ ] Create evaluation pipeline (ROUGE, BLEU)

## License

MIT License - see LICENSE file for details

## Contact

For questions or collaboration opportunities, please open an issue or reach out via GitHub.

---

**Built with** FastAPI • ChromaDB • OpenAI • Docker