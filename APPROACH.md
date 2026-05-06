# Approach: Phantom Consensus Engine (Tier S)

## Architecture Overview

Phantom Consensus is a modular, four-layer Strategic Consensus Engine that processes multi-format political datasets to determine which proposals should pass, who supports them, and which alliances are genuine.

The Tier S upgrade adds five advanced strategic layers that transform the engine from a competent system into an exceptional one, handling adversarial scenarios, scaling challenges, and game-theoretic traps.

### Pipeline Architecture

```
DATA LOADING -> SANITIZATION -> FEATURE ENGINEERING -> STRATEGIC LOGIC (Tier S) -> CONSENSUS -> OUTPUT
                                                            |
                                          +-----------------+-----------------+
                                          |                 |                 |
                                    Phase 1-2          Phase 3-4          Phase 5
                                  Core + Z-score     Graph + Chain     False Friends
                                   Detection          Cascade          + Coherence
```

---

## Layer 1 -- Data Sanitization

### Mixed-format Ingestion
- **JSON** (`representatives.json`, `proposals.json`, `objections.json`): Parsed with `json.load()` and validated as arrays.
- **CSV** (`relations.csv`): Parsed with `csv.DictReader` with whitespace-aware key/value stripping.

### ID Normalization (Issue #6)
All IDs are lowercased and stripped of whitespace. This catches traps like `REP_001` vs `rep_001` and `" rep_004"` vs `rep_004`.

### Type Coercion & Clamping (Issue #7)
- **Influence**: Cast to float, clamped to [0, 100]. `null` -> 0, `"70"` -> 70.0, `150` -> 100.
- **Severity**: Supports both numeric and named values (`"high"` -> 8). Negative values clamped to 0.
- **Betrayal probability**: Clamped to [0, 1]. `1.5` -> 1.0, missing -> 0.5 default.
- **Trust/Rivalry**: Clamped to [0, 100]. Non-numeric values (`"high"`) -> 0.

### Deduplication (Issue #8)
First-occurrence-wins strategy for both proposals and representatives sharing the same normalized ID.

### Ghost Reference Removal (Issue #9)
Orphaned proposals (sponsor doesn't exist), objections (rep or proposal missing), and relations (endpoints missing) are all dropped with logged warnings.

### Cleaned Data Persistence
After sanitization, all four datasets are written to `data/cleaned/` with only canonical fields retained (junk columns stripped). This makes the cleaning auditable.

---

## Layer 2 -- Feature Engineering

### Relationship Score (Issue #10)
```
relationship_score = trust * (1 - betrayal_prob)
```
Collapses trust and risk into a single reliability metric (0-100 scale). A rep with trust=90 but betrayal=0.75 scores only 22.5.

### Objection Weight (Issue #11)
```
objection_weight(proposal) = SUM(severity * objector_influence)
```
Weights each objection by the political power of the objector.

### Proposal Viability
```
controversy = objection_weight / max_objection_weight  (normalized 0-1)
proposal_viability = priority * (1 - controversy)
```

---

## Layer 4 -- Strategic Logic (Tier S Anti-Trap Detection)

### Phase 1: Core Threat Detection

#### Trojan Horse Detection (Issue #12)
Screens representatives with influence >= 60 **AND** average outgoing betrayal probability >= 0.50. These look attractive but would destabilize the consensus.

#### Poison Pill Detection (Issue #13)
Rejects proposals where viability <= 0 (objection weight completely overwhelms priority). Even if a bill has priority=10, devastating opposition makes it toxic.

### Phase 2: Adaptive Risk -- Statistical Climate Model (Tier S)

**Section: Adaptive Risk**

Static betrayal thresholds (e.g., "exclude if betrayal > 0.5") fail at scale. When a dataset has 50+ representatives, the betrayal distribution may shift -- what's "normal" in one political climate is extreme in another.

The **Z-score Statistical Climate Model** replaces static thresholds:

```
mean_betrayal = mean(all betrayal probabilities in dataset)
std_betrayal  = std(all betrayal probabilities in dataset)
threshold     = mean_betrayal + 2.0 * std_betrayal
```

Any representative whose **average outgoing betrayal** exceeds this threshold is automatically excluded. This ensures:
- **Scale invariance**: The threshold adapts to the dataset, not hardcoded.
- **Statistical rigor**: Only true outliers (> 2 sigma above mean) are flagged.
- **Robustness**: Works for datasets of 6 reps or 600 reps without tuning.

### Phase 3: Graph-Based Cascading Risk (Tier S)

**Section: Graph Cascading Risk**

Relationships are modeled as a **directed graph**. A "safe" representative may be compromised through adjacency -- if they have a **high-trust bond (trust > 80)** leading directly to a known **Trojan Horse**, their risk score is boosted:

```
boosted_risk = base_avg_betrayal + 0.30 (cascade boost)
```

If the boosted risk exceeds the Trojan Horse betrayal threshold (0.50), that representative is excluded. This catches **secondary betrayal** -- the risk of being manipulated by a trusted-but-dangerous neighbor.

### Phase 4: Chain-Based Cascading Betrayal

Detects chains A -> B -> C where each individual hop's betrayal looks safe but the cumulative risk is dangerous:

```
cumulative_risk = 1 - (1 - betrayal_AB) * (1 - betrayal_BC)
```

Only flags chains where individual hops are below the Trojan Horse threshold (hidden cascading risk).

### Phase 5: Alliance Modeling -- False Friend Detection (Tier S)

**Section: Alliance Modeling**

A "False Friend" is a dangerous asymmetric relationship where:
- Rep A trusts Rep B **> 70%** (high trust)
- But Rep B trusts Rep A **< 40%** (low reciprocity)

Even if the **average** trust is acceptable, the directional imbalance creates an exploitable vulnerability. The engine performs an explicit **bidirectional trust parity check**:

```
if trust(A->B) > 70 AND trust(B->A) < 40:
    FLAG as False Friend
    REJECT alliance between A and B
```

This is stricter than the generic relationship_score check because it operates on **raw trust values** (before betrayal discounting), catching cases where a moderate betrayal probability might mask the trust asymmetry.

Genuine alliances require:
1. Both directional relationship_scores > 50
2. No False Friend flag in either direction
3. Neither party excluded by any prior detection

---

## Consensus Formulation (Issue #17)

### Phase 6: Stability Algorithms -- Supporter Coherence (Tier S)

**Section: Stability Algorithms**

A critical game-theoretic insight: a representative **cannot credibly support** an agreement containing proposals they strongly oppose. The **Supporter Coherence Validation** enforces this:

```
For each candidate supporter:
  For each selected proposal in the agreement:
    If the supporter has an objection with severity > 5:
      REMOVE from supporting_reps
```

This prevents **internal collapse** of the agreement. Without this check, the consensus could include a rep who sponsors one proposal but objects violently to another -- creating an unstable coalition that would fracture under pressure.

### Full Decision Loop

1. Remove Poison Pill proposals
2. Rank remaining proposals by viability (descending)
3. Select proposals with valid, non-excluded sponsors
4. Build supporter set: sponsors + their alliance partners (minus excluded reps)
5. **Tier S Coherence**: Remove any supporter who objects (severity > 5) to any selected proposal
6. Output final stable agreement

---

## Section: Faction Integrity -- Infiltrator Detection (Tier S)

**Purpose**: Ensure long-term faction stability by detecting internal saboteurs.

A representative is classified as a **Faction Infiltrator** if they have a `betrayal_prob > 0.80` against any member of their **own faction**. This is a strict threshold -- it only catches blatant spies, not representatives with legitimate intra-faction disagreements.

```
if faction(src) == faction(dst) AND betrayal_prob(src -> dst) > 0.80:
    FLAG src as Infiltrator
    EXCLUDE from supporting_reps regardless of influence score
```

Key design decisions:
- **Influence is irrelevant**: A high-influence infiltrator is more dangerous, not less. Exclusion is absolute.
- **Directional check**: Only the betrayer is flagged, not the victim.
- **Faction labels are verified independently**: Shared labels don't guarantee safety.

---

## Edge Case Handling (Issue #19)

- All reps excluded -> empty agreement (no crash)
- All proposals poisoned -> empty agreement
- Single valid rep/proposal -> still produces valid output
- Complete rivalry graph -> empty alliances array
- No data at all -> correct empty JSON schema
- Coherence removes all supporters -> proposals still listed (orphaned agreement)

## Performance (Issue #20)

The pipeline completes in <10ms for the current dataset. All operations are O(n^2) or better:
- Feature engineering: O(n) per relation/objection
- Alliance detection: O(n^2) pairwise combinations
- Z-score computation: O(n) single pass
- Graph cascade: O(edges) single pass
- No exponential graph searches

Scales cleanly to 50+ reps and 30+ proposals without threshold tuning (Z-score adapts automatically).
