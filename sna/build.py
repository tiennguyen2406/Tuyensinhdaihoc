"""EduRadar V2 - xay dung mang va tinh do do SNA.

Dau vao : data/eduradar.db (tu pipeline.clean)
Dau ra  : data/network/<mang>_<nam>.json      (cho trang /network)
          data/network/metrics/<mang>_<nam>.csv (do do tung dinh)
          data/network/gexf/<mang>_<nam>.gexf   (mo bang Gephi)
          data/network/fig/*.png                (phan bo bac)
          data/network/summary.csv              (bang tong hop cho bao cao)

Bon mang:
  G1 uni_major     : hai phia Truong - Nganh (canh = truong co tuyen nganh)
  G2 uni_uni       : chieu tu G1, trong so Jaccard tap nganh
  G3 major_major   : chieu tu G1, trong so Jaccard tap truong
  G4 competition   : co huong A->B neu cung nganh (THPT), diem B cao hon A trong vong 2 diem

Chay: python -m sna.build [--years 2024 2025 2026] [--jaccard 0.25] [--gap 2] [--out <thu muc>]
     (--out: ghi ra thu muc khac, VD khi phan tich do nhay, khong de len data/network/)
Can: pandas, networkx, matplotlib (pip install pandas networkx matplotlib scipy)
"""

from __future__ import annotations

import argparse
import itertools
import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd
from networkx.algorithms import bipartite, community

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "eduradar.db"
OUT = ROOT / "data" / "network"
VIZ_EDGE_LIMIT = 1500  # so canh toi da gui len web (giu canh nang nhat)


def r4(x):
    return round(float(x), 4)


def load(year: int) -> tuple[pd.DataFrame, dict, dict]:
    with sqlite3.connect(DB) as c:
        adm = pd.read_sql(
            "SELECT uni_code, major_code, method, score, scale_max, flag FROM admissions "
            "WHERE year = ? AND major_code IS NOT NULL",
            c,
            params=(year,),
        )
        unis = dict(
            c.execute("SELECT uni_code, COALESCE(short_name, name) FROM universities").fetchall()
        )
        majors = dict(c.execute("SELECT major_code, major_name FROM majors").fetchall())
    return adm, unis, majors


# ---------------------------------------------------------------- graphs
def g1_bipartite(adm: pd.DataFrame) -> nx.Graph:
    g = nx.Graph()
    pairs = adm.groupby(["uni_code", "major_code"]).size()
    for (u, m), w in pairs.items():
        g.add_node(f"U:{u}", bipartite=0, kind="uni")
        g.add_node(f"M:{m}", bipartite=1, kind="major")
        g.add_edge(f"U:{u}", f"M:{m}", weight=int(w))
    return g


def jaccard_projection(g1: nx.Graph, side: str, threshold: float) -> nx.Graph:
    nodes = [n for n, d in g1.nodes(data=True) if d["kind"] == side]
    nb = {n: set(g1[n]) for n in nodes}
    g = nx.Graph()
    g.add_nodes_from(nodes, kind=side)
    # chi xet cap co it nhat 1 hang xom chung (qua dinh ben kia)
    other = [n for n, d in g1.nodes(data=True) if d["kind"] != side]
    seen = set()
    for o in other:
        for a, b in itertools.combinations(sorted(g1[o]), 2):
            if (a, b) in seen:
                continue
            seen.add((a, b))
            inter = len(nb[a] & nb[b])
            j = inter / len(nb[a] | nb[b])
            if j >= threshold:
                g.add_edge(a, b, weight=r4(j), shared=inter)
    return g


def g4_competition(adm: pd.DataFrame, gap: float = 2.0) -> nx.DiGraph:
    thpt = adm[(adm.method == "THPT") & (adm.scale_max == 30) & (adm.flag == "")]
    best = thpt.groupby(["major_code", "uni_code"])["score"].max().reset_index()
    g = nx.DiGraph()
    g.add_nodes_from((f"U:{u}" for u in best.uni_code.unique()), kind="uni")
    w = defaultdict(int)
    for _, grp in best.groupby("major_code"):
        rows = list(grp.itertuples(index=False))
        for a, b in itertools.permutations(rows, 2):
            d = b.score - a.score
            if 0 < d <= gap:
                w[(f"U:{a.uni_code}", f"U:{b.uni_code}")] += 1
    for (a, b), k in w.items():
        g.add_edge(a, b, weight=k)
    return g


# ---------------------------------------------------------------- metrics
def lcc(g: nx.Graph) -> nx.Graph:
    comps = nx.weakly_connected_components(g) if g.is_directed() else nx.connected_components(g)
    return g.subgraph(max(comps, key=len)).copy()


def undirected_metrics(g: nx.Graph) -> tuple[dict, dict]:
    t = time.time()
    big = lcc(g)
    node = {
        "degree": dict(g.degree()),
        "degree_centrality": nx.degree_centrality(g),
        "betweenness": nx.betweenness_centrality(g, normalized=True),
        "closeness": nx.closeness_centrality(g),
        "eigenvector": nx.eigenvector_centrality_numpy(big, weight="weight")
        if big.number_of_edges()
        else {},
        "clustering": nx.clustering(g, weight=None),
        "pagerank": nx.pagerank(g, weight="weight"),
    }
    comms = community.louvain_communities(g, weight="weight", seed=42)
    group = {n: i for i, c in enumerate(sorted(comms, key=len, reverse=True)) for n in c}
    node["community"] = group
    summary = {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "density": r4(nx.density(g)),
        "components": nx.number_connected_components(g),
        "lcc_nodes": big.number_of_nodes(),
        "avg_degree": r4(2 * g.number_of_edges() / max(g.number_of_nodes(), 1)),
        "avg_clustering": r4(nx.average_clustering(g)),
        "transitivity": r4(nx.transitivity(g)),
        "avg_path_length_lcc": r4(nx.average_shortest_path_length(big))
        if big.number_of_nodes() > 1
        else 0,
        "diameter_lcc": nx.diameter(big) if big.number_of_nodes() > 1 else 0,
        "assortativity": r4(nx.degree_assortativity_coefficient(g)) if g.number_of_edges() else 0,
        "louvain_communities": len(comms),
        "modularity_louvain": r4(community.modularity(g, comms, weight="weight")),
    }
    # so sanh Girvan-Newman tren do thi con (60 dinh bac cao nhat) - thuat toan O(m^2 n) nen chi chay mau
    sub = g.subgraph(sorted(g, key=lambda n: -g.degree(n))[:60]).copy()
    if sub.number_of_edges() > 0:
        t0 = time.time()
        best_q, best_k = -1.0, 0
        for k, parts in zip(range(2, 12), community.girvan_newman(sub)):
            q = community.modularity(sub, parts)
            if q > best_q:
                best_q, best_k = q, len(parts)
        gn_time = time.time() - t0
        t0 = time.time()
        lv = community.louvain_communities(sub, seed=42)
        summary.update(
            {
                "gn_sample_nodes": sub.number_of_nodes(),
                "gn_best_modularity": r4(best_q),
                "gn_best_k": best_k,
                "gn_seconds": r4(gn_time),
                "louvain_sample_modularity": r4(community.modularity(sub, lv)),
                "louvain_sample_seconds": r4(time.time() - t0),
            }
        )
    summary["compute_seconds"] = r4(time.time() - t)
    return node, summary


def directed_metrics(g: nx.DiGraph) -> tuple[dict, dict]:
    hubs, auths = nx.hits(g, max_iter=1000, normalized=True) if g.number_of_edges() else ({}, {})
    node = {
        "in_degree": dict(g.in_degree()),
        "out_degree": dict(g.out_degree()),
        "in_strength": dict(g.in_degree(weight="weight")),
        "pagerank": nx.pagerank(g, weight="weight"),
        "hub": hubs,
        "authority": auths,
        "betweenness": nx.betweenness_centrality(g, normalized=True),
    }
    big = lcc(g)
    summary = {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "density": r4(nx.density(g)),
        "weak_components": nx.number_weakly_connected_components(g),
        "strong_components": nx.number_strongly_connected_components(g),
        "reciprocity": r4(nx.reciprocity(g)) if g.number_of_edges() else 0,
        "lcc_nodes": big.number_of_nodes(),
    }
    return node, summary


def degree_plot(g, path: Path, title: str, nodes=None, kind: str = "") -> None:
    """Ve phan bo bac. nodes: chi tinh bac (trong do thi g) cua cac dinh nay;
    kind: "in"/"out" cho do thi co huong."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    view = g.in_degree() if kind == "in" else g.out_degree() if kind == "out" else g.degree()
    deg = [d for n, d in view if d > 0 and (nodes is None or n in nodes)]
    if not deg:
        return
    cnt = pd.Series(deg).value_counts().sort_index()
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].hist(deg, bins=30, color="#1f5eff")
    ax[0].set(title=f"{title}: phân bố bậc", xlabel="bậc k", ylabel="số đỉnh")
    ax[1].loglog(cnt.index, cnt.values / cnt.sum(), "o", ms=4, color="#e8590c")
    ax[1].set(title="log–log P(k)", xlabel="k", ylabel="P(k)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------- export
def export(name, year, g, node_metrics, summary, labels, title, desc, size_key, top_keys):
    for d in ("metrics", "gexf", "fig"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(node_metrics).rename_axis("id").reset_index()
    df.insert(1, "label", df["id"].map(lambda n: labels.get(n, n)))
    df.insert(2, "kind", df["id"].map(lambda n: g.nodes[n].get("kind")))
    df.round(5).to_csv(OUT / "metrics" / f"{name}_{year}.csv", index=False, encoding="utf-8-sig")

    gx = g.copy()
    for n in gx.nodes:
        gx.nodes[n]["label"] = labels.get(n, n)
        for k, vals in node_metrics.items():
            if n in vals:
                gx.nodes[n][k] = float(vals[n])
    nx.write_gexf(gx, OUT / "gexf" / f"{name}_{year}.gexf")

    edges = sorted(g.edges(data=True), key=lambda e: -e[2].get("weight", 1))[:VIZ_EDGE_LIMIT]
    keep = {n for e in edges for n in e[:2]}
    size = node_metrics.get(size_key, {})
    payload = {
        "title": title,
        "description": desc,
        "directed": g.is_directed(),
        "year": year,
        "summary": summary,
        "top": {
            k: [
                [labels.get(n, n), r4(v)]
                for n, v in sorted(node_metrics[k].items(), key=lambda x: -x[1])[:10]
            ]
            for k in top_keys
            if k in node_metrics
        },
        "nodes": [
            {
                "id": n,
                "label": labels.get(n, n),
                "kind": g.nodes[n].get("kind"),
                "group": node_metrics.get("community", {}).get(n),
                "size": r4(size.get(n, 0)) + 0.0001,
                "metrics": {
                    k: r4(v[n]) for k, v in node_metrics.items() if n in v and k != "community"
                },
            }
            for n in keep
        ],
        "edges": [{"source": a, "target": b, "weight": d.get("weight", 1)} for a, b, d in edges],
    }
    (OUT / f"{name}_{year}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    return {"network": name, "year": year, **summary}


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025, 2026])
    ap.add_argument("--jaccard", type=float, default=0.25, help="nguong Jaccard cho G2/G3")
    ap.add_argument("--gap", type=float, default=2.0, help="khoang diem cho mang canh tranh G4")
    ap.add_argument("--out", type=Path, default=OUT, help="thu muc ket qua (mac dinh data/network)")
    args = ap.parse_args()
    OUT = args.out
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for year in args.years:
        adm, unis, majors = load(year)
        if adm.empty:
            continue
        labels = {
            **{f"U:{k}": v for k, v in unis.items()},
            **{f"M:{k}": v for k, v in majors.items()},
        }
        print(f"== {year}: {len(adm):,} dong")

        g1 = g1_bipartite(adm)
        U = [n for n, d in g1.nodes(data=True) if d["kind"] == "uni"]
        M = [n for n, d in g1.nodes(data=True) if d["kind"] == "major"]
        deg = dict(g1.degree())
        m1 = {
            "degree": deg,
            "degree_centrality": bipartite.degree_centrality(g1, U),
            "betweenness": bipartite.betweenness_centrality(g1, U),
        }
        s1 = {
            "nodes": g1.number_of_nodes(),
            "universities": len(U),
            "majors": len(M),
            "edges": g1.number_of_edges(),
            "bipartite_density": r4(bipartite.density(g1, U)),
            "avg_majors_per_uni": r4(sum(deg[u] for u in U) / len(U)),
            "avg_unis_per_major": r4(sum(deg[m] for m in M) / len(M)),
            "components": nx.number_connected_components(g1),
        }
        rows.append(
            export(
                "g1_uni_major",
                year,
                g1,
                m1,
                s1,
                labels,
                "G1 · Trường – Ngành (hai phía)",
                "Cạnh nối trường với ngành trường đó tuyển. Kim cương = ngành, tròn = trường.",
                "degree",
                ["degree", "betweenness"],
            )
        )
        # bac cua dinh nganh tinh tren G1 (= so truong mo nganh); truoc day dung subgraph(M) khong co canh
        degree_plot(g1, OUT / "fig" / f"g1_major_degree_{year}.png", "Ngành (G1)", nodes=set(M))
        degree_plot(g1, OUT / "fig" / f"g1_uni_degree_{year}.png", "Trường (G1)", nodes=set(U))
        degree_plot(g1, OUT / "fig" / f"g1_degree_{year}.png", "G1")

        for name, side, title, desc in [
            (
                "g2_uni_uni",
                "uni",
                "G2 · Trường – Trường",
                "Hai trường nối nhau khi tập ngành giống nhau (Jaccard ≥ ngưỡng). Màu = cộng đồng Louvain.",
            ),
            (
                "g3_major_major",
                "major",
                "G3 · Ngành – Ngành",
                "Hai ngành nối nhau khi thường cùng được một trường mở. Màu = cộng đồng Louvain.",
            ),
        ]:
            g = jaccard_projection(g1, side, args.jaccard)
            g.remove_nodes_from([n for n in list(g) if g.degree(n) == 0])
            nm, sm = undirected_metrics(g)
            sm["jaccard_threshold"] = args.jaccard
            rows.append(
                export(
                    name,
                    year,
                    g,
                    nm,
                    sm,
                    labels,
                    title,
                    desc,
                    "degree",
                    ["degree", "betweenness", "closeness", "eigenvector", "pagerank", "clustering"],
                )
            )
            degree_plot(g, OUT / "fig" / f"{name}_degree_{year}.png", title.split("·")[1].strip())
            if side == "major":  # du doan lien ket -> goi y nganh tuong tu
                pred = sorted(nx.adamic_adar_index(g), key=lambda x: -x[2])[:300]
                pd.DataFrame(
                    [(labels.get(a, a), labels.get(b, b), r4(s)) for a, b, s in pred],
                    columns=["nganh_a", "nganh_b", "adamic_adar"],
                ).to_csv(
                    OUT / "metrics" / f"link_prediction_{year}.csv",
                    index=False,
                    encoding="utf-8-sig",
                )
                sim = {}
                for n in g:
                    nbrs = sorted(g[n].items(), key=lambda x: -x[1]["weight"])[:8]
                    sim[n[2:]] = [[m[2:], labels.get(m, m), d["weight"]] for m, d in nbrs]
                (OUT / f"similar_majors_{year}.json").write_text(
                    json.dumps(sim, ensure_ascii=False), encoding="utf-8"
                )

        g4 = g4_competition(adm, args.gap)
        g4.remove_nodes_from([n for n in list(g4) if g4.degree(n) == 0])
        if g4.number_of_edges():
            degree_plot(g4, OUT / "fig" / f"g4_in_degree_{year}.png", "G4 bậc vào", kind="in")
            degree_plot(g4, OUT / "fig" / f"g4_out_degree_{year}.png", "G4 bậc ra", kind="out")
            nm, sm = directed_metrics(g4)
            thpt = (
                adm[(adm.method == "THPT") & (adm.scale_max == 30)]
                .groupby("uni_code")["score"]
                .mean()
            )
            avg = {f"U:{k}": v for k, v in thpt.items()}
            common = [n for n in g4 if n in avg]
            sm["spearman_authority_vs_avg_score"] = r4(
                pd.Series({n: nm["authority"][n] for n in common})
                .rank()
                .corr(pd.Series({n: avg[n] for n in common}).rank())
            )
            sm["spearman_pagerank_vs_avg_score"] = r4(
                pd.Series({n: nm["pagerank"][n] for n in common})
                .rank()
                .corr(pd.Series({n: avg[n] for n in common}).rank())
            )
            sm["score_gap"] = args.gap
            rows.append(
                export(
                    "g4_competition",
                    year,
                    g4,
                    nm,
                    sm,
                    labels,
                    "G4 · Mạng cạnh tranh (có hướng)",
                    f"A → B nếu cùng ngành, B có điểm THPT cao hơn A trong vòng {args.gap} điểm. Authority cao = trường được 'nhắm tới'.",
                    "authority",
                    ["authority", "hub", "pagerank", "in_strength"],
                )
            )
    summ = pd.DataFrame(rows)
    summ.to_csv(OUT / "summary.csv", index=False, encoding="utf-8-sig")
    print(summ.to_string())


if __name__ == "__main__":
    main()
