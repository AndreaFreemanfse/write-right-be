import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
BASE_URL = os.getenv("BASE_URL")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")

required = {
    "SUPABASE_JWKS_URL": SUPABASE_JWKS_URL, 
    "DATABASE_URL": DATABASE_URL,
    "API_KEY": API_KEY,
    "BASE_URL": BASE_URL,
    "MODEL": MODEL,
}

missing = [name for name, value in required.items() if not value]

if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}"
    )