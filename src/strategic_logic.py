"""
Module: strategic_logic
Issues addressed: #12 (Trojan Horses), #13 (Poison Pills),
                  #14 (Genuine Alliances), #15 (Asymmetric Trust / False Friends),
                  #16 (Faction Infiltrators), Cascading Betrayal

Anti-trap detection layer that screens out destabilizing actors and proposals.
"""

from typing import List, Dict, Any, Set, Tuple
import itertools


# ========================== CONFIGURABLE THRESHOLDS ==========================
TROJAN_HORSE_INFLUENCE_THRESH = 60      # High influence to be "desirable"
TROJAN_HORSE_BETRAYAL_THRESH = 0.50     # Any avg betrayal ≥ this → Trojan Horse
POISON_PILL_VIABILITY_THRESH = 0.0      # Viability must be > 0 (non-negative)
ALLIANCE_SCORE_THRESH = 50              # Minimum relationship_score for alliance
ASYMMETRY_RATIO = 0.5                   # If min/max score < this → False Friend
INFILTRATOR_BETRAYAL_THRESH = 0.40      # Intra-faction betrayal ≥ this → spy
CASCADE_BETRAYAL_CHAIN_THRESH = 0.60    # Cumulative betrayal risk in chain


# ---------------------------------------------------------------------------
# Issue #12: Filter Trojan Horse Representatives
# ---------------------------------------------------------------------------

def detect_trojan_horses(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
) -> Set[str]:
    """
    Trojan Horse = high influence BUT high average betrayal probability.
    These individuals look attractive but would destabilize the consensus.
    """
    # Build per-rep average betrayal from outgoing relations
    betrayal_sums: Dict[str, List[float]] = {}
    for rel in relations:
        src = rel["from"]
        betrayal_sums.setdefault(src, []).append(rel["betrayal_prob"])

    trojan_horses: Set[str] = set()
    for rep in reps:
        rid = rep["id"]
        influence = rep["influence"]
        avg_betrayal = 0.0
        if rid in betrayal_sums:
            vals = betrayal_sums[rid]
            avg_betrayal = sum(vals) / len(vals) if vals else 0.0

        if influence >= TROJAN_HORSE_INFLUENCE_THRESH and avg_betrayal >= TROJAN_HORSE_BETRAYAL_THRESH:
            trojan_horses.add(rid)
            print(f"[STRATEGY] Trojan Horse detected: {rid} "
                  f"(influence={influence}, avg_betrayal={avg_betrayal:.2f})")

    return trojan_horses


# ---------------------------------------------------------------------------
# Issue #13: Reject Poison Pill Proposals
# ---------------------------------------------------------------------------

def detect_poison_pills(proposals: List[Dict[str, Any]]) -> Set[str]:
    """
    Poison Pill = proposal whose viability is effectively zero or negative,
    meaning objection weight overwhelms priority despite a seemingly high
    priority score.
    """
    poison_pills: Set[str] = set()
    for prop in proposals:
        # A high-priority proposal that has controversy ≈ 1 → viability ≈ 0
        if prop["viability"] <= POISON_PILL_VIABILITY_THRESH:
            poison_pills.add(prop["id"])
            print(f"[STRATEGY] Poison Pill rejected: {prop['id']} "
                  f"(priority={prop['priority']}, controversy={prop['controversy']:.2f}, "
                  f"viability={prop['viability']:.2f})")
    return poison_pills


# ---------------------------------------------------------------------------
# Issue #14 & #15: Genuine Alliances + Asymmetric Trust (False Friends)
# ---------------------------------------------------------------------------

def _build_score_lookup(relations: List[Dict[str, Any]]) -> Dict[Tuple[str, str], float]:
    """Create directional {(from, to): relationship_score} lookup."""
    return {(r["from"], r["to"]): r["relationship_score"] for r in relations}


def detect_alliances(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    excluded_reps: Set[str],
) -> List[List[str]]:
    """
    Issue #14: Genuine alliances require MUTUAL high relationship_score.
    Issue #15: Reject asymmetric trust (False Friends).

    A pair (A, B) is a genuine alliance when:
      - Both A→B and B→A relationship scores exceed ALLIANCE_SCORE_THRESH
      - The ratio min(scoreAB, scoreBA) / max(scoreAB, scoreBA) ≥ ASYMMETRY_RATIO
      - Neither A nor B is in the excluded set
    """
    score_map = _build_score_lookup(relations)
    valid_reps = [r["id"] for r in reps if r["id"] not in excluded_reps]
    alliances: List[List[str]] = []

    for a, b in itertools.combinations(valid_reps, 2):
        score_ab = score_map.get((a, b))
        score_ba = score_map.get((b, a))
        if score_ab is None or score_ba is None:
            continue
        if score_ab < ALLIANCE_SCORE_THRESH or score_ba < ALLIANCE_SCORE_THRESH:
            continue
        # Asymmetry check
        min_s = min(score_ab, score_ba)
        max_s = max(score_ab, score_ba)
        if max_s == 0:
            continue
        ratio = min_s / max_s
        if ratio < ASYMMETRY_RATIO:
            print(f"[STRATEGY] False Friend detected: ({a}, {b}) "
                  f"scores=({score_ab:.1f}, {score_ba:.1f}), ratio={ratio:.2f}")
            continue
        alliances.append(sorted([a, b]))

    return alliances


# ---------------------------------------------------------------------------
# Issue #16: Faction Infiltrators
# ---------------------------------------------------------------------------

def detect_faction_infiltrators(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
) -> Set[str]:
    """
    Infiltrator = shares a faction label with another rep but has high
    betrayal probability toward members of that same faction.
    """
    # Build faction membership
    faction_map: Dict[str, str] = {r["id"]: r.get("faction", "") for r in reps}
    infiltrators: Set[str] = set()

    for rel in relations:
        src, dst = rel["from"], rel["to"]
        src_faction = faction_map.get(src, "")
        dst_faction = faction_map.get(dst, "")
        if src_faction and src_faction == dst_faction:
            if rel["betrayal_prob"] >= INFILTRATOR_BETRAYAL_THRESH:
                infiltrators.add(src)
                print(f"[STRATEGY] Faction Infiltrator detected: {src} "
                      f"(faction={src_faction}, betrayal toward {dst}={rel['betrayal_prob']:.2f})")

    return infiltrators


# ---------------------------------------------------------------------------
# Cascading Betrayal Detection
# ---------------------------------------------------------------------------

def detect_cascading_betrayal_risks(
    relations: List[Dict[str, Any]],
    reps: List[Dict[str, Any]],
    already_excluded: Set[str] = None,
) -> Set[str]:
    """
    Detect HIDDEN cascading betrayal: chains A -> B -> C where each
    individual hop's betrayal is below the Trojan Horse threshold
    (i.e., each hop looks "safe") but the cumulative risk
    1 - prod(1 - betrayal_i) exceeds CASCADE_BETRAYAL_CHAIN_THRESH.

    Only flags reps not already caught by other detections.
    """
    if already_excluded is None:
        already_excluded = set()

    # Build adjacency: from -> [(to, betrayal_prob)]
    adj: Dict[str, List[Tuple[str, float]]] = {}
    for r in relations:
        adj.setdefault(r["from"], []).append((r["to"], r["betrayal_prob"]))

    flagged: Set[str] = set()
    valid_ids = {r["id"] for r in reps} - already_excluded

    for start in valid_ids:
        if start not in adj:
            continue
        for mid, b1 in adj[start]:
            # Skip chains that route through already-excluded nodes
            if mid in already_excluded:
                continue
            # Each individual hop must be below obvious-threat threshold
            if b1 >= TROJAN_HORSE_BETRAYAL_THRESH:
                continue
            if mid not in adj:
                continue
            for end, b2 in adj[mid]:
                if end == start or end in already_excluded:
                    continue
                if b2 >= TROJAN_HORSE_BETRAYAL_THRESH:
                    continue
                cumulative = 1 - (1 - b1) * (1 - b2)
                if cumulative >= CASCADE_BETRAYAL_CHAIN_THRESH:
                    flagged.add(start)
                    flagged.add(end)
                    print(f"[STRATEGY] Cascading betrayal risk: {start} -> {mid} -> {end} "
                          f"(cumulative={cumulative:.2f})")

    return flagged
