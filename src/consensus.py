"""
Module: consensus (Tier S)
Issues addressed: #17 (Formulate Consensus Output), #19 (Edge Cases)

Tier S upgrade:
  - Supporter Coherence Validation: A representative cannot be in
    supporting_reps if they have an objection severity > 5 for ANY
    proposal in the final_agreement.

Core decision-making loop that produces the final stable agreement.
"""

from typing import List, Dict, Any, Set

# Tier S: Coherence threshold
COHERENCE_SEVERITY_THRESH = 5  # Objection severity > this -> incoherent supporter


def formulate_agreement(
    proposals: List[Dict[str, Any]],
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    objections: List[Dict[str, Any]],
    poison_pills: Set[str],
    excluded_reps: Set[str],
    alliances: List[List[str]],
) -> Dict[str, Any]:
    """
    Issue #17: Select optimal proposals and supporting reps.
    Issue #19: Gracefully handle edge cases.

    Strategy:
    1. Remove Poison Pill proposals.
    2. Rank remaining proposals by viability (descending).
    3. Select proposals with viability > 0 and valid sponsor.
    4. Supporting reps = sponsors + their allies (minus excluded).
    5. Tier S Coherence: Remove reps who object (severity > 5) to any selected proposal.
    6. Empty data -> empty result.
    """
    if not proposals or not reps:
        return _empty_result()

    viable = [p for p in proposals if p["id"] not in poison_pills and p["viability"] > 0]
    viable.sort(key=lambda p: p["viability"], reverse=True)

    if not viable:
        return _empty_result()

    valid_reps = {r["id"] for r in reps if r["id"] not in excluded_reps}
    if not valid_reps:
        return _empty_result()

    selected_proposals: List[str] = []
    sponsoring_reps: Set[str] = set()
    for prop in viable:
        if prop["sponsor"] in valid_reps:
            selected_proposals.append(prop["id"])
            sponsoring_reps.add(prop["sponsor"])

    allied_set: Set[str] = set()
    for pair in alliances:
        a, b = pair[0], pair[1]
        if a in sponsoring_reps:
            allied_set.add(b)
        if b in sponsoring_reps:
            allied_set.add(a)

    supporting_reps = (sponsoring_reps | allied_set) & valid_reps

    if not selected_proposals:
        return _empty_result()

    # ================================================================
    # Tier S: Supporter Coherence Validation
    # A rep cannot support the agreement if they have a strong objection
    # (severity > 5) to ANY proposal in the final agreement.
    # ================================================================
    selected_set = set(selected_proposals)
    incoherent_reps: Set[str] = set()
    for obj in objections:
        rep_id = obj.get("rep_id", "")
        prop_id = obj.get("proposal_id", "")
        severity = obj.get("severity", 0)
        if rep_id in supporting_reps and prop_id in selected_set:
            if severity > COHERENCE_SEVERITY_THRESH:
                incoherent_reps.add(rep_id)
                print(f"[TIER-S] Coherence violation: {rep_id} objects to "
                      f"{prop_id} (severity={severity}) -- REMOVED from supporters")

    supporting_reps -= incoherent_reps

    return {
        "final_agreement": {
            "proposals": sorted(selected_proposals),
            "supporting_reps": sorted(supporting_reps),
        },
        "alliances": [sorted(pair) for pair in alliances],
    }


def _empty_result() -> Dict[str, Any]:
    """Return correct schema with empty lists for edge cases (#19)."""
    return {
        "final_agreement": {"proposals": [], "supporting_reps": []},
        "alliances": [],
    }
