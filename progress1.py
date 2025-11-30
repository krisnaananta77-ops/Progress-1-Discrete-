# streamlit_app.py
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random
from io import BytesIO

# ---------- Page config ----------
st.set_page_config(
    page_title="Matrix → Graph",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Minimalist dark CSS ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #0b0c0d; color: #e6eef3; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .sidebar .sidebar-content { background: #0f1112; }
    h1, h2, h3, h4, h5, h6 { color: #f5f7fa; }
    .card {
        padding: 16px;
        border-radius: 10px;
        background: #101214;
        border: 1px solid #1f2529;
        margin-bottom: 12px;
    }
    .small-muted { color: #98a0a6; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Header ----------
st.markdown("<h1 style='text-align:center;'>Matrix → Graph App</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#9aa3aa;'>Visualize a graph from a random matrix, view per-node degrees and the adjacency matrix</p>", unsafe_allow_html=True)
st.write("")

# ---------- Sidebar: controls ----------
with st.sidebar:
    st.header("Controls")
    num_vertices = st.number_input("Number of vertices", min_value=1, max_value=200, value=6, step=1)
    max_possible_edges = num_vertices * (num_vertices - 1) // 2
    num_edges = st.number_input("Number of edges", min_value=0, max_value=max_possible_edges, value=min(6, max_possible_edges), step=1)
    layout_type = st.selectbox("Layout", ["Spring", "Circular", "Shell", "Random"])
    show_labels = st.checkbox("Show labels", value=True)
    color_by_degree = st.checkbox("Color nodes by degree", value=True)
    st.divider()
    st.write("Export / Download")
    download_adj = st.button("Prepare adjacency CSV")
    st.write("")
    st.write("Tip: adjust vertices/edges and use download buttons below.")

# ---------- Build graph ----------
def create_random_graph(n, m):
    G = nx.Graph()
    G.add_nodes_from(range(n))
    possible_edges = [(i, j) for i in range(n) for j in range(i+1, n)]
    # handle case when edges > possible
    m = min(m, len(possible_edges))
    chosen_edges = random.sample(possible_edges, m)
    G.add_edges_from(chosen_edges)
    return G

G = create_random_graph(num_vertices, num_edges)

# ---------- Layout ----------
if layout_type == "Spring":
    pos = nx.spring_layout(G, seed=42)
elif layout_type == "Circular":
    pos = nx.circular_layout(G)
elif layout_type == "Shell":
    pos = nx.shell_layout(G)
else:
    pos = nx.random_layout(G, seed=42)

# ---------- Left: visualization, Right: tables ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Graph visualization")
    # Node colors based on degree
    degrees = dict(G.degree())
    deg_values = np.array([degrees.get(n, 0) for n in G.nodes()])
    if color_by_degree and len(G.nodes())>0:
        # normalize degrees for colormap
        if deg_values.max() == deg_values.min():
            node_colors = ["#6daedb" for _ in deg_values]
        else:
            cmap = plt.get_cmap("plasma")
            norm = (deg_values - deg_values.min()) / (deg_values.max() - deg_values.min())
            node_colors = [cmap(float(v)) for v in norm]
    else:
        node_colors = "#6daedb"

    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    ax.set_facecolor("#0b0c0d")
    # draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#6e7072", alpha=0.9)
    # draw nodes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=400, node_color=node_colors)
    # labels
    if show_labels:
        nx.draw_networkx_labels(G, pos, ax=ax, font_color="white", font_size=9)
    ax.set_axis_off()
    st.pyplot(fig)
    # Download PNG
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    st.download_button("Download graph PNG", data=buf, file_name="graph.png", mime="image/png")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Node degrees")
    # degree table
    degree_df = pd.DataFrame({
        "Node": [f"V{n}" for n in degrees.keys()],
        "Degree": list(degrees.values())
    }).sort_values(by="Node").reset_index(drop=True)
    st.table(degree_df.style.format({"Node": lambda v: v}))

    st.write("")
    st.subheader("Adjacency matrix")
    adj = nx.to_numpy_array(G, dtype=int)
    adj_df = pd.DataFrame(adj, index=[f"V{i}" for i in range(num_vertices)], columns=[f"V{i}" for i in range(num_vertices)])
    # display compact
    st.dataframe(adj_df, use_container_width=True, height=300)

    # Download adjacency CSV
    csv_buf = BytesIO()
    adj_df.to_csv(csv_buf)
    csv_buf.seek(0)
    st.download_button("Download adjacency CSV", data=csv_buf, file_name="adjacency_matrix.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Additional stats (bottom) ----------
st.markdown("<div class='card'>", unsafe_allow_html=True)
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Nodes", len(G.nodes()))
col_b.metric("Edges", len(G.edges()))
col_c.metric("Avg degree", round(float(np.mean(list(dict(G.degree()).values()))) if len(G.nodes())>0 else 0, 2))
col_d.metric("Components", nx.number_connected_components(G) if len(G.nodes())>0 else 0)
st.markdown("</div>", unsafe_allow_html=True)