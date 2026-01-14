from openai import AsyncOpenAI
from core.config import Config

class LLMProvider:
    @staticmethod
    def get_client():
        """
        Generic client factory. 
        Detects if we are using a custom HF/Ollama endpoint or standard OpenAI.
        """
        if Config.BASE_URL:
            return AsyncOpenAI(
                    base_url=Config.BASE_URL,
                api_key=Config.API_KEY or Config.OPENAI_API_KEY
            )
        else:
            # Default to standard OpenAI
            return AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

# Singleton client instance
llm_client = LLMProvider.get_client()
