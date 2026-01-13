from openai import AsyncOpenAI
from core.config import Config

class LLMProvider:
    @staticmethod
    def get_client():
        """
        Generic client factory. 
        Detects if we are using a custom HF/Ollama endpoint or standard OpenAI.
        """
        if Config.LLM_PROVIDER == "huggingface":
            return AsyncOpenAI(
                base_url=f"{Config.HF_SPACE_URL}/v1",
                api_key=Config.HF_TOKEN
            )
        else:
            # Default to standard OpenAI
            return AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

# Singleton client instance
llm_client = LLMProvider.get_client()