import ollama
from app.config import settings
import asyncio

async def embed_texts_async(texts: list[str]) -> list[list[float]]:
    """
    Uses Ollama's Python library to generate embeddings.
    """
    client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
    embeddings = []
    
    for text in texts:
        try:
            # Use the official embed method
            response = await client.embed(
                model=settings.EMBEDDING_MODEL_NAME,
                input=text
            )
            # Ollama Python library returns 'embeddings'
            if hasattr(response, 'embeddings'):
                embeddings.extend(response.embeddings)
            elif 'embeddings' in response:
                embeddings.extend(response['embeddings'])
        except Exception as e:
            print(f"Ollama Embedding Error: {e}")
            embeddings.append([0.0] * 1024) 
                
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
