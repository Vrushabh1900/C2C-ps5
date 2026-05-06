"""
Module: strategic_logic (Tier S)
Issues addressed: #12 (Trojan Horses), #13 (Poison Pills),
                  #14 (Genuine Alliances), #15 (Asymmetric Trust / False Friends),
                  #16 (Faction Infiltrators), Cascading Betrayal

Tier S upgrades:
  - Explicit False Friend detection (trust parity check)
  - Faction Infiltrator with strict 0.80 threshold
  - Relative Risk Thresholds via Z-score (Statistical Climate Model)
  - Graph-Based Cascading Risk (secondary betrayal propagation)

Anti-trap detection layer that screens out destabilizing actors and proposals.
"""

from typing import List, Dict, Any, Set, Tuple
import itertools
import math


# ========================== CONFIGURABLE THRESHOLDS ==========================
TROJAN_HORSE_INFLUENCE_THRESH = 60      # High influence to be "desirable"
TROJAN_HORSE_BETRAYAL_THRESH = 0.50     # Any avg betrayal >= this -> Trojan Horse
POISON_PILL_VIABILITY_THRESH = 0.0      # Viability must be > 0 (non-negative)
ALLIANCE_SCORE_THRESH = 50              # Minimum relationship_score for alliance
CASCADE_BETRAYAL_CHAIN_THRESH = 0.60    # Cumulative betrayal risk in chain

# Tier S: Explicit False Friend thresholds (raw trust, not relationship_score)
FALSE_FRIEND_TRUST_HIGH = 70            # A trusts B > this
FALSE_FRIEND_TRUST_LOW = 40             # But B trusts A < this -> False Friend

# Tier S: Faction Infiltrator strict threshold
INFILTRATOR_BETRAYAL_THRESH = 0.80      # Intra-faction betrayal > this -> spy

# Tier S: Relative Risk (Z-score) parameters
ZSCORE_EXCLUSION_SIGMA = 2.0            # Exclude reps > 2 std above mean

# Tier S: Graph-Based Cascading Risk
CASCADE_GRAPH_TRUST_THRESH = 80         # "high-trust bond" to a Trojan Horse
CASCADE_GRAPH_RISK_BOOST = 0.30         # Risk score increase for adjacency


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
        if prop["viability"] <= POISON_PILL_VIABILITY_THRESH:
            poison_pills.add(prop["id"])
            print(f"[STRATEGY] Poison Pill rejected: {prop['id']} "
                  f"(priority={prop['priority']}, controversy={prop['controversy']:.2f}, "
                  f"viability={prop['viability']:.2f})")
    return poison_pills


# ---------------------------------------------------------------------------
# Tier S: Explicit False Friend Detection (Issue #15)
# ---------------------------------------------------------------------------

def _build_trust_lookup(relations: List[Dict[str, Any]]) -> Dict[Tuple[str, str], float]:
    """Create directional {(from, to): trust} lookup from raw trust values."""
    return {(r["from"], r["to"]): r["trust"] for r in relations}


def _build_score_lookup(relations: List[Dict[str, Any]]) -> Dict[Tuple[str, str], float]:
    """Create directional {(from, to): relationship_score} lookup."""
    return {(r["from"], r["to"]): r["relationship_score"] for r in relations}


def detect_false_friends(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    excluded_reps: Set[str],
) -> Set[Tuple[str, str]]:
    """
    Tier S: Explicit False Friend detection.
    If Rep A trusts Rep B > 70% but Rep B trusts Rep A < 40%,
    flag this as a False Friend pair. The alliance must be rejected.

    Returns a set of (a, b) tuples representing untrustworthy directional pairs.
    """
    trust_map = _build_trust_lookup(relations)
    valid_reps = [r["id"] for r in reps if r["id"] not in excluded_reps]
    false_friend_pairs: Set[Tuple[str, str]] = set()

    for a, b in itertools.combinations(valid_reps, 2):
        trust_ab = trust_map.get((a, b))
        trust_ba = trust_map.get((b, a))
        if trust_ab is None or trust_ba is None:
            continue

        # Check A->B direction: A trusts B highly but B doesn't trust A
        if trust_ab > FALSE_FRIEND_TRUST_HIGH and trust_ba < FALSE_FRIEND_TRUST_LOW:
            false_friend_pairs.add((a, b))
            print(f"[TIER-S] False Friend detected: {a} trusts {b} "
                  f"({trust_ab:.0f}%) but {b} trusts {a} only ({trust_ba:.0f}%) "
                  f"-- ALLIANCE REJECTED")

        # Check B->A direction: B trusts A highly but A doesn't trust B
        if trust_ba > FALSE_FRIEND_TRUST_HIGH and trust_ab < FALSE_FRIEND_TRUST_LOW:
            false_friend_pairs.add((b, a))
            print(f"[TIER-S] False Friend detected: {b} trusts {a} "
                  f"({trust_ba:.0f}%) but {a} trusts {b} only ({trust_ab:.0f}%) "
                  f"-- ALLIANCE REJECTED")

    return false_friend_pairs


# ---------------------------------------------------------------------------
# Issue #14 & #15: Genuine Alliances + False Friend Filtering
# ---------------------------------------------------------------------------

def detect_alliances(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    excluded_reps: Set[str],
    false_friend_pairs: Set[Tuple[str, str]] = None,
) -> List[List[str]]:
    """
    Issue #14: Genuine alliances require MUTUAL high relationship_score.
    Issue #15: Reject False Friends using explicit trust parity check.

    A pair (A, B) is a genuine alliance when:
      - Both A->B and B->A relationship scores exceed ALLIANCE_SCORE_THRESH
      - Neither direction is flagged as a False Friend pair
      - Neither A nor B is in the excluded set
    """
    if false_friend_pairs is None:
        false_friend_pairs = set()

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

        # Tier S: Check explicit False Friend pairs (either direction blocks alliance)
        if (a, b) in false_friend_pairs or (b, a) in false_friend_pairs:
            continue

        alliances.append(sorted([a, b]))

    return alliances


# ---------------------------------------------------------------------------
# Issue #16: Faction Infiltrators (Tier S: strict 0.80 threshold)
# ---------------------------------------------------------------------------

def detect_faction_infiltrators(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
) -> Set[str]:
    """
    Tier S Infiltrator: A representative with betrayal_prob > 0.80 against
    members of their OWN faction is a spy. They are excluded from
    supporting_reps regardless of their influence score.
    """
    faction_map: Dict[str, str] = {r["id"]: r.get("faction", "") for r in reps}
    infiltrators: Set[str] = set()

    for rel in relations:
        src, dst = rel["from"], rel["to"]
        src_faction = faction_map.get(src, "")
        dst_faction = faction_map.get(dst, "")
        if src_faction and src_faction == dst_faction:
            if rel["betrayal_prob"] > INFILTRATOR_BETRAYAL_THRESH:
                infiltrators.add(src)
                print(f"[TIER-S] Faction Infiltrator detected: {src} "
                      f"(faction={src_faction}, betrayal toward {dst}={rel['betrayal_prob']:.2f}) "
                      f"-- EXCLUDED from supporting_reps")

    return infiltrators


# ---------------------------------------------------------------------------
# Tier S: Relative Risk Thresholds (Z-score Statistical Climate Model)
# ---------------------------------------------------------------------------

def compute_statistical_risk_exclusions(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    already_excluded: Set[str] = None,
) -> Set[str]:
    """
    Tier S: Replace static betrayal thresholds with a Statistical Climate Model.
    Calculate the mean and standard deviation of betrayal_prob across the
    entire dataset. Automatically exclude any rep whose average outgoing
    betrayal risk is > 2 standard deviations above the mean.

    This scales gracefully for 50+ representatives -- the threshold adapts
    to the dataset's risk distribution rather than being a fixed magic number.
    """
    if already_excluded is None:
        already_excluded = set()

    # Collect ALL betrayal probabilities across the dataset
    all_betrayals: List[float] = [r["betrayal_prob"] for r in relations]
    if not all_betrayals:
        return set()

    # Calculate population statistics
    n = len(all_betrayals)
    mean_b = sum(all_betrayals) / n
    variance = sum((b - mean_b) ** 2 for b in all_betrayals) / n
    std_b = math.sqrt(variance) if variance > 0 else 0.0
    threshold = mean_b + ZSCORE_EXCLUSION_SIGMA * std_b

    print(f"[TIER-S] Statistical Climate Model: mean={mean_b:.3f}, "
          f"std={std_b:.3f}, z-threshold (mean+{ZSCORE_EXCLUSION_SIGMA}*std)={threshold:.3f}")

    # Build per-rep average betrayal
    betrayal_per_rep: Dict[str, List[float]] = {}
    for rel in relations:
        src = rel["from"]
        betrayal_per_rep.setdefault(src, []).append(rel["betrayal_prob"])

    flagged: Set[str] = set()
    for rep in reps:
        rid = rep["id"]
        if rid in already_excluded:
            continue
        if rid in betrayal_per_rep:
            avg = sum(betrayal_per_rep[rid]) / len(betrayal_per_rep[rid])
            z_score = (avg - mean_b) / std_b if std_b > 0 else 0.0
            if avg > threshold:
                flagged.add(rid)
                print(f"[TIER-S] Z-score exclusion: {rid} "
                      f"(avg_betrayal={avg:.3f}, z-score={z_score:.2f}, "
                      f"threshold={threshold:.3f}) -- EXCLUDED")

    return flagged


# ---------------------------------------------------------------------------
# Tier S: Graph-Based Cascading Risk (secondary betrayal propagation)
# ---------------------------------------------------------------------------

def compute_graph_cascading_risk(
    reps: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    trojan_horses: Set[str],
    already_excluded: Set[str] = None,
) -> Set[str]:
    """
    Tier S: Treat relationships as a directed graph. If a "safe" representative
    has a high-trust bond (trust > 80) leading DIRECTLY to a "Trojan Horse",
    increase that rep's individual risk score to account for secondary betrayal.

    If the boosted risk score pushes them above the Trojan Horse betrayal
    threshold, they are flagged for exclusion.
    """
    if already_excluded is None:
        already_excluded = set()

    # Build per-rep average betrayal
    betrayal_per_rep: Dict[str, List[float]] = {}
    for rel in relations:
        betrayal_per_rep.setdefault(rel["from"], []).append(rel["betrayal_prob"])

    flagged: Set[str] = set()

    for rel in relations:
        src = rel["from"]
        dst = rel["to"]

        # Only check "safe" reps bonded to Trojan Horses
        if src in already_excluded or src in trojan_horses:
            continue
        if dst not in trojan_horses:
            continue

        # High-trust bond to a Trojan Horse?
        if rel["trust"] > CASCADE_GRAPH_TRUST_THRESH:
            # Calculate the rep's base risk
            base_betrayals = betrayal_per_rep.get(src, [])
            base_risk = sum(base_betrayals) / len(base_betrayals) if base_betrayals else 0.0
            boosted_risk = base_risk + CASCADE_GRAPH_RISK_BOOST

            print(f"[TIER-S] Graph Cascade: {src} has high-trust bond "
                  f"(trust={rel['trust']:.0f}) to Trojan Horse {dst} -- "
                  f"risk boosted {base_risk:.3f} -> {boosted_risk:.3f}")

            if boosted_risk >= TROJAN_HORSE_BETRAYAL_THRESH:
                flagged.add(src)
                print(f"[TIER-S] Graph Cascade EXCLUSION: {src} "
                      f"(boosted_risk={boosted_risk:.3f} >= threshold={TROJAN_HORSE_BETRAYAL_THRESH}) "
                      f"-- EXCLUDED")

    return flagged


# ---------------------------------------------------------------------------
# Legacy: Cascading Betrayal Detection (chain-based)
# ---------------------------------------------------------------------------

def detect_cascading_betrayal_risks(
    relations: List[Dict[str, Any]],
    reps: List[Dict[str, Any]],
    already_excluded: Set[str] = None,
) -> Set[str]:
    """
    Detect HIDDEN cascading betrayal: chains A -> B -> C where each
    individual hop's betrayal is below the Trojan Horse threshold
    but the cumulative risk exceeds CASCADE_BETRAYAL_CHAIN_THRESH.
    """
    if already_excluded is None:
        already_excluded = set()

    adj: Dict[str, List[Tuple[str, float]]] = {}
    for r in relations:
        adj.setdefault(r["from"], []).append((r["to"], r["betrayal_prob"]))

    flagged: Set[str] = set()
    valid_ids = {r["id"] for r in reps} - already_excluded

    for start in valid_ids:
        if start not in adj:
            continue
        for mid, b1 in adj[start]:
            if mid in already_excluded:
                continue
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
