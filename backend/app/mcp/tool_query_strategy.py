from pydantic import BaseModel, Field
from ..rag.qdrant_client import search_strategies
from ..rag.embedder import embed_texts_async

class QueryStrategyInput(BaseModel):
    query: str = Field(description="The query string to search for strategies")
    top_k: int = Field(5, description="Number of strategies to retrieve")

async def query_strategy_data(input_data: QueryStrategyInput) -> list:
    """
    Queries the strategy knowledge base via RAG.
    """
    try:
        # Embed the query
        query_emb = (await embed_texts_async([input_data.query]))[0]
        # Search Qdrant
        results = search_strategies(query_emb, top_k=input_data.top_k)
        return results
    except Exception as e:
        print(f"Error in query_strategy tool: {e}")
        return []
