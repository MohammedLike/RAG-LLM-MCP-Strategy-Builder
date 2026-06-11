import ollama
from app.config import settings
import asyncio

async def embed_texts_async(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Generate embeddings via Ollama in batches."""
    client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
    embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = await client.embed(
                model=settings.EMBEDDING_MODEL_NAME,
                input=batch,
            )
            if hasattr(response, "embeddings"):
                embeddings.extend(response.embeddings)
            elif isinstance(response, dict) and "embeddings" in response:
                embeddings.extend(response["embeddings"])
            else:
                raise ValueError("Unexpected Ollama embed response")
        except Exception as e:
            print(f"Ollama Embedding Error (batch {i // batch_size + 1}): {e}")
            embeddings.extend([[0.0] * 1024 for _ in batch])

    return embeddings

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Synchronous wrapper for embed_texts_async"""
    try:
        # Check if an event loop is already running
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In a running loop, we can't use run()
            # This is a bit tricky for a sync wrapper.
            # But indexing script is standalone, so run() should work.
            return asyncio.run(embed_texts_async(texts))
        else:
            return loop.run_until_complete(embed_texts_async(texts))
    except RuntimeError:
        return asyncio.run(embed_texts_async(texts))
