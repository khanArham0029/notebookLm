from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None

class Citation(BaseModel):
    chunk_index: int
    chunk_source_id: str
    chunk_lines_from: int
    chunk_lines_to: int

class AIResponseOutput(BaseModel):
    text: str
    citations: List[Citation] = []

class AIResponse(BaseModel):
    output: List[AIResponseOutput]

class DocumentUpload(BaseModel):
    file_path: str
    notebook_id: str
    source_id: str

class ProcessDocumentRequest(BaseModel):
    file_path: str
    source_id: str
    notebook_id: str

class ProcessDocumentResponse(BaseModel):
    success: bool
    message: str
    source_id: str

class NotebookGeneration(BaseModel):
    notebook_id: str
    source_type: str
    file_path: Optional[str] = None
    content: Optional[str] = None

class NotebookMetadata(BaseModel):
    title: str
    summary: str
    notebook_icon: str
    background_color: str
    example_questions: List[str]

class ExtractedText(BaseModel):
    extracted_text: str

class VectorStoreDocument(BaseModel):
    page_content: str
    metadata: Dict[str, Any]