"""Week 1 – inspect the structure of the GPTs-are-GPTs occupation-level exposure dataset.

Dataset: occ_level.csv from github.com/openai/GPTs-are-GPTs (Eloundou, Manning, Mishkin & Rock).
Run (from the data-analysis folder): python3 scripts/inspect_occ_level.py data/raw/occ_level.csv data/raw/national_May2021_dl.csv
"""
import sys
import pandas as pd

occ_path, oews_path = sys.argv[1], sys.argv[2]
df = pd.read_csv(occ_path)

print("== SHAPE ==")
print(df.shape)
print("\n== COLUMNS / DTYPES / NULLS / UNIQUE ==")
info = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "non_null": df.notna().sum(),
    "nulls": df.isna().sum(),
    "unique": df.nunique(),
})
print(info.to_string())

score_cols = [c for c in df.columns if c.endswith(("_alpha", "_beta", "_gamma"))]
print("\n== DESCRIPTIVE STATS (scores) ==")
print(df[score_cols].describe().round(3).to_string())

print("\n== RANGE CHECK (all scores should be in [0,1]) ==")
print(((df[score_cols] < 0) | (df[score_cols] > 1)).sum().to_string())

print("\n== IDENTITY CHECK: beta == (alpha + gamma)/2 ? ==")
for p in ("dv_rating", "human_rating"):
    diff = (df[f"{p}_beta"] - (df[f"{p}_alpha"] + df[f"{p}_gamma"]) / 2).abs().max()
    print(p, "max abs diff:", diff)

print("\n== ORDERING CHECK: alpha <= beta <= gamma ==")
for p in ("dv_rating", "human_rating"):
    ok = ((df[f"{p}_alpha"] <= df[f"{p}_beta"] + 1e-9) & (df[f"{p}_beta"] <= df[f"{p}_gamma"] + 1e-9)).mean()
    print(p, f"{ok:.1%} of rows ordered")

print("\n== KEY CHECKS ==")
code = df["O*NET-SOC Code"]
print("duplicate O*NET codes:", code.duplicated().sum())
print("code format OK (NN-NNNN.NN):", code.str.fullmatch(r"\d{2}-\d{4}\.\d{2}").mean())
df["soc6"] = code.str[:7]
print("distinct 6-digit SOC codes:", df["soc6"].nunique())
print("O*NET rows that are sub-specialties (suffix != .00):", (~code.str.endswith(".00")).sum())
df["major_group"] = code.str[:2]
print("\n== ROWS PER SOC MAJOR GROUP ==")
print(df["major_group"].value_counts().sort_index().to_string())

print("\n== GPT-4 vs HUMAN agreement (Pearson r) ==")
for s in ("alpha", "beta", "gamma"):
    print(s, round(df[f"dv_rating_{s}"].corr(df[f"human_rating_{s}"]), 3))

print("\n== TOP / BOTTOM 5 by human_rating_beta ==")
cols = ["O*NET-SOC Code", "Title", "human_rating_beta", "dv_rating_beta"]
print(df.sort_values("human_rating_beta", ascending=False)[cols].head(5).to_string(index=False))
print(df.sort_values("human_rating_beta")[cols].head(5).to_string(index=False))
print("occupations with human_rating_beta == 0:", (df["human_rating_beta"] == 0).sum())
print("occupations with human_rating_gamma == 1:", (df["human_rating_gamma"] == 1).sum())

# ---- Joinability test with BLS OEWS (May 2021 national file bundled in the repo) ----
print("\n== JOIN TEST WITH BLS OEWS (6-digit SOC) ==")
oews = pd.read_csv(oews_path, dtype=str)
print("OEWS columns:", list(oews.columns)[:12], "...")
det = oews[oews["O_GROUP"].str.lower() == "detailed"] if "O_GROUP" in oews.columns else oews
print("OEWS detailed occupations:", det["OCC_CODE"].nunique())
agg = df.groupby("soc6")[score_cols].mean().reset_index()
m = agg.merge(det[["OCC_CODE", "TOT_EMP", "A_MEAN"]], left_on="soc6", right_on="OCC_CODE", how="left", indicator=True)
print("6-digit SOC codes matched to OEWS:", (m["_merge"] == "both").sum(), "of", len(agg))
unmatched = m.loc[m["_merge"] == "left_only", "soc6"].tolist()
print("unmatched examples:", unmatched[:10])
matched = m[m["_merge"] == "both"].copy()
for c in ("TOT_EMP", "A_MEAN"):
    matched[c] = pd.to_numeric(matched[c].str.replace(",", ""), errors="coerce")
print("matched rows with suppressed wage (A_MEAN NaN):", matched["A_MEAN"].isna().sum())
w = matched.dropna(subset=["TOT_EMP"])
print("employment covered by matched occupations:", int(w["TOT_EMP"].sum()))
print("employment-weighted mean human_rating_beta:", round((w["human_rating_beta"] * w["TOT_EMP"]).sum() / w["TOT_EMP"].sum(), 3))
print("corr(wage, human_rating_beta):", round(matched["A_MEAN"].corr(matched["human_rating_beta"]), 3))
