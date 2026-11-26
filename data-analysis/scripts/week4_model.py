"""Week 4 – scenario runs, sensitivity analysis and external benchmarks.

Re-implements the team's calculator from the definitions in the round-2 parameter file
(Parametrii noi.tura2). The developers' own code was not available; rerun against it when it is.

Core (as defined by the team): freed task time = jobs x exposure x deployment_share x time_saved,
valued at labor_cost_proxy (2022 median wage x benefit loading).
Financial layer (team's handoff-only settings, applied here as stated):
  displaced jobs/yr = realized_displacement x jobs (allocated to groups by spare capacity)
  spare capacity    = freed x (1 - demand_response)
  implementation    = AI users x implementation_cost, AI users = deployment_share x jobs (Week 3 reading)
  training          = displaced jobs x training_proxy (paid in the year of displacement)
Horizon: 5 years, full deployment from year 1 (assumption; the files give no horizon).
Run (from the data-analysis folder): python3 scripts/week4_model.py data/team/round2 outputs
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

t2, out = Path(sys.argv[1]), Path(sys.argv[2])
P = pd.read_csv(t2 / "all_parameters.csv", dtype={"scope": str})
SC = pd.read_csv(t2 / "scenarios.csv")
H = 5

grp = P[P.scope != "global"]
G = grp.pivot(index="scope", columns="key", values="value")
G["human_alpha"] = grp.pivot(index="scope", columns="key", values="low")["exposure"]
G["human_gamma"] = grp.pivot(index="scope", columns="key", values="high")["exposure"]
G["human_beta"] = G["exposure"]
BL = float(P.loc[P.key == "benefit_loading", "value"].iloc[0])
G["wage"] = G.labor_cost_proxy / BL          # back out the 2022 median wage
E = G.employment.sum()

# observed benchmarks (source)
OBS_TIME_SAVED_SHARE = 0.0216    # RPS / FRED RPSGENAITSALL, Q1 2026: share of all work hours saved by genAI
OBS_AI_CUTS_PER_YR = 145_681     # Challenger, AI-cited announced cuts, Jan-Oct 2026 annualised
OBS_GENAI_WORK_USERS = 0.392     # RPS, Q2 2026: employed adults using genAI for work in past week


def run(deploy, time_saved, measure, displacement, demand, impl, training,
        loading=BL, wage_mult=1.0, cap=True, horizon=H, by_group=False):
    cost = G.wage * wage_mult * loading
    freed_g = G.employment * G[measure] * deploy * time_saved
    freed = freed_g.sum()
    value = (freed_g * cost).sum()
    spare_g = freed_g * (1 - demand)
    spare = spare_g.sum()
    share_g = spare_g / spare if spare > 0 else freed_g / freed if freed > 0 else freed_g * 0
    per_yr = E * displacement
    cum, prev, labor_sav, train_cost = [], 0.0, [], []
    for t in range(1, horizon + 1):
        c = per_yr * t
        if cap:
            c = min(c, spare)
        new = c - prev
        cum.append(c); prev = c
        labor_sav.append(float((share_g * c * cost).sum()))
        train_cost.append(new * training)
    users = E * deploy
    impl_yr = users * impl
    net = [ls - impl_yr - tc for ls, tc in zip(labor_sav, train_cost)]
    r = dict(freed_share=freed / E, freed_jobs_M=freed / 1e6, freed_value_bn=value / 1e9,
             redeployed_jobs_M=freed * demand / 1e6, spare_jobs_M=spare / 1e6,
             displaced_per_yr_M=per_yr / 1e6, displaced_cum_M=cum[-1] / 1e6,
             displaced_y1_M=cum[0] / 1e6, impl_bn_yr=impl_yr / 1e9,
             training_bn_total=sum(train_cost) / 1e9,
             labor_saving_y5_bn=labor_sav[-1] / 1e9, net_y1_bn=net[0] / 1e9, net_y5_bn=net[-1] / 1e9,
             net_cum_bn=sum(net) / 1e9)
    if by_group:
        r["groups"] = pd.DataFrame({"freed_jobs": freed_g, "displaced_cum": share_g * cum[-1],
                                    "employment": G.employment})
    return r


def scen(s, **kw):
    a = dict(deploy=s.deployment_share, time_saved=s.time_saved, measure=s.exposure_measure,
             displacement=s.realized_displacement, demand=s.demand_response,
             impl=s.implementation_cost, training=s.training_proxy)
    a.update(kw)
    return run(**a)


print("== 1. SCENARIO RUNS (as given, displacement capped at spare capacity) ==")
rows = []
for s in SC.itertuples():
    for cap in (True, False):
        r = scen(s, cap=cap); r.update(id=s.id, cap=cap); rows.append(r)
R = pd.DataFrame(rows)
cols = ["id", "cap", "freed_share", "freed_jobs_M", "freed_value_bn", "redeployed_jobs_M", "spare_jobs_M",
        "displaced_per_yr_M", "displaced_cum_M", "impl_bn_yr", "training_bn_total", "labor_saving_y5_bn",
        "net_y1_bn", "net_y5_bn", "net_cum_bn"]
pd.set_option("display.width", 250)
print(R[cols].round(3).to_string(index=False))
R[cols].to_csv(out / "week4_scenarios.csv", index=False)

print("\n== 2. S2 BY GROUP (capped) ==")
s2 = SC.set_index("id").loc["S2"]
rg = scen(s2, by_group=True)["groups"]
names = {"11": "Management", "13": "Business & financial", "15": "Computer & math", "17": "Architecture & engineering",
         "19": "Life & social science", "21": "Community & social service", "23": "Legal", "25": "Education & library",
         "27": "Arts, design & media", "29": "Healthcare practitioners", "31": "Healthcare support",
         "33": "Protective service", "35": "Food preparation & serving", "37": "Building & grounds cleaning",
         "39": "Personal care & service", "41": "Sales", "43": "Office & admin support", "45": "Farming, fishing & forestry",
         "47": "Construction & extraction", "49": "Installation & repair", "51": "Production", "53": "Transportation & moving"}
rg["group"] = [names[i] for i in rg.index]
rg["displaced_pct_of_group"] = rg.displaced_cum / rg.employment
rg = rg.sort_values("displaced_cum", ascending=False)
print(rg[["group", "freed_jobs", "displaced_cum", "displaced_pct_of_group"]].head(8).round(4).to_string())
rg.to_csv(out / "week4_s2_by_group.csv")

print("\n== 3. ONE-AT-A-TIME SENSITIVITY AROUND S2 (capped) ==")
base = scen(s2)
tests = [("deployment_share", "deploy", 0.1, 0.6), ("time_saved", "time_saved", 0.12, 0.40),
         ("exposure measure", "measure", "human_alpha", "human_gamma"),
         ("demand_response", "demand", 1.0, 0.0), ("realized_displacement", "displacement", 0.001, 0.01),
         ("integration multiplier", "impl", s2.license_annual_proxy * 1, s2.license_annual_proxy * 3),
         ("benefit_loading", "loading", 1.43, 1.46), ("wages 2022 -> uprated +19.7%", "wage_mult", 1.0, 1.197)]
S = []
for name, k, lo, hi in tests:
    a, b = scen(s2, **{k: lo}), scen(s2, **{k: hi})
    S.append(dict(parameter=name, low_setting=lo, high_setting=hi,
                  freed_lo=a["freed_jobs_M"], freed_hi=b["freed_jobs_M"],
                  net5_lo=a["net_y5_bn"], net5_hi=b["net_y5_bn"],
                  disp5_lo=a["displaced_cum_M"], disp5_hi=b["displaced_cum_M"]))
S = pd.DataFrame(S)
S["net5_swing"] = (S.net5_hi - S.net5_lo).abs()
S = S.sort_values("net5_swing", ascending=False)
print(f"S2 base: freed {base['freed_jobs_M']:.2f}M, displaced 5y {base['displaced_cum_M']:.2f}M, net y5 ${base['net_y5_bn']:.1f}bn")
print(S.round(2).to_string(index=False))
S.to_csv(out / "week4_sensitivity.csv", index=False)

print("\n== 4. EXTERNAL BENCHMARKS (not validation) ==")
for s in SC.itertuples():
    r = scen(s)
    print(f"{s.id}: freed time {r['freed_share']:.2%} of hours vs observed {OBS_TIME_SAVED_SHARE:.2%} "
          f"({r['freed_share']/OBS_TIME_SAVED_SHARE:.2f}x); displaced/yr {r['displaced_per_yr_M']*1e6:,.0f} vs observed "
          f"{OBS_AI_CUTS_PER_YR:,} ({r['displaced_per_yr_M']*1e6/OBS_AI_CUTS_PER_YR:.1f}x); deployment {s.deployment_share:.0%} "
          f"vs genAI work users {OBS_GENAI_WORK_USERS:.1%}")
# what deployment would reproduce the observed time saving at S2's other settings?
k = base["freed_share"] / s2.deployment_share
print(f"deployment that reproduces observed 2.16% at S2 time_saved/beta: {OBS_TIME_SAVED_SHARE / k:.3f}")
json.dump({"base": {k: v for k, v in base.items()}}, open(out / "week4_base.json", "w"), indent=1, default=float)
