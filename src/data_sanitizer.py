"""
Module: data_sanitizer
Issues addressed: #6 (Sanitize IDs), #7 (Invalid Attribute Types),
                  #8 (Deduplicate Proposals), #9 (Validate Missing References)

Cleans, normalizes, deduplicates, and validates all ingested data.
"""

from typing import List, Dict, Any, Set, Tuple
import math
import json
import csv
import os


# ---------------------------------------------------------------------------
# Issue #6: Normalize IDs
# ---------------------------------------------------------------------------

def normalize_id(raw_id: Any) -> str:
    """Lowercase, strip whitespace from an ID string."""
    if raw_id is None:
        return ""
    return str(raw_id).strip().lower()


def normalize_ids_in_list(records: List[Dict[str, Any]], id_field: str) -> List[Dict[str, Any]]:
    """Apply normalize_id to every record's id_field."""
    for rec in records:
        rec[id_field] = normalize_id(rec.get(id_field))
    return records


# ---------------------------------------------------------------------------
# Issue #7: Handle Invalid Attribute Types
# ---------------------------------------------------------------------------

_SEVERITY_MAP = {
    "critical": 10, "high": 8, "medium": 5, "low": 3, "minimal": 1,
}


def safe_numeric(value: Any, low: float = 0, high: float = 100,
                 default: float = 0, label: str = "") -> float:
    """
    Cast value to float. Clamp to [low, high].
    Handles None, strings (including named severity), and out-of-range.
    """
    if value is None:
        return default
    if isinstance(value, str):
        mapped = _SEVERITY_MAP.get(value.strip().lower())
        if mapped is not None:
            return float(mapped)
        try:
            value = float(value)
        except (ValueError, TypeError):
            return default
    try:
        num = float(value)
    except (ValueError, TypeError):
        return default
    if math.isnan(num) or math.isinf(num):
        return default
    return max(low, min(high, num))


def sanitize_representatives(reps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Full sanitization pipeline for representatives:
      - Normalize IDs  (#6)
      - Cast influence to numeric, clamp 0-100  (#7)
      - Deduplicate by ID (first occurrence wins)
      - Drop records with empty IDs
    """
    normalize_ids_in_list(reps, "id")
    seen: Dict[str, Dict[str, Any]] = {}
    for rep in reps:
        rid = rep["id"]
        if not rid:
            continue
        rep["influence"] = safe_numeric(rep.get("influence"), 0, 100, default=0, label=f"influence({rid})")
        # First-occurrence wins deduplication
        if rid not in seen:
            seen[rid] = rep
    return list(seen.values())


def sanitize_proposals(props: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Issue #8: Deduplicate proposals (first occurrence wins).
    Also normalizes sponsor IDs and ensures priority is numeric.
    """
    normalize_ids_in_list(props, "id")
    for p in props:
        p["sponsor"] = normalize_id(p.get("sponsor"))
        p["priority"] = safe_numeric(p.get("priority"), 0, 10, default=0, label=f"priority({p['id']})")
    seen: Dict[str, Dict[str, Any]] = {}
    for p in props:
        pid = p["id"]
        if not pid:
            continue
        if pid not in seen:
            seen[pid] = p
    return list(seen.values())


def sanitize_objections(objs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize IDs, cast severity, drop duplicates (same rep + same proposal)."""
    for o in objs:
        o["rep_id"] = normalize_id(o.get("rep_id"))
        o["proposal_id"] = normalize_id(o.get("proposal_id"))
        o["severity"] = safe_numeric(o.get("severity"), 0, 10, default=0, label="severity")
    # Deduplicate by (rep_id, proposal_id) – keep first
    seen: Set[Tuple[str, str]] = set()
    unique: List[Dict[str, Any]] = []
    for o in objs:
        key = (o["rep_id"], o["proposal_id"])
        if key not in seen:
            seen.add(key)
            unique.append(o)
    return unique


def sanitize_relations(rels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize IDs, cast numeric fields, clamp trust/rivalry 0-100, betrayal 0-1."""
    for r in rels:
        r["from"] = normalize_id(r.get("from"))
        r["to"] = normalize_id(r.get("to"))
        r["trust"] = safe_numeric(r.get("trust"), 0, 100, default=0, label="trust")
        r["rivalry"] = safe_numeric(r.get("rivalry"), 0, 100, default=0, label="rivalry")
        r["betrayal_prob"] = safe_numeric(r.get("betrayal_prob"), 0, 1, default=0.5, label="betrayal_prob")
    # Deduplicate by (from, to) – keep first
    seen: Set[Tuple[str, str]] = set()
    unique: List[Dict[str, Any]] = []
    for r in rels:
        key = (r["from"], r["to"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


# ---------------------------------------------------------------------------
# Issue #9: Validate Missing / Ghost References
# ---------------------------------------------------------------------------

def validate_references(
    reps: List[Dict[str, Any]],
    props: List[Dict[str, Any]],
    objs: List[Dict[str, Any]],
    rels: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove orphaned records that reference non-existent entities.
    Returns sanitized (proposals, objections, relations).
    """
    valid_rep_ids: Set[str] = {r["id"] for r in reps}
    valid_prop_ids: Set[str] = {p["id"] for p in props}

    # Proposals: drop those whose sponsor doesn't exist
    clean_props = [p for p in props if p["sponsor"] in valid_rep_ids]
    orphaned_props = [p for p in props if p["sponsor"] not in valid_rep_ids]
    for op in orphaned_props:
        print(f"[SANITIZE] Dropping orphaned proposal {op['id']} (sponsor {op['sponsor']} not found)")

    # Update valid_prop_ids after sponsor check
    valid_prop_ids = {p["id"] for p in clean_props}

    # Objections: drop those referencing ghost reps or ghost proposals
    clean_objs = [
        o for o in objs
        if o["rep_id"] in valid_rep_ids and o["proposal_id"] in valid_prop_ids
    ]
    dropped_objs = len(objs) - len(clean_objs)
    if dropped_objs:
        print(f"[SANITIZE] Dropped {dropped_objs} orphaned objection(s)")

    # Relations: drop those referencing ghost reps
    clean_rels = [
        r for r in rels
        if r["from"] in valid_rep_ids and r["to"] in valid_rep_ids
    ]
    dropped_rels = len(rels) - len(clean_rels)
    if dropped_rels:
        print(f"[SANITIZE] Dropped {dropped_rels} orphaned relation(s)")

    return clean_props, clean_objs, clean_rels


# ---------------------------------------------------------------------------
# Persist cleaned data to disk
# ---------------------------------------------------------------------------

# Define canonical fields for each dataset (strips junk columns)
_REP_FIELDS = ["id", "name", "faction", "influence"]
_PROP_FIELDS = ["id", "title", "sponsor", "priority", "category"]
_OBJ_FIELDS = ["rep_id", "proposal_id", "severity", "reason"]
_REL_FIELDS = ["from", "to", "trust", "rivalry", "betrayal_prob"]


def _pick_fields(records: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
    """Return records with only the canonical fields, in order."""
    return [{k: rec.get(k) for k in fields} for rec in records]


def write_cleaned_data(
    reps: List[Dict[str, Any]],
    props: List[Dict[str, Any]],
    objs: List[Dict[str, Any]],
    rels: List[Dict[str, Any]],
    output_dir: str,
) -> None:
    """
    Persist fully sanitized datasets to disk under output_dir/cleaned/.
    - representatives.json, proposals.json, objections.json as JSON
    - relations.csv as CSV
    All dirty values are fixed, duplicates removed, orphans dropped.
    """
    cleaned_dir = os.path.join(output_dir, "cleaned")
    os.makedirs(cleaned_dir, exist_ok=True)

    # Representatives
    clean_reps = _pick_fields(reps, _REP_FIELDS)
    with open(os.path.join(cleaned_dir, "representatives.json"), "w", encoding="utf-8") as f:
        json.dump(clean_reps, f, indent=2, ensure_ascii=False)
    print(f"[CLEANED] representatives.json -> {len(clean_reps)} records")

    # Proposals
    clean_props = _pick_fields(props, _PROP_FIELDS)
    with open(os.path.join(cleaned_dir, "proposals.json"), "w", encoding="utf-8") as f:
        json.dump(clean_props, f, indent=2, ensure_ascii=False)
    print(f"[CLEANED] proposals.json -> {len(clean_props)} records")

    # Objections
    clean_objs = _pick_fields(objs, _OBJ_FIELDS)
    with open(os.path.join(cleaned_dir, "objections.json"), "w", encoding="utf-8") as f:
        json.dump(clean_objs, f, indent=2, ensure_ascii=False)
    print(f"[CLEANED] objections.json -> {len(clean_objs)} records")

    # Relations (CSV)
    clean_rels = _pick_fields(rels, _REL_FIELDS)
    with open(os.path.join(cleaned_dir, "relations.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_REL_FIELDS)
        writer.writeheader()
        writer.writerows(clean_rels)
    print(f"[CLEANED] relations.csv -> {len(clean_rels)} records")

    print(f"[CLEANED] All cleaned files written to {cleaned_dir}")

