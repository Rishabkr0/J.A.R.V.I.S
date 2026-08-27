from abc import ABC, abstractmethod
from typing import Any

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    async def stream(self, prompt: str) -> Any:
        pass

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        # Initialize gracefully even without key
    
    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError('Gemini API key not configured.')
        return 'Not implemented'

    async def stream(self, prompt: str) -> Any:
        if not self.api_key:
            raise ValueError('Gemini API key not configured.')
        yield 'Not implemented'

class LocalProvider(AIProvider):
    async def generate(self, prompt: str) -> str:
        return 'Not implemented'
    
    async def stream(self, prompt: str) -> Any:
        yield 'Not implemented'
