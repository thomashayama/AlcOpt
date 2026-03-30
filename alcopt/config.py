import os

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/alcopt.db")
# Railway provides postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Google OAuth - constant URLs
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REFRESH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"

# Google OAuth - credentials (set via env vars)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_SCOPE = os.getenv("GOOGLE_SCOPE", "openid email profile")

# Security
ADMIN_EMAILS = [
    e.strip() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
]
