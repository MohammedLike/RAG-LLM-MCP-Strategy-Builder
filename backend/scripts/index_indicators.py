import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.embedder import embed_texts
from app.rag.qdrant_client import init_collection, upsert_chunks
from app.config import settings

def index_indicators(excel_path: str):
    print(f"Reading indicators from {excel_path}")
    df = pd.read_excel(excel_path)
    
    # Fill merged indicator cells
    df['Indicator'] = df['Indicator'].ffill()
    
    # Process only relevant columns
    df = df[['Indicator', 'Bullish Suggestion', 'Bearish Suggestion', 'Tag', 'Tag.1', 'Categories']]
    
    chunks = []
    
    for _, row in df.iterrows():
        indicator = row['Indicator']
        category = row['Categories'] if pd.notna(row['Categories']) else "General"
        
        # Bullish entry
        if pd.notna(row['Bullish Suggestion']):
            text = f"Indicator: {indicator}\nSide: Bullish\nCondition: {row['Bullish Suggestion']}\nTag: {row.get('Tag.1', '')}\nCategory: {category}"
            chunks.append({
                "text": text,
                "metadata": {
                    "type": "indicator_suggestion",
                    "indicator": indicator,
                    "side": "bullish",
                    "category": category
                }
            })
            
        # Bearish entry
        if pd.notna(row['Bearish Suggestion']):
            text = f"Indicator: {indicator}\nSide: Bearish\nCondition: {row['Bearish Suggestion']}\nTag: {row.get('Tag', '')}\nCategory: {category}"
            chunks.append({
                "text": text,
                "metadata": {
                    "type": "indicator_suggestion",
                    "indicator": indicator,
                    "side": "bearish",
                    "category": category
                }
            })

    if not chunks:
        print("No indicator suggestions found.")
        return

    print(f"Embedding {len(chunks)} indicator suggestions...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    
    print("Upserting to Qdrant...")
    upsert_chunks(chunks, embeddings)
    print("Success!")

if __name__ == "__main__":
    excel_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Streak_Indicators_Final_Bullish_Bearish.xlsx'))
    if os.path.exists(excel_file):
        index_indicators(excel_file)
    else:
        print(f"Excel file not found at {excel_file}")
