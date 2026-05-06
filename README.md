# Phantom Consensus

## Team Information
- **Team Name**: orangeoxyzen  
- **Year**: 2nd  
- **All-Female Team**: No  

---

## Architecture Overview

### Data Cleaning Approach
The engine uses a normalization layer to standardize IDs to lowercase and trim whitespace, ensuring referential integrity. Missing influence values default to `0`, while out-of-range data is clamped to maximum boundaries. Conflicting duplicates are removed, and "ghost references" to non-existent entities are pruned to prevent execution crashes.

---

### Alliance Detection Logic
Alliances are validated through bidirectional trust checks. The engine identifies **"False Friends"** by rejecting pairs with asymmetric trust or high betrayal probabilities.

We derive a `relationship_score` using:

relationship_score = trust × (1 - betrayal_prob)

This ensures alliances are built on genuine, mutual stability rather than raw trust values.

---

### Proposal Prioritization Strategy
Proposals are ranked by a `proposal_viability` score that balances raw priority against a weighted `objection_weight`.

The objection weight is calculated as:

objection_weight = Σ(severity × objector_influence)


This ensures that objections from powerful representatives significantly reduce a proposal's priority compared to those from low-influence actors.

---

### Consensus Stability Strategy
Our engine uses an adaptive Z-score model to identify betrayal outliers based on the dataset’s "political climate".

- **Poison Pills**: Mitigated by rejecting high-priority bills with extreme objection weights.  
- **Trojan Horses**: Excluded via graph-based risk analysis and Supporter Coherence checks.  

Supporter Coherence ensures that no supporter holds high-severity objections to the final agreement, maintaining stability in the consensus.
