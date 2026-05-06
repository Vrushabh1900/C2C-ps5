# Results: Phantom Consensus Engine (Tier S)

## Execution Summary

| Metric | Value |
|--------|-------|
| Raw representatives loaded | 8 |
| After sanitization (dedup + normalize) | 6 |
| Raw proposals loaded | 6 |
| After sanitization (dedup + orphan removal) | 4 |
| Raw objections loaded | 8 |
| After sanitization | 6 |
| Raw relations loaded | 16 |
| After sanitization | 15 |
| Pipeline execution time | ~6ms |

## Data Cleaning Actions

| Action | Count | Details |
|--------|-------|---------|
| ID normalization | All records | `REP_001` -> `rep_001`, `" rep_004"` -> `rep_004` |
| Influence clamping | 2 | `rep_005`: 150 -> 100, `rep_004`: null -> 0 |
| Type casting | 2 | `rep_002` influence: `"70"` -> 70, objection severity: `"high"` -> 8 |
| Severity clamping | 1 | -3 -> 0 (negative severity) |
| Betrayal clamping | 1 | 1.5 -> 1.0 (out of range) |
| Duplicate reps removed | 2 | `REP_001` (dup of `rep_001`), `" rep_004"` (dup of `rep_004`) |
| Duplicate proposals removed | 1 | `prop_003` duplicate |
| Orphaned proposal dropped | 1 | `prop_005` (sponsor `rep_099` doesn't exist) |
| Ghost objection dropped | 1 | Objector `rep_099` doesn't exist |
| Duplicate relation dropped | 1 | `rep_001 -> rep_002` duplicate row |

## Feature Engineering Results

### Proposal Viability Scores

| Proposal | Priority | Objection Weight | Controversy | Viability | Status |
|----------|----------|-----------------|-------------|-----------|--------|
| prop_003 | 9.5 | 350.0 | 0.41 | **5.61** | Passed |
| prop_002 | 10.0 | 680.0 | 0.80 | **2.05** | Passed |
| prop_001 | 8.0 | 760.0 | 0.89 | **0.89** | Passed |
| prop_004 | 10.0 | 855.0 | 1.00 | **0.00** | Poison Pill |

## Tier S Strategic Detections

### Phase 1: Core Threats

| Detection | Rep ID | Reason |
|-----------|--------|--------|
| Trojan Horse | rep_005 | influence=100, avg_betrayal=0.57 |
| Trojan Horse | rep_006 | influence=92, avg_betrayal=0.78 |

### Phase 2: Statistical Climate Model (Z-score)

| Metric | Value |
|--------|-------|
| Mean betrayal (dataset) | 0.358 |
| Std deviation | 0.295 |
| Z-threshold (mean + 2*std) | 0.947 |
| Reps excluded by Z-score | 0 (Trojans already caught by Phase 1) |

### Phase 3: Graph-Based Cascading Risk

No additional exclusions -- no safe rep has a high-trust bond (>80) to a Trojan Horse that isn't already caught by other layers.

### Phase 4: Chain-Based Cascading Betrayal

No additional exclusions -- all dangerous chains route through already-excluded Trojan Horses.

### Phase 5: False Friend Detection

No False Friend pairs detected in current dataset. All relationships with sufficient trust have adequate reciprocity (no case where A trusts B > 70% while B trusts A < 40%).

### Representative Final Risk Assessment

| Rep ID | Name | Influence | Avg Betrayal | Status | Reason |
|--------|------|-----------|-------------|--------|--------|
| rep_001 | Senator Aria | 85 | 0.25 | Coherence Violation | Objects to prop_002 (severity=8) |
| rep_002 | Councilor Blake | 70 | 0.26 | Active | -- |
| rep_003 | Minister Chen | 95 | 0.38 | Coherence Violation | Objects to prop_001 (severity=8) |
| rep_004 | Delegate Davis | 0 | 0.11 | **Active Supporter** | No strong objections |
| rep_005 | Ambassador Ellis | 100 | 0.57 | Excluded | Trojan Horse |
| rep_006 | Director Fox | 92 | 0.78 | Excluded | Trojan Horse |

### Tier S: Supporter Coherence Violations

| Rep | Objected Proposal | Severity | Action |
|-----|------------------|----------|--------|
| rep_003 | prop_001 | 8.0 | REMOVED from supporters |
| rep_001 | prop_002 | 8.0 | REMOVED from supporters |

## Final Consensus Output

```json
{
  "final_agreement": {
    "proposals": ["prop_001", "prop_002", "prop_003"],
    "supporting_reps": ["rep_004"]
  },
  "alliances": [["rep_001", "rep_004"]]
}
```

### Why This Agreement Is Stable (Tier S Analysis)

1. **Proposal selection**: All 3 proposals have positive viability. The Poison Pill (prop_004) was correctly rejected despite priority=10.
2. **Trojan Horse exclusion**: rep_005 and rep_006 excluded before any alliance or coherence checks.
3. **Coherence enforcement**: rep_001 and rep_003 pass all security checks but fail coherence -- they object strongly (severity=8) to proposals in the agreement. Including them would create internal contradiction.
4. **Sole stable supporter**: rep_004 is the only representative who (a) sponsors a selected proposal (prop_003), (b) is not excluded by any strategic detection, and (c) has no strong objections to any selected proposal.
5. **Alliance preserved**: The rep_001/rep_004 alliance is genuine but rep_001 cannot be a *supporter* due to coherence. The alliance still informs the network topology.
6. **Z-score model ready to scale**: For larger datasets, the statistical threshold will automatically adapt rather than using a fixed 0.50 cutoff.
