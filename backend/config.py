import os
from dotenv import load_dotenv
from functools import lru_cache

# Load .env file
load_dotenv()


class Settings:
    """Configuration from environment variables"""

    def __init__(self):
        # OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

        # News APIs
        self.nyt_api_key = os.getenv("NYT_API_KEY", "")

        # Bloomberg Credentials (for web scraping)
        self.bloomberg_email = os.getenv("BLOOMBERG_EMAIL", "")
        self.bloomberg_password = os.getenv("BLOOMBERG_PASSWORD", "")
        self.bloomberg_enabled = os.getenv("BLOOMBERG_ENABLED", "false").lower() == "true"

        # Database (Supabase PostgreSQL)
        self.database_url = os.getenv("DATABASE_URL", "")

        # For Supabase, construct URL from credentials if not provided
        if not self.database_url:
            supabase_host = os.getenv("SUPABASE_HOST", "")
            supabase_user = os.getenv("SUPABASE_USER", "postgres")
            supabase_password = os.getenv("SUPABASE_PASSWORD", "")
            supabase_db = os.getenv("SUPABASE_DB", "postgres")
            supabase_port = os.getenv("SUPABASE_PORT", "5432")

            if supabase_host and supabase_password:
                self.database_url = f"postgresql://{supabase_user}:{supabase_password}@{supabase_host}:{supabase_port}/{supabase_db}"

        # App settings
        self.app_name = os.getenv("APP_NAME", "Personalized News Feed")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"


@lru_cache()
def get_settings():
    return Settings()
