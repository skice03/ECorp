"""Week 3 – compare the reference baseline inputs with observed data.

Reference baseline = the values the model would load from the Week 1-2 data
(out/analysis_table_week2.csv). Observed values are typed in below with their source;
each one was read from the cited page on 25 Nov 2026.
Run (from the data-analysis folder): python3 scripts/week3_checks.py data/raw outputs
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

data, out = Path(sys.argv[1]), Path(sys.argv[2])
d = pd.read_csv(out / "analysis_table_week2.csv")
emp_k = d.emp_2022_k.sum()
w = d.emp_2022_k

def wmean(x):
    m = x.notna()
    return float(np.average(x[m], weights=w[m]))

def wmedian(x):
    m = x.notna()
    xs, ws = x[m].to_numpy(), w[m].to_numpy()
    o = np.argsort(xs); xs, ws = xs[o], ws[o]
    return float(np.interp(0.5, np.cumsum(ws) / ws.sum(), xs))

# ---------------- observed values (source in comment) ----------------
BLS_MEDIAN_2022 = 46310          # BLS EP Table 1.1, all occupations, median annual wage 2022
ECEC_WAGE_SHARE = 0.700          # BLS ECEC June 2026, private industry: wages = 70.0% of compensation
OEWS_2021_MEAN_ANNUAL = 58260    # OEWS May 2021 national file (bundled), all occupations
OEWS_2025_MEAN_HOURLY = 33.54    # BLS OEWS May 2025, U.S. average hourly wage
AI_CUTS_2026_JAN_OCT = 121401    # Challenger, AI-cited announced cuts Jan-Oct 2026
AI_CUTS_SINCE_2023_TO_JUL26 = 184538  # Challenger July 2026 report, cumulative since 2023
AI_CUTS_2026_JAN_JUL = 112713    # Challenger July 2026 report, YTD
RCT_TIME_REDUCTION = {"Customer support (Brynjolfsson, Li & Raymond)": 1 - 1 / 1.14,
                      "Consultants inside frontier (Dell'Acqua et al.)": 0.251,
                      "Professional writing (Noy & Zhang)": 0.40}
LICENSE_USD_MONTH = (21, 30)     # Microsoft 365 Copilot Business standard / enterprise add-on list price
ATD_TRAINING = (846, 1254)       # ATD direct learning expenditure per employee, 2025 and 2024

print("== P1 LABOR COST ==")
wm, wmed = wmean(d.median_wage), wmedian(d.median_wage)
print(f"baseline emp-weighted median of occupation medians: {wmed:,.0f} vs BLS published {BLS_MEDIAN_2022:,} "
      f"-> {wmed / BLS_MEDIAN_2022 - 1:+.1%}")
print(f"baseline emp-weighted mean of medians: {wm:,.0f}")
print(f"wage -> total employer cost multiplier: 1/{ECEC_WAGE_SHARE} = {1 / ECEC_WAGE_SHARE:.3f}; "
      f"loaded mean labor cost = {wm / ECEC_WAGE_SHARE:,.0f}")
m25 = OEWS_2025_MEAN_HOURLY * 2080
print(f"OEWS mean wage 2021 {OEWS_2021_MEAN_ANNUAL:,} -> May 2025 {m25:,.0f} (hourly x 2080): {m25 / OEWS_2021_MEAN_ANNUAL - 1:+.1%}")

print("\n== P2 DISPLACEMENT ==")
beta = wmean(d.human_rating_beta)
exposed_jobs = (d.human_rating_beta * d.emp_2022_k).sum() / 1000
print(f"baseline if exposure used as displacement: beta {beta:.3f} -> {exposed_jobs:.1f}M job-equivalents")
cum = AI_CUTS_SINCE_2023_TO_JUL26 + (AI_CUTS_2026_JAN_OCT - AI_CUTS_2026_JAN_JUL)
print(f"observed AI-cited announced cuts since 2023 through Oct 2026: {cum:,} = {cum / (emp_k * 1000):.3%} of 2022 jobs")
annual_2026 = AI_CUTS_2026_JAN_OCT / 10 * 12
print(f"2026 pace annualised: {annual_2026:,.0f} = {annual_2026 / (emp_k * 1000):.3%} of jobs per year")
print(f"gap: exposure-implied / observed cumulative = {exposed_jobs * 1e6 / cum:,.0f}x")

ep12 = pd.read_excel(data / "occupation_2023_final.xlsx", sheet_name="Table 1.12", header=1)
ep12.columns = ["title", "code", "ind", "indcode", "factor"]
ep12 = ep12.dropna(subset=["factor"])
ai = ep12[ep12.factor.str.contains(r"artificial intelligence|\bAI\b|machine learning|chatbot", case=False, regex=True)]
print(f"BLS EP 2022-32 Table 1.12: {ep12.code.nunique()} occupations with a stated factor, {ai.code.nunique()} cite AI/ML")
ai_codes = set(ai.code)
sub = d[d.code.isin(ai_codes)]
print(f"  those AI-cited occupations in analysis table: {len(sub)}, emp-weighted beta {np.average(sub.human_rating_beta, weights=sub.emp_2022_k):.3f}, "
      f"projected change {(sub.emp_2032_k.sum() / sub.emp_2022_k.sum() - 1):+.1%}")

print("\n== P4 PRODUCTIVITY ==")
print("baseline exposure definition: exposed tasks take >=50% less time")
print(f"labor time saved economy-wide if beta x 50%: {beta * 0.5:.1%}")
for k, v in RCT_TIME_REDUCTION.items():
    print(f"  {k}: time reduction {v:.1%} -> economy-wide {beta * v:.1%}")
lo, hi = min(RCT_TIME_REDUCTION.values()), max(RCT_TIME_REDUCTION.values())
print(f"observed range {lo:.1%}-{hi:.1%} -> economy-wide labor time saved {beta * lo:.1%}-{beta * hi:.1%}")

print("\n== P5 IMPLEMENTATION COST (license only) ==")
loaded = wm / ECEC_WAGE_SHARE
for p in LICENSE_USD_MONTH:
    print(f"  ${p}/user/month = ${p * 12}/yr = {p * 12 / loaded:.2%} of loaded labor cost per worker")

print("\n== P6 RETRAINING (proxy) ==")
for t in ATD_TRAINING:
    print(f"  ${t} = {t / loaded:.2%} of loaded labor cost per worker")
