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
    
    # Forward fill the 'Indicator' column to handle grouped rows
    df['Indicator'] = df['Indicator'].ffill()
    
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    
    for idx, row in df.iterrows():
        indicator = str(row['Indicator']).strip()
        category = str(row['Categories']).strip() if pd.notna(row['Categories']) else ""
        
        # 1. Process Bullish Suggestions
        if pd.notna(row['Bullish Suggestion']):
            tag = str(row['Tag.1']).strip() if pd.notna(row['Tag.1']) else ""
            name = f"{indicator} {tag} Bullish Setup".replace("  ", " ").strip()
            # If name is redundant, clean it up
            if category and category not in name:
                name = f"{name} ({category})"
            
            slug = slugify(f"bull_{indicator}_{tag}_{idx}")
            
            strategy = {
                "name": name,
                "slug": slug,
                "category": "Indicator Based",
                "description": f"Standard bullish setup using {indicator} for {category if category else 'trading'}.",
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
                "tags": [indicator, "Bullish", tag, category]
            }
            # Remove empty tags
            strategy["tags"] = [t for t in strategy["tags"] if t]
            
            with open(os.path.join(output_dir, f"{slug}.json"), 'w') as f:
                json.dump(strategy, f, indent=2)
            count += 1

        # 2. Process Bearish Suggestions
        if pd.notna(row['Bearish Suggestion']):
            tag = str(row['Tag']).strip() if pd.notna(row['Tag']) else ""
            name = f"{indicator} {tag} Bearish Setup".replace("  ", " ").strip()
            if category and category not in name:
                name = f"{name} ({category})"
                
            slug = slugify(f"bear_{indicator}_{tag}_{idx}")
            
            strategy = {
                "name": name,
                "slug": slug,
                "category": "Indicator Based",
                "description": f"Standard bearish setup using {indicator} for {category if category else 'trading'}.",
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
                "tags": [indicator, "Bearish", tag, category]
            }
            strategy["tags"] = [t for t in strategy["tags"] if t]
            
            with open(os.path.join(output_dir, f"{slug}.json"), 'w') as f:
                json.dump(strategy, f, indent=2)
            count += 1
            
        # 3. Process Generic Suggestions (if any)
        if pd.notna(row['Suggestion']):
            tag = str(row['Tag.2']).strip() if pd.notna(row['Tag.2']) else ""
            name = f"{indicator} {tag} Setup".replace("  ", " ").strip()
            if category and category not in name:
                name = f"{name} ({category})"
                
            slug = slugify(f"gen_{indicator}_{tag}_{idx}")
            
            strategy = {
                "name": name,
                "slug": slug,
                "category": "Indicator Based",
                "description": f"Standard indicator setup using {indicator}.",
                "logic": {
                    "entry": {
                        "condition": row['Suggestion'],
                        "timeframe": "15min"
                    },
                    "exit": {
                        "stop_loss": "1%",
                        "target": "2%"
                    }
                },
                "tags": [indicator, tag, category]
            }
            strategy["tags"] = [t for t in strategy["tags"] if t]
            
            with open(os.path.join(output_dir, f"{slug}.json"), 'w') as f:
                json.dump(strategy, f, indent=2)
            count += 1
            
    print(f"Generated {count} total strategy presets in {output_dir}")

if __name__ == "__main__":
    excel_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Streak_Indicators_Final_Bullish_Bearish.xlsx'))
    output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/strategies/auto_generated'))
    
    # Clear old auto-generated files first to avoid clutter
    if os.path.exists(output_directory):
        for f in os.listdir(output_directory):
            if f.endswith(".json"):
                os.remove(os.path.join(output_directory, f))
                
    if os.path.exists(excel_file):
        generate_strategies(excel_file, output_directory)
    else:
        print(f"Excel file not found at {excel_file}")
