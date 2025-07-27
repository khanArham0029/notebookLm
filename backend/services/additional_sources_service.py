import asyncio
import aiohttp
from typing import List
import logging

from services.document_service import DocumentService

logger = logging.getLogger(__name__)

class AdditionalSourcesService:
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service

    async def process_multiple_websites(self, notebook_id: str, urls: List[str], source_ids: List[str]):
        """Process multiple websites"""
        await self.document_service.process_multiple_websites(notebook_id, urls, source_ids)

    async def process_copied_text(self, notebook_id: str, title: str, content: str, source_id: str):
        """Process copied text"""
        await self.document_service.process_copied_text(notebook_id, title, content, source_id)
