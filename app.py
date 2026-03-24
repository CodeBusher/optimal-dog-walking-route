from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

from src.bellman_ford import bellman_ford, reconstruct_path
from src.graph import Graph
from src.models import Edge, Node

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_DATA_PATH = Path("data/sample_data.json")

def _discover_sample_files() -> dict[str, Path]:
    """Scan data/ and data/sample_data/ for JSON files.

    Returns an ordered dict mapping display name -> Path,
    with sample_data.json first.
    """
    files: dict[str, Path] = {}
    default = SAMPLE_DATA_PATH
    if default.exists():
        files[default.stem] = default
    for p in sorted(Path("data/sample_data").glob("*.json")):
        files[p.stem] = p
    return files

PATH_COLOR = "#F1C40F"

DEFAULT_NODE_COLOR = "#8E44AD"
DEFAULT_NODE_LABEL_PREFIX = "📍"

NODE_TYPE_COLORS: dict[str, str] = {
    "home": "#4A90D9",
    "park": "#27AE60",
    "intersection": "#95A5A6",
    "rest_stop": "#F39C12",
    "trigger_zone": "#E74C3C",
    "trail": "#2ECC71",
}

NODE_TYPE_LABELS: dict[str, str] = {
    "home": "🏠 Home",
    "park": "🌳 Park",
    "intersection": "🔀 Intersection",
    "rest_stop": "☕ Rest Stop",
    "trigger_zone": "⚠️ Trigger Zone",
    "trail": "🥾 Trail",
}


def _node_color(node_type: str) -> str:
    return NODE_TYPE_COLORS.get(node_type, DEFAULT_NODE_COLOR)


def _node_label(node_type: str) -> str:
    return NODE_TYPE_LABELS.get(
        node_type,
        f"{DEFAULT_NODE_LABEL_PREFIX} {node_type.replace('_', ' ').title()}",
    )

# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------


def load_graph_from_dict(data: dict) -> Graph:
    """Build a Graph from parsed JSON data."""
    graph = Graph()
    for n in data["nodes"]:
        graph.add_node(Node(**n))
    for e in data["edges"]:
        graph.add_edge(Edge(**e))
    return graph


def _to_nx(graph: Graph) -> nx.DiGraph:
    """Convert internal Graph to a networkx DiGraph for layout."""
    G = nx.DiGraph()
    for nid in graph.nodes:
        G.add_node(nid)
    for edge in graph.edges:
        G.add_edge(edge.from_id, edge.to_id)
    return G


def _path_edge_set(path: list[int] | None) -> set[tuple[int, int]]:
    """Return (from, to) pairs along a path."""
    if not path or len(path) < 2:
        return set()
    return {(path[i], path[i + 1]) for i in range(len(path) - 1)}


def _node_positions(
    graph: Graph, G: nx.DiGraph,
) -> dict[int, tuple[float, float]]:
    """Use node x,y coordinates when every node has them, else spring layout."""
    if all(n.x is not None and n.y is not None for n in graph.nodes.values()):
        return {nid: (node.x, node.y) for nid, node in graph.nodes.items()}
    return nx.spring_layout(G, seed=42, k=2.5)


def _collect_path_edges(graph: Graph, path: list[int]) -> list[Edge]:
    """Return the ordered list of Edge objects along *path*."""
    edges: list[Edge] = []
    for i in range(len(path) - 1):
        edge = next(
            e for e in graph.edges
            if e.from_id == path[i] and e.to_id == path[i + 1]
        )
        edges.append(edge)
    return edges


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------


def create_graph_figure(
    graph: Graph,
    path: list[int] | None = None,
) -> plt.Figure:
    """Render the graph with the optimal path highlighted in gold."""
    G = _to_nx(graph)
    pos = _node_positions(graph, G)

    path_edges = _path_edge_set(path)
    path_nodes = set(path) if path else set()
    other_edges = [e for e in G.edges() if e not in path_edges]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    node_size = 600

    if other_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=other_edges, ax=ax,
            edge_color="#666666", width=1.5, arrows=True,
            arrowsize=20, arrowstyle="-|>",
            node_size=node_size, alpha=0.4,
        )

    if path_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=list(path_edges), ax=ax,
            edge_color=PATH_COLOR, width=3.5, arrows=True,
            arrowsize=25, arrowstyle="-|>",
            node_size=node_size,
        )

    # Nodes
    node_list = list(G.nodes())
    colors = [_node_color(graph.nodes[n].node_type) for n in node_list]
    border_colors = [
        PATH_COLOR if n in path_nodes else "#2C3E50"
        for n in node_list
    ]
    linewidths = [3.0 if n in path_nodes else 1.5 for n in node_list]

    nx.draw_networkx_nodes(
        G, pos, nodelist=node_list, ax=ax,
        node_color=colors, node_size=node_size,
        edgecolors=border_colors, linewidths=linewidths,
    )

    # Node labels
    y_vals = [v[1] for v in pos.values()]
    label_offset = (max(y_vals) - min(y_vals)) * 0.08 if len(y_vals) > 1 else 0.12
    label_pos = {k: (v[0], v[1] + label_offset) for k, v in pos.items()}
    labels = {nid: node.name for nid, node in graph.nodes.items()}
    nx.draw_networkx_labels(
        G, label_pos, labels=labels, ax=ax,
        font_size=9, font_weight="bold", font_color="white",
        bbox=dict(
            boxstyle="round,pad=0.3", facecolor="#333333",
            edgecolor="none", alpha=0.7,
        ),
    )

    # Edge weight labels
    edge_labels = {
        (e.from_id, e.to_id): f"{e.final_weight:+.1f}"
        for e in graph.edges
    }
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax,
        font_size=7, font_color="#CCCCCC",
        bbox=dict(
            boxstyle="round,pad=0.2", facecolor="#222222",
            edgecolor="none", alpha=0.8,
        ),
    )

    ax.set_axis_off()
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _render_step_breakdown(
    graph: Graph, edges_list: list[Edge],
) -> None:
    """Render the step-by-step expanders for a route."""
    for i, edge in enumerate(edges_list):
        from_node = graph.nodes[edge.from_id]
        to_node = graph.nodes[edge.to_id]
        with st.expander(
            f"Step {i + 1}: {from_node.name} → {to_node.name}  "
            f"(weight {edge.final_weight:+.1f})",
            expanded=True,
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Travel Time", f"{edge.time_cost:.1f} min")
            c2.metric("Edge Reward", f"{edge.edge_reward:+.1f}")
            c3.metric("Dest. Reward", f"{to_node.reward:+.1f}")
            st.caption(
                f"Weight = {edge.time_cost:.1f} − {edge.edge_reward:.1f} "
                f"− ({to_node.reward:+.1f}) = {edge.final_weight:+.1f}"
            )


# ---------------------------------------------------------------------------
# Page config & session state
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Optimal Dog Walking Route",
    page_icon="🐕",
    layout="wide",
)

if "graph" not in st.session_state:
    st.session_state.graph = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐕 Route Planner")
    st.markdown("---")

    # ---- data source ----
    st.subheader("Graph Data")
    data_source = st.radio(
        "Data source",
        ["Sample data", "Upload JSON"],
        label_visibility="collapsed",
    )

    if data_source == "Sample data":
        sample_files = _discover_sample_files()
        if not sample_files:
            st.error("No sample data files found in data/.")
        else:
            names = list(sample_files.keys())
            selected = st.selectbox(
                "Choose dataset",
                names,
                index=0,
            )
            chosen_path = sample_files[selected]
            g = Graph()
            g.load_from_json(str(chosen_path))
            st.session_state.graph = g
    else:
        uploaded = st.file_uploader("Upload a JSON file", type=["json"])
        if uploaded is not None:
            try:
                data = json.load(uploaded)
                st.session_state.graph = load_graph_from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                st.error(f"Invalid JSON: {exc}")
                st.session_state.graph = None
        else:
            st.session_state.graph = None

    if st.session_state.graph:
        g = st.session_state.graph
        st.success(f"Loaded {g.get_node_count()} nodes, {g.get_edge_count()} edges")

    st.markdown("---")

    # ---- route selection ----
    source_id: int | None = None
    dest_id: int | None = None

    if st.session_state.graph:
        g = st.session_state.graph
        st.subheader("Route Selection")

        node_ids = list(g.nodes.keys())
        fmt = {
            nid: f"{g.nodes[nid].name} ({g.nodes[nid].node_type})"
            for nid in node_ids
        }

        source_id = st.selectbox(
            "Start location", node_ids, format_func=lambda x: fmt[x],
        )
        dest_id = st.selectbox(
            "Destination", node_ids,
            format_func=lambda x: fmt[x],
            index=len(node_ids) - 1,
        )

    st.markdown("---")

    # ---- legend ----
    st.subheader("Legend")
    seen_types: set[str] = set()
    if st.session_state.graph:
        seen_types = {n.node_type for n in st.session_state.graph.nodes.values()}
    all_types = list(NODE_TYPE_LABELS.keys()) + sorted(seen_types - NODE_TYPE_LABELS.keys())
    for ntype in all_types:
        if ntype not in seen_types and st.session_state.graph:
            continue
        color = _node_color(ntype)
        label = _node_label(ntype)
        st.markdown(
            f'<span style="color:{color}; font-size:16px;">●</span> {label}',
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.caption("**Path Colors**")
    st.markdown(
        f'<span style="color:{PATH_COLOR}; font-weight:bold;">━━</span> Optimal path',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("🐕 Optimal Dog Walking Route")
st.caption(
    "Find the most rewarding path for your dog walk — balancing travel time "
    "with parks, trails, and rest stops while avoiding trigger zones."
)

if st.session_state.graph is None:
    st.info("👈 Load graph data from the sidebar to get started.")
    st.stop()

graph = st.session_state.graph

if source_id is None or dest_id is None:
    st.stop()

if source_id == dest_id:
    st.warning("Source and destination must differ. Choose different locations.")
    st.stop()

# ---- algorithm ----
result = bellman_ford(graph, source_id)

if result.has_negative_cycle:
    st.error("Negative cycle detected — shortest paths are undefined.")
    fig = create_graph_figure(graph)
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.stop()

path = reconstruct_path(result, source_id, dest_id)

# ---- graph visualisation ----
st.subheader("Route Map")
fig = create_graph_figure(graph, path or None)
st.pyplot(fig, width="stretch")
plt.close(fig)

st.markdown("---")

# ---- all-destinations overview ----
st.subheader("All Destinations from " + graph.nodes[source_id].name)
dest_rows = []
for nid, node in graph.nodes.items():
    if nid == source_id:
        continue
    d = result.dist.get(nid, math.inf)
    reachable = not math.isinf(d)
    dest_rows.append({
        "Destination": node.name,
        "Type": node.node_type,
        "Optimal Cost": f"{d:+.1f}" if reachable else "—",
        "Reachable": "✓" if reachable else "✗",
    })
dest_rows.sort(key=lambda r: float(r["Optimal Cost"]) if r["Reachable"] == "✓" else float("inf"))
st.dataframe(dest_rows, width="stretch", hide_index=True)

st.markdown("---")

# ---- route details ----
if not path:
    st.warning(
        f"No reachable path from **{graph.nodes[source_id].name}** "
        f"to **{graph.nodes[dest_id].name}**."
    )
else:
    st.subheader("Route Details")

    out_edges = _collect_path_edges(graph, path)
    out_cost = result.dist[dest_id]
    out_time = sum(e.time_cost for e in out_edges)
    out_rewards = out_time - out_cost

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cost", f"{out_cost:+.1f}")
    m2.metric("Walking Time", f"{out_time:.0f} min")
    m3.metric("Rewards Earned", f"{out_rewards:+.1f}")
    m4.metric("Stops", str(len(path)))

    st.markdown(
        "**Optimal Path:** "
        + " → ".join(f"**{graph.nodes[nid].name}**" for nid in path)
    )

    st.markdown("**Step-by-Step Breakdown:**")
    _render_step_breakdown(graph, out_edges)

# ---- data tables ----
st.markdown("---")

with st.expander("All Nodes"):
    st.dataframe(
        [
            {
                "ID": nid,
                "Name": n.name,
                "Type": n.node_type,
                "Reward": n.reward,
                "x": n.x,
                "y": n.y,
            }
            for nid, n in graph.nodes.items()
        ],
        width="stretch",
        hide_index=True,
    )

with st.expander("All Edges"):
    st.dataframe(
        [
            {
                "From": graph.nodes[e.from_id].name,
                "To": graph.nodes[e.to_id].name,
                "Time Cost": e.time_cost,
                "Edge Reward": e.edge_reward,
                "Final Weight": e.final_weight,
            }
            for e in graph.edges
        ],
        width="stretch",
        hide_index=True,
    )
