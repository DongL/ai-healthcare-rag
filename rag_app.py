import logging
import sys
import time
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import BaseModel, Field, validator
from sentence_transformers import SentenceTransformer

from config import settings

# Import vector stores
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, will use FAISS fallback")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# ------------------------------
# Production RAG Healthcare API
# ------------------------------

# Configure structured logging using settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready RAG API for healthcare document retrieval",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# CORS middleware using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# Application startup
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")
    try:
        global model, chroma_client, collection, faiss_index, faiss_documents, openai_client, use_chromadb

        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        else:
            openai_client = None
            logger.warning("OPENAI_API_KEY not set - answer generation disabled")

        # Load embedding model using settings
        logger.info(f"Loading sentence transformer model: {settings.EMBEDDING_MODEL}")
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Model loaded successfully")

        # Synthetic healthcare corpus (de-identified)
        documents = [
            "Patients with hypertension should monitor their blood pressure regularly.",
            "Metformin is commonly prescribed as a first-line therapy for type 2 diabetes.",
            "MRI is a non-invasive imaging technique often used to detect brain tumors.",
            "COVID-19 vaccines have significantly reduced severe cases and mortality rates.",
        ]

        # Initialize vector store (ChromaDB with FAISS fallback)
        use_chromadb = False
        chroma_client = None
        collection = None
        faiss_index = None
        faiss_documents = None

        if settings.USE_CHROMADB and CHROMADB_AVAILABLE:
            try:
                # Initialize ChromaDB client with retry logic
                logger.info(f"Connecting to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")

                import time
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        chroma_client = chromadb.HttpClient(
                            host=settings.CHROMA_HOST,
                            port=settings.CHROMA_PORT
                        )
                        # Test connection
                        chroma_client.heartbeat()
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.info(f"ChromaDB connection attempt {attempt + 1} failed, retrying...")
                            time.sleep(2)
                        else:
                            raise

                logger.info("ChromaDB client connected")

                # Get or create collection
                collection = chroma_client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": settings.CHROMA_DISTANCE_METRIC}
                )
                logger.info(f"Collection '{settings.CHROMA_COLLECTION_NAME}' ready")

                # Populate ChromaDB collection if empty
                if collection.count() == 0:
                    logger.info("Populating ChromaDB collection...")
                    embeddings = model.encode(documents).tolist()
                    collection.add(
                        embeddings=embeddings,
                        documents=documents,
                        ids=[f"doc_{i}" for i in range(len(documents))],
                        metadatas=[{"source": "synthetic", "index": i} for i in range(len(documents))]
                    )
                    logger.info(f"Added {len(documents)} documents to ChromaDB")
                else:
                    logger.info(f"Collection already contains {collection.count()} documents")

                use_chromadb = True
                logger.info("Using ChromaDB as vector store")

            except Exception as chroma_error:
                logger.warning(f"ChromaDB initialization failed: {chroma_error}")
                logger.info("Falling back to FAISS")
                use_chromadb = False

        if not use_chromadb:
            if not FAISS_AVAILABLE:
                raise RuntimeError("Neither ChromaDB nor FAISS is available. Cannot start application.")

            # Fallback to FAISS
            logger.info("Initializing FAISS fallback...")
            faiss_documents = documents
            embeddings = np.array(model.encode(documents)).astype('float32')
            faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
            faiss_index.add(embeddings)
            logger.info(f"FAISS index built with {len(documents)} documents")
            logger.info("Using FAISS as vector store")

        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")

# Request/response timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response


# Request/Response models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=settings.MAX_QUERY_LENGTH, description="Search query text")
    k: int = Field(default=settings.DEFAULT_RESULTS, ge=1, le=settings.MAX_RESULTS, description="Number of results to retrieve")

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class QueryResponse(BaseModel):
    query: str
    retrieved_contexts: list[str]
    num_results: int
    answer: Optional[str] = None  # LLM-generated answer
    processing_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime_seconds: Optional[float] = None
    index_size: Optional[int] = None


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Verify critical components are loaded
        if 'model' not in globals():
            raise HTTPException(status_code=503, detail="Service not ready")

        # Determine index size based on active vector store
        index_size = 0
        if use_chromadb and collection is not None:
            index_size = collection.count()
        elif faiss_index is not None and faiss_documents is not None:
            index_size = len(faiss_documents)

        return HealthResponse(
            status="healthy",
            version=settings.APP_VERSION,
            timestamp=datetime.utcnow().isoformat(),
            index_size=index_size
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/rag", response_model=QueryResponse, tags=["RAG"])
async def rag_endpoint(request: QueryRequest):
    """
    Retrieve relevant healthcare documents and generate an answer using OpenAI

    - **query**: The search query text (1-500 characters)
    - **k**: Number of results to return (1-10, default: 2)
    """
    try:
        start_time = time.time()

        logger.info(f"Processing RAG query: '{request.query}' (k={request.k})")

        # Query based on active vector store
        results = []

        if use_chromadb and collection is not None:
            # Query ChromaDB
            query_embedding = model.encode([request.query]).tolist()
            chroma_results = collection.query(
                query_embeddings=query_embedding,
                n_results=request.k
            )
            results = chroma_results['documents'][0] if chroma_results['documents'] else []

        elif faiss_index is not None and faiss_documents is not None:
            # Query FAISS fallback
            query_embedding = np.array(model.encode([request.query])).astype('float32')
            D, I = faiss_index.search(query_embedding, k=request.k)
            results = [faiss_documents[i] for i in I[0] if i < len(faiss_documents)]

        else:
            raise HTTPException(status_code=503, detail="No vector store available")

        # Generate answer using OpenAI
        answer = None
        if settings.GENERATE_ANSWER and openai_client and results:
            try:
                context = "\n".join(results)
                completion = openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful medical assistant. Answer questions based only on the provided context. If the context doesn't contain relevant information, say so."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.query}\n\nAnswer:"}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                answer = completion.choices[0].message.content
                logger.info("Generated answer using OpenAI")
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}")
                answer = None

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(f"Retrieved {len(results)} documents in {processing_time:.2f}ms")

        return QueryResponse(
            query=request.query,
            retrieved_contexts=results,
            num_results=len(results),
            answer=answer,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.utcnow().isoformat()
        )

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"RAG endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query")
