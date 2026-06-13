import asyncio
from app.db.session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        res = await s.execute(text("SELECT id, name, category, slug FROM strategies"))
        rows = res.fetchall()
        print(f"Total strategies in DB: {len(rows)}")
        for r in rows:
            print(f"ID: {r[0]}, Name: {r[1]}, Category: {r[2]}, Slug: {r[3]}")

if __name__ == "__main__":
    asyncio.run(main())
