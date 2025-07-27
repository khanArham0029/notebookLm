import os
import json
import asyncio
from typing import List, Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from supabase import create_client, Client
import logging

from models.schemas import AIResponse, AIResponseOutput, Citation

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are tasked with answering a question using provided chunks of information.

Your goal is to provide an accurate answer from these chunks while citing your sources. When you use information from a specific chunk in your answer, you must cite it using the specified JSON output format.

The citation should appear at the end of the sentence or paragraph where the information is used.

If you cannot answer the question using the provided chunks, say "Sorry I don't know".

Context:
{context}

Question: {query}

Please respond in the following JSON format:
{{
    "output": [
        {{
            "text": "Your response text here...",
            "citations": [
                {{
                    "chunk_index": 0,
                    "chunk_source_id": "source_id_here",
                    "chunk_lines_from": 1,
                    "chunk_lines_to": 50
                }}
            ]
        }}
    ]
}}

Important: Only base your answers on information in the provided chunks from the vector store."""

class ChatService:
    def __init__(self):
        # Initialize Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        
        # Memory for conversations
        self.conversations: Dict[str, ConversationBufferWindowMemory] = {}
    
    def get_conversation_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationBufferWindowMemory(
                k=20,  # Keep last 20 messages
                return_messages=True
            )
        return self.conversations[session_id]
    
    async def retrieve_relevant_documents(self, query: str, notebook_id: str, k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from vector store"""
        try:
            # Search for relevant documents
            docs = await self.vector_store.asimilarity_search_with_score(
                query,
                k=k,
                filter={"notebook_id": notebook_id}
            )
            
            relevant_docs = []
            for doc, score in docs:
                relevant_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return relevant_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def generate_response_with_citations(self, query: str, relevant_docs: List[Dict[str, Any]]) -> AIResponse:
        """Generate AI response with citations"""
        try:
            context_parts = []
            for i, doc in enumerate(relevant_docs):
                context_parts.append(f"[Document {i}]: {doc['content']}")
            
            context = "\n\n".join(context_parts)
            
            prompt = PROMPT_TEMPLATE.format(context=context, query=query)

            response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
            ai_response_text = response.generations[0][0].text
            
            try:
                parsed_response = json.loads(ai_response_text)
                return AIResponse(**parsed_response)
            except json.JSONDecodeError:
                return AIResponse(output=[
                    AIResponseOutput(
                        text=ai_response_text,
                        citations=[]
                    )
                ])
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return AIResponse(output=[
                AIResponseOutput(
                    text="Sorry, I encountered an error creating a response. Please check the error log.",
                    citations=[]
                )
            ])
    
    async def save_message_to_db(self, session_id: str, message_type: str, content: str):
        """Save message to database"""
        try:
            message_data = {
                "session_id": session_id,
                "message": {
                    "type": message_type,
                    "content": content,
                }
            }
            
            result = self.supabase.table("chat_histories").insert(message_data).execute()
            logger.info(f"Saved message to database: {result}")
            
        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
    
    async def process_message(self, session_id: str, message: str, user_id: str) -> AIResponse:
        """Process a chat message and generate response"""
        try:
            logger.info(f"Processing message for session {session_id}: {message}")
            
            await self.save_message_to_db(session_id, "human", message)
            
            memory = self.get_conversation_memory(session_id)
            memory.chat_memory.add_user_message(message)
            
            relevant_docs = await self.retrieve_relevant_documents(message, session_id)
            
            if not relevant_docs:
                ai_response = AIResponse(output=[
                    AIResponseOutput(
                        text="I don't have any relevant information to answer your question. Please make sure you have uploaded documents to this notebook.",
                        citations=[]
                    )
                ])
            else:
                ai_response = await self.generate_response_with_citations(message, relevant_docs)
            
            ai_response_json = ai_response.json()
            
            await self.save_message_to_db(session_id, "ai", ai_response_json)
            
            memory.chat_memory.add_ai_message(ai_response_json)
            
            logger.info(f"Successfully processed message for session {session_id}")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = AIResponse(output=[
                AIResponseOutput(
                    text="Sorry, I encountered an error processing your message. Please try again.",
                    citations=[]
                )
            ])
            await self.save_message_to_db(session_id, "ai", error_response.json())
            return error_response