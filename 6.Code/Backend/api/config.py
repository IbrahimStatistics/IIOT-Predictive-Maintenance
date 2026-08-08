import os

DB_DSN = os.environ.get("DB_DSN", "postgresql://postgres:postgres@localhost:5433/postgres")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-this")
if JWT_SECRET == "dev-secret-change-this":
    print("WARNING: Using default JWT_SECRET. Set the JWT_SECRET env var before any real deployment or demo on a shared machine.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60