from pydantic import BaseModel, Field

class QueryStrategyInput(BaseModel):
    query: str = Field(description="The query string to search for strategies")
    top_k: int = Field(5, description="Number of strategies to retrieve")

def query_strategy_data(input_data: QueryStrategyInput) -> list:
    """
    Simulates querying strategy data from Qdrant.
    """
    # In a full implementation, this calls qdrant_client.search()
    return [
        {
            "name": "Short Strangle",
            "score": 0.95,
            "content": "A short strangle involves selling a call and a put..."
        }
    ]
