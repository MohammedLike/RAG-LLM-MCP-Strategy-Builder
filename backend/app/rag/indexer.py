import json
import glob
from .chunker import chunk_strategy
from .embedder import embed_texts
from .qdrant_client import init_collection, upsert_chunks

def index_all_strategies(strategies_dir: str):
    init_collection()
    
    files = glob.glob(f"{strategies_dir}/*.json")
    for file in files:
        if '_schema' in file:
            continue
        with open(file, 'r') as f:
            data = json.load(f)
            
        chunks = chunk_strategy(data)
        texts = [c["text"] for c in chunks]
        
        embeddings = embed_texts(texts)
        upsert_chunks(chunks, embeddings)
        print(f"Indexed {len(chunks)} chunks for {data.get('name')}")
