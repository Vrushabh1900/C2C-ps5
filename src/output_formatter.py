"""
Module: output_formatter
Issue addressed: #18 (Format JSON Output)

Produces the final consensus_result.json file.
"""

import json
import os
from typing import Dict, Any


def write_result(result: Dict[str, Any], output_dir: str, filename: str = "consensus_result.json") -> str:
    """Write result dict to JSON file. Returns the output filepath."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[OUTPUT] Result written to {filepath}")
    return filepath
