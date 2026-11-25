"""Week 3 (rerun) – compare the TEAM's baseline inputs with observed data.

Inputs:  team/all_parameters.csv, team/scenarios.csv (Enache parameter file + scenario design)
         out/analysis_table_week2.csv (for coverage and wage checks)
Observed values are typed in below with their source (read 25 Nov 2026).
Run (from the data-analysis folder): python3 scripts/week3_checks_team.py data/team/round1 outputs
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

team, out = Path(sys.argv[1]), Path(sys.argv[2])
p = pd.read_csv(team / "all_parameters.csv", dtype={"scope": str})
sc = pd.read_csv(team / "scenarios.csv")
an = pd.read_csv(out / "analysis_table_week2.csv")

# ---------------- observed (source) ----------------
BLS_EP_TOTAL_2022 = 164_482_600      # BLS EP 2022-32 Table 1.1, total employment 2022
ECEC_WAGE_SHARE_PRIVATE = 0.700      # BLS ECEC Jun 2026, private industry, all workers
ECEC_WAGE_SHARE_PRIVATE_FT = 0.685   # BLS ECEC Jun 2026, private industry, full-time
ECEC_TOTAL_COMP_HOURLY = 46.89       # BLS ECEC Jun 2026, private industry total comp per hour worked
OEWS_2025_MEAN_HOURLY = 33.54        # BLS OEWS May 2025, U.S. average hourly wage
OEWS_2021_MEAN_ANNUAL = 58_260       # OEWS May 2021 national file (bundled)
BTOS_EMP_AT_AI_FIRMS = 0.32          # Census CES-WP-26-25: firms using AI, employment-weighted
BTOS_EMP_WORKER_TASK_USE = 0.41      # Census CES-WP-26-25: firms where workers use AI in tasks, employment-weighted
AI_CUTS_CUM_TO_OCT26 = 193_226       # Challenger, AI-cited announced cuts 2023-Oct 2026 (see week3_checks.py)
AEI_COMPUTER_MATH_SHARE = 0.35       # Anthropic Economic Index Mar 2026: Computer & Math share of Claude.ai conversations
RCT_TIME = (0.123, 0.40)             # time reduction range from the three trials (see week3_checks.py)

g = p[p.scope != "global"].pivot(index="scope", columns="key", values="value")
lo = p[p.scope != "global"].pivot(index="scope", columns="key", values="low")["exposure"]
hi = p[p.scope != "global"].pivot(index="scope", columns="key", values="high")["exposure"]
g["exp_alpha"], g["exp_beta"], g["exp_gamma"] = lo, g["exposure"], hi
G = {r.key: r for r in p[p.scope == "global"].itertuples()}
emp = g.employment
E = emp.sum()

print("== FILE INTEGRITY ==")
print("groups:", len(g), "| employment sum:", f"{E:,.0f}", "| dataset_employment:", f"{G['dataset_employment'].value:,.0f}")
print("blank-by-design keys:", [k for k, r in G.items() if pd.isna(r.value)])
print("scenarios:\n", sc.to_string(index=False))

print("\n== CHECK 1: employment coverage ==")
print(f"team total {E/1e6:.2f}M vs BLS total 2022 {BLS_EP_TOTAL_2022/1e6:.2f}M -> {E/BLS_EP_TOTAL_2022:.1%} coverage")

print("\n== CHECK 2: labor cost ==")
team_cost = np.average(g.labor_cost_proxy, weights=emp)
print(f"team emp-weighted labor_cost_proxy: ${team_cost:,.0f}/yr (2022 wages x {G['benefit_loading'].value})")
oews25_loaded = OEWS_2025_MEAN_HOURLY * 2080 / ECEC_WAGE_SHARE_PRIVATE
ecec_annual = ECEC_TOTAL_COMP_HOURLY * 2080
print(f"observed: OEWS May 2025 mean wage x 2080 / 0.70 = ${oews25_loaded:,.0f}; ECEC Jun 2026 total comp x 2080 = ${ecec_annual:,.0f}")
print(f"team vs OEWS-2025 loaded: {team_cost/oews25_loaded-1:+.1%}; vs ECEC: {team_cost/ecec_annual-1:+.1%}")
print(f"wage growth OEWS mean 2021->2025: {OEWS_2025_MEAN_HOURLY*2080/OEWS_2021_MEAN_ANNUAL-1:+.1%}")
print(f"benefit loading observed range: 1/{ECEC_WAGE_SHARE_PRIVATE} = {1/ECEC_WAGE_SHARE_PRIVATE:.2f} to 1/{ECEC_WAGE_SHARE_PRIVATE_FT} = {1/ECEC_WAGE_SHARE_PRIVATE_FT:.2f}")
nowage = an[an.median_wage.isna()]
print(f"jobs with no wage (excluded from labor cost): {nowage.emp_2022_k.sum():,.1f}k in {len(nowage)} occupations")

print("\n== CHECK 3: scenarios -> freed capacity ==")
meas = {"human_alpha": "exp_alpha", "human_beta": "exp_beta", "human_gamma": "exp_gamma"}
rows = []
for s in sc.itertuples():
    e = g[meas[s.exposure_measure]]
    hours_share = float((emp * e).sum() / E) * s.deployment_share * s.time_saved
    jobs_eq = float((emp * e).sum()) * s.deployment_share * s.time_saved
    value = float((emp * e * g.labor_cost_proxy).sum()) * s.deployment_share * s.time_saved
    rows.append(dict(id=s.id, deploy=s.deployment_share, time_saved=s.time_saved, measure=s.exposure_measure,
                     exp_w=float((emp * e).sum() / E), share_labor_time=hours_share, job_equiv_M=jobs_eq / 1e6,
                     value_bn=value / 1e9, x_observed_ai_cuts=jobs_eq / AI_CUTS_CUM_TO_OCT26))
R = pd.DataFrame(rows)
print(R.round(4).to_string(index=False))
R.to_csv(out / "week3_team_scenarios.csv", index=False)
print(f"S3 / S1 freed capacity ratio: {R.loc[3,'job_equiv_M']/R.loc[1,'job_equiv_M']:.0f}x")

print("\n== CHECK 4: deployment_share vs observed adoption bounds ==")
for s in sc.itertuples():
    tag = ("within" if s.deployment_share <= BTOS_EMP_AT_AI_FIRMS else
           "above firm-use bound, within worker-task bound" if s.deployment_share <= BTOS_EMP_WORKER_TASK_USE else
           "above every observed bound")
    print(f"{s.id} deployment {s.deployment_share:.0%}: {tag} (32% emp at AI-using firms; 41% emp at firms where workers use AI in tasks)")

print("\n== CHECK 5: time_saved vs trials ==")
ts = G["time_saved"]
print(f"team {ts.value} [{ts.low}, {ts.high}] vs trials {RCT_TIME[0]:.3f}-{RCT_TIME[1]:.2f}")

print("\n== CHECK 6: where exposure says capacity is vs observed AI use ==")
s2 = emp * g.exp_beta
share = s2 / s2.sum()
print(f"Computer & math (15) share of S2 freed capacity: {share['15']:.1%} vs {AEI_COMPUTER_MATH_SHARE:.0%} of Claude.ai conversations")
print(f"Office & admin (43) share: {share['43']:.1%}; Sales (41): {share['41']:.1%}")

print("\n== CHECK 7: one-at-a-time sensitivity around S2 (freed job-equivalents, M) ==")
base = dict(d=0.3, t=0.25, m="exp_beta")
def je(d, t, m): return float((emp * g[m]).sum()) * d * t / 1e6
b = je(**base)
print(f"S2 base: {b:.2f}M")
for name, vals in [("deployment_share", [("d", 0.1), ("d", 0.6)]), ("time_saved", [("t", 0.12), ("t", 0.40)]),
                   ("exposure measure", [("m", "exp_alpha"), ("m", "exp_gamma")])]:
    out_ = []
    for k, v in vals:
        kw = dict(base); kw[k] = v; out_.append(je(**kw))
    print(f"  {name}: {out_[0]:.2f}M to {out_[1]:.2f}M (x{out_[1]/out_[0]:.1f})")
