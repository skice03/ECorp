"""Week 3, round 2 – checks on the team's revised inputs (Parametrii noi.tura2).

New in round 2: realized_displacement, implementation_cost (= license x integration_multiplier),
demand_response and per-scenario financial settings. Group rows are unchanged from round 1.
Run (from the data-analysis folder): python3 scripts/week3_checks_round2.py data/team/round2 data/team/round1 outputs
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

t2, t1, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
p = pd.read_csv(t2 / "all_parameters.csv", dtype={"scope": str})
p1 = pd.read_csv(t1 / "all_parameters.csv", dtype={"scope": str})
sc = pd.read_csv(t2 / "scenarios.csv")

# observed (source) – see week3_checks.py / week3_checks_team.py
AI_CUTS_2026_ANNUALISED = 145_681   # Challenger Jan-Oct 2026 AI-cited cuts (121,401) x 12/10
LICENSE_BAND = (252, 360)           # Microsoft 365 Copilot list price, USD/user/yr
ATD_TRAINING = (846, 1254)          # ATD direct learning spend per employee, 2025 / 2024
BTOS_SUPPLEMENT, BTOS_REPLACED, BTOS_NEW = 0.44, 0.10, 0.11  # share of AI-using firms (Census BTOS supplement)

print("== WHAT CHANGED VS ROUND 1 ==")
k = ["key", "scope"]
m = p.merge(p1, on=k, how="outer", suffixes=("", "_r1"), indicator=True)
added = m[m._merge == "left_only"].key.tolist()
changed = m[(m._merge == "both") & ~((m.value == m.value_r1) | (m.value.isna() & m.value_r1.isna()))].key.tolist()
print("added keys:", added, "| changed values:", changed)
grp_changed = m[(m.scope != "global") & (m._merge == "both") & (m.value != m.value_r1)]
print("group rows changed:", len(grp_changed))
for key in ["us_firm_adoption_context", "benefit_loading"]:
    r = p[p.key == key].iloc[0]; print(f"  still: {key} class={r['class']} status={r.status}")
print("scenario columns:", list(sc.columns))

g = p[p.scope != "global"].pivot(index="scope", columns="key", values="value")
g["exp_alpha"] = p[p.scope != "global"].pivot(index="scope", columns="key", values="low")["exposure"]
g["exp_gamma"] = p[p.scope != "global"].pivot(index="scope", columns="key", values="high")["exposure"]
g["exp_beta"] = g["exposure"]
emp = g.employment; E = emp.sum()
meas = {"human_alpha": "exp_alpha", "human_beta": "exp_beta", "human_gamma": "exp_gamma"}

print("\n== CHECK A: implementation cost = license x multiplier ==")
ok = (sc.license_annual_proxy * sc.integration_multiplier - sc.implementation_cost).abs().max()
print("max |license*multiplier - implementation_cost|:", ok)
print(f"license column within observed band {LICENSE_BAND} for S1-S3:",
      sc.loc[sc.id != "S0", "license_annual_proxy"].between(*LICENSE_BAND).all())
print(f"training within ATD range {ATD_TRAINING} for S1-S3:", sc.loc[sc.id != "S0", "training_proxy"].between(*ATD_TRAINING).all())

print("\n== CHECK B: displacement vs observed ==")
rows = []
for s in sc.itertuples():
    e = g[meas[s.exposure_measure]]
    freed = float((emp * e).sum()) * s.deployment_share * s.time_saved           # job-equivalents
    value = float((emp * e * g.labor_cost_proxy).sum()) * s.deployment_share * s.time_saved
    slack = freed * (1 - s.demand_response)                                      # freed capacity not redeployed
    displaced = E * s.realized_displacement                                       # jobs per year
    users = E * s.deployment_share                                                # reading: AI users = deployment share x jobs
    cost = users * s.implementation_cost
    rows.append(dict(id=s.id, displacement=s.realized_displacement, displaced_per_yr_M=displaced / 1e6,
                     x_observed=displaced / AI_CUTS_2026_ANNUALISED if displaced else 0,
                     freed_M=freed / 1e6, demand_response=s.demand_response, slack_M=slack / 1e6,
                     years_until_displaced_exceeds_slack=(slack / displaced) if displaced else np.nan,
                     ai_users_M=users / 1e6, impl_cost_bn=cost / 1e9, freed_value_bn=value / 1e9,
                     value_per_user=value / users if users else np.nan, impl_cost_per_user=s.implementation_cost,
                     value_to_cost=(value / cost) if cost else np.nan,
                     training_bn_if_displaced=displaced * s.training_proxy / 1e9))
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False))
R.to_csv(out / "week3_round2_scenarios.csv", index=False)
print(f"observed 2026 AI-cited cut pace: {AI_CUTS_2026_ANNUALISED:,} = {AI_CUTS_2026_ANNUALISED/E:.3%} of jobs/yr")

print("\n== CHECK C: demand response vs observed use pattern ==")
print(f"BTOS: of AI-using firms, {BTOS_SUPPLEMENT:.0%} say AI supplemented existing work, {BTOS_REPLACED:.0%} replaced a task, {BTOS_NEW:.0%} added a new task")
print("scenario demand_response:", dict(zip(sc.id, sc.demand_response)))

print("\n== CHECK D: one-at-a-time sensitivity of S2 implementation cost and displacement ==")
s2 = sc.set_index("id").loc["S2"]
v2 = R.set_index("id").loc["S2"]
for mult in (1, 2, 3):
    c = E * s2.deployment_share * s2.license_annual_proxy * mult
    print(f"  integration x{mult}: cost ${c/1e9:,.1f}bn vs freed value ${v2.freed_value_bn:,.0f}bn ({v2.freed_value_bn*1e9/c:.1f}x)")
for d in (0.001, 0.005, 0.01):
    print(f"  displacement {d:.1%}: {E*d/1e6:.2f}M jobs/yr; slack lasts {v2.slack_M*1e6/(E*d):.1f} yrs")
