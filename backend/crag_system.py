"""
Corrective RAG (CRAG) System
Combines retrieval, generation, and corrective validation
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import os

from dotenv import load_dotenv
import openai
import numpy as np
from sentence_transformers import SentenceTransformer

from Embeddings.faiss_retriever import FAISSRetriever

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("crag_system")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBEDDING_MODEL = "all-mpnet-base-v2"  # 768-dim model, compatible with your FAISS index
LLM_MODEL = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "openai" or "groq" - default is groq (free)


class CRAGRetriever:
    """Handles document retrieval for CRAG"""
    
    def __init__(self, faiss_retriever: FAISSRetriever, top_k: int = 5):
        """
        Initialize CRAG Retriever
        
        Args:
            faiss_retriever: FAISSRetriever instance
            top_k: Number of documents to retrieve
        """
        self.retriever = faiss_retriever
        self.top_k = top_k
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        LOGGER.info(f"CRAGRetriever initialized with top_k={top_k}")
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query string
            
        Returns:
            List of retrieved documents with scores
        """
        try:
            # Embed the query
            query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
            
            # Search FAISS index using retrieve() method
            results = self.retriever.retrieve(query_embedding, k=self.top_k)
            
            # Convert results to expected format
            retrieved_docs = []
            for doc_metadata, score in results:
                retrieved_docs.append({
                    'id': doc_metadata.get('id', 0),
                    'content': doc_metadata.get('text', doc_metadata.get('content', '')),
                    'source': doc_metadata.get('metadata', {}).get('source_title', 'Unknown'),
                    'score': float(score),
                    'metadata': doc_metadata
                })
            
            LOGGER.info(f"Retrieved {len(retrieved_docs)} documents for query: {query[:50]}...")
            return retrieved_docs
            
        except Exception as e:
            LOGGER.error(f"Error during retrieval: {e}")
            return []


class CRAGGenerator:
    """Handles response generation using LLM (OpenAI or Groq)"""
    
    def __init__(self, model: str = LLM_MODEL, api_key: Optional[str] = None, provider: str = "groq"):
        """
        Initialize CRAG Generator
        
        Args:
            model: LLM model name
            api_key: API key for the provider
            provider: "openai" or "groq"
        """
        self.model = model
        self.provider = provider
        
        if provider == "groq":
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key or GROQ_API_KEY)
            except ImportError:
                raise ImportError("Groq SDK not installed. Run: pip install groq")
        elif provider == "openai":
            import openai
            openai.api_key = api_key or OPENAI_API_KEY
            self.client = openai
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        LOGGER.info(f"CRAGGenerator initialized with provider={provider}, model={model}")
    
    def generate(self, query: str, context: List[Dict]) -> str:
        """
        Generate response using LLM with retrieved context
        
        Args:
            query: User query
            context: List of retrieved documents
            
        Returns:
            Generated response string
        """
        if not context:
            return "No relevant context found. Unable to generate a response."
        
        try:
            # Build context string
            context_str = self._build_context(context)
            
            # Create prompt
            prompt = self._create_prompt(query, context_str)
            
            # Call LLM based on provider
            if self.provider == "groq":
                return self._generate_groq(prompt)
            elif self.provider == "openai":
                return self._generate_openai(prompt)
                
        except Exception as e:
            LOGGER.error(f"Error during generation: {e}")
            return f"Error generating response: {str(e)}"
    
    def _generate_groq(self, prompt: str) -> str:
        """Generate using Groq (free, fast)"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Stable Groq model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for Meezan Bank. Answer questions based on the provided context. If the context doesn't contain relevant information, say so."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            LOGGER.info(f"Generated response using Groq")
            return answer
            
        except Exception as e:
            LOGGER.error(f"Groq generation error: {e}")
            raise
    
    def _generate_openai(self, prompt: str) -> str:
        """Generate using OpenAI (paid)"""
        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for Meezan Bank. Answer questions based on the provided context. If the context doesn't contain relevant information, say so."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response['choices'][0]['message']['content']
            LOGGER.info(f"Generated response using OpenAI")
            return answer
            
        except Exception as e:
            LOGGER.error(f"OpenAI generation error: {e}")
            raise
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        context = "## Relevant Context\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"### Source {i}: {doc.get('source', 'Unknown')}\n"
            context += f"Content: {doc.get('content', '')}\n\n"
        return context
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt for LLM"""
        return f"""{context}

## User Question:
{query}

## Answer:
Based on the provided context, here's my answer:"""


class CRAGCorrector:
    """Corrective layer to validate LLM response against context"""
    
    def __init__(self, model: str = LLM_MODEL, api_key: Optional[str] = None, provider: str = "groq"):
        """
        Initialize CRAG Corrector
        
        Args:
            model: LLM model name
            api_key: API key
            provider: "openai" or "groq"
        """
        self.model = model
        self.provider = provider
        
        if provider == "groq":
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key or GROQ_API_KEY)
            except ImportError:
                raise ImportError("Groq SDK not installed. Run: pip install groq")
        elif provider == "openai":
            import openai
            openai.api_key = api_key or OPENAI_API_KEY
            self.client = openai
            
        LOGGER.info(f"CRAGCorrector initialized with provider={provider}")
    
    def verify_response(self, query: str, response: str, context: List[Dict]) -> Dict:
        """
        Verify if response is grounded in the retrieved context
        
        Args:
            query: Original user query
            response: Generated response
            context: Retrieved context documents
            
        Returns:
            Verification result with feedback
        """
        try:
            context_str = self._build_context(context)
            
            verification_prompt = f"""{context_str}

## Generated Response to Verify:
{response}

## Verification Task:
1. Is this response grounded in the provided context?
2. Are there any hallucinations or unsupported claims?
3. Is the response accurate and helpful?

Provide your verification in JSON format:
{{
    "is_grounded": true/false,
    "confidence": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "suggestions": "improvement suggestions if any"
}}"""

            if self.provider == "groq":
                result_text = self._verify_groq(verification_prompt)
            else:
                result_text = self._verify_openai(verification_prompt)
            
            # Parse JSON from response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    json_str = result_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result_text
                
                result = json.loads(json_str)
            except:
                result = {
                    "is_grounded": True,
                    "confidence": 0.5,
                    "issues": [],
                    "suggestions": result_text
                }
            
            LOGGER.info(f"Verification result - Grounded: {result.get('is_grounded')}")
            return result
            
        except Exception as e:
            LOGGER.error(f"Error during verification: {e}")
            return {
                "is_grounded": False,
                "confidence": 0.0,
                "issues": [str(e)],
                "suggestions": "Verification failed. Please try again."
            }
    
    def _verify_groq(self, prompt: str) -> str:
        """Verify using Groq"""
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Stable model
            messages=[
                {
                    "role": "system",
                    "content": "You are a verification expert. Analyze if the response is grounded in the context. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    
    def _verify_openai(self, prompt: str) -> str:
        """Verify using OpenAI"""
        response = self.client.ChatCompletion.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a verification expert. Analyze if the response is grounded in the context."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response['choices'][0]['message']['content']
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from documents"""
        context = "## Available Context:\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"{i}. {doc.get('content', '')[:200]}...\n"
        return context


class CRAGSystem:
    """Complete CRAG system combining retrieval, generation, and correction"""
    
    def __init__(
        self,
        faiss_retriever: FAISSRetriever,
        llm_model: str = LLM_MODEL,
        api_key: Optional[str] = None,
        top_k: int = 5,
        provider: str = "groq"
    ):
        """
        Initialize complete CRAG system
        
        Args:
            faiss_retriever: FAISSRetriever instance
            llm_model: LLM model name
            api_key: API key
            top_k: Number of documents to retrieve
            provider: "groq" (free, fast) or "openai" (paid, powerful)
        """
        self.retriever = CRAGRetriever(faiss_retriever, top_k=top_k)
        self.generator = CRAGGenerator(llm_model, api_key, provider=provider)
        self.corrector = CRAGCorrector(llm_model, api_key, provider=provider)
        self.provider = provider
        LOGGER.info(f"CRAG System initialized with provider={provider}")
    
    def query(self, question: str, use_correction: bool = True) -> Dict:
        """
        Process a query through the complete CRAG pipeline
        
        Args:
            question: User question
            use_correction: Whether to use the corrective layer
            
        Returns:
            Complete response with context, answer, and verification
        """
        LOGGER.info(f"Processing query: {question}")
        
        # Step 1: Retrieve relevant documents
        context = self.retriever.retrieve(question)
        
        # Step 2: Generate response
        response = self.generator.generate(question, context)
        
        # Step 3: (Optional) Verify response
        verification = None
        if use_correction and self.provider == "openai":  # Only correct with OpenAI for cost
            verification = self.corrector.verify_response(question, response, context)
        
        result = {
            "query": question,
            "answer": response,
            "context": context,
            "verification": verification,
            "status": "success"
        }
        
        return result
    
    def query_without_correction(self, question: str) -> Dict:
        """Faster query without correction layer"""
        return self.query(question, use_correction=False)


if __name__ == "__main__":
    # Test the CRAG system
    try:
        # Initialize FAISS retriever
        faiss_retriever = FAISSRetriever()
        
        # Initialize CRAG system
        crag = CRAGSystem(faiss_retriever, top_k=5)
        
        # Example query
        test_query = "What is Meezan Bank?"
        result = crag.query(test_query)
        
        print("\n" + "="*60)
        print("CRAG System Test")
        print("="*60)
        print(f"Query: {result['query']}")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nContext Retrieved: {len(result['context'])} documents")
        if result['verification']:
            print(f"Verification - Grounded: {result['verification'].get('is_grounded')}")
            print(f"Confidence: {result['verification'].get('confidence')}")
        print("="*60)
        
    except Exception as e:
        LOGGER.error(f"Test failed: {e}")
