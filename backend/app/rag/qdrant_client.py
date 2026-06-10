from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings
import uuid

client = QdrantClient(url=settings.QDRANT_URL)
COLLECTION_NAME = "strategies"

def init_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE) # BGE-M3 size
        )

def upsert_chunks(chunks, embeddings):
    points = []
    for chunk, emb in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"]
                }
            )
        )
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def search_strategies(query_embedding: list[float], top_k: int = 5, category: str = None):
    query_filter = None
    if category:
        query_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        )
        
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        query_filter=query_filter
    )
    
    return [
        {
            "text": res.payload["text"],
            "score": res.score,
            "metadata": {k: v for k, v in res.payload.items() if k != "text"}
        }
        for res in results
    ]
