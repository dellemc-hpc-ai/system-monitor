"""
statute_loader.py — Load state statute template and produce a resolved statute.json
for the given state. If statute.json already exists in data/..., ask before regenerating.
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def load_statute(state_abbrev: str, data_dir: str, force: bool = False) -> dict:
    """
    Load or generate the statute JSON for the given state.

    Steps:
    1. Check if statute.json exists in data_dir — if yes and not force, ask user
    2. Otherwise, load the template from config/state_statute_templates/<state>.json
    3. Resolve template references and save as statute.json in data_dir
    """
    data_path = os.path.join(data_dir, "statute.json")
    # Try state abbreviation first, then state name
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "state_statute_templates", f"{state_abbrev.lower()}.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "state_statute_templates", f"{state_abbrev.lower().replace('tx', 'texas')}.json"),
    ]
    template_path = None
    for p in candidates:
        if os.path.exists(p):
            template_path = p
            break
    if not template_path:
        raise FileNotFoundError(
            f"No statute template found for state '{state_abbrev}'. Looked in:\n" +
            "\n".join(f"  {p}" for p in candidates)
        )
    with open(template_path, encoding="utf-8") as f:
        statute = json.load(f)

    return statute


def save_statute(statute: dict, data_dir: str) -> None:
    data_path = os.path.join(data_dir, "statute.json")
    os.makedirs(data_dir, exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(statute, f, indent=2, ensure_ascii=False)
    print(f"[statute_loader] Saved statute to {data_path}")


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "TX"
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "data/TX_TEST"
    statute = load_statute(state, data_dir)
    print(f"Loaded statute for {statute['state_name']} ({statute['state']})")
    print(f"Distance rules: {list(statute['distance_rules'].keys())}")
    print(f"Modes: {list(statute['modes'].keys())}")
    print(f"Holidays: {list(statute['holidays'].keys())}")
