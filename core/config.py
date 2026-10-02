import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # DATABASE_URL: If set to postgresql:// or postgres://, uses PostgreSQL (psycopg3).
    # If unset or sqlite://, uses SQLite.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///fieldai.db")
    
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    PORT: int = int(os.getenv("PORT", "8501"))
    
    @classmethod
    def is_postgres(cls) -> bool:
        db_url = cls.DATABASE_URL.lower()
        return db_url.startswith("postgres://") or db_url.startswith("postgresql://")

config = Config()
