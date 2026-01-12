import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Models
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
    PATCHER_MODEL = os.getenv("PATCHER_MODEL", "gpt-4o")
    
    # Credentials
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # Paths
    WORKSPACE_DIR = "./workspaces"