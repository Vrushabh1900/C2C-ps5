# Approach: Phantom Consensus Engine

## Architecture Overview

Phantom Consensus is a modular, four-layer Strategic Consensus Engine that processes multi-format political datasets to determine which proposals should pass, who supports them, and which alliances are genuine.

### Pipeline Architecture

```
DATA LOADING -> SANITIZATION -> FEATURE ENGINEERING -> STRATEGIC LOGIC -> CONSENSUS -> OUTPUT
```

## Layer 1 – Data Sanitization

### Mixed-format Ingestion
- **JSON** (`representatives.json`, `proposals.json`, `objections.json`): Parsed with `json.load()` and validated as arrays.
- **CSV** (`relations.csv`): Parsed with `csv.DictReader` with whitespace-aware key/value stripping.

### ID Normalization (Issue #6)
All IDs are lowercased and stripped of whitespace. This catches traps like `REP_001` vs `rep_001` and `" rep_004"` vs `rep_004`.

### Type Coercion & Clamping (Issue #7)
- **Influence**: Cast to float, clamped to [0, 100]. `null` → 0, `"70"` → 70.0, `150` → 100.
- **Severity**: Supports both numeric and named values (`"high"` → 8). Negative values clamped to 0.
- **Betrayal probability**: Clamped to [0, 1]. `1.5` → 1.0, missing → 0.5 default.
- **Trust/Rivalry**: Clamped to [0, 100]. Non-numeric values (`"high"`) → 0.

### Deduplication (Issue #8)
First-occurrence-wins strategy for both proposals and representatives sharing the same normalized ID.

### Ghost Reference Removal (Issue #9)
Orphaned proposals (sponsor doesn't exist), objections (rep or proposal missing), and relations (endpoints missing) are all dropped with logged warnings.

## Layer 2 – Feature Engineering

### Relationship Score (Issue #10)
```
relationship_score = trust × (1 - betrayal_prob)
```
Collapses trust and risk into a single reliability metric (0-100 scale). A rep with trust=90 but betrayal=0.75 scores only 22.5.

### Objection Weight (Issue #11)
```
objection_weight(proposal) = Σ(severity × objector_influence)
```
Weights each objection by the political power of the objector.

### Proposal Viability
```
controversy = objection_weight / max_objection_weight  (normalized 0-1)
proposal_viability = priority × (1 - controversy)
```

## Layer 4 – Strategic Logic (Anti-Trap Detection)

### Trojan Horse Detection (Issue #12)
Screens representatives with influence ≥ 60 **AND** average outgoing betrayal probability ≥ 0.50. These look attractive but would destabilize the consensus.

### Poison Pill Detection (Issue #13)
Rejects proposals where viability ≤ 0 (objection weight completely overwhelms priority). Even if a bill has priority=10, devastating opposition makes it toxic.

### Alliance Detection with False Friend Filtering (Issues #14, #15)
- **Genuine alliances** require mutual relationship_score ≥ 50 in BOTH directions.
- **Asymmetric trust** is caught by requiring min(scoreAB, scoreBA) / max(scoreAB, scoreBA) ≥ 0.5.

### Faction Infiltrator Detection (Issue #16)
Cross-references faction membership with intra-faction betrayal probabilities. A rep claiming "Progressives" but having betrayal ≥ 0.40 toward fellow Progressives is flagged as a spy.

### Cascading Betrayal Detection
Detects chains A→B→C where each individual hop's betrayal looks safe (below Trojan threshold) but the cumulative risk `1 - Π(1 - betrayal_i) ≥ 0.60` is dangerous. Only flags reps not already caught by other detections.

## Consensus Formulation (Issue #17)

1. Remove Poison Pill proposals
2. Rank remaining proposals by viability (descending)
3. Select proposals with valid, non-excluded sponsors
4. Supporting reps = sponsors ∪ their alliance partners (minus excluded)

## Edge Case Handling (Issue #19)

- All reps excluded → empty agreement
- All proposals poisoned → empty agreement  
- Single valid rep/proposal → still produces valid output
- Complete rivalry graph → empty alliances array
- No crashes, no infinite loops

## Performance (Issue #20)

The pipeline completes in <5ms for the current dataset. All operations are O(n²) or better — no exponential graph searches. Scales cleanly to 50+ reps and 30+ proposals.
