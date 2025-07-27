from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging

from services.chat_service import ChatService
from services.document_service import DocumentService
from services.notebook_service import NotebookService
from services.auth_service import AuthService
from services.notebook_details_service import NotebookDetailsService
from services.additional_sources_service import AdditionalSourcesService
from models.schemas import (
    ChatMessage, AIResponse, DocumentUpload, NotebookGeneration,
    ProcessDocumentRequest, ProcessDocumentResponse
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InsightsLM API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
auth_service = AuthService()
document_service = DocumentService()
notebook_details_service = NotebookDetailsService()
notebook_service = NotebookService(document_service, notebook_details_service)
additional_sources_service = AdditionalSourcesService(document_service)
chat_service = ChatService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and get current user"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.get("/")
async def root():
    return {"message": "InsightsLM API is running"}

@app.post("/chat/send", response_model=AIResponse)
async def send_chat_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send a chat message and get AI response"""
    try:
        response = await chat_service.process_message(
            message.session_id,
            message.message,
            current_user["id"]
        )
        return response
    except Exception as e:
        logger.error(f"Error in send_chat_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process a document and extract text"""
    try:
        await document_service.process_document(
            request.file_path,
            request.source_id,
            request.notebook_id
        )
        
        return ProcessDocumentResponse(
            success=True,
            message="Document processing started",
            source_id=request.source_id
        )
    except Exception as e:
        logger.error(f"Error in process_document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notebooks/generate")
async def generate_notebook_content(
    request: NotebookGeneration,
    current_user: dict = Depends(get_current_user)
):
    """Generate notebook title, description, and metadata"""
    try:
        await notebook_service.generate_notebook_content(
            request.notebook_id,
            request.source_type,
            request.file_path,
            request.content
        )
        
        return {"success": True, "message": "Notebook generation started"}
    except Exception as e:
        logger.error(f"Error in generate_notebook_content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sources/process-additional")
async def process_additional_sources(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Process additional sources (websites, text, etc.)"""
    try:
        source_type = request.get("type")
        notebook_id = request.get("notebookId")
        
        if source_type == "multiple-websites":
            await additional_sources_service.process_multiple_websites(
                notebook_id,
                request.get("urls", []),
                request.get("sourceIds", [])
            )
        elif source_type == "copied-text":
            await additional_sources_service.process_copied_text(
                notebook_id,
                request.get("title"),
                request.get("content"),
                request.get("sourceIds", [None])[0]
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")
        
        return {"success": True, "message": f"Processing {source_type} started"}
    except Exception as e:
        logger.error(f"Error in process_additional_sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
