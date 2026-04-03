"""
FastAPI Backend for CRAG System
Provides REST API endpoints for CRAG queries
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from crag_system import CRAGSystem
from Embeddings.faiss_retriever import FAISSRetriever

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Meezan CRAG API",
    description="Corrective RAG System for Meezan Bank",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global CRAG system instance
crag_system = None


class QueryRequest(BaseModel):
    """Request model for CRAG queries"""
    query: str
    use_correction: bool = True
    top_k: int = 5


class QueryResponse(BaseModel):
    """Response model for CRAG queries"""
    query: str
    answer: str
    context: List[dict]
    verification: Optional[dict] = None
    status: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize CRAG system on startup"""
    global crag_system
    try:
        logger.info("Initializing CRAG System...")
        faiss_retriever = FAISSRetriever()
        
        # Use Groq by default (free), switch to openai if needed
        provider = os.getenv("LLM_PROVIDER", "groq")
        
        crag_system = CRAGSystem(
            faiss_retriever,
            llm_model="llama-3.1-8b-instant" if provider == "groq" else "gpt-4-turbo-preview",
            api_key=os.getenv("GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"),
            top_k=5,
            provider=provider
        )
        logger.info(f"✅ CRAG System initialized successfully with provider={provider}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize CRAG System: {e}")
        crag_system = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if crag_system:
        return {
            "status": "healthy",
            "message": "CRAG System is ready"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail="CRAG System not initialized"
        )


@app.post("/query", response_model=QueryResponse)
async def query_crag(request: QueryRequest):
    """
    Process a query through CRAG system
    
    Args:
        request: Query request with question and options
        
    Returns:
        CRAG response with answer, context, and verification
    """
    if not crag_system:
        raise HTTPException(
            status_code=503,
            detail="CRAG System not initialized"
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info(f"Processing query: {request.query[:50]}...")
        
        # Update top_k if different
        if request.top_k != crag_system.retriever.top_k:
            crag_system.retriever.top_k = request.top_k
        
        # Process query
        result = crag_system.query(request.query, use_correction=request.use_correction)
        
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            context=result["context"],
            verification=result["verification"],
            status=result["status"]
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/query-fast")
async def query_crag_fast(request: QueryRequest):
    """
    Fast query without correction (for speed)
    
    Args:
        request: Query request
        
    Returns:
        CRAG response without verification
    """
    if not crag_system:
        raise HTTPException(
            status_code=503,
            detail="CRAG System not initialized"
        )
    
    try:
        logger.info(f"Processing fast query: {request.query[:50]}...")
        result = crag_system.query_without_correction(request.query)
        
        return {
            "query": result["query"],
            "answer": result["answer"],
            "context": result["context"],
            "status": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error processing fast query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Meezan CRAG API",
        "version": "1.0.0",
        "description": "Corrective RAG System for Meezan Bank",
        "endpoints": {
            "POST /query": "Full CRAG query with correction",
            "POST /query-fast": "Fast query without correction",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with: uvicorn main:app --reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
