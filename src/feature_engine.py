"""
Module: feature_engine
Issues addressed: #10 (Relationship Scores), #11 (Objection Weights),
                  + Proposal Viability calculation

Derives actionable metrics from sanitized data.
"""

from typing import List, Dict, Any, Tuple


# ---------------------------------------------------------------------------
# Issue #10: Relationship Score
# ---------------------------------------------------------------------------

def compute_relationship_scores(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    relationship_score = trust * (1 - betrayal_prob)

    This metric collapses trust + betrayal risk into a single reliability
    number (0-100 scale). A high trust with high betrayal ≈ low score.
    """
    for rel in relations:
        trust = rel.get("trust", 0)
        betrayal = rel.get("betrayal_prob", 0.5)
        rel["relationship_score"] = round(trust * (1 - betrayal), 4)
    return relations


# ---------------------------------------------------------------------------
# Issue #11: Objection Weights
# ---------------------------------------------------------------------------

def compute_objection_weights(
    objections: List[Dict[str, Any]],
    rep_influence_map: Dict[str, float],
) -> Dict[str, float]:
    """
    objection_weight(proposal) = Σ (severity * objector_influence)

    Returns {proposal_id: aggregate_weight}.
    """
    weights: Dict[str, float] = {}
    for obj in objections:
        pid = obj["proposal_id"]
        severity = obj.get("severity", 0)
        influence = rep_influence_map.get(obj["rep_id"], 0)
        w = severity * influence
        weights[pid] = weights.get(pid, 0) + w
    return weights


# ---------------------------------------------------------------------------
# Proposal Viability (combined metric)
# ---------------------------------------------------------------------------

def compute_proposal_viability(
    proposals: List[Dict[str, Any]],
    objection_weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    controversy = normalized objection weight for the proposal (0-1 scale)
    proposal_viability = priority * (1 - controversy)

    Normalizes objection weights across all proposals so the maximum
    observed weight maps to controversy = 1.0.
    """
    max_weight = max(objection_weights.values()) if objection_weights else 1
    if max_weight == 0:
        max_weight = 1  # Avoid division by zero

    for prop in proposals:
        pid = prop["id"]
        raw_weight = objection_weights.get(pid, 0)
        controversy = raw_weight / max_weight
        prop["controversy"] = round(controversy, 4)
        prop["objection_weight"] = raw_weight
        prop["viability"] = round(prop["priority"] * (1 - controversy), 4)
    return proposals


# ---------------------------------------------------------------------------
# Convenience: build influence lookup
# ---------------------------------------------------------------------------

def build_influence_map(reps: List[Dict[str, Any]]) -> Dict[str, float]:
    """Create {rep_id: influence} lookup from sanitized representatives."""
    return {r["id"]: r["influence"] for r in reps}
