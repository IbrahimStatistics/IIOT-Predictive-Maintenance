import os

DB_DSN = os.environ.get("DB_DSN", "postgresql://postgres:password@localhost:5432/postgres")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-this")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60