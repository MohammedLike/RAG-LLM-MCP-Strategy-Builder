from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from ..config import settings
import uuid

client = None
COLLECTION_NAME = "strategies"

def get_client():
    global client
    if client is None:
        try:
            client = QdrantClient(url=settings.QDRANT_URL)
        except Exception as e:
            print(f"Qdrant connection error: {e}")
            client = None
    return client

def init_collection():
    c = get_client()
    if c is None:
        return
    try:
        if not c.collection_exists(COLLECTION_NAME):
            c.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
    except Exception as e:
        print(f"Qdrant init error: {e}")

def upsert_chunks(chunks, embeddings):
    c = get_client()
    if c is None:
        return
    points = []
    for chunk, emb in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={"text": chunk["text"], **chunk["metadata"]}
            )
        )
    try:
        c.upsert(collection_name=COLLECTION_NAME, points=points)
    except Exception as e:
        print(f"Qdrant upsert error: {e}")

def search_strategies(query_embedding: list[float], top_k: int = 5, category: str = None):
    c = get_client()
    if c is None:
        return []
    query_filter = None
    if category:
        query_filter = Filter(must=[FieldCondition(key="category", match=MatchValue(value=category))])
    try:
        results = c.search(collection_name=COLLECTION_NAME, query_vector=query_embedding, limit=top_k, query_filter=query_filter)
        return [{"text": res.payload["text"], "score": res.score, "metadata": {k: v for k, v in res.payload.items() if k != "text"}} for res in results]
    except Exception as e:
        print(f"Qdrant search error: {e}")
        return []
