import json
import glob
from .chunker import chunk_strategy
from .embedder import embed_texts
from .qdrant_client import init_collection, upsert_chunks

def index_all_strategies(strategies_dir: str, batch_size: int = 64):
    init_collection()

    files = glob.glob(f"{strategies_dir}/**/*.json", recursive=True)
    all_chunks = []
    for file in files:
        if "_schema" in file:
            continue
        with open(file, "r") as f:
            data = json.load(f)
        all_chunks.extend(chunk_strategy(data))

    if not all_chunks:
        print("No strategy chunks found.")
        return

    print(f"Embedding {len(all_chunks)} strategy chunks...")
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        embeddings = embed_texts(texts)
        upsert_chunks(batch, embeddings)
        print(f"Indexed {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")
