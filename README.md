# Phantom Consensus

## Team Information
- **Team Name**: orangeoxyzen  
- **Year**: 2nd  
- **All-Female Team**: No  

---

## Architecture Overview

## Consensus Stability Strategy

Our engine employs a **multi-layered defense** to ensure robust and stable consensus formation.

---

### 1. Integrity & Data Sanitization
We resolve common data issues through a pre-processing layer:

- **ID Normalization**: Enforces lowercase consistency  
- **Null Influence Handling**: Defaults missing values to `0`  
- **Dirty CSV Handling**: Clamps out-of-range values to `(0–100)`  
- **Duplicate Removal**: Eliminates redundant proposals  
- **Ghost Sponsors**: Pruned using referential integrity checks  

---

### 2. Strategic Logic (Trap Detection)
To neutralize malicious or unstable entities:

- **Trojan Horses & Faction Infiltrators**:  
  Detected using an **adaptive Z-score model** that identifies betrayal outliers relative to the dataset’s "political climate"

- **False Friends Detection**:  
  Uses **bidirectional trust audits**  
  Rejects relationships where:

  betrayal > trust 

  
---

### 3. Conflict Resolution Mechanism
We mitigate disruptive proposals and conflicts using weighted logic:

- **Poison Pills & Faction Wars**:  
Evaluated using:

objection_weight = severity × influence


- Ensures that **high-influence objections** outweigh raw proposal priority  

- **Alliance Hijack Prevention**:  
Uses **graph-based risk analysis** to isolate stable alliance cores from disruptive nodes  

---

### 4. Consensus Coherence (Final Safeguard)
The **Supporter Coherence Check** ensures internal consistency:

- Prevents any representative with **high-severity objections** from being included in the `supporting_reps` list  
- Eliminates risk of **Cascading Betrayal**  
- Guarantees a **logically aligned and stable agreement**

---

### 5. Scalability
- Designed to scale efficiently for **50+ representatives**  
- Maintains a **Minimum Viable Consensus** even in high-rivalry environments  

---

### 6. Strategic Audit Dashboard (Frontend)
The system includes a high-fidelity **Strategic Audit Dashboard** built with Dash and Plotly. It provides:

- **Tactical Dark-Mode UI**: A military-intelligence aesthetic using JetBrains Mono for readability and authority.
- **Decision Transparency**: Clear visual proof of why specific representatives or proposals were rejected (e.g., Trojan Horse vs. Z-Score outliers).
- **Supporter Coherence Heatmap**: A sentiment-driven audit proving that every supporter genuinely backs the final agreement.
- **Risk Mapping**: A graph-based topology that isolates "Danger Zones" from stable alliance cores.