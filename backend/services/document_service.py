import os
import asyncio
import aiohttp
from typing import List, Optional
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from supabase import create_client, Client
import logging
import tempfile
import fitz  # PyMuPDF
from io import BytesIO
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class DocumentService:
    def __init__(self):
        # Initialize Supabase
        self.supabase_url =os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        
        print(f"[DEBUG DocumentService] SUPABASE_URL: {self.supabase_url}")
        print(f"[DEBUG DocumentService] SUPABASE_SERVICE_ROLE_KEY: {self.supabase_key}")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing required Supabase environment variables in DocumentService")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def download_file_from_supabase(self, file_path: str) -> bytes:
        """Download file from Supabase storage"""
        try:
            signed_url_response = self.supabase.storage.from_("sources").create_signed_url(
                file_path, 60
            )
            
            if not signed_url_response.get("signedURL"):
                raise Exception("Failed to generate signed URL")
            
            signed_url = signed_url_response["signedURL"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(signed_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        raise Exception(f"Failed to download file: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
            
    def extract_text_from_file(self, file_bytes: bytes, file_path: str) -> str:
        """Extract text from various file types"""
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self.extract_text_from_pdf(file_bytes)
            elif file_extension in ['txt', 'md']:
                return file_bytes.decode('utf-8')
            else:
                try:
                    return file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    raise Exception(f"Unsupported file type: {file_extension}")
                    
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            raise
    
    async def process_document(self, file_path: str, source_id: str, notebook_id: str):
        """Process a document and add to vector store"""
        try:
            logger.info(f"Processing document: {file_path}")
            
            file_bytes = await self.download_file_from_supabase(file_path)
            
            extracted_text = self.extract_text_from_file(file_bytes, file_path)
            
            title, summary = await self.generate_title_and_summary(extracted_text)
            
            self.supabase.table("sources").update({
                "content": extracted_text,
                "display_name": title,
                "summary": summary,
                "processing_status": "completed"
            }).eq("id", source_id).execute()
            
            await self.process_text_for_vector_store(extracted_text, source_id, notebook_id, title)
            
            logger.info(f"Successfully processed document: {source_id}")
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            self.supabase.table("sources").update({
                "processing_status": "failed"
            }).eq("id", source_id).execute()
            raise
    
    async def generate_title_and_summary(self, text: str) -> tuple[str, str]:
        """Generate title and summary for document using AI"""
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.schema import HumanMessage
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            prompt = f"""Based on the data provided, output an appropriate title and summary of the document.

Only output in JSON in the following format:
{{
    "title": "<ADD>",
    "summary": "<ADD>"
}}

Document content (first 4000 characters):
{text[:4000]}"""

            response = await llm.agenerate([[HumanMessage(content=prompt)]])
            response_text = response.generations[0][0].text
            
            import json
            parsed = json.loads(response_text)
            return parsed["title"], parsed["summary"]
            
        except Exception as e:
            logger.error(f"Error generating title and summary: {e}")
            return "Untitled Document", "No summary available"
    
    async def add_documents_to_vector_store(self, documents: List[Document]):
        """Add documents to vector store"""
        try:
            # Add documents to vector store
            await self.vector_store.aadd_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    async def fetch_webpage_content(self, url: str) -> str:
        """Fetch webpage content using Jina.ai"""
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"Accept": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("content", "")
                    else:
                        raise Exception(f"Failed to fetch webpage: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {e}")
            raise
    
    async def process_multiple_websites(self, notebook_id: str, urls: List[str], source_ids: List[str]):
        """Process multiple websites"""
        try:
            for i, url in enumerate(urls):
                source_id = source_ids[i] if i < len(source_ids) else None
                if not source_id:
                    continue
                
                try:
                    content = await self.fetch_webpage_content(url)
                    
                    title, summary = await self.generate_title_and_summary(content)
                    
                    file_path = f"{notebook_id}/{source_id}.txt"
                    file_content = f"{url}\n{content}"
                    
                    self.supabase.storage.from_("sources").upload(
                        file_path,
                        file_content.encode('utf-8'),
                        {"content-type": "text/plain"}
                    )
                    
                    self.supabase.table("sources").update({
                        "content": content,
                        "title": title,
                        "display_name": title,
                        "summary": summary,
                        "file_path": file_path,
                        "file_size": len(file_content),
                        "processing_status": "completed"
                    }).eq("id", source_id).execute()
                    
                    await self.process_text_for_vector_store(content, source_id, notebook_id, title)
                    
                except Exception as e:
                    logger.error(f"Error processing website {url}: {e}")
                    self.supabase.table("sources").update({
                        "processing_status": "failed"
                    }).eq("id", source_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing multiple websites: {e}")
            raise
    
    async def process_copied_text(self, notebook_id: str, title: str, content: str, source_id: str):
        """Process copied text"""
        try:
            _, summary = await self.generate_title_and_summary(content)
            
            file_path = f"{notebook_id}/{source_id}.txt"
            
            self.supabase.storage.from_("sources").upload(
                file_path,
                content.encode('utf-8'),
                {"content-type": "text/plain"}
            )
            
            self.supabase.table("sources").update({
                "content": content,
                "title": title,
                "display_name": title,
                "summary": summary,
                "file_path": file_path,
                "file_size": len(content),
                "processing_status": "completed"
            }).eq("id", source_id).execute()
            
            await self.process_text_for_vector_store(content, source_id, notebook_id, title)
            
        except Exception as e:
            logger.error(f"Error processing copied text: {e}")
            self.supabase.table("sources").update({
                "processing_status": "failed"
            }).eq("id", source_id).execute()
            raise
    
    async def process_text_for_vector_store(self, text: str, source_id: str, notebook_id: str, title: str):
        """Process text and add to vector store"""
        try:
            documents = self.text_splitter.create_documents(
                [text],
                metadatas=[{
                    "source_id": source_id,
                    "notebook_id": notebook_id,
                    "title": title
                }]
            )
            
            await self.add_documents_to_vector_store(documents)
            
        except Exception as e:
            logger.error(f"Error processing text for vector store: {e}")
            raise