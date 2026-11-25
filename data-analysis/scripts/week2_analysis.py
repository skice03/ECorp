"""Week 2 – build the analysis table and descriptive statistics.

Inputs (all from github.com/openai/GPTs-are-GPTs, data/ folder):
  occ_level.csv                 – AI exposure scores per O*NET occupation (Eloundou et al.)
  occupation_2023_final.xlsx    – BLS Employment Projections 2022–32, Table 1.7
                                  (2022 employment incl. self-employed, 2032 projection,
                                   median annual wage 2022, typical entry education)
Run (from the data-analysis folder): python3 scripts/week2_analysis.py data/raw outputs
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

data, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

# ---------- exposure, collapsed to 6-digit SOC ----------
occ = pd.read_csv(data / "occ_level.csv")
occ["soc6"] = occ["O*NET-SOC Code"].str[:7]
score_cols = ["human_rating_alpha", "human_rating_beta", "human_rating_gamma",
              "dv_rating_alpha", "dv_rating_beta", "dv_rating_gamma"]
exp6 = occ.groupby("soc6").agg(n_onet=("Title", "size"), **{c: (c, "mean") for c in score_cols}).reset_index()

# ---------- BLS Employment Projections, Table 1.7 ----------
ep = pd.read_excel(data / "occupation_2023_final.xlsx", sheet_name="Table 1.7", header=1)
ep.columns = ["title", "code", "type", "emp_2022_k", "emp_2032_k", "chg_k", "chg_pct",
              "self_emp_pct", "openings_k", "median_wage", "education", "experience", "training"]
ep = ep[ep["code"].astype(str).str.fullmatch(r"\d{2}-\d{4}")]
total_emp_k = float(ep.loc[ep["code"] == "00-0000", "emp_2022_k"].iloc[0])
ep["title"] = ep["title"].astype(str).str.strip()
line = ep[ep["type"] == "Line item"].copy()
for c in ["emp_2022_k", "emp_2032_k", "chg_k", "chg_pct", "self_emp_pct", "openings_k", "median_wage"]:
    line[c] = pd.to_numeric(line[c], errors="coerce")

# ---------- crosswalk: exact SOC first, then the BLS broad code (XX-XXX0) ----------
codes = set(line["code"])
# O*NET still uses some pre-2018 SOC codes; BLS EP merged them into one 2018 code.
MANUAL = {"21-1011": "21-1018", "21-1014": "21-1018",   # substance abuse / mental health counselors
          "25-2055": "25-2052", "25-2056": "25-2052",   # special ed teachers, kindergarten + elementary
          "25-9042": "25-9045", "25-9043": "25-9045",   # teaching assistants
          "51-2022": "51-2028", "51-2023": "51-2028",   # electrical/electronic assemblers
          "53-1042": "53-1047", "53-1043": "53-1047", "53-1044": "53-1047"}  # transport supervisors
def map_code(s):
    if s in codes:
        return s, "exact"
    if s in MANUAL and MANUAL[s] in codes:
        return MANUAL[s], "manual"
    broad = s[:6] + "0"
    if broad in codes:
        return broad, "broad"
    return None, "unmatched"
exp6[["ep_code", "match"]] = exp6["soc6"].apply(lambda s: pd.Series(map_code(s)))
print("== MATCHING exposure SOC codes to BLS EP line items ==")
print(exp6["match"].value_counts().to_string())
print("unmatched:", exp6.loc[exp6.match == "unmatched", "soc6"].tolist())

# several O*NET/SOC codes can map to one BLS code (broad) -> average exposure per BLS code
exp_ep = exp6.dropna(subset=["ep_code"]).groupby("ep_code")[score_cols].mean().reset_index()
df = line.merge(exp_ep, left_on="ep_code" if False else "code", right_on="ep_code", how="left")
df["has_exposure"] = df["human_rating_beta"].notna()
df["major"] = df["code"].str[:2]
majors = ep[ep["code"].str.endswith("-0000") & (ep["code"] != "00-0000")][["code", "title"]]
majors["major"] = majors["code"].str[:2]
majors["group"] = majors["title"].str.replace(" occupations", "", regex=False)
df = df.merge(majors[["major", "group"]], on="major", how="left")

cov = df[df.has_exposure]
print("\n== COVERAGE ==")
print("BLS line-item occupations:", len(df), "| with exposure score:", len(cov))
print(f"employment covered: {cov.emp_2022_k.sum():,.1f}k of {df.emp_2022_k.sum():,.1f}k line-item jobs "
      f"({cov.emp_2022_k.sum()/df.emp_2022_k.sum():.1%}); BLS total all occupations {total_emp_k:,.1f}k")
print("missing median wage among covered:", cov.median_wage.isna().sum())
print("not covered (largest):")
print(df[~df.has_exposure].nlargest(8, "emp_2022_k")[["code", "title", "emp_2022_k"]].to_string(index=False))

cov = cov.copy()
cov.to_csv(out / "analysis_table_week2.csv", index=False)

def wmean(x, w):
    m = x.notna() & w.notna()
    return float(np.average(x[m], weights=w[m]))

def wquant(x, w, q):
    m = x.notna() & w.notna()
    x, w = x[m].to_numpy(), w[m].to_numpy()
    o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(np.interp(q, cw, x))

# ---------- Table A: descriptive statistics for main variables ----------
print("\n== TABLE A: descriptive statistics, occupation level (n = %d) ==" % len(cov))
vars_ = {"emp_2022_k": "Employment 2022 (thousands)", "chg_pct": "Projected employment change 2022-32 (%)",
         "median_wage": "Median annual wage 2022 (USD)", "self_emp_pct": "Self-employed 2022 (%)",
         "human_rating_beta": "AI exposure, human beta (0-1)", "human_rating_gamma": "AI exposure, human gamma (0-1)",
         "dv_rating_beta": "AI exposure, GPT-4 beta (0-1)"}
rows = []
for c, lab in vars_.items():
    s = cov[c]
    r = dict(variable=lab, n=int(s.notna().sum()), mean=s.mean(), sd=s.std(), min=s.min(),
             p25=s.quantile(.25), median=s.median(), p75=s.quantile(.75), max=s.max())
    if c != "emp_2022_k":
        r["emp_weighted_mean"] = wmean(s, cov.emp_2022_k)
        r["emp_weighted_median"] = wquant(s, cov.emp_2022_k, .5)
    rows.append(r)
tA = pd.DataFrame(rows)
print(tA.round(3).to_string(index=False))
tA.to_csv(out / "tableA_descriptives.csv", index=False)
print("skew employment:", round(cov.emp_2022_k.skew(), 2), "| top 10 occupations share of jobs:",
      f"{cov.nlargest(10,'emp_2022_k').emp_2022_k.sum()/cov.emp_2022_k.sum():.1%}")

# ---------- Table B: by major group ----------
g = cov.groupby("group")
tB = pd.DataFrame({
    "occupations": g.size(),
    "emp_2022_m": g.emp_2022_k.sum() / 1000,
    "emp_share_pct": g.emp_2022_k.sum() / cov.emp_2022_k.sum() * 100,
    "median_wage_wmed": g.apply(lambda x: wquant(x.median_wage, x.emp_2022_k, .5)),
    "chg_pct_group": (g.emp_2032_k.sum() / g.emp_2022_k.sum() - 1) * 100,
    "beta_wmean": g.apply(lambda x: wmean(x.human_rating_beta, x.emp_2022_k)),
    "gamma_wmean": g.apply(lambda x: wmean(x.human_rating_gamma, x.emp_2022_k)),
    "exposed_jobs_beta_m": g.apply(lambda x: (x.human_rating_beta * x.emp_2022_k).sum() / 1000),
}).sort_values("beta_wmean", ascending=False)
print("\n== TABLE B: by major group (employment-weighted) ==")
print(tB.round(3).to_string())
tB.to_csv(out / "tableB_by_major_group.csv")

# ---------- Table C: by exposure quintile (employment-weighted quintiles of human beta) ----------
cov = cov.sort_values("human_rating_beta")
cw = cov.emp_2022_k.cumsum() / cov.emp_2022_k.sum()
cov["exp_quintile"] = np.minimum((cw * 5).apply(np.ceil).astype(int), 5)
g = cov.groupby("exp_quintile")
tC = pd.DataFrame({
    "beta_range": g.human_rating_beta.agg(lambda s: f"{s.min():.2f}-{s.max():.2f}"),
    "occupations": g.size(),
    "emp_2022_m": g.emp_2022_k.sum() / 1000,
    "beta_wmean": g.apply(lambda x: wmean(x.human_rating_beta, x.emp_2022_k)),
    "median_wage_wmed": g.apply(lambda x: wquant(x.median_wage, x.emp_2022_k, .5)),
    "chg_pct_group": (g.emp_2032_k.sum() / g.emp_2022_k.sum() - 1) * 100,
    "self_emp_wmean": g.apply(lambda x: wmean(x.self_emp_pct, x.emp_2022_k)),
    "bachelor_plus_share": g.apply(lambda x: x.loc[x.education.isin(["Bachelor's degree", "Master's degree", "Doctoral or professional degree"]), "emp_2022_k"].sum() / x.emp_2022_k.sum() * 100),
})
print("\n== TABLE C: by employment-weighted exposure quintile (Q1 = least exposed) ==")
print(tC.round(3).to_string())
tC.to_csv(out / "tableC_by_exposure_quintile.csv")

# ---------- correlations ----------
print("\n== CORRELATIONS (occupation level) ==")
c = cov[["human_rating_beta", "median_wage", "chg_pct", "self_emp_pct"]].corr(method="spearman")
print("Spearman:\n", c.round(3).to_string())
print("Pearson beta~log(wage):", round(cov.human_rating_beta.corr(np.log(cov.median_wage)), 3))

# ---------- headline numbers ----------
print("\n== HEADLINES ==")
print("emp-weighted mean human beta:", round(wmean(cov.human_rating_beta, cov.emp_2022_k), 3))
print("emp-weighted mean human gamma:", round(wmean(cov.human_rating_gamma, cov.emp_2022_k), 3))
print("emp-weighted mean human alpha:", round(wmean(cov.human_rating_alpha, cov.emp_2022_k), 3))
for t in (0.5,):
    m = cov.human_rating_beta.round(9) >= t  # round: 0.5 can be stored as 0.4999...
    print(f"jobs in occupations with beta >= {t}: {cov.loc[m,'emp_2022_k'].sum()/1000:.1f}M "
          f"({cov.loc[m,'emp_2022_k'].sum()/cov.emp_2022_k.sum():.1%})")
m = cov.human_rating_beta == 0
print(f"jobs with beta == 0: {cov.loc[m,'emp_2022_k'].sum()/1000:.1f}M")
print("task-weighted exposed jobs (sum beta*emp):", round((cov.human_rating_beta * cov.emp_2022_k).sum() / 1000, 1), "M")
print("\nLargest 10 occupations:")
print(cov.nlargest(10, "emp_2022_k")[["code", "title", "emp_2022_k", "median_wage", "human_rating_beta", "chg_pct"]].to_string(index=False))

# chart data
cov[["code", "title", "group", "emp_2022_k", "median_wage", "human_rating_beta", "chg_pct"]].to_csv(out / "chart_scatter_data.csv", index=False)
