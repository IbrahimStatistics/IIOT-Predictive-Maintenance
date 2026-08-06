import asyncio
import sys
import asyncpg
from passlib.context import CryptContext

from config import DB_DSN

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(username: str, password: str, role: str = "admin"):
    conn = await asyncpg.connect(DB_DSN)
    hashed = pwd_context.hash(password)
    try:
        await conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES ($1, $2, $3)",
            username, hashed, role,
        )
        print(f"Created user '{username}' with role '{role}'")
    except asyncpg.UniqueViolationError:
        print(f"User '{username}' already exists.")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <username> <password> [role]")
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "admin"
    asyncio.run(create_user(username, password, role))