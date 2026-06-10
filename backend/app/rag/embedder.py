import httpx
from app.config import settings
import asyncio

async def embed_texts_async(texts: list[str]) -> list[list[float]]:
    """
    Uses Ollama's API to generate embeddings, removing the need for local torch/transformers.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/embed"
    embeddings = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            try:
                response = await client.post(
                    url,
                    json={
                        "model": settings.EMBEDDING_MODEL_NAME,
                        "input": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                # Ollama returns "embeddings" which is a list of lists if input was list, 
                # or single list if input was string. In newer versions it's "embeddings".
                if "embeddings" in result:
                    embeddings.extend(result["embeddings"])
                elif "embedding" in result:
                    embeddings.append(result["embedding"])
            except Exception as e:
                print(f"Ollama Embedding Error: {e}")
                # Return zero vector as fallback to avoid crashing the whole batch
                embeddings.append([0.0] * 1024) 
                
    return embeddings

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Synchronous wrapper for embed_texts_async"""
    return asyncio.run(embed_texts_async(texts))
