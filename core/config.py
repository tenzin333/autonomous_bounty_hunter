import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Your HF Space URL (e.g., https://username-spacename.hf.space/v1)
    # Ensure you append /v1 if using Ollama's OpenAI compatibility layer
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai") # or "huggingface"
    HF_SPACE_URL = os.getenv("HF_SPACE_URL") 
    HF_TOKEN = os.getenv("HF_TOKEN") # Use your HF Read Token
    
    #Blockchain 
    RPC_URL = os.getenv("RPC_URL")
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY", "0xYourPrivateKeyHere")  
    ABI_PATH = os.getenv("ABI_PATH", "./abis/BountyHub.json")
    COMMITMENT_SALT = os.getenv("COMMITMENT_SALT", "your_salt_here")
    
    #Database
    DATABASE_URL = os.getenv("DB_URL", "postgresql://user:password@localhost:5432/hunterdb")
    
    #Base url 
    BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    API_KEY = os.getenv("LLM_API_KEY")

    # Models
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
    PATCHER_MODEL = os.getenv("PATCHER_MODEL", "gpt-4o")
    
    # Credentials
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # Paths
    WORKSPACE_DIR = "./workspaces"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    TARGET_REPO = os.getenv("TARGET_REPO", "owner/repo")  # e.g., "tenzin333/jobpilot2.0"
