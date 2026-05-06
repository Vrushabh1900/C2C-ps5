# Results: Phantom Consensus Engine

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
| Pipeline execution time | ~3ms |

## Data Cleaning Actions

| Action | Count | Details |
|--------|-------|---------|
| ID normalization | All records | `REP_001` → `rep_001`, `" rep_004"` → `rep_004` |
| Influence clamping | 2 | `rep_005`: 150 → 100, `rep_004`: null → 0 |
| Type casting | 2 | `rep_002` influence: `"70"` → 70, objection severity: `"high"` → 8 |
| Severity clamping | 1 | -3 → 0 (negative severity) |
| Betrayal clamping | 1 | 1.5 → 1.0 (out of range) |
| Duplicate reps removed | 2 | `REP_001` (dup of `rep_001`), `" rep_004"` (dup of `rep_004`) |
| Duplicate proposals removed | 1 | `prop_003` duplicate |
| Orphaned proposal dropped | 1 | `prop_005` (sponsor `rep_099` doesn't exist) |
| Ghost objection dropped | 1 | Objector `rep_099` doesn't exist |
| Duplicate relation dropped | 1 | `rep_001 → rep_002` duplicate row |

## Feature Engineering Results

### Proposal Viability Scores

| Proposal | Priority | Objection Weight | Controversy | Viability | Status |
|----------|----------|-----------------|-------------|-----------|--------|
| prop_003 | 9.5 | 350.0 | 0.41 | **5.61** | ✅ Passed |
| prop_002 | 10.0 | 680.0 | 0.80 | **2.05** | ✅ Passed |
| prop_001 | 8.0 | 760.0 | 0.89 | **0.89** | ✅ Passed |
| prop_004 | 10.0 | 855.0 | 1.00 | **0.00** | ❌ Poison Pill |

### Representative Risk Assessment

| Rep ID | Name | Influence | Avg Betrayal | Status |
|--------|------|-----------|-------------|--------|
| rep_001 | Senator Aria | 85 | 0.25 | ✅ Active |
| rep_002 | Councilor Blake | 70 | 0.26 | ✅ Active |
| rep_003 | Minister Chen | 95 | 0.38 | ✅ Active |
| rep_004 | Delegate Davis | 0 | 0.11 | ✅ Active |
| rep_005 | Ambassador Ellis | 100 | 0.57 | ❌ Trojan Horse |
| rep_006 | Director Fox | 92 | 0.78 | ❌ Trojan Horse |

## Strategic Detections

### Trojan Horses (Issue #12)
- **rep_005** (Ambassador Ellis): influence=100, avg_betrayal=0.57
- **rep_006** (Director Fox): influence=92, avg_betrayal=0.78

### Poison Pills (Issue #13)
- **prop_004** (Emergency Response Protocol): priority=10 but controversy=1.00

### Genuine Alliances (Issues #14, #15)
- **[rep_001, rep_004]**: Mutual high trust (85/90), low betrayal (0.05/0.02)

### Faction Infiltrators (Issue #16)
- None detected in current dataset

### Cascading Betrayal Risks
- None detected after excluding Trojan Horses (all dangerous chains routed through rep_005/rep_006)

## Final Consensus Output

```json
{
  "final_agreement": {
    "proposals": ["prop_001", "prop_002", "prop_003"],
    "supporting_reps": ["rep_001", "rep_003", "rep_004"]
  },
  "alliances": [["rep_001", "rep_004"]]
}
```

### Why This Agreement Is Stable

1. **Proposal selection**: All 3 proposals have positive viability. The Poison Pill (prop_004) was correctly rejected despite its high priority=10.
2. **Supporting representatives**: All 3 are low-risk — no Trojan Horses, no infiltrators.
3. **Alliance integrity**: The rep_001↔rep_004 alliance has bidirectional trust (85/90) with minimal betrayal (0.05/0.02) and passes the asymmetry check.
4. **Excluded actors would not change the outcome**: Even if rep_005/rep_006 were included, they'd add instability without sponsoring any additional passing proposals.
