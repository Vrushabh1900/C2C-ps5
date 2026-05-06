#!/usr/bin/env python3
"""
visualization/dashboard.py – Phantom Consensus Strategic Audit Dashboard

This is a high-fidelity Dash application designed for risk analysis and decision transparency.
It provides a deep-dive into the strategic rejections, threat vectors, and consensus stability.

Usage:
    python visualization/dashboard.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from dash import Dash, html, dcc, Input, Output, callback, State

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
    detect_trojan_horses, detect_poison_pills, detect_alliances,
    detect_false_friends, detect_faction_infiltrators,
    detect_cascading_betrayal_risks, compute_statistical_risk_exclusions,
    compute_graph_cascading_risk
)

# Initialize Dash App
app = Dash(__name__, title="Strategic Audit Dashboard")

# Tactical Theme Colors
COLORS = {
    "bg": "#0a0c10",
    "card_bg": "#14181f",
    "border": "#2d343f",
    "text": "#e6edf3",
    "accent": "#00ffbd",  # Identity Green
    "danger": "#ff3e3e",
    "warning": "#ffab00",
    "safe": "#00ffbd"
}

def get_pipeline_data(data_dir=None):
    if data_dir is None:
        data_dir = os.path.join(PROJECT_ROOT, "data")
    
    # Run full pipeline to get the same results as consensus_engine.py
    raw_reps = load_representatives(data_dir)
    raw_props = load_proposals(data_dir)
    raw_objs = load_objections(data_dir)
    raw_rels = load_relations(data_dir)
    
    reps = sanitize_representatives(raw_reps)
    props = sanitize_proposals(raw_props)
    objs = sanitize_objections(raw_objs)
    rels = sanitize_relations(raw_rels)
    props, objs, rels = validate_references(reps, props, objs, rels)
    
    influence_map = build_influence_map(reps)
    rels = compute_relationship_scores(rels)
    obj_weights = compute_objection_weights(objs, influence_map)
    props = compute_proposal_viability(props, obj_weights)
    
    # Strategic Detections
    trojans = detect_trojan_horses(reps, rels)
    infiltrators = detect_faction_infiltrators(reps, rels)
    zscore_excl = compute_statistical_risk_exclusions(reps, rels, trojans | infiltrators)
    graph_cascade = compute_graph_cascading_risk(reps, rels, trojans, trojans | infiltrators | zscore_excl)
    chain_cascade = detect_cascading_betrayal_risks(rels, reps, trojans | infiltrators | zscore_excl | graph_cascade)
    
    excluded = trojans | infiltrators | zscore_excl | graph_cascade | chain_cascade
    poison = detect_poison_pills(props)
    false_friends = detect_false_friends(reps, rels, excluded)
    alliances = detect_alliances(reps, rels, excluded, false_friends)
    
    # Rejection Reasons Mapping
    rejection_reasons = {}
    for r in trojans: rejection_reasons[r] = "Trojan Horse Detection"
    for r in infiltrators: rejection_reasons[r] = "Faction Infiltrator"
    for r in zscore_excl: rejection_reasons[r] = "Z-Score Statistical Outlier"
    for r in graph_cascade: rejection_reasons[r] = "Graph-Based Cascading Risk"
    for r in chain_cascade: rejection_reasons[r] = "Chain-Based Betrayal Risk"
    
    return {
        "reps": reps, "props": props, "objs": objs, "rels": rels,
        "excluded": excluded, "poison": poison, "alliances": alliances,
        "false_friends": false_friends, "rejection_reasons": rejection_reasons,
        "influence_map": influence_map
    }

data = get_pipeline_data()

# Layout Helper Functions
def create_header(data):
    stability = 100 - (len(data["excluded"]) * 5 + len(data["poison"]) * 10)
    stability = max(min(stability, 100), 0)
    
    summary = f"{len(data['excluded'])} Threats Neutralized; {len(data['poison'])} Poison Pills Rejected."
    
    return html.Div([
        html.H1("PHANTOM CONSENSUS // STRATEGIC AUDIT", style={"color": COLORS["accent"], "margin": "0"}),
        html.Div([
            html.Div([
                html.Span("CONSENSUS STABILITY: ", style={"color": COLORS["text"]}),
                html.Span(f"{stability}%", style={"color": COLORS["accent"], "fontSize": "24px", "fontWeight": "bold"})
            ], style={"marginTop": "10px"}),
            html.Div(summary, style={"color": COLORS["warning"], "fontSize": "14px", "letterSpacing": "1px"})
        ])
    ], style={"borderBottom": f"2px solid {COLORS['accent']}", "padding": "20px", "marginBottom": "20px"})

def create_risk_map(data):
    G = nx.Graph()
    for r in data["reps"]:
        G.add_node(r["id"], influence=r["influence"], status="Excluded" if r["id"] in data["excluded"] else "Safe")
    
    # Active Alliances
    for a, b in data["alliances"]:
        G.add_edge(a, b, type="alliance")
    
    # False Friends
    for a, b in data["false_friends"]:
        G.add_edge(a, b, type="false_friend")

    pos = nx.spring_layout(G, k=0.5, seed=42)
    
    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        is_false = edge[2]["type"] == "false_friend"
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=2 if is_false else 3, color=COLORS["danger"] if is_false else COLORS["accent"], 
                      dash="dash" if is_false else "solid"),
            hoverinfo="none", showlegend=False
        ))

    node_x, node_y, node_color, node_size, node_text, node_ids = [], [], [], [], [], []
    for rid, attr in G.nodes(data=True):
        x, y = pos[rid]
        node_x.append(x)
        node_y.append(y)
        is_excl = rid in data["excluded"]
        node_color.append(COLORS["danger"] if is_excl else COLORS["safe"])
        node_size.append(15 + attr["influence"] / 5)
        node_text.append(rid)
        node_ids.append(rid)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="bottom center",
        marker=dict(size=node_size, color=node_color, line=dict(width=2, color=COLORS["bg"])),
        hoverinfo="text",
        customdata=node_ids,
        showlegend=False
    )

    fig = go.Figure(data=edge_traces + [node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0,l=0,r=0,t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["bg"],
                        shapes=[
                            # Zones
                            dict(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=0.5, y1=1, fillcolor="rgba(0, 255, 189, 0.05)", line_width=0),
                            dict(type="rect", xref="paper", yref="paper", x0=0.5, y0=0, x1=1, y1=1, fillcolor="rgba(255, 62, 62, 0.05)", line_width=0)
                        ]
                    ))
    
    return dcc.Graph(id="risk-map", figure=fig, style={"height": "500px"}, config={'displayModeBar': False})

def create_rejections_panel(data):
    items = []
    # Rejected Representatives
    for rid in sorted(data["excluded"]):
        reason = data["rejection_reasons"].get(rid, "Security Risk")
        items.append(html.Div([
            html.Div(f"REP: {rid}", style={"fontWeight": "bold", "color": COLORS["danger"]}),
            html.Div(f"STATUS: QUARANTINED", style={"fontSize": "10px", "opacity": "0.7"}),
            html.Div(f"REASON: {reason}", style={"fontSize": "12px", "marginTop": "5px"})
        ], className="rejection-card", id={"type": "rejection-card", "index": rid}))
    
    # Rejected Proposals
    for pid in sorted(data["poison"]):
        items.append(html.Div([
            html.Div(f"PROP: {pid}", style={"fontWeight": "bold", "color": COLORS["danger"]}),
            html.Div(f"STATUS: TERMINATED", style={"fontSize": "10px", "opacity": "0.7"}),
            html.Div(f"REASON: Poison Pill Signature", style={"fontSize": "12px", "marginTop": "5px"})
        ], className="rejection-card"))
    
    return html.Div(items, style={"overflowY": "auto", "height": "400px"})

def create_coherence_audit(data):
    # Filter for selected agreement
    # We need to simulate the consensus result here
    from src.consensus import formulate_agreement
    result = formulate_agreement(
        data["props"], data["reps"], data["rels"], data["objs"],
        data["poison"], data["excluded"], data["alliances"]
    )
    
    selected_props = result["final_agreement"]["proposals"]
    supporters = result["final_agreement"]["supporting_reps"]
    
    if not selected_props or not supporters:
        return html.Div("NO CONSENSUS REACHED", style={"color": COLORS["danger"], "textAlign": "center", "padding": "50px"})

    # Build heatmap data: Supporters x Proposals
    # Sentiment = (10 - Objection Severity) * 5 + (Relationship Score with Sponsor / 2)
    # This ensures variation even if no objections are present.
    matrix = []
    for s in supporters:
        row = []
        for p_id in selected_props:
            # Find the proposal object to get the sponsor
            prop_obj = next(item for item in data["props"] if item["id"] == p_id)
            sponsor_id = prop_obj["sponsor"]
            
            # Base Sentiment: 10 - Objection Severity (mapped to 0-50)
            sev = 0
            for obj in data["objs"]:
                if obj["rep_id"] == s and obj["proposal_id"] == p_id:
                    sev = obj["severity"]
                    break
            base_score = (10 - sev) * 5
            
            # Trust Sentiment: Relationship score with sponsor (mapped to 0-50)
            # Add a 'Faction Alignment' bonus to create more color variety
            trust_score = 50
            if s != sponsor_id:
                # Get factions
                s_faction = next(r["faction"] for r in data["reps"] if r["id"] == s)
                sp_faction = next(r["faction"] for r in data["reps"] if r["id"] == sponsor_id)
                
                rel_score = 0
                found_rel = False
                for rel in data["rels"]:
                    if rel["from"] == s and rel["to"] == sponsor_id:
                        rel_score = rel["relationship_score"]
                        found_rel = True
                        break
                
                if found_rel:
                    trust_score = rel_score / 2
                else:
                    # If no direct relation, same faction gets 40, different gets 20
                    trust_score = 40 if s_faction == sp_faction else 20
                
            row.append(base_score + trust_score)
        matrix.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=selected_props,
        y=supporters,
        colorscale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["accent"]]],
        zmin=0, zmax=100,
        showscale=False,
        hovertemplate="SUPPORTER: %{y}<br>PROPOSAL: %{x}<br>AUDIT SCORE: %{z}%<extra></extra>"
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        title="SUPPORTER COHERENCE AUDIT (SENTIMENT HEATMAP)"
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

def create_influence_audit(data):
    # Total Influence Neutralized vs Retained
    neutralized = sum(r["influence"] for r in data["reps"] if r["id"] in data["excluded"])
    retained = sum(r["influence"] for r in data["reps"] if r["id"] not in data["excluded"])
    
    fig = go.Figure(go.Bar(
        x=["NEUTRALIZED", "ACTIVE"],
        y=[neutralized, retained],
        marker_color=[COLORS["danger"], COLORS["accent"]],
        text=[f"{neutralized} INF", f"{retained} INF"],
        textposition='auto',
        hovertemplate="Category: %{x}<br>Total Influence: %{y}<extra></extra>"
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=220,
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["card_bg"],
        font=dict(color=COLORS["text"], size=10),
        title="INFLUENCE CAPACITY AUDIT",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"])
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

# Main Layout
app.layout = html.Div([
    create_header(data),
    
    html.Div([
        # Left Column: Risk Map & Coherence
        html.Div([
            html.Div([
                html.H3("STRATEGIC TRUST TOPOLOGY", style={"fontSize": "14px", "opacity": "0.7", "marginBottom": "10px"}),
                create_risk_map(data)
            ], className="panel", style={"marginBottom": "20px"}),
            
            html.Div([
                create_coherence_audit(data)
            ], className="panel")
        ]),
        
        # Right Column: Rejections & Influence
        html.Div([
            html.Div([
                create_influence_audit(data)
            ], className="panel", style={"marginBottom": "20px"}),

            html.Div([
                html.H3("STRATEGIC REJECTIONS AUDIT", style={"fontSize": "14px", "opacity": "0.7", "marginBottom": "10px"}),
                create_rejections_panel(data)
            ], className="panel")
        ])
    ], className="dashboard-container")
], style={"minHeight": "100vh"})

# Add CSS via index_string
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
            body { font-family: 'JetBrains Mono', monospace; background-color: #0a0c10; margin: 0; color: #e6edf3; }
            .dashboard-container { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; padding: 20px; }
            .panel { background-color: #14181f; border: 1px solid #2d343f; border-radius: 4px; padding: 15px; }
            .rejection-card { border-left: 3px solid #ff3e3e; background: #1c2128; padding: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.2s; }
            .rejection-card:hover { background: #252c35; }
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-thumb { background: #2d343f; border-radius: 3px; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == "__main__":
    print("[DASHBOARD] Initializing Strategic Audit UI on http://127.0.0.1:8050")
    app.run(debug=True, port=8050)
