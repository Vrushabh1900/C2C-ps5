# Limitations: Phantom Consensus Engine

## 1. Threshold Sensitivity

All strategic detections rely on configurable thresholds (defined in `src/strategic_logic.py`):

| Threshold | Default | Risk |
|-----------|---------|------|
| Trojan Horse influence | ≥ 60 | Could miss moderate-influence betrayers |
| Trojan Horse betrayal | ≥ 0.50 | Border cases (0.49 vs 0.50) flip outcomes |
| Alliance score | ≥ 50 | Tight threshold; a score of 49.9 is excluded |
| Asymmetry ratio | ≥ 0.50 | Some unequal-but-stable alliances may be rejected |
| Infiltrator betrayal | ≥ 0.40 | Faction-internal politics may have legitimate tension |
| Cascade cumulative | ≥ 0.60 | Very sensitive to chain length |

**Mitigation**: All thresholds are module-level constants, easily tunable without code changes.

## 2. First-Occurrence-Wins Deduplication

When duplicate IDs are found (e.g., `REP_001` and `rep_001`), the first record in file order wins. This is deterministic but could lose better data from later records.

**Mitigation**: Could be extended to merge attributes (e.g., take maximum influence), but this risks combining unrelated entities.

## 3. Static Influence Model

Influence scores are treated as fixed. The engine does not model:
- Influence decay over time
- Influence gains from successful alliances
- Dynamic reputation based on historical betrayal

## 4. Binary Exclusion

Flagged representatives are fully excluded — there's no partial penalty. A borderline Trojan Horse is treated identically to an extreme one.

**Mitigation**: A future version could assign risk weights rather than binary exclusions.

## 5. Pairwise Alliance Detection Only

Alliances are detected as pairs. The engine does not identify multi-party coalitions (triads, blocs) beyond what emerges from the union of pairwise alliances.

## 6. No Temporal Modeling

The `last_interaction` field in relations.csv is loaded but not used. Recent interactions should arguably carry more weight than older ones.

## 7. Objection Severity Scale Ambiguity

The severity field mixes numeric scores (0-10), string labels ("high"), null values, and negative numbers. While the engine handles all these, the underlying meaning may vary across data sources.

## 8. No Cross-Validation Against Hidden Tests

The engine was designed against the 20 documented issues and the provided sample data. The "18 hidden scenario-based tests" referenced in the briefing cannot be validated without access to those scenarios. The architecture is designed to be resilient via:
- Comprehensive edge case handling (Issue #19)
- Graceful degradation (empty results rather than crashes)
- Configurable thresholds for easy tuning

## 9. Single-Pass Pipeline

The engine runs a single forward pass. It does not iterate (e.g., "what if we include a borderline rep?"). A more sophisticated approach could use optimization or simulation.

## 10. Visualization Dependency

The interactive Plotly dashboard requires `plotly` and `networkx` to be installed. A static HTML fallback is provided, but it lacks interactivity.
