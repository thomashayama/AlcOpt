import logging
import os

log = logging.getLogger(__name__)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/alcopt.db")

# Google OAuth - constant URLs
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Google OAuth - credentials (set via env vars)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_SCOPE = os.getenv("GOOGLE_SCOPE", "openid email profile")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7

# Frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Security
ADMIN_EMAILS = [
    e.strip() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
]


def validate_config():
    """Check that required secrets are set. Call during app startup."""
    missing = []
    if not JWT_SECRET:
        missing.append("JWT_SECRET")
    if not GOOGLE_CLIENT_ID:
        missing.append("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_SECRET:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not GOOGLE_REDIRECT_URI:
        missing.append("GOOGLE_REDIRECT_URI")
    if missing:
        msg = f"Missing required environment variables: {', '.join(missing)}"
        if DATABASE_URL.startswith("sqlite"):
            log.warning(msg + " (auth will not work)")
        else:
            raise RuntimeError(msg)
