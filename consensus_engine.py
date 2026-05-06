#!/usr/bin/env python3
"""
consensus_engine.py  --  Phantom Consensus (Tier S)  --  Primary Entry Point

Executes the full pipeline:
  1. Data Loading          (Issues #2-#5)
  2. Data Sanitization     (Issues #6-#9)
  3. Feature Engineering   (Issues #10-#11)
  4. Strategic Logic       (Issues #12-#16) + Tier S upgrades
  5. Consensus Building    (Issues #17, #19) + Supporter Coherence
  6. Output Formatting     (Issue #18)
  7. Performance-safe      (Issue #20)

Tier S Layers:
  - Explicit False Friend Detection (trust parity)
  - Supporter Coherence Validation (objection severity gate)
  - Faction Infiltrator Detection (>0.80 intra-faction betrayal)
  - Relative Risk Thresholds (Z-score Statistical Climate Model)
  - Graph-Based Cascading Risk (secondary betrayal propagation)

Usage:
    python consensus_engine.py [--data-dir DATA_DIR] [--output-dir OUTPUT_DIR]
"""

import argparse
import os
import sys
import time

# Ensure the project root is on sys.path so `src` is importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.data_loader import (
    load_representatives,
    load_proposals,
    load_objections,
    load_relations,
)
from src.data_sanitizer import (
    sanitize_representatives,
    sanitize_proposals,
    sanitize_objections,
    sanitize_relations,
    validate_references,
    write_cleaned_data,
)
from src.feature_engine import (
    build_influence_map,
    compute_relationship_scores,
    compute_objection_weights,
    compute_proposal_viability,
)
from src.strategic_logic import (
    detect_trojan_horses,
    detect_poison_pills,
    detect_alliances,
    detect_false_friends,
    detect_faction_infiltrators,
    detect_cascading_betrayal_risks,
    compute_statistical_risk_exclusions,
    compute_graph_cascading_risk,
)
from src.consensus import formulate_agreement
from src.output_formatter import write_result


def run_pipeline(data_dir: str, output_dir: str) -> dict:
    """Execute the full Phantom Consensus pipeline (Tier S)."""
    t0 = time.perf_counter()

    # ==== LAYER 1: DATA LOADING ====
    print("=" * 60)
    print("LAYER 1 -- DATA LOADING")
    print("=" * 60)
    raw_reps = load_representatives(data_dir)
    raw_props = load_proposals(data_dir)
    raw_objs = load_objections(data_dir)
    raw_rels = load_relations(data_dir)
    print(f"  Loaded: {len(raw_reps)} reps, {len(raw_props)} proposals, "
          f"{len(raw_objs)} objections, {len(raw_rels)} relations")

    # ==== LAYER 1b: DATA SANITIZATION ====
    print("\n" + "=" * 60)
    print("LAYER 1b -- DATA SANITIZATION")
    print("=" * 60)
    reps = sanitize_representatives(raw_reps)
    props = sanitize_proposals(raw_props)
    objs = sanitize_objections(raw_objs)
    rels = sanitize_relations(raw_rels)
    print(f"  After sanitization: {len(reps)} reps, {len(props)} proposals, "
          f"{len(objs)} objections, {len(rels)} relations")

    # Validate cross-references
    props, objs, rels = validate_references(reps, props, objs, rels)
    print(f"  After ref validation: {len(props)} proposals, "
          f"{len(objs)} objections, {len(rels)} relations")

    # Persist cleaned data to disk
    write_cleaned_data(reps, props, objs, rels, output_dir)

    # ==== LAYER 2: FEATURE ENGINEERING ====
    print("\n" + "=" * 60)
    print("LAYER 2 -- FEATURE ENGINEERING")
    print("=" * 60)
    influence_map = build_influence_map(reps)
    rels = compute_relationship_scores(rels)
    obj_weights = compute_objection_weights(objs, influence_map)
    props = compute_proposal_viability(props, obj_weights)

    for p in props:
        print(f"  {p['id']}: priority={p['priority']}, "
              f"controversy={p['controversy']:.2f}, viability={p['viability']:.2f}")

    # ==== LAYER 4: STRATEGIC LOGIC (TIER S) ====
    print("\n" + "=" * 60)
    print("LAYER 4 -- STRATEGIC LOGIC (TIER S ANTI-TRAP DETECTION)")
    print("=" * 60)

    # --- Phase 1: Core detections ---
    print("\n  --- Phase 1: Core Threat Detection ---")
    trojan_horses = detect_trojan_horses(reps, rels)
    infiltrators = detect_faction_infiltrators(reps, rels)

    # --- Phase 2: Tier S - Relative Risk (Z-score) ---
    print("\n  --- Phase 2: Tier S - Statistical Climate Model ---")
    zscore_excluded = compute_statistical_risk_exclusions(
        reps, rels, already_excluded=trojan_horses | infiltrators)

    # --- Phase 3: Tier S - Graph-Based Cascading Risk ---
    print("\n  --- Phase 3: Tier S - Graph-Based Cascading Risk ---")
    graph_cascade = compute_graph_cascading_risk(
        reps, rels, trojan_horses,
        already_excluded=trojan_horses | infiltrators | zscore_excluded)

    # --- Phase 4: Legacy chain-based cascading ---
    print("\n  --- Phase 4: Chain-Based Cascading Betrayal ---")
    chain_cascade = detect_cascading_betrayal_risks(
        rels, reps,
        already_excluded=trojan_horses | infiltrators | zscore_excluded | graph_cascade)

    # Union of all excluded representatives
    excluded_reps = (trojan_horses | infiltrators | zscore_excluded
                     | graph_cascade | chain_cascade)
    print(f"\n  [SUMMARY] Excluded reps (total): {sorted(excluded_reps)}")
    print(f"    Trojan Horses:     {sorted(trojan_horses)}")
    print(f"    Infiltrators:      {sorted(infiltrators)}")
    print(f"    Z-score excluded:  {sorted(zscore_excluded)}")
    print(f"    Graph cascade:     {sorted(graph_cascade)}")
    print(f"    Chain cascade:     {sorted(chain_cascade)}")

    # --- Poison Pill detection ---
    print("\n  --- Poison Pill Detection ---")
    poison_pills = detect_poison_pills(props)
    print(f"  Poison Pill proposals: {sorted(poison_pills)}")

    # --- Phase 5: Tier S - False Friend Detection ---
    print("\n  --- Phase 5: Tier S - False Friend Detection ---")
    false_friend_pairs = detect_false_friends(reps, rels, excluded_reps)

    # --- Alliance Detection (with False Friend filtering) ---
    print("\n  --- Alliance Detection ---")
    alliances = detect_alliances(reps, rels, excluded_reps, false_friend_pairs)
    print(f"  Genuine alliances: {alliances}")

    # ==== CONSENSUS (with Tier S Coherence) ====
    print("\n" + "=" * 60)
    print("CONSENSUS FORMULATION (TIER S - WITH COHERENCE CHECK)")
    print("=" * 60)
    result = formulate_agreement(
        proposals=props,
        reps=reps,
        relations=rels,
        objections=objs,
        poison_pills=poison_pills,
        excluded_reps=excluded_reps,
        alliances=alliances,
    )

    # ==== OUTPUT ====
    filepath = write_result(result, output_dir)
    elapsed = time.perf_counter() - t0
    print(f"\n{'=' * 60}")
    print(f"PIPELINE COMPLETE in {elapsed:.3f}s")
    print(f"Result: {filepath}")
    print(f"{'=' * 60}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Phantom Consensus Engine (Tier S)")
    parser.add_argument(
        "--data-dir",
        default=os.path.join(PROJECT_ROOT, "data", "raw"),
        help="Path to the raw data directory",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(PROJECT_ROOT, "data"),
        help="Path to write consensus_result.json",
    )
    args = parser.parse_args()
    run_pipeline(args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
