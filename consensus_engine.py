#!/usr/bin/env python3
"""
consensus_engine.py  –  Phantom Consensus  –  Primary Entry Point

Executes the full pipeline:
  1. Data Loading        (Issues #2–#5)
  2. Data Sanitization   (Issues #6–#9)
  3. Feature Engineering  (Issues #10–#11)
  4. Strategic Logic      (Issues #12–#16)
  5. Consensus Building   (Issues #17, #19)
  6. Output Formatting    (Issue #18)
  7. Performance-safe     (Issue #20)

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
    detect_faction_infiltrators,
    detect_cascading_betrayal_risks,
)
from src.consensus import formulate_agreement
from src.output_formatter import write_result


def run_pipeline(data_dir: str, output_dir: str) -> dict:
    """Execute the full Phantom Consensus pipeline."""
    t0 = time.perf_counter()

    # ==== LAYER 1: DATA LOADING ====
    print("=" * 60)
    print("LAYER 1 – DATA LOADING")
    print("=" * 60)
    raw_reps = load_representatives(data_dir)
    raw_props = load_proposals(data_dir)
    raw_objs = load_objections(data_dir)
    raw_rels = load_relations(data_dir)
    print(f"  Loaded: {len(raw_reps)} reps, {len(raw_props)} proposals, "
          f"{len(raw_objs)} objections, {len(raw_rels)} relations")

    # ==== LAYER 1b: DATA SANITIZATION ====
    print("\n" + "=" * 60)
    print("LAYER 1b – DATA SANITIZATION")
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
    print("LAYER 2 – FEATURE ENGINEERING")
    print("=" * 60)
    influence_map = build_influence_map(reps)
    rels = compute_relationship_scores(rels)
    obj_weights = compute_objection_weights(objs, influence_map)
    props = compute_proposal_viability(props, obj_weights)

    for p in props:
        print(f"  {p['id']}: priority={p['priority']}, "
              f"controversy={p['controversy']:.2f}, viability={p['viability']:.2f}")

    # ==== LAYER 4: STRATEGIC LOGIC ====
    print("\n" + "=" * 60)
    print("LAYER 4 – STRATEGIC LOGIC (ANTI-TRAP DETECTION)")
    print("=" * 60)

    trojan_horses = detect_trojan_horses(reps, rels)
    infiltrators = detect_faction_infiltrators(reps, rels)
    cascade_risks = detect_cascading_betrayal_risks(rels, reps, already_excluded=trojan_horses | infiltrators)

    # Union of all excluded representatives
    excluded_reps = trojan_horses | infiltrators | cascade_risks
    print(f"  Excluded reps (total): {sorted(excluded_reps)}")

    poison_pills = detect_poison_pills(props)
    print(f"  Poison Pill proposals: {sorted(poison_pills)}")

    alliances = detect_alliances(reps, rels, excluded_reps)
    print(f"  Genuine alliances: {alliances}")

    # ==== CONSENSUS ====
    print("\n" + "=" * 60)
    print("CONSENSUS FORMULATION")
    print("=" * 60)
    result = formulate_agreement(
        proposals=props,
        reps=reps,
        relations=rels,
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
    parser = argparse.ArgumentParser(description="Phantom Consensus Engine")
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
