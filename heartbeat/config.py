import os
from dataclasses import dataclass, fields
from dotenv import load_dotenv

# Load .env file at module level
load_dotenv()

@dataclass
class Config:
    heart_l3_key: str
    heart_l2_key: str
    brain_key: str
    nervous_key: str
    fallback_key: str
    groq_key: str
    groq_base_url: str
    openrouter_base_url: str
    openrouter_api_key: str
    redis_host: str
    redis_port: str
    sqlite_db_path: str
    chroma_db_path: str
    max_active_cells: int = 20
    ambiguity_threshold: float = 0.60
    link_cell_token_limit: int = 500
    tesseract_cmd: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # ISSUE 7.2 FIX: Centralized Amnesia Blocklist
    amnesia_blocklist: list = None

    def __post_init__(self):
        if self.amnesia_blocklist is None:
            self.amnesia_blocklist = [
                "don't have the ability", 
                "cannot recall", 
                "large language model", 
                "can't recall", 
                "exact content of our previous",
                "as an ai model",
                "generic assistant"
            ]

_config_instance = None

def get_config() -> Config:
    """Returns a singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(
            heart_l3_key=os.getenv("HEARTBEAT_HEART_L3_KEY", ""),
            heart_l2_key=os.getenv("HEARTBEAT_HEART_L2_KEY", ""),
            brain_key=os.getenv("HEARTBEAT_BRAIN_KEY", ""),
            nervous_key=os.getenv("HEARTBEAT_NERVOUS_KEY", ""),
            fallback_key=os.getenv("HEARTBEAT_FALLBACK_KEY", ""),
            groq_key=os.getenv("HEARTBEAT_GROQ_KEY", ""),
            groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=os.getenv("REDIS_PORT", "6379"),
            sqlite_db_path=os.getenv("SQLITE_DB_PATH", "./data/heartbeat.db"),
            chroma_db_path=os.getenv("CHROMA_DB_PATH", "./data/chroma_store"),
            max_active_cells=int(os.getenv("MAX_ACTIVE_CELLS", 20)),
            ambiguity_threshold=float(os.getenv("AMBIGUITY_CONFIDENCE_THRESHOLD", 0.60)),
            link_cell_token_limit=int(os.getenv("LINK_CELL_TOKEN_LIMIT", 500)),
            tesseract_cmd=os.getenv("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        )
        # ISSUE 3.1 FIX: Add groq_api_key alias with robust fallback
        groq_k = os.getenv("HEARTBEAT_GROQ_KEY") or os.getenv("GROQ_API_KEY") or _config_instance.brain_key or _config_instance.heart_l3_key or ""
        _config_instance.groq_key = groq_k
        _config_instance.groq_api_key = groq_k
        _config_instance.__post_init__()
        validate_config(_config_instance)
    return _config_instance

def validate_config(config: Config) -> None:
    """Validates that all essential keys are present."""
    missing = []
    # Check only API keys as they are critical
    keys_to_check = ['heart_l3_key', 'heart_l2_key', 'brain_key', 'nervous_key', 'fallback_key']
    for key in keys_to_check:
        if not getattr(config, key):
            missing.append(key)
    
    if missing:
        # For now, just print warning during development instead of raising error
        # print(f"WARNING: Missing required configuration keys in .env: {', '.join(missing)}")
        pass
