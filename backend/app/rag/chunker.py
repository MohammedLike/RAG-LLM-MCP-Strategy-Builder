from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

def chunk_strategy(strategy_dict):
    text_content = json.dumps(strategy_dict, indent=2)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_text(text_content)
    
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
