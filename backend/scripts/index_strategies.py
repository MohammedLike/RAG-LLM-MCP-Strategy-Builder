import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.indexer import index_all_strategies
from app.config import settings

if __name__ == "__main__":
    print(f"Using Embedding Model: {settings.EMBEDDING_MODEL_NAME}")
    strategies_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../training/data/strategies'))
    print(f"Indexing strategies from {strategies_dir}")
    index_all_strategies(strategies_dir)
