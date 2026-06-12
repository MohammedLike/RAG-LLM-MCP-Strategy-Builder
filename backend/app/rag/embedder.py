from ..config import settings
import asyncio
import httpx

EMBEDDING_URL = f"{settings.OLLAMA_BASE_URL}/api/embed"

async def embed_texts_async(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    embeddings: list[list[float]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            try:
                response = await client.post(EMBEDDING_URL, json={"model": settings.EMBEDDING_MODEL_NAME, "input": batch})
                if response.status_code == 200:
                    data = response.json()
                    if "embeddings" in data:
                        embeddings.extend(data["embeddings"])
                    else:
                        embeddings.extend([[0.0] * 1024 for _ in batch])
                else:
                    embeddings.extend([[0.0] * 1024 for _ in batch])
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.extend([[0.0] * 1024 for _ in batch])
    return embeddings

def embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(embed_texts_async(texts))
            except ImportError:
                return [[0.0] * 1024 for _ in texts]
        else:
            return loop.run_until_complete(embed_texts_async(texts))
    except RuntimeError:
        return asyncio.run(embed_texts_async(texts))

async def embed_texts_async_call(texts: list[str]) -> list[list[float]]:
    return await embed_texts_async(texts)
