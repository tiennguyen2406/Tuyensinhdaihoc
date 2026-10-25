"""Read-only report calculations; print reproducible JSON, never export networks.

Run: .venv/Scripts/python.exe -X utf8 scripts/report_network_supplement.py
Sources: data/eduradar.db, data/network/summary.csv and metrics/*.csv.
"""

from __future__ import annotations

import itertools
import json
import sqlite3
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sna import build  # noqa: E402


def main() -> None:
    summary = pd.read_csv(ROOT / "data/network/summary.csv")
    with sqlite3.connect(f"file:{build.DB.as_posix()}?mode=ro", uri=True) as con:
        names = dict(con.execute("SELECT uni_code, name FROM universities"))
        major_names = dict(con.execute("SELECT major_code, major_name FROM majors"))
    result = {"global": {}, "clustering_top10_2026": {}, "temporal": []}
    g3_by_year = {}
    for year in (2024, 2025, 2026):
        adm, _, _ = build.load(year)
        g1 = build.g1_bipartite(adm)
        g2 = build.jaccard_projection(g1, "uni", 0.25)
        g3 = build.jaccard_projection(g1, "major", 0.25)
        g4 = build.g4_competition(adm, 2)
        for graph in (g2, g3, g4):
            graph.remove_nodes_from(list(nx.isolates(graph)))
        graphs = dict(
            zip(
                ("g1_uni_major", "g2_uni_uni", "g3_major_major", "g4_competition"),
                (g1, g2, g3, g4),
                strict=True,
            )
        )
        for name, graph in graphs.items():
            saved = summary[(summary.network == name) & (summary.year == year)].iloc[0]
            assert (len(graph), graph.number_of_edges()) == (saved.nodes, saved.edges), (
                name,
                year,
                len(graph),
                graph.number_of_edges(),
                saved.nodes,
                saved.edges,
            )
        g3_by_year[year] = g3
        big1 = build.lcc(g1)
        scc4 = g4.subgraph(max(nx.strongly_connected_components(g4), key=len)).copy()
        n4, m4 = len(g4), g4.number_of_edges()
        assert (
            len(build.lcc(g4))
            == summary[(summary.network == "g4_competition") & (summary.year == year)]
            .iloc[0]
            .lcc_nodes
        )
        result["global"][year] = {
            "g1_uni_major": {
                "lcc_nodes": len(big1),
                "avg_degree": build.r4(2 * g1.number_of_edges() / len(g1)),
                "avg_path_length_lcc": build.r4(nx.average_shortest_path_length(big1)),
                "diameter_lcc": nx.diameter(big1),
                "assortativity": build.r4(nx.degree_assortativity_coefficient(g1)),
                "avg_clustering": build.r4(nx.average_clustering(g1, weight=None)),
                "transitivity": build.r4(nx.transitivity(g1)),
            },
            "g4_competition": {
                "weak_lcc_nodes": len(build.lcc(g4)),
                "largest_scc_nodes": len(scc4),
                "avg_path_length_largest_scc": build.r4(nx.average_shortest_path_length(scc4)),
                "diameter_largest_scc": nx.diameter(scc4),
                "avg_total_degree": build.r4(2 * m4 / n4),
                "avg_in_degree": build.r4(m4 / n4),
                "avg_out_degree": build.r4(m4 / n4),
                "avg_clustering_directed": build.r4(nx.average_clustering(g4, weight=None)),
                "assortativity_out_in": build.r4(nx.degree_assortativity_coefficient(g4)),
                "transitivity_undirected_projection": build.r4(nx.transitivity(g4.to_undirected())),
            },
        }

    for name in ("g2_uni_uni", "g3_major_major"):
        data = pd.read_csv(ROOT / f"data/network/metrics/{name}_2026.csv")
        top = data[data.degree >= 5].nlargest(10, "clustering")
        result["clustering_top10_2026"][name] = [
            {
                "id": row.id,
                "name": names[row.id[2:]] if row.id.startswith("U:") else row.label,
                "degree": int(row.degree),
                "clustering": float(row.clustering),
            }
            for row in top.itertuples()
        ]

    codes_by_name = {}
    for code, name in major_names.items():
        codes_by_name.setdefault(name, []).append(f"M:{code}")
    for before, after in ((2024, 2025), (2025, 2026), (2024, 2026)):
        old, new = g3_by_year[before], g3_by_year[after]
        common = set(old) & set(new)
        baseline_pairs = list(nx.non_edges(old.subgraph(common)))
        new_edges = sum(new.has_edge(a, b) for a, b in baseline_pairs)
        pred = pd.read_csv(ROOT / f"data/network/metrics/link_prediction_{before}.csv")
        assert len(pred) == 300
        hits, eligible = [], 0
        for row in pred.itertuples():
            candidates = [
                (a, b)
                for a, b in itertools.product(
                    codes_by_name[row.nganh_a], codes_by_name[row.nganh_b]
                )
                if a != b and a in common and b in common
            ]
            eligible += bool(candidates)
            hits.append(any(new.has_edge(a, b) for a, b in candidates))
        baseline_rate = new_edges / len(baseline_pairs)
        result["temporal"].append(
            {
                "from": before,
                "to": after,
                "hits_top10": sum(hits[:10]),
                "hits_top100": sum(hits[:100]),
                "hits_top300": sum(hits),
                "precision_top300": sum(hits) / 300,
                "eligible_of_300": eligible,
                "baseline_new_edges": new_edges,
                "baseline_non_edges": len(baseline_pairs),
                "baseline_rate": baseline_rate,
                "lift": (sum(hits) / 300) / baseline_rate,
            }
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
