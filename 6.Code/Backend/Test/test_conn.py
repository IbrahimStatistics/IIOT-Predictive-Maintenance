import asyncio
import asyncpg

DB_DSN = "postgresql://postgres:yourpassword@localhost:5432/postgres"

async def main():
    conn = await asyncpg.connect(DB_DSN)
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    print("Tables visible via asyncpg:", [r["tablename"] for r in rows])
    version = await conn.fetchval("SELECT version()")
    print("Connected to:", version)
    await conn.close()

asyncio.run(main())