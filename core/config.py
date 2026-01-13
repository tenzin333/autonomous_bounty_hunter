import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Your HF Space URL (e.g., https://username-spacename.hf.space/v1)
    # Ensure you append /v1 if using Ollama's OpenAI compatibility layer
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai") # or "huggingface"
    HF_SPACE_URL = os.getenv("HF_SPACE_URL") 
    HF_TOKEN = os.getenv("HF_TOKEN") # Use your HF Read Token
    
    # Models
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
    PATCHER_MODEL = os.getenv("PATCHER_MODEL", "gpt-4o")
    
    # Credentials
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # Paths
    WORKSPACE_DIR = "./workspaces"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")