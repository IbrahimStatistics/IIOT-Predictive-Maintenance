import asyncpg
from config import DB_DSN

pool: asyncpg.Pool | None = None

async def connect():
    global pool
    pool = await asyncpg.create_pool(DB_DSN)

async def disconnect():
    await pool.close()

def get_pool() -> asyncpg.Pool:
    return pool