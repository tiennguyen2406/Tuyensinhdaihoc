"""EduRadar V2 - ve hinh mang tinh cho bao cao (G2, G3).

Dau vao : data/network/gexf/<mang>_<nam>.gexf (tu sna.build, da co community + degree)
Dau ra  : data/network/fig/<mang>_net_<nam>.png

Chi ve thanh phan lien thong lon nhat (cac manh nho bi spring layout day ra xa lam hinh bi nen).
Spring layout (seed co dinh), mau = cong dong Louvain, kich thuoc = bac,
nhan cho 15 dinh bac cao nhat (truong: ma truong, nganh: ten nganh), day nhan ra xa nhau.

Chay: python -m sna.draw [--year 2026] [--top 15]
"""

from __future__ import annotations

import argparse
import itertools
from collections import Counter
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
NET = ROOT / "data" / "network"
PALETTE = [
    "#1f5eff", "#e8590c", "#2b8a3e", "#c2255c", "#7048e8",
    "#0c8599", "#e67700", "#5c940d", "#862e9c", "#495057",
]  # fmt: skip
OTHER = "#adb5bd"  # cong dong nho (ngoai 9 cong dong lon nhat)


def spread_labels(
    pos: dict, nodes: list, min_dist: float, aspect: float = 1.0, rounds: int = 300
) -> dict:
    """Day vi tri nhan ra xa nhau toi thieu min_dist (don gian, khong can thu vien ngoai).
    aspect > 1: nhan dai theo chieu ngang -> can cach xa hon theo truc x."""
    lp = {n: [float(pos[n][0]), float(pos[n][1])] for n in nodes}
    for _ in range(rounds):
        moved = False
        for a, b in itertools.combinations(nodes, 2):
            dx, dy = (lp[b][0] - lp[a][0]) / aspect, lp[b][1] - lp[a][1]
            d = (dx * dx + dy * dy) ** 0.5
            if d < min_dist:
                if d == 0:
                    dx, dy, d = 0.0, 1.0, 1.0
                push = (min_dist - d) / 2
                lp[a][0] -= dx / d * push * aspect
                lp[a][1] -= dy / d * push
                lp[b][0] += dx / d * push * aspect
                lp[b][1] += dy / d * push
                moved = True
        if not moved:
            break
    return lp


def draw(name: str, year: int, title: str, top: int, seed: int = 42) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    full = nx.read_gexf(NET / "gexf" / f"{name}_{year}.gexf")
    g = full.subgraph(max(nx.connected_components(full), key=len)).copy()
    comm = {n: int(d["community"]) for n, d in g.nodes(data=True)}
    big = [c for c, _ in Counter(comm.values()).most_common(len(PALETTE) - 1)]
    color = {c: PALETTE[i] for i, c in enumerate(big)}
    deg = dict(g.degree())

    # k lon hon mac dinh de cac cong dong tach ra; trong so Jaccard keo cac dinh giong nhau lai gan
    pos = nx.spring_layout(g, k=4 / len(g) ** 0.5, iterations=300, seed=seed, weight="weight")
    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_edges(g, pos, ax=ax, width=0.4, alpha=0.15, edge_color="#868e96")
    nodes = sorted(g, key=lambda n: deg[n])  # dinh lon ve sau, nam tren
    nx.draw_networkx_nodes(
        g,
        pos,
        nodelist=nodes,
        ax=ax,
        node_size=[12 + 6 * deg[n] for n in nodes],
        node_color=[color.get(comm[n], OTHER) for n in nodes],
        linewidths=0.4,
        edgecolors="white",
    )
    hubs = sorted(g, key=lambda n: -deg[n])[:top]
    text = {n: n[2:] if n.startswith("U:") else g.nodes[n]["label"] for n in hubs}
    xs = [p[0] for p in pos.values()]
    # nhan ten nganh dai ~ 20-40 ky tu: can khoang cach ngang lon hon nhieu so voi doc
    aspect = max(1.0, sum(len(t) for t in text.values()) / len(text) / 6)
    lp = spread_labels(pos, hubs, min_dist=0.045 * (max(xs) - min(xs)), aspect=aspect)
    for n in hubs:
        ax.annotate(
            text[n],
            xy=pos[n],
            xytext=lp[n],
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.8},
            arrowprops={"arrowstyle": "-", "color": "#495057", "lw": 0.5},
        )

    sizes = Counter(comm.values())
    handles = [
        plt.Line2D(
            [], [], marker="o", ls="", color=color[c], label=f"Cộng đồng {c} ({sizes[c]} đỉnh)"
        )
        for c in big
    ]
    rest = sum(v for c, v in sizes.items() if c not in color)
    if rest:
        handles.append(
            plt.Line2D(
                [], [], marker="o", ls="", color=OTHER, label=f"Cộng đồng khác ({rest} đỉnh)"
            )
        )
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=False)
    n_comm = len({d["community"] for _, d in full.nodes(data=True)})
    ax.set_title(
        f"{title} {year} — thành phần lớn nhất: {g.number_of_nodes()}/{full.number_of_nodes()} "
        f"đỉnh, {g.number_of_edges()} cạnh; {len(sizes)}/{n_comm} cộng đồng Louvain"
    )
    ax.axis("off")
    fig.tight_layout()
    out = NET / "fig" / f"{name}_net_{year}.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--top", type=int, default=15, help="so dinh duoc gan nhan")
    args = ap.parse_args()
    for name, title in [
        ("g2_uni_uni", "G2 Trường – Trường"),
        ("g3_major_major", "G3 Ngành – Ngành"),
    ]:
        print("Da ve", draw(name, args.year, title, args.top).relative_to(ROOT))


if __name__ == "__main__":
    main()
