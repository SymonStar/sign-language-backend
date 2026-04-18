"""
Filter gesture templates to only the most distinct signs
Based on movement patterns, height, and direction variance
"""

import json
from pathlib import Path

# Most distinct signs based on analysis
DISTINCT_SIGNS = [
    # Very high movement, unique patterns
    'SATURDAY',      # 81.9 movement, horizontal_left, low height
    'DARK',          # 91.7 movement, horizontal_left
    'SUNDAY',        # 78.1 movement, vertical_up
    'LIGHT',         # 61.2 movement, horizontal
    
    # Unique height positions
    'WHEELCHAIR PERSON',  # 0.85 height (very high)
    'FATHER',        # 0.37 height (very low)
    'GRANDFATHER',   # 0.38 height (very low)
    'CHICKEN',       # 0.49 height (low)
    'TODAY',         # 0.83 height (very high)
    
    # Common/useful signs with distinct patterns
    'HELLO',         # Common greeting
    'THANK YOU',     # Common courtesy
    'YES',           # Basic response
    'NO',            # Basic response
    'HELP',          # Emergency (if exists)
    'UNDERSTAND',    # Communication
]

def filter_templates():
    """Filter templates to only distinct signs"""
    
    # Load full templates
    input_path = Path(__file__).parent / 'data' / 'gesture_templates_v2.json'
    output_path = Path(__file__).parent / 'data' / 'gesture_templates_v2_filtered.json'
    
    print(f"[LOAD] Loading templates from {input_path}")
    
    with open(input_path, 'r') as f:
        all_templates = json.load(f)
    
    print(f"[INFO] Total templates: {len(all_templates)}")
    
    # Filter to distinct signs
    filtered_templates = {}
    
    for sign in DISTINCT_SIGNS:
        if sign in all_templates:
            filtered_templates[sign] = all_templates[sign]
            template_count = len(all_templates[sign]['templates'])
            print(f"[KEEP] {sign}: {template_count} templates")
        else:
            print(f"[WARN] {sign} not found in templates")
    
    # Save filtered templates
    with open(output_path, 'w') as f:
        json.dump(filtered_templates, f, indent=2)
    
    print(f"\n[SAVE] Filtered templates saved to {output_path}")
    print(f"[INFO] Kept {len(filtered_templates)} out of {len(all_templates)} signs")
    print(f"[INFO] Reduction: {(1 - len(filtered_templates)/len(all_templates))*100:.1f}%")
    
    return filtered_templates

if __name__ == '__main__':
    print("="*60)
    print("FILTERING TO DISTINCT SIGNS")
    print("="*60)
    
    filtered = filter_templates()
    
    print("\n" + "="*60)
    print("FILTERED SIGNS:")
    print("="*60)
    for sign in filtered.keys():
        print(f"  - {sign}")
    
    print("\n[NEXT] Update app_v2.py to load gesture_templates_v2_filtered.json")
