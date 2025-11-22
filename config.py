import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AssistantConfig:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    max_conversation_history: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    database_path: str = os.getenv("DATABASE_PATH", "conversations.db")
    knowledge_base_path: str = os.getenv("KNOWLEDGE_BASE_PATH", "./data/knowledge")
    top_k_retrieval: int = int(os.getenv("TOP_K_RETRIEVAL", "3"))
    max_react_steps: int = int(os.getenv("MAX_REACT_STEPS", "3"))

config = AssistantConfig()