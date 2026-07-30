import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")

required = {
    "DATABASE_URL": DATABASE_URL, 
    "SUPABASE_JWKS_URL": SUPABASE_JWKS_URL,  
}

missing = [name for name, value in required.items() if not value]

if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}"
    )