from typing import Any, AsyncGenerator
import logging
from app.providers.base import AIProvider
from app.core.config import settings

logger = logging.getLogger('jarvis.gemini')

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

JARVIS_SYSTEM_PROMPT = """You are J.A.R.V.I.S., a highly capable, concise, and professional personal AI assistant.
Keep your responses intelligent, calm, and slightly futuristic.
Do not be excessively verbose.
Do not pretend to have capabilities you do not currently possess (e.g., if you cannot execute OS commands yet, clearly state so).
"""

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        if self.api_key and genai:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def generate(self, prompt: str, memory_context: str = "") -> str:
        if not self.client:
            raise ValueError('Gemini API key not configured or google-genai not installed.')
        
        sys_inst = JARVIS_SYSTEM_PROMPT
        if memory_context:
            sys_inst += "\n" + memory_context

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
            )
        )
        return response.text

    async def stream(self, prompt: str, history: list = None, memory_context: str = "") -> AsyncGenerator[str, None]:
        if not self.client:
            raise ValueError('Gemini API key not configured.')
        
        # Format history for google-genai
        contents = []
        if history:
            for msg in history:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['content'])]))
        
        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=prompt)]))

        sys_inst = JARVIS_SYSTEM_PROMPT
        if memory_context:
            sys_inst += "\n" + memory_context

        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=sys_inst,
                )
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f'Gemini stream error: {e}')
            raise
