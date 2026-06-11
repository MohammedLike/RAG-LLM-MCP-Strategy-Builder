import pandas as pd
import json
import os
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def generate_strategies(excel_path: str, output_dir: str):
    print(f"Reading indicators from {excel_path}")
    df = pd.read_excel(excel_path)
    df['Indicator'] = df['Indicator'].ffill()
    
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    for _, row in df.iterrows():
        indicator = row['Indicator']
        
        # Bullish Strategy
        if pd.notna(row['Bullish Suggestion']):
            name = f"{indicator} Bullish Setup"
            slug = slugify(name)
            strategy = {
                "name": name,
                "slug": slug,
                "category": "Indicator Based",
                "description": f"Standard bullish setup using {indicator}.",
                "logic": {
                    "entry": {
                        "condition": row['Bullish Suggestion'],
                        "timeframe": "15min"
                    },
                    "exit": {
                        "stop_loss": "1%",
                        "target": "2%"
                    }
                },
                "tags": [indicator, "Bullish", row.get('Tag.1', '')]
            }
            with open(os.path.join(output_dir, f"{slug}.json"), 'w') as f:
                json.dump(strategy, f, indent=2)
            count += 1

        # Bearish Strategy
        if pd.notna(row['Bearish Suggestion']):
            name = f"{indicator} Bearish Setup"
            slug = slugify(name)
            strategy = {
                "name": name,
                "slug": slug,
                "category": "Indicator Based",
                "description": f"Standard bearish setup using {indicator}.",
                "logic": {
                    "entry": {
                        "condition": row['Bearish Suggestion'],
                        "timeframe": "15min"
                    },
                    "exit": {
                        "stop_loss": "1%",
                        "target": "2%"
                    }
                },
                "tags": [indicator, "Bearish", row.get('Tag', '')]
            }
            with open(os.path.join(output_dir, f"{slug}.json"), 'w') as f:
                json.dump(strategy, f, indent=2)
            count += 1
            
    print(f"Generated {count} strategy files in {output_dir}")

if __name__ == "__main__":
    excel_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Streak_Indicators_Final_Bullish_Bearish.xlsx'))
    output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/strategies/auto_generated'))
    if os.path.exists(excel_file):
        generate_strategies(excel_file, output_directory)
    else:
        print(f"Excel file not found at {excel_file}")
