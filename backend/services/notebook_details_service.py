import os
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import logging

from models.schemas import NotebookMetadata

logger = logging.getLogger(__name__)

class NotebookDetailsService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    async def generate_details(self, text: str) -> NotebookMetadata:
        """Generate notebook details using AI"""
        try:
            prompt = f"""Based on the data provided, output an appropriate title and summary of the document. 

Also output an appropriate UTF-8 emoji for the notebook. - example: 🏆
And output an appropriate color from this list

slate
gray
zinc
neutral
stone
red
orange
amber
yellow
lime
green
emerald
teal
cyan
sky
blue
indigo
violet
purple
fuchsia
pink
rose

Also output a list of 5 Example Questions that could be asked of this document. For example "How are the rules and regulations of tennis enforced?" - Maximum 10 words each

Only output in JSON.

Document content (first 4000 characters):
{text[:4000]}"""

            response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
            response_text = response.generations[0][0].text

            parsed = json.loads(response_text)
            return NotebookMetadata(**parsed)

        except Exception as e:
            logger.error(f"Error generating notebook details: {e}")
            return NotebookMetadata(
                title="Untitled Notebook",
                summary="No summary available",
                notebook_icon="📝",
                background_color="slate",
                example_questions=[]
            )
