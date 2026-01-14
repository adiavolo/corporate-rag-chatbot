import openai
from app.config import settings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenRouterClient:
    def __init__(self):
        self.client = openai.OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY
        )
        self.model = settings.LLM_MODEL

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat_completion(self, messages: list, temperature: float = None) -> str:
        """
        Sends a chat completion request to OpenRouter.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                # OpenRouter specific headers can be added here if needed, usually via extra_headers
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000", # Required by OpenRouter
                    "X-Title": "Corporate RAG Bot"
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise e

    def check_health(self) -> bool:
        """
        Simple ping to check if API key is valid and service reachable.
        Uses a very cheap/free model or just checks if we get an auth error.
        """
        try:
            # Just listing models or a tiny completion
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False

openrouter_client = OpenRouterClient()
