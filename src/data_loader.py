"""
Module: data_loader
Issues addressed: #2 (Parse Representatives), #3 (Parse Proposals),
                  #4 (Parse Objections), #5 (Parse Relationships)

Handles raw file ingestion from /data/raw/.
"""

import json
import csv
import os
from typing import List, Dict, Any


def _read_json(filepath: str) -> List[Dict[str, Any]]:
    """Safely read a JSON array file, returning an empty list on failure."""
    if not os.path.isfile(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"[WARN] Expected JSON array in {filepath}, got {type(data).__name__}")
        return []
    return data


def load_representatives(data_dir: str) -> List[Dict[str, Any]]:
    """Issue #2: Ingest representatives.json."""
    return _read_json(os.path.join(data_dir, "representatives.json"))


def load_proposals(data_dir: str) -> List[Dict[str, Any]]:
    """Issue #3: Ingest proposals.json."""
    return _read_json(os.path.join(data_dir, "proposals.json"))


def load_objections(data_dir: str) -> List[Dict[str, Any]]:
    """Issue #4: Ingest objections.json."""
    return _read_json(os.path.join(data_dir, "objections.json"))


def load_relations(data_dir: str) -> List[Dict[str, Any]]:
    """Issue #5: Ingest relations.csv using a distinct CSV parsing approach."""
    filepath = os.path.join(data_dir, "relations.csv")
    if not os.path.isfile(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
    rows: List[Dict[str, Any]] = []
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys and values
            cleaned = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
            rows.append(cleaned)
    return rows
