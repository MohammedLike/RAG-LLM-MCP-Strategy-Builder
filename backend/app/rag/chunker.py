import json

def chunk_strategy(strategy_dict):
    """
    Zero-dependency recursive character text splitter to avoid PyTorch DLL issues.
    """
    text = json.dumps(strategy_dict, indent=2)
    chunk_size = 600
    chunk_overlap = 100
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start += (chunk_size - chunk_overlap)
    
    return [
        {
            "text": chunk,
            "metadata": {
                "strategy_name": strategy_dict.get("name"),
                "category": strategy_dict.get("category"),
                "slug": strategy_dict.get("slug", strategy_dict.get("name", "").lower().replace(" ", "_"))
            }
        }
        for chunk in chunks
    ]
