import json
import os
import glob

def generate_pairs(strategy_file):
    with open(strategy_file, 'r') as f:
        data = json.load(f)
    
    pairs = []
    name = data['name']
    
    # Hypothesis
    pairs.append({
        "instruction": f"What is the core hypothesis of the {name} strategy?",
        "output": data['hypothesis']
    })
    
    # Entry
    conds = ", ".join(data['entry_rules']['conditions'])
    pairs.append({
        "instruction": f"When should I enter a {name}?",
        "output": f"You should enter based on these conditions: {conds}. Sizing: {data['entry_rules']['position_sizing']}"
    })
    
    # Exit
    pairs.append({
        "instruction": f"What are the exit rules for {name}?",
        "output": f"Stop loss: {data['exit_rules']['stop_loss']}. Target: {data['exit_rules']['target']}. Time exit: {data['exit_rules']['time_exit']}."
    })
    
    return pairs

if __name__ == "__main__":
    strategy_files = glob.glob(os.path.join(os.path.dirname(__file__), '../data/strategies/*.json'))
    all_pairs = []
    
    for sf in strategy_files:
        if '_schema' in sf:
            continue
        all_pairs.extend(generate_pairs(sf))
        
    out_path = os.path.join(os.path.dirname(__file__), '../data/qa_pairs/training_data.jsonl')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w') as f:
        for p in all_pairs:
            f.write(json.dumps(p) + '\n')
    print(f"Generated {len(all_pairs)} QA pairs.")
