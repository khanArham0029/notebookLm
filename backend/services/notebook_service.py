import os
from supabase import create_client, Client
import logging

from services.document_service import DocumentService
from services.notebook_details_service import NotebookDetailsService

logger = logging.getLogger(__name__)

class NotebookService:
    def __init__(self, document_service: DocumentService, notebook_details_service: NotebookDetailsService):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.document_service = document_service
        self.notebook_details_service = notebook_details_service

    async def generate_notebook_content(self, notebook_id: str, source_type: str, file_path: str = None, content: str = None):
        """Generate notebook content including title, description, and metadata"""
        try:
            logger.info(f"Generating notebook content for: {notebook_id}")

            self.supabase.table("notebooks").update({
                "generation_status": "generating"
            }).eq("id", notebook_id).execute()

            if source_type == 'file' and file_path:
                file_bytes = await self.document_service.download_file_from_supabase(file_path)
                extracted_text = self.document_service.extract_text_from_file(file_bytes, file_path)
            elif content:
                extracted_text = content
            else:
                raise ValueError("Either file_path or content must be provided")

            metadata = await self.notebook_details_service.generate_details(extracted_text)

            self.supabase.table("notebooks").update({
                "title": metadata.title,
                "description": metadata.summary,
                "icon": metadata.notebook_icon,
                "background_color": metadata.background_color,
                "example_questions": metadata.example_questions,
                "generation_status": "completed"
            }).eq("id", notebook_id).execute()

            logger.info(f"Successfully generated notebook content for: {notebook_id}")

        except Exception as e:
            logger.error(f"Error generating notebook content: {e}")
            self.supabase.table("notebooks").update({
                "generation_status": "failed"
            }).eq("id", notebook_id).execute()
            raise