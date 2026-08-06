import asyncio
import sys
import bcrypt
import asyncpg

from config import DB_DSN


async def reset_password(username: str, new_password: str):
    conn = await asyncpg.connect(DB_DSN)
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    try:
        result = await conn.execute(
            "UPDATE users SET hashed_password = $1 WHERE username = $2",
            hashed, username,
        )
        if result == "UPDATE 0":
            print(f"No user found with username '{username}'.")
        else:
            print(f"Password reset for user '{username}'.")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    asyncio.run(reset_password(sys.argv[1], sys.argv[2]))