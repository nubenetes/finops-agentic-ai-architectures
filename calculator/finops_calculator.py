#!/usr/bin/env python3
"""FinOps calculator for enterprise agentic-AI platforms on Microsoft Azure.

A parametric model (Python standard library only) that compares four architecture
families -- A: pure serverless, B: managed agentic platform, C: managed Kubernetes,
D: container PaaS with enterprise integration -- and estimates:

* Monthly cloud bill and unit cost per query, in EUR and USD.
* Monthly TCO (cloud + operations effort + amortised build cost).
* The unit-efficiency threshold (volume at which fixed cost stops dominating).
* Crossover volumes between architectures.
* Value break-even (ROI) and payback period.
* Break-even against per-seat SaaS licences.
* Break-even of a self-hosted small language model on GPUs.
* Regional variations across the main European and US Azure regions.

All assumptions live in ``assumptions.json``. Replace them with your own contract
prices, region, volumes and effort data.

Quick start::

    python calculator/finops_calculator.py --queries 25000 --profile P3 --agents 3
    python calculator/finops_calculator.py --queries 400000 --region eastus2 --k8s-team
    python calculator/finops_calculator.py --list-regions
    python calculator/finops_calculator.py --update-docs   # regenerate report tables
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_ASSUMPTIONS = HERE / "assumptions.json"
ARCHS = ("A", "B", "C", "D")
ARCH_SHORT = {
    "A": "A · Serverless (Functions)",
    "B": "B · Foundry + Functions",
    "C": "C · AKS Automatic",
    "D": "D · ACA + SB Premium + APIM",
}
BASELINE_REGION = "spaincentral"


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
_USD_PER_EUR = 1.15  # overwritten by FinOpsModel.__init__


def fmt_num(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def _adaptive_decimals(value: float) -> int:
    value = abs(value)
    if value == 0 or value >= 100:
        return 0
    if value >= 1:
        return 2
    if value >= 0.1:
        return 3
    return 4


def eur(value: float, decimals: Optional[int] = None) -> str:
    d = _adaptive_decimals(value) if decimals is None else decimals
    sign = "-" if value < 0 else ""
    return f"{sign}€{fmt_num(abs(value), d)}"


def usd(value_eur: float, decimals: Optional[int] = None) -> str:
    value = value_eur * _USD_PER_EUR
    d = _adaptive_decimals(value) if decimals is None else decimals
    sign = "-" if value < 0 else ""
    return f"{sign}${fmt_num(abs(value), d)}"


def money(value_eur: float, decimals: Optional[int] = None) -> str:
    """EUR and USD side by side, e.g. '€1,107 / $1,273'."""
    return f"{eur(value_eur, decimals)} / {usd(value_eur, decimals)}"


def queries_label(q: float) -> str:
    if q >= 1_000_000:
        millions = q / 1_000_000
        return f"{fmt_num(millions, 0 if millions == int(millions) else 1)} M"
    if q >= 1_000 and q % 1000 == 0:
        return f"{fmt_num(q / 1000)} k"
    return fmt_num(q)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
@dataclass
class Scenario:
    queries: float
    profile: str = "P3"
    query_profile: str = "standard"
    optimization: str = "none"
    agents: int = 1
    region: str = BASELINE_REGION
    ai_deployment: Optional[str] = None  # None -> profile default
    dr_regions: int = 0
    extra_cells: int = 0
    k8s_team: bool = False
    shared_integration: bool = False
    shared_edge: bool = False
    include_build: bool = True


@dataclass
class CostBreakdown:
    arch: str
    cloud_fixed: float
    cloud_variable: float
    steps: float
    ops: float
    build_amortized: float
    queries: float
    notes: List[str] = field(default_factory=list)

    @property
    def cloud_total(self) -> float:
        return self.cloud_fixed + self.cloud_variable + self.steps

    @property
    def tco(self) -> float:
        return self.cloud_total + self.ops + self.build_amortized

    @property
    def cloud_per_query(self) -> float:
        return self.cloud_total / self.queries if self.queries else float("inf")

    @property
    def tco_per_query(self) -> float:
        return self.tco / self.queries if self.queries else float("inf")

    @property
    def fixed_share(self) -> float:
        return self.cloud_fixed / self.cloud_total if self.cloud_total else 0.0


class FinOpsModel:
    def __init__(self, assumptions: Dict):
        global _USD_PER_EUR
        self.a = assumptions
        _USD_PER_EUR = assumptions["currency"]["usd_per_eur"]

    @classmethod
    def load(cls, path: Path = DEFAULT_ASSUMPTIONS) -> "FinOpsModel":
        with open(path, encoding="utf-8") as fh:
            return cls(json.load(fh))

    # ---- building blocks ------------------------------------------------- #
    def regions(self) -> Dict[str, Dict]:
        return {k: v for k, v in self.a["regions"].items() if not k.startswith("_")}

    def region_index(self, region: str) -> float:
        try:
            return self.regions()[region]["index"]
        except KeyError as exc:
            raise ValueError(f"Unknown region '{region}'. Use --list-regions.") from exc

    def deployment(self, s: Scenario) -> str:
        return s.ai_deployment or self.a["profiles"][s.profile]["default_ai_deployment"]

    def ai_per_query(self, s: Scenario) -> float:
        base = self.a["query_profiles"][s.query_profile]["ai_eur_per_query"]
        factor = self.a["ai_deployment_types"][self.deployment(s)]
        saving = self.a["ai_optimization_savings"][s.optimization]
        return base * factor * (1 - saving)

    def platform_per_query(self, arch: str, s: Scenario) -> float:
        return self.a["architectures"][arch]["platform_variable_eur_per_query"] * self.region_index(s.region)

    def variable_per_query(self, arch: str, s: Scenario) -> float:
        return self.ai_per_query(s) + self.platform_per_query(arch, s)

    def region_multiplier(self, arch: str, s: Scenario) -> float:
        cfg = self.a["multi_region"]
        pro = self.a["architectures"][arch]["pro_share_of_fixed"]
        return (
            1
            + s.dr_regions * cfg["dr_region_factor_of_pro"] * pro
            + s.extra_cells * cfg["extra_active_cell_factor_of_pro"] * pro
        )

    def fixed(self, arch: str, s: Scenario) -> float:
        base = self.a["architectures"][arch]["fixed_eur_month"][s.profile]
        shared = self.a["shared_services"]
        if s.shared_integration and arch == "D":
            base -= shared["integration_discount_eur_month"][s.profile]
        if s.shared_edge:
            base -= shared["edge_discount_eur_month"][s.profile]
        return max(base, 0.0) * self.region_index(s.region) * self.region_multiplier(arch, s)

    def steps(self, s: Scenario) -> float:
        total = sum(st["extra_eur_month"] for st in self.a["volume_steps"] if s.queries >= st["from_queries"])
        return total * self.region_index(s.region)

    def ops_fte(self, arch: str, s: Scenario) -> float:
        cfg = self.a["architectures"][arch]
        base = cfg["ops_fte_base"]
        if arch == "C" and s.k8s_team:
            base = self.a["shared_services"]["k8s_team_marginal_fte"]
        extra_regions = s.dr_regions + s.extra_cells
        return (
            base
            + cfg["ops_fte_per_extra_agent"] * max(s.agents - 1, 0)
            + extra_regions * self.a["multi_region"]["ops_fte_per_extra_region"]
        )

    def build_one_off(self, arch: str, s: Scenario) -> float:
        cfg = self.a["architectures"][arch]
        factor = cfg["build_factor"]
        if arch == "C" and s.k8s_team:
            factor = self.a["shared_services"]["k8s_team_build_factor"]
        per_agent = cfg["build_per_extra_agent_eur"] * max(s.agents - 1, 0)
        return self.a["build"]["one_off_eur"][s.profile] * factor + per_agent

    def build_amortized(self, arch: str, s: Scenario) -> float:
        if not s.include_build:
            return 0.0
        return self.build_one_off(arch, s) / self.a["build"]["amortization_months"]

    # ---- full cost ------------------------------------------------------- #
    def cost(self, arch: str, s: Scenario) -> CostBreakdown:
        return CostBreakdown(
            arch=arch,
            cloud_fixed=self.fixed(arch, s),
            cloud_variable=s.queries * self.variable_per_query(arch, s),
            steps=self.steps(s),
            ops=self.ops_fte(arch, s) * self.a["people"]["fte_loaded_eur_month"],
            build_amortized=self.build_amortized(arch, s),
            queries=s.queries,
        )

    def all_costs(self, s: Scenario) -> Dict[str, CostBreakdown]:
        return {arch: self.cost(arch, s) for arch in ARCHS}

    # ---- thresholds ------------------------------------------------------ #
    def efficiency_threshold(self, arch: str, s: Scenario) -> float:
        """Volume at which variable cost equals fixed cost (fixed = 50% of the bill)."""
        return self.fixed(arch, s) / self.variable_per_query(arch, s)

    def crossover(self, x: str, y: str, s: Scenario, tco: bool = False) -> Optional[float]:
        """Volume at which X and Y cost the same (steps cancel out). None if no positive crossover."""
        fx, fy = self.fixed(x, s), self.fixed(y, s)
        if tco:
            fte = self.a["people"]["fte_loaded_eur_month"]
            fx += self.ops_fte(x, s) * fte + self.build_amortized(x, s)
            fy += self.ops_fte(y, s) * fte + self.build_amortized(y, s)
        vx, vy = self.variable_per_query(x, s), self.variable_per_query(y, s)
        if abs(vx - vy) < 1e-12:
            return None
        q = (fy - fx) / (vx - vy)
        return q if q > 0 else None

    def value_per_query(self) -> float:
        """Realised ('hard') value per incoming query."""
        v = self.a["value"]
        gross = v["minutes_saved_per_resolved_query"] / 60 * v["loaded_hourly_cost_eur"]
        return gross * v["automation_rate"] * v["realization_rate"]

    def roi_breakeven(self, arch: str, s: Scenario) -> Optional[float]:
        margin = self.value_per_query() - self.variable_per_query(arch, s)
        if margin <= 0:
            return None
        c = self.cost(arch, replace(s, queries=0))
        return (c.cloud_fixed + c.ops + c.build_amortized) / margin

    def payback_months(self, arch: str, s: Scenario) -> Optional[float]:
        c = self.cost(arch, replace(s, include_build=False))
        net = s.queries * self.value_per_query() - c.tco
        if net <= 0:
            return None
        return self.build_one_off(arch, s) / net

    def saas_breakeven_users(self, arch: str, s: Scenario) -> Optional[float]:
        saas = self.a["saas"]
        margin = saas["seat_eur_month"] - saas["queries_per_user_month"] * self.variable_per_query(arch, s)
        if margin <= 0:
            return None
        c = self.cost(arch, replace(s, queries=0))
        return (c.cloud_fixed + c.ops + c.build_amortized) / margin

    def slm_breakeven_queries(self) -> float:
        cfg = self.a["self_hosted_slm"]
        return cfg["gpu_nodes_fixed_eur_month"] / cfg["ai_eur_per_query_saved"]

    # ---- recommendation -------------------------------------------------- #
    def recommend(self, s: Scenario, needs_gpu_or_portability: bool = False) -> Dict:
        costs = self.all_costs(s)
        ranking = sorted(costs.values(), key=lambda c: c.tco)
        best = ranking[0]
        reasons: List[str] = []
        if needs_gpu_or_portability:
            reasons.append(
                "Non-economic requirement (GPU / self-hosted model, multi-cloud portability or "
                "on-premises sovereignty): C is the option by design; cost becomes secondary."
            )
            best = costs["C"]
        else:
            runner = ranking[1]
            gap = (runner.tco - best.tco) / best.tco
            reasons.append(
                f"{ARCH_SHORT[best.arch]} minimises monthly TCO ({money(best.tco)}); "
                f"the runner-up ({ARCH_SHORT[runner.arch]}) costs {fmt_num(gap * 100, 1)}% more."
            )
            if gap < 0.10:
                reasons.append(
                    "Gap below 10%: decide on non-economic criteria (team skills, native governance, "
                    "time-to-market, lock-in)."
                )
        if best.fixed_share > 0.5:
            reasons.append(
                f"Fixed cost is {fmt_num(best.fixed_share * 100)}% of the cloud bill: infrastructure dominates AI. "
                "Prioritise adding use cases on the same foundation, or lower the security profile if risk allows."
            )
        return {"best": best.arch, "ranking": [c.arch for c in ranking], "reasons": reasons, "costs": costs}


# --------------------------------------------------------------------------- #
# Markdown tables for the report
# --------------------------------------------------------------------------- #
def md_table(headers: List[str], rows: Iterable[List[str]], align: Optional[List[str]] = None) -> str:
    align = align or ["left"] + ["right"] * (len(headers) - 1)
    sep = {"left": ":---", "right": "---:", "center": ":---:"}
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep[a] for a in align) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def _fmt_q(q: Optional[float]) -> str:
    if q is None:
        return "No crossover"
    if q > 50_000_000:
        return "> 50 M"
    return queries_label(round(q, -3) if q >= 10_000 else round(q, -2))


def crossover_label(m: FinOpsModel, x: str, y: str, s: Scenario, tco: bool) -> str:
    q = m.crossover(x, y, s, tco=tco)
    if q is not None:
        return _fmt_q(q)
    probe = replace(s, queries=1_000)
    cx, cy = m.cost(x, probe), m.cost(y, probe)
    vx, vy = (cx.tco, cy.tco) if tco else (cx.cloud_total, cy.cloud_total)
    return f"Always {x}" if vx <= vy else f"Always {y}"


def table_reference(m: FinOpsModel) -> str:
    s1 = Scenario(queries=1000, include_build=False)
    s25 = Scenario(queries=25000, include_build=False)
    c1, c25 = m.all_costs(s1), m.all_costs(s25)
    base = c1["D"].cloud_total
    rows = [
        ["Monthly cloud bill @ 1,000 queries/month"] + [money(c1[a].cloud_total) for a in ARCHS],
        ["Cost per query @ 1,000 queries/month"] + [money(c1[a].cloud_per_query) for a in ARCHS],
        ["Fixed-cost share @ 1,000 queries/month"] + [f"{fmt_num(c1[a].fixed_share * 100, 1)}%" for a in ARCHS],
        ["Monthly cloud bill @ 25,000 queries/month"] + [money(c25[a].cloud_total) for a in ARCHS],
        ["Cost per query @ 25,000 queries/month"] + [money(c25[a].cloud_per_query) for a in ARCHS],
        ["Annual saving vs. D @ 1,000 queries/month"]
        + [
            "Baseline"
            if a == "D"
            else f"{money((base - c1[a].cloud_total) * 12)} (−{fmt_num((1 - c1[a].cloud_total / base) * 100, 1)}%)"
            for a in ARCHS
        ],
        ["Estimated operations effort (FTE, 1 agent)"] + [fmt_num(m.ops_fte(a, s1), 2) for a in ARCHS],
        ["Governance, CI/CD evaluation, multi-agent", "Custom code", "Native and unified", "Self-managed on K8s", "Manual + APIM"],
    ]
    return md_table(["KPI (P3 Regulated, standard query, Spain Central)"] + [ARCH_SHORT[a] for a in ARCHS], rows)


VOLUMES = [1_000, 3_000, 10_000, 25_000, 50_000, 100_000, 250_000, 1_000_000, 5_000_000]


def table_volume_matrix(m: FinOpsModel, profile: str = "P3") -> str:
    rows = []
    for q in VOLUMES:
        c = m.all_costs(Scenario(queries=q, profile=profile, include_build=False))
        cheapest = min(ARCHS, key=lambda a: c[a].cloud_total)
        cells = []
        for a in ARCHS:
            cell = f"{money(c[a].cloud_total)}<br>{money(c[a].cloud_per_query)} per query"
            cells.append(f"**{cell}**" if a == cheapest else cell)
        rows.append([queries_label(q)] + cells)
    return md_table(["Queries/month"] + [ARCH_SHORT[a] for a in ARCHS], rows)


def chart_unit_cost(m: FinOpsModel) -> str:
    vols = [3_000, 10_000, 25_000, 50_000, 100_000, 250_000, 1_000_000]
    values = [m.cost("B", Scenario(queries=q, include_build=False)).cloud_per_query * 100 for q in vols]
    labels = ", ".join(f'"{queries_label(q)}"' for q in vols)
    top = int(max(values) // 5 + 1) * 5
    return "\n".join(
        [
            "```mermaid",
            "xychart-beta",
            '    title "Architecture B (P3, Spain Central): cloud cost per query in euro cents"',
            f"    x-axis [{labels}]",
            f'    y-axis "EUR cents per query" 0 --> {top}',
            "    bar [" + ", ".join(f"{v:.1f}" for v in values) + "]",
            "```",
        ]
    )


def chart_pilot(m: FinOpsModel) -> str:
    c = m.all_costs(Scenario(queries=1000, include_build=False))
    top = int(max(x.cloud_total for x in c.values()) // 500 + 1) * 500
    return "\n".join(
        [
            "```mermaid",
            "xychart-beta",
            '    title "Monthly cloud bill at 1,000 queries/month (P3, Spain Central, EUR)"',
            '    x-axis ["A Serverless", "B Foundry", "C AKS", "D ACA+SB+APIM"]',
            f'    y-axis "EUR/month" 0 --> {top}',
            "    bar [" + ", ".join(str(round(c[a].cloud_total)) for a in ARCHS) + "]",
            "```",
        ]
    )


def table_profiles(m: FinOpsModel) -> str:
    rows = []
    for a in ARCHS:
        fixed = [m.fixed(a, Scenario(queries=0, profile=p)) for p in ("P1", "P2", "P3")]
        thresholds = [
            queries_label(round(m.efficiency_threshold(a, Scenario(queries=0, profile=p)), -2)) for p in ("P1", "P2", "P3")
        ]
        rows.append([ARCH_SHORT[a]] + [money(f) for f in fixed] + thresholds)
    return md_table(
        [
            "Architecture",
            "Fixed P1 Essential",
            "Fixed P2 Standard",
            "Fixed P3 Regulated",
            "Efficiency threshold P1",
            "Efficiency threshold P2",
            "Efficiency threshold P3",
        ],
        rows,
    )


def table_crossovers(m: FinOpsModel) -> str:
    rows = []
    for x, y in [("A", "B"), ("B", "C"), ("A", "C"), ("B", "D"), ("C", "D")]:
        s = Scenario(queries=0, profile="P3")
        rows.append(
            [
                f"{x} ↔ {y}",
                crossover_label(m, x, y, s, tco=False),
                crossover_label(m, x, y, s, tco=True),
                crossover_label(m, x, y, replace(s, k8s_team=True), tco=True) if "C" in (x, y) else "—",
                crossover_label(m, x, y, replace(s, shared_integration=True), tco=True) if "D" in (x, y) else "—",
            ]
        )
    return md_table(
        [
            "Pair",
            "Crossover, cloud bill only",
            "Crossover, TCO (cloud + operations + build)",
            "Crossover, TCO with an amortised K8s team",
            "Crossover, TCO with shared corporate APIM/Service Bus",
        ],
        rows,
    )


def table_agents(m: FinOpsModel, queries: int = 10_000, profile: str = "P2") -> str:
    rows = []
    for n in (1, 2, 3, 4, 6, 8, 12):
        c = m.all_costs(Scenario(queries=queries, profile=profile, agents=n))
        best = min(ARCHS, key=lambda a: c[a].tco)
        rows.append([str(n)] + [f"**{money(c[a].tco)}**" if a == best else money(c[a].tco) for a in ARCHS])
    return md_table(["Agents / use cases"] + [f"TCO {ARCH_SHORT[a]}" for a in ARCHS], rows)


def table_query_profiles(m: FinOpsModel) -> str:
    rows = []
    for qp in ("light", "standard", "agentic"):
        for opt in ("none", "routing_and_cache"):
            s25 = Scenario(queries=25_000, query_profile=qp, optimization=opt, include_build=False)
            s1m = replace(s25, queries=1_000_000)
            b25, b1m = m.cost("B", s25), m.cost("B", s1m)
            ai_share = s1m.queries * m.ai_per_query(s1m) / b1m.cloud_total
            rows.append(
                [
                    m.a["query_profiles"][qp]["name"],
                    "Model router + semantic cache" if opt != "none" else "Not optimised",
                    money(m.ai_per_query(s25)),
                    money(b25.cloud_per_query),
                    money(b1m.cloud_per_query),
                    money(b1m.cloud_total),
                    f"{fmt_num(ai_share * 100)}%",
                ]
            )
    return md_table(
        [
            "Query profile",
            "AI optimisation",
            "AI cost / query",
            "B cost / query @ 25 k",
            "B cost / query @ 1 M",
            "B monthly bill @ 1 M",
            "AI share @ 1 M",
        ],
        rows,
    )


# (segment, user range, representative users, queries/month, profile, agents)
SEGMENTS = [
    ("XS · Start-up / micro", "< 50", 30, 1_000, "P1", 1),
    ("S · Small business", "50 – 250", 150, 5_000, "P1", 2),
    ("M · Mid-size company", "250 – 2,000", 1_000, 25_000, "P2", 3),
    ("L · Large enterprise", "2,000 – 20,000", 8_000, 120_000, "P3", 6),
    ("XL · Global corporation / B2C app", "> 20,000", 50_000, 1_500_000, "P3", 10),
]


def table_segments(m: FinOpsModel) -> str:
    seat = m.a["saas"]["seat_eur_month"]
    rows = []
    for name, users, rep_users, q, profile, agents in SEGMENTS:
        extra = 2 if name.startswith("XL") else 0
        rec = m.recommend(Scenario(queries=q, profile=profile, agents=agents, extra_cells=extra))
        best = rec["costs"][rec["best"]]
        rows.append(
            [
                name,
                users,
                queries_label(q),
                f"{profile} · {agents} agent{'s' if agents > 1 else ''}" + (" · 3 regions" if extra else ""),
                ARCH_SHORT[rec["best"]],
                money(best.cloud_total),
                money(best.cloud_per_query),
                money(best.tco),
                f"{money(rep_users * seat)} ({fmt_num(rep_users)} users)",
                "SaaS / low-code" if rep_users * seat < best.tco else "Own platform",
            ]
        )
    return md_table(
        [
            "Segment",
            "Users",
            "Queries/month",
            "Profile · agents",
            "Lowest TCO (model)",
            "Cloud/month",
            "Cloud/query",
            "TCO/month",
            "Equivalent per-seat SaaS",
            "Economic verdict",
        ],
        rows,
    )


def table_roadmap(m: FinOpsModel) -> str:
    stages = [
        ("Milestone 1 · Pilot (1 use case)", 3_000, 1),
        ("Milestone 2 · 3 use cases", 15_000, 3),
        ("Milestone 3 · 6 use cases", 45_000, 6),
        ("Milestone 4 · Company-wide assistant", 120_000, 10),
    ]
    rows = []
    vpq = m.value_per_query()
    for name, q, agents in stages:
        s = Scenario(queries=q, profile="P3", agents=agents)
        c = m.cost("B", s)
        value = q * vpq
        payback = m.payback_months("B", s)
        rows.append(
            [
                name,
                queries_label(q),
                money(c.cloud_total),
                money(c.cloud_per_query),
                money(c.tco),
                money(value),
                money(value - c.tco),
                f"{fmt_num(value / c.tco, 1)}x",
                f"{fmt_num(payback, 1)} months" if payback else "Not recovered",
            ]
        )
    return md_table(
        [
            "Stage (architecture B, P3)",
            "Queries/month",
            "Cloud/month",
            "Cloud/query",
            "TCO/month",
            "Realised value/month",
            "Net benefit/month (after amortisation)",
            "Value/TCO",
            "Payback of initial investment",
        ],
        rows,
    )


def table_multi_region(m: FinOpsModel) -> str:
    stages = [
        ("Stage 1 · Pilot", "Spain Central", 3_000, 0, 0),
        ("Stage 2 · Multi-department", "Spain Central", 25_000, 0, 0),
        ("Stage 3 · High availability", "Spain Central + warm DR in France Central", 45_000, 1, 0),
        ("Stage 4 · EU + US", "Spain Central + East US 2 (2 active sovereign cells)", 150_000, 0, 1),
        ("Stage 5 · EU + US with DR", "2 cells + DR (France Central, Central US)", 500_000, 2, 1),
    ]
    rows = []
    for name, topo, q, dr, cells in stages:
        c = m.cost("B", Scenario(queries=q, profile="P3", dr_regions=dr, extra_cells=cells, include_build=False))
        rows.append([name, topo, queries_label(q), money(c.cloud_fixed), money(c.cloud_total), money(c.cloud_per_query)])
    return md_table(
        ["Stage", "Topology", "Queries/month", "Fixed cloud", "Total cloud/month", "Cost/query"],
        rows,
        ["left", "left", "right", "right", "right", "right"],
    )


def table_region_index(m: FinOpsModel) -> str:
    rows = []
    for key, r in m.regions().items():
        rows.append(
            [
                f"{r['name']} (`{key}`)",
                r["geo"],
                fmt_num(r["index"], 2),
                r["paired"],
                r["data_zone"],
            ]
        )
    return md_table(
        ["Region", "Geography", "Infra price index (Spain Central = 1.00)", "Paired region / DR option", "AI data zone"],
        rows,
        ["left", "left", "right", "left", "left"],
    )


def table_region_costs(m: FinOpsModel) -> str:
    rows = []
    for key, r in m.regions().items():
        b_pilot = m.cost("B", Scenario(queries=1_000, region=key, include_build=False))
        b_mid = m.cost("B", Scenario(queries=25_000, region=key, profile="P2", include_build=False))
        a_small = m.cost("A", Scenario(queries=5_000, region=key, profile="P1", include_build=False))
        c_big = m.cost("C", Scenario(queries=1_000_000, region=key, include_build=False))
        rows.append(
            [
                r["name"],
                money(a_small.cloud_total),
                money(b_pilot.cloud_total),
                money(b_mid.cloud_total),
                money(c_big.cloud_total),
            ]
        )
    return md_table(
        [
            "Region",
            "A · P1 · 5 k queries",
            "B · P3 · 1 k queries (pilot)",
            "B · P2 · 25 k queries",
            "C · P3 · 1 M queries",
        ],
        rows,
    )


def table_saas(m: FinOpsModel) -> str:
    saas = m.a["saas"]
    rows = []
    for users in (25, 50, 100, 250, 1_000, 5_000, 20_000):
        q = users * saas["queries_per_user_month"]
        profile = "P1" if users <= 100 else ("P2" if users <= 1_000 else "P3")
        b = m.cost("B", Scenario(queries=q, profile=profile, agents=2))
        lic = users * saas["seat_eur_month"]
        rows.append(
            [fmt_num(users), queries_label(q), profile, money(lic), money(b.tco), "Platform" if b.tco < lic else "SaaS"]
        )
    return md_table(
        ["Users", "Queries/month", "Profile", "Per-seat SaaS/month", "Platform B TCO/month", "Cheaper"],
        rows,
        ["right", "right", "center", "right", "right", "center"],
    )


def table_breakevens(m: FinOpsModel) -> str:
    rows = []
    for p in ("P1", "P2", "P3"):
        s = Scenario(queries=0, profile=p)
        rows.append(
            [p]
            + [_fmt_q(m.roi_breakeven(a, s)) for a in ARCHS]
            + [fmt_num(round(m.saas_breakeven_users("B", s))) + " users"]
        )
    return md_table(["Profile"] + [f"ROI break-even {a}" for a in ARCHS] + ["Break-even vs. SaaS (B)"], rows)


def table_fte_sensitivity(m: FinOpsModel) -> str:
    """How the loaded cost of engineers shifts the A/B and B/C decisions."""
    rows = []
    original = m.a["people"]["fte_loaded_eur_month"]
    for label, fte in [
        ("Southern / Eastern Europe", 4_500),
        ("Model default", original),
        ("Northern / Western Europe", 9_000),
        ("United States", 11_500),
    ]:
        m.a["people"]["fte_loaded_eur_month"] = fte
        threshold = next(
            (
                n
                for n in range(1, 30)
                if m.cost("B", Scenario(queries=10_000, profile="P2", agents=n)).tco
                < m.cost("A", Scenario(queries=10_000, profile="P2", agents=n)).tco
            ),
            None,
        )
        s = Scenario(queries=0, profile="P3")
        rows.append(
            [
                label,
                money(fte),
                f"{threshold} agents" if threshold else "> 30",
                crossover_label(m, "B", "C", s, tco=True),
                crossover_label(m, "B", "C", replace(s, k8s_team=True), tco=True),
            ]
        )
    m.a["people"]["fte_loaded_eur_month"] = original
    return md_table(
        [
            "Labour market",
            "Loaded FTE cost/month",
            "B beats A from (P2, 10 k queries)",
            "B ↔ C TCO crossover (P3)",
            "B ↔ C with amortised K8s team",
        ],
        rows,
    )


GENERATORS = {
    "table-fte-sensitivity": table_fte_sensitivity,
    "table-reference": table_reference,
    "table-volume-matrix": table_volume_matrix,
    "chart-unit-cost": chart_unit_cost,
    "chart-pilot": chart_pilot,
    "table-profiles": table_profiles,
    "table-crossovers": table_crossovers,
    "table-agents": table_agents,
    "table-query-profiles": table_query_profiles,
    "table-segments": table_segments,
    "table-roadmap": table_roadmap,
    "table-multi-region": table_multi_region,
    "table-region-index": table_region_index,
    "table-region-costs": table_region_costs,
    "table-saas": table_saas,
    "table-breakevens": table_breakevens,
}


def scalar_values(m: FinOpsModel) -> Dict[str, str]:
    """Inline values quoted in prose (<!-- val:name -->...<!-- /val --> markers)."""
    p3 = Scenario(queries=0, profile="P3")
    us = m.cost("B", Scenario(queries=1000, region="eastus2", include_build=False)).cloud_total
    es = m.cost("B", Scenario(queries=1000, include_build=False)).cloud_total
    return {
        "value-per-query": money(m.value_per_query(), 2),
        "slm-breakeven": _fmt_q(m.slm_breakeven_queries()),
        "saas-breakeven-p1": fmt_num(round(m.saas_breakeven_users("B", replace(p3, profile="P1")))),
        "saas-breakeven-p3": fmt_num(round(m.saas_breakeven_users("B", p3))),
        "bc-cloud": _fmt_q(m.crossover("B", "C", p3)),
        "bc-tco": _fmt_q(m.crossover("B", "C", p3, tco=True)),
        "bc-tco-team": crossover_label(m, "B", "C", replace(p3, k8s_team=True), tco=True),
        "usd-per-eur": fmt_num(m.a["currency"]["usd_per_eur"], 2),
        "b-pilot-es": money(es),
        "b-pilot-us": money(us),
        "us-vs-es-pct": fmt_num((1 - us / es) * 100, 0),
    }


def update_docs(m: FinOpsModel, files: Iterable[Path]) -> List[Path]:
    changed = []
    values = scalar_values(m)
    for path in files:
        text = path.read_text(encoding="utf-8")
        original = text
        for key, gen in GENERATORS.items():
            pattern = re.compile(rf"(<!-- BEGIN:{key} -->\n).*?(<!-- END:{key} -->)", re.S)
            text = pattern.sub(lambda mt, g=gen: mt.group(1) + g(m) + "\n" + mt.group(2), text)
        for key, val in values.items():
            pattern = re.compile(rf"(<!-- val:{key} -->).*?(<!-- /val -->)")
            text = pattern.sub(lambda mt, v=val: mt.group(1) + v + mt.group(2), text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(path)
    return changed


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def print_report(m: FinOpsModel, s: Scenario, gpu: bool) -> None:
    rec = m.recommend(s, needs_gpu_or_portability=gpu)
    region = m.regions()[s.region]["name"]
    print(
        f"\nScenario: {queries_label(s.queries)} queries/month · profile {s.profile} "
        f"({m.a['profiles'][s.profile]['name']}) · region {region} · '{s.query_profile}' queries · "
        f"AI deployment '{m.deployment(s)}' · optimisation '{s.optimization}' · {s.agents} agent(s) · "
        f"DR regions {s.dr_regions} · extra cells {s.extra_cells}"
    )
    print(f"Figures in EUR / USD (1 EUR = {m.a['currency']['usd_per_eur']} USD)\n")
    headers = ["Architecture", "Fixed", "Variable", "Steps", "Cloud", "Per query", "Operations", "Build", "TCO"]
    rows = []
    for a in rec["ranking"]:
        c = rec["costs"][a]
        rows.append(
            [
                ARCH_SHORT[a],
                money(c.cloud_fixed),
                money(c.cloud_variable),
                money(c.steps),
                money(c.cloud_total),
                money(c.cloud_per_query),
                money(c.ops),
                money(c.build_amortized),
                money(c.tco),
            ]
        )
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    for line in [headers] + rows:
        print("  ".join(str(v).rjust(w) if i else str(v).ljust(w) for i, (v, w) in enumerate(zip(line, widths))))
    print(f"\nRecommendation: {ARCH_SHORT[rec['best']]}")
    for r in rec["reasons"]:
        print(f"  - {r}")
    print(f"\nRealised value per query (assumptions): {money(m.value_per_query(), 2)}")
    print(f"ROI break-even for {rec['best']}: {_fmt_q(m.roi_breakeven(rec['best'], s))} queries/month")
    pb = m.payback_months(rec["best"], s)
    print(f"Payback of the initial build: {fmt_num(pb, 1) + ' months' if pb else 'not recovered at this volume'}")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--assumptions", type=Path, default=DEFAULT_ASSUMPTIONS)
    p.add_argument("--queries", type=float, default=25_000, help="Production queries per month")
    p.add_argument("--profile", choices=["P1", "P2", "P3"], default="P3")
    p.add_argument("--region", default=BASELINE_REGION, help="Azure region name, e.g. westeurope, eastus2")
    p.add_argument("--query-profile", choices=["light", "standard", "agentic"], default="standard")
    p.add_argument("--ai-deployment", choices=["global", "data_zone", "regional"], default=None)
    p.add_argument("--optimization", choices=["none", "routing", "routing_and_cache"], default="none")
    p.add_argument("--agents", type=int, default=1)
    p.add_argument("--dr-regions", type=int, default=0)
    p.add_argument("--extra-cells", type=int, default=0)
    p.add_argument("--k8s-team", action="store_true", help="An amortised Kubernetes platform team already exists")
    p.add_argument("--shared-integration", action="store_true", help="Corporate APIM and Service Bus Premium already exist")
    p.add_argument("--shared-edge", action="store_true", help="Corporate Front Door/WAF already exists")
    p.add_argument("--no-build", action="store_true", help="Exclude build-cost amortisation")
    p.add_argument("--needs-gpu", action="store_true", help="GPU / self-hosted model or multi-cloud portability requirement")
    p.add_argument("--json", action="store_true", help="JSON output (EUR and USD)")
    p.add_argument("--list-regions", action="store_true")
    p.add_argument("--update-docs", action="store_true", help="Regenerate marked tables in README.md and docs/")
    args = p.parse_args(argv)

    m = FinOpsModel.load(args.assumptions)
    if args.list_regions:
        for key, r in m.regions().items():
            print(f"{key:20} {r['index']:.2f}  {r['geo']:16} {r['name']}")
        return 0
    if args.update_docs:
        files = [REPO / "README.md", *sorted((REPO / "docs").glob("*.md"))]
        changed = update_docs(m, [f for f in files if f.exists()])
        print("Updated:" if changed else "No changes.", *[str(c.relative_to(REPO)) for c in changed])
        return 0

    s = Scenario(
        queries=args.queries,
        profile=args.profile,
        query_profile=args.query_profile,
        optimization=args.optimization,
        agents=args.agents,
        region=args.region,
        ai_deployment=args.ai_deployment,
        dr_regions=args.dr_regions,
        extra_cells=args.extra_cells,
        k8s_team=args.k8s_team,
        shared_integration=args.shared_integration,
        shared_edge=args.shared_edge,
        include_build=not args.no_build,
    )
    m.region_index(s.region)  # validate early
    if args.json:
        rec = m.recommend(s, needs_gpu_or_portability=args.needs_gpu)
        fx = m.a["currency"]["usd_per_eur"]

        def both(v: float, nd: int = 2) -> Dict[str, float]:
            return {"eur": round(v, nd), "usd": round(v * fx, nd)}

        out = {
            "scenario": s.__dict__,
            "best": rec["best"],
            "ranking": rec["ranking"],
            "reasons": rec["reasons"],
            "costs": {
                a: {
                    "cloud_fixed": both(c.cloud_fixed),
                    "cloud_variable": both(c.cloud_variable),
                    "steps": both(c.steps),
                    "cloud_total": both(c.cloud_total),
                    "cloud_per_query": both(c.cloud_per_query, 5),
                    "ops": both(c.ops),
                    "build_amortized": both(c.build_amortized),
                    "tco": both(c.tco),
                }
                for a, c in rec["costs"].items()
            },
        }
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print_report(m, s, args.needs_gpu)
    return 0


if __name__ == "__main__":
    sys.exit(main())
