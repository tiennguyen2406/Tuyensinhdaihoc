"""Ve hinh bao cao tu SQLite, metrics va bang do nhay da luu; khong crawl."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sna.build import g1_bipartite, g4_competition, jaccard_projection, load  # noqa: E402

FIG = ROOT / "docs/fig"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def diagram(name, labels):
    fig, ax = plt.subplots(figsize=(10, 2.1))
    ax.axis("off")
    for i, label in enumerate(labels):
        x = (i + 0.5) / len(labels)
        ax.text(
            x,
            0.5,
            label,
            ha="center",
            va="center",
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=.65", facecolor="#e5eff9", edgecolor="#34668a"),
        )
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=((i + 1.28) / len(labels), 0.5),
                xytext=((i + 0.75) / len(labels), 0.5),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color="#34668a"),
            )
    save(fig, name)


def degree(g, nodes, name, title, kind=""):
    view = g.in_degree() if kind == "in" else g.out_degree() if kind == "out" else g.degree()
    deg = [d for n, d in view if n in nodes]
    cnt = pd.Series(deg).value_counts().sort_index()
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.1))
    ax[0].hist(deg, bins=25, color="#2b718e")
    ax[0].set(title=title, xlabel="Bậc k", ylabel="Số đỉnh")
    positive = cnt[cnt.index > 0]
    ax[1].loglog(positive.index, positive / len(deg), "o", color="#c45c27", ms=4)
    ax[1].set(title="Phân bố log–log (k > 0)", xlabel="k", ylabel="P(k)")
    save(fig, name)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    diagram(
        "data_flow.png",
        [
            "Crawler\nAPI / HTML",
            "Raw\nJSON / HTML",
            "Làm sạch\nchuẩn hoá",
            "SQLite",
            "Mạng SNA\nỨng dụng",
        ],
    )
    fig, ax = plt.subplots(figsize=(9, 2.8))
    ax.axis("off")
    for x, y, text in [
        (0.22, 0.5, "G1: Trường–Ngành\nQuan hệ tuyển sinh"),
        (0.72, 0.78, "G2: Trường–Trường\nJaccard tập ngành"),
        (0.72, 0.22, "G3: Ngành–Ngành\nJaccard tập trường"),
    ]:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=.6", facecolor="#e5eff9", edgecolor="#34668a"),
        )
    for y in (0.78, 0.22):
        ax.annotate(
            "",
            xy=(0.56, y),
            xytext=(0.37, 0.5),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color="#34668a"),
        )
    save(fig, "projection.png")
    fig, ax = plt.subplots(figsize=(8, 3))
    stages = ["Thô", "Bỏ 69 dòng điểm lỗi", "Gộp 4.961 cặp", "Bỏ 685 dòng trùng"]
    values = [76726, 76657, 71696, 71011]
    ax.barh(
        stages[::-1],
        values[::-1],
        left=[(values[0] - v) / 2 for v in values[::-1]],
        color=["#24617c", "#3484a4", "#69a8c0", "#a1cbd9"],
    )
    for i, v in enumerate(values[::-1]):
        ax.text(values[0] / 2, i, f"{v:,}", va="center", ha="center", color="black", weight="bold")
    ax.set(xlim=(0, 85000), xlabel="Số dòng", title="Số dòng qua các bước làm sạch")
    save(fig, "cleaning_funnel.png")
    with sqlite3.connect(ROOT / "data/eduradar.db") as db:
        adm = pd.read_sql("SELECT * FROM admissions", db)
    table = adm.groupby(["method", "year"]).size().unstack()
    ax = table.plot.bar(figsize=(10, 3.8), color=["#aac8d5", "#4b91ac", "#204c6b"], rot=25)
    ax.set(xlabel="Phương thức", ylabel="Dòng sạch", title="Dữ liệu theo năm và phương thức")
    save(ax.figure, "year_method.png")
    counts = adm.match_how.fillna("").replace("", "chua_map").value_counts()
    fig, ax = plt.subplots(figsize=(9, 3.5))
    counts.plot.barh(ax=ax, color="#347b95")
    for i, n in enumerate(counts):
        ax.text(n + 400, i, f"{n / len(adm):.2%}", va="center")
    ax.set(xlim=(0, 65000), xlabel="Số dòng", title="Phương pháp ánh xạ mã ngành")
    save(fig, "mapping_share.png")
    data, _, _ = load(2026)
    g1 = g1_bipartite(data)
    degree(g1, {n for n in g1 if n.startswith("U:")}, "g1_uni_degree_2026.png", "G1 — phía trường")
    degree(g1, {n for n in g1 if n.startswith("M:")}, "g1_major_degree_2026.png", "G1 — phía ngành")
    for name, side, label in [
        ("g2_uni_uni", "uni", "G2 — Trường–Trường"),
        ("g3_major_major", "major", "G3 — Ngành–Ngành"),
    ]:
        g = jaccard_projection(g1, side, 0.25)
        g.remove_nodes_from(list(nx.isolates(g)))
        degree(g, set(g), f"{name}_degree_2026.png", label)
        metrics = pd.read_csv(ROOT / f"data/network/metrics/{name}_2026.csv").set_index("id")
        # Bo cuc tung thanh phan rieng de cac cum tach roi khong ep LCC thanh mot cham nho.
        comps = sorted(nx.connected_components(g), key=len, reverse=True)
        base_pos = nx.spring_layout(g.subgraph(comps[0]), seed=42, weight="weight", iterations=140)
        pos = {n: (xy[0] * 0.8 - 0.25, xy[1]) for n, xy in base_pos.items()}
        for i, comp in enumerate(comps[1:]):
            small = nx.circular_layout(sorted(comp), scale=0.095)
            center = 0.85 - 1.7 * i / max(len(comps) - 2, 1)
            pos.update({n: (xy[0] + 1.05, xy[1] + center) for n, xy in small.items()})
        fig, ax = plt.subplots(figsize=(9, 6))
        nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.16, width=0.45)
        nx.draw_networkx_nodes(
            g,
            pos,
            ax=ax,
            node_size=[12 + g.degree(n) * 2 for n in g],
            node_color=[metrics.loc[n, "community"] for n in g],
            cmap="tab20",
        )
        top = metrics.nlargest(8, "betweenness")
        labels = {n: str(top.loc[n, "label"]).replace("Đại học", "ĐH") for n in top.index}
        nx.draw_networkx_labels(
            g,
            pos,
            labels=labels,
            ax=ax,
            font_size=7,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none", pad=0.3),
        )
        ax.text(1.05, 1.08, "Thành phần nhỏ", ha="center", fontsize=8)
        ax.set(xlim=(-1.2, 1.25), ylim=(-1.15, 1.18))
        ax.set_title(f"{label} 2026 — màu cộng đồng Louvain; nhãn top betweenness")
        ax.axis("off")
        save(fig, f"{name}_net_2026.png")
    g4 = g4_competition(data, 2)
    g4.remove_nodes_from(list(nx.isolates(g4)))
    degree(g4, set(g4), "g4_in_degree_2026.png", "G4 — bậc vào", "in")
    degree(g4, set(g4), "g4_out_degree_2026.png", "G4 — bậc ra", "out")
    m = (
        pd.read_csv(ROOT / "data/network/metrics/g3_major_major_2026.csv")
        .nlargest(10, "betweenness")
        .iloc[::-1]
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(m.label, m.betweenness, color="#347b95")
    for i, v in enumerate(m.betweenness):
        ax.text(v + 0.002, i, f"{v:.4f}", va="center", fontsize=8)
    ax.set(
        xlim=(0, 0.19),
        xlabel="Betweenness chuẩn hoá, không trọng số",
        title="10 ngành có betweenness cao nhất G3 2026",
    )
    save(fig, "g3_betweenness_top10.png")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, year in zip(axes, [2024, 2025, 2026]):
        m = pd.read_csv(ROOT / f"data/network/metrics/g4_competition_{year}.csv")
        av = (
            adm[
                (adm.year == year)
                & adm.major_code.notna()
                & (adm.method == "THPT")
                & (adm.scale_max == 30)
            ]
            .groupby("uni_code")
            .score.mean()
        )
        m["avg_score"] = m.id.str[2:].map(av)
        m["rank"] = m.pagerank.rank(ascending=False, method="average")
        ax.scatter(m["rank"], m.avg_score, s=10, alpha=0.55, color="#347b95")
        ax.set(
            title=str(year),
            xlabel="Hạng PageRank (1 = cao nhất)",
            ylabel="Điểm THPT trung bình" if year == 2024 else "",
        )
        ax.grid(alpha=0.2)
    save(fig, "g4_pagerank_score.png")
    # Nguồn: các bảng mục 2 và 3 docs/do_nhay_sna.md, năm 2026.
    x = [0.15, 0.20, 0.25, 0.30, 0.35]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
    for name, lcc, q, edges in [
        (
            "G2",
            [95.4, 94.6, 92.8, 83.5, 64.7],
            [0.260, 0.360, 0.482, 0.614, 0.702],
            [7453, 4437, 2531, 1326, 717],
        ),
        (
            "G3",
            [99, 98.2, 96.6, 63.8, 8.4],
            [0.685, 0.773, 0.836, 0.880, 0.899],
            [3461, 2164, 1412, 917, 589],
        ),
    ]:
        for ax, values in zip(axes, [lcc, q, edges]):
            ax.plot(x, values, "o-", label=name)
    for ax, ylabel in zip(axes, ["LCC (%)", "Modularity Q", "Số cạnh"]):
        ax.axvline(0.25, color="gray", ls="--")
        ax.set(xlabel="Ngưỡng Jaccard", ylabel=ylabel)
        ax.legend()
        ax.grid(alpha=0.2)
    save(fig, "sensitivity_jaccard.png")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    axes[0].plot([1, 2, 3], [6098, 9215, 11492], "o-", label="G4 2026")
    axes[0].set(xlabel="Khoảng điểm", ylabel="Số cạnh")
    axes[0].legend()
    for label, vals in [
        ("PageRank 2026", [0.527, 0.607, 0.664]),
        ("Authority 2026", [0.233, 0.234, 0.248]),
        ("Authority 2024", [-0.384, -0.401, -0.309]),
    ]:
        axes[1].plot([1, 2, 3], vals, "o-", label=label)
    axes[1].set(xlabel="Khoảng điểm", ylabel="Spearman với điểm TB")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.2)
    save(fig, "sensitivity_gap.png")
    assert all(
        (FIG / p).exists()
        for p in ["g3_betweenness_top10.png", "g4_pagerank_score.png", "data_flow.png"]
    )
    print("Created 17 report figures from DB, metrics and docs/do_nhay_sna.md.")


if __name__ == "__main__":
    main()
