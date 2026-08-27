import logging
import time
from typing import AsyncGenerator
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider

logger = logging.getLogger('jarvis.router')

class BrainRouter:
    def __init__(self):
        self.gemini_provider = GeminiProvider()

    def select_provider(self) -> AIProvider:
        return self.gemini_provider

    async def stream_response(self, prompt: str, history: list = None) -> AsyncGenerator[dict, None]:
        provider = self.select_provider()
        
        start_time = time.time()
        logger.info('Provider routing started.')
        
        try:
            stream = provider.stream(prompt, history)
            first_token_received = False
            
            async for chunk in stream:
                if not first_token_received:
                    first_token_received = True
                    time_to_first_token = time.time() - start_time
                    logger.info(f'First token received in {time_to_first_token:.3f}s')
                yield {'chunk': chunk}
                
            total_time = time.time() - start_time
            logger.info(f'Generation completed in {total_time:.3f}s')
            
        except Exception as e:
            logger.error(f'Provider error: {e}')
            yield {'error': str(e)}
