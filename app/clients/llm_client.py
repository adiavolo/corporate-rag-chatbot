from abc import ABC, abstractmethod
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import openai
from loguru import logger
from app.core.config import LLMConfig
from app.core.exceptions import LLMError

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text response from prompt."""
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """Check availability."""
        pass

class OpenRouterClient(LLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = openai.OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
        self.model = self.config.model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Corporate RAG Bot"
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            # We don't log here if we re-raise and log in callers, but we should log raw errors
            logger.warning(f"OpenRouter attempt failed: {e}")
            raise e # Retry will catch this

    def generate(self, prompt: str) -> str:
        try:
            return self._make_request(prompt)
        except Exception as e:
            logger.error(f"LLM Generation failed after retries: {e}")
            raise LLMError(f"OpenRouter API failed: {str(e)}")

    def check_health(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False
