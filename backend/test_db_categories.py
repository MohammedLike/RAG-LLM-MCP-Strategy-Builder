import asyncio
from app.db.session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        res = await s.execute(text("SELECT id, name, category, slug, hypothesis FROM strategies WHERE category IN ('Options', 'Equity')"))
        for r in res.fetchall():
            print(f"Name: {r[1]} | Category: {r[2]} | Slug: {r[3]} | Description: {r[4][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
