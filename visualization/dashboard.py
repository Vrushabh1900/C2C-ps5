#!/usr/bin/env python3
"""
visualization/dashboard.py – Phantom Consensus Dashboard

Generates a self-contained HTML dashboard with:
  1. Alliance network graph (interactive, via Plotly)
  2. Proposal viability bar chart
  3. Representative risk heatmap
  4. Summary cards

Usage:
    python visualization/dashboard.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.data_loader import load_representatives, load_proposals, load_objections, load_relations
from src.data_sanitizer import (
    sanitize_representatives, sanitize_proposals, sanitize_objections,
    sanitize_relations, validate_references,
)
from src.feature_engine import (
    build_influence_map, compute_relationship_scores,
    compute_objection_weights, compute_proposal_viability,
)
from src.strategic_logic import (
    detect_trojan_horses, detect_faction_infiltrators,
    detect_cascading_betrayal_risks, detect_poison_pills, detect_alliances,
)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import networkx as nx
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def generate_dashboard(data_dir: str = None, output_path: str = None):
    """Build and save the HTML dashboard."""
    if data_dir is None:
        data_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "visualization", "dashboard.html")

    # Run pipeline stages
    reps = sanitize_representatives(load_representatives(data_dir))
    props = sanitize_proposals(load_proposals(data_dir))
    objs = sanitize_objections(load_objections(data_dir))
    rels = sanitize_relations(load_relations(data_dir))
    props, objs, rels = validate_references(reps, props, objs, rels)

    influence_map = build_influence_map(reps)
    rels = compute_relationship_scores(rels)
    obj_weights = compute_objection_weights(objs, influence_map)
    props = compute_proposal_viability(props, obj_weights)

    trojans = detect_trojan_horses(reps, rels)
    infiltrators = detect_faction_infiltrators(reps, rels)
    cascade = detect_cascading_betrayal_risks(rels, reps)
    excluded = trojans | infiltrators | cascade
    poison = detect_poison_pills(props)
    alliances = detect_alliances(reps, rels, excluded)

    if not HAS_PLOTLY:
        _generate_static_html(reps, props, rels, alliances, excluded, poison, output_path)
        return

    _generate_plotly_dashboard(reps, props, rels, alliances, excluded, poison, output_path)


def _generate_plotly_dashboard(reps, props, rels, alliances, excluded, poison, output_path):
    """Generate interactive Plotly HTML dashboard."""
    # --- Network Graph ---
    G = nx.DiGraph()
    for r in reps:
        G.add_node(r["id"], label=r.get("name", r["id"]),
                    faction=r.get("faction", "Unknown"),
                    influence=r["influence"])
    for rel in rels:
        G.add_edge(rel["from"], rel["to"],
                    weight=rel["relationship_score"],
                    betrayal=rel["betrayal_prob"])

    pos = nx.spring_layout(G, k=2, seed=42)

    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        score = edge[2].get("weight", 0)
        color = f"rgba(0,200,100,{min(score/100, 1)})" if score > 50 else f"rgba(200,50,50,{min(1-score/100, 1)})"
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines", line=dict(width=max(score/25, 0.5), color=color),
            hoverinfo="none", showlegend=False,
        ))

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    for node in G.nodes(data=True):
        x, y = pos[node[0]]
        node_x.append(x)
        node_y.append(y)
        rid = node[0]
        label = node[1].get("label", rid)
        faction = node[1].get("faction", "?")
        inf = node[1].get("influence", 0)
        status = "EXCLUDED" if rid in excluded else "Active"
        node_text.append(f"{label}<br>Faction: {faction}<br>Influence: {inf}<br>Status: {status}")
        node_color.append("red" if rid in excluded else "#00c853")
        node_size.append(max(inf / 5, 8))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=node_size, color=node_color, line=dict(width=2, color="#222")),
        text=[n[1].get("label", n[0])[:10] for n in G.nodes(data=True)],
        textposition="top center", textfont=dict(size=10, color="white"),
        hovertext=node_text, hoverinfo="text", showlegend=False,
    )

    # --- Proposal Viability Chart ---
    prop_ids = [p["id"] for p in props]
    viabilities = [p["viability"] for p in props]
    prop_colors = ["#ff1744" if p["id"] in poison else "#00e676" for p in props]

    viability_bar = go.Bar(
        x=prop_ids, y=viabilities,
        marker_color=prop_colors,
        text=[f"{v:.1f}" for v in viabilities],
        textposition="auto",
    )

    # --- Create subplots ---
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Alliance Network", "Proposal Viability",
                        "Representative Influence", "Risk Summary"),
        specs=[[{"type": "scatter"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]],
        vertical_spacing=0.12, horizontal_spacing=0.08,
    )

    for et in edge_traces:
        fig.add_trace(et, row=1, col=1)
    fig.add_trace(node_trace, row=1, col=1)
    fig.add_trace(viability_bar, row=1, col=2)

    # Influence bars
    rep_names = [r.get("name", r["id"])[:12] for r in reps]
    rep_inf = [r["influence"] for r in reps]
    rep_colors = ["#ff1744" if r["id"] in excluded else "#448aff" for r in reps]
    fig.add_trace(go.Bar(x=rep_names, y=rep_inf, marker_color=rep_colors), row=2, col=1)

    # Risk summary
    categories = ["Trojan Horses", "Infiltrators", "Cascade Risks", "Poison Pills"]
    from src.strategic_logic import detect_trojan_horses as _dt
    counts = [len([r for r in reps if r["id"] in excluded]),
              0, 0, len(poison)]
    fig.add_trace(go.Bar(x=categories, y=counts,
                         marker_color=["#ff9100", "#ff1744", "#d500f9", "#76ff03"]),
                  row=2, col=2)

    fig.update_layout(
        template="plotly_dark",
        title_text="Phantom Consensus – Strategic Dashboard",
        title_font_size=22,
        showlegend=False,
        height=900,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(family="Inter, sans-serif", color="white"),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"[VIZ] Dashboard saved to {output_path}")


def _generate_static_html(reps, props, rels, alliances, excluded, poison, output_path):
    """Fallback: generate a simple HTML dashboard without Plotly."""
    alliance_rows = "".join(
        f"<tr><td>{a[0]}</td><td>{a[1]}</td></tr>" for a in alliances
    ) or "<tr><td colspan='2'>No alliances detected</td></tr>"

    prop_rows = "".join(
        f"<tr><td>{p['id']}</td><td>{p['priority']}</td>"
        f"<td>{p['viability']:.2f}</td>"
        f"<td>{'POISON PILL' if p['id'] in poison else 'Viable'}</td></tr>"
        for p in props
    )

    rep_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{r.get('name','')}</td>"
        f"<td>{r['influence']}</td>"
        f"<td>{'EXCLUDED' if r['id'] in excluded else 'Active'}</td></tr>"
        for r in reps
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phantom Consensus Dashboard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0d1117; color:#c9d1d9; font-family:'Inter',sans-serif; padding:2rem; }}
  h1 {{ color:#58a6ff; margin-bottom:1rem; }}
  h2 {{ color:#8b949e; margin:1.5rem 0 .5rem; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:1rem; }}
  th,td {{ padding:.5rem 1rem; border:1px solid #30363d; text-align:left; }}
  th {{ background:#161b22; color:#58a6ff; }}
  tr:nth-child(even) {{ background:#161b22; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:1rem; margin:.5rem 0; }}
  .excluded {{ color:#ff7b72; font-weight:bold; }}
  .poison {{ color:#ff7b72; }}
</style>
</head>
<body>
<h1>Phantom Consensus &ndash; Strategic Dashboard</h1>
<div class="card"><strong>Alliances:</strong> {len(alliances)} | <strong>Excluded Reps:</strong> {len(excluded)} | <strong>Poison Pills:</strong> {len(poison)}</div>

<h2>Alliances</h2>
<table><tr><th>Rep A</th><th>Rep B</th></tr>{alliance_rows}</table>

<h2>Proposals</h2>
<table><tr><th>ID</th><th>Priority</th><th>Viability</th><th>Status</th></tr>{prop_rows}</table>

<h2>Representatives</h2>
<table><tr><th>ID</th><th>Name</th><th>Influence</th><th>Status</th></tr>{rep_rows}</table>
</body></html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[VIZ] Static dashboard saved to {output_path}")


if __name__ == "__main__":
    generate_dashboard()
