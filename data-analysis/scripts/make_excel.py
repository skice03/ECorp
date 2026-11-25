"""Week 2 – convert outputs/analysis_table_week2.csv into a formatted Excel workbook.

Sheet "Analysis table": 785 occupations, readable headers with units, filter + frozen panes,
and six summary formulas under the table. Sheet "Notes": sources, definitions, join method.
Run (from the data-analysis folder): python3 scripts/make_excel.py outputs
"""
import sys
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

out = Path(sys.argv[1])
d = pd.read_csv(out / "analysis_table_week2.csv")
for c in ["title", "group", "education", "experience", "training"]:
    d[c] = d[c].astype("string").str.strip()
d = d.sort_values("code")
pct = lambda s: s / 100
cols = [  # (source column, header, number format, width, transform)
    ("code", "SOC code (BLS 2018)", "@", 12, None),
    ("title", "Occupation", "@", 48, None),
    ("group", "Major occupational group", "@", 36, None),
    ("emp_2022_k", "Employment 2022 (thousands)", "#,##0.0", 14, None),
    ("emp_2032_k", "Employment 2032, projected (thousands)", "#,##0.0", 16, None),
    ("chg_k", "Employment change 2022–32 (thousands)", "#,##0.0;-#,##0.0;-", 16, None),
    ("chg_pct", "Employment change 2022–32 (%)", "0.0%;-0.0%;0.0%", 14, pct),
    ("self_emp_pct", "Self-employed 2022 (%)", "0.0%", 13, pct),
    ("openings_k", "Annual openings 2022–32 (thousands)", "#,##0.0", 15, None),
    ("median_wage", "Median annual wage 2022 (USD)", "$#,##0", 14, None),
    ("education", "Typical entry education", "@", 30, None),
    ("experience", "Work experience required", "@", 20, None),
    ("training", "Typical on-the-job training", "@", 28, None),
    ("human_rating_alpha", "AI exposure – human alpha (0–1)", "0.000", 13, None),
    ("human_rating_beta", "AI exposure – human beta (0–1)", "0.000", 13, None),
    ("human_rating_gamma", "AI exposure – human gamma (0–1)", "0.000", 13, None),
    ("dv_rating_alpha", "AI exposure – GPT-4 alpha (0–1)", "0.000", 13, None),
    ("dv_rating_beta", "AI exposure – GPT-4 beta (0–1)", "0.000", 13, None),
    ("dv_rating_gamma", "AI exposure – GPT-4 gamma (0–1)", "0.000", 13, None),
]
F = "Arial"
wb = Workbook(); ws = wb.active; ws.title = "Analysis table"
for j, (_, h, _, w, _) in enumerate(cols, 1):
    c = ws.cell(row=1, column=j, value=h)
    c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
    c.fill = PatternFill("solid", fgColor="1F3864")
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.column_dimensions[get_column_letter(j)].width = w
ws.row_dimensions[1].height = 45
body = Font(name=F, size=10)
for i, (_, r) in enumerate(d.iterrows(), 2):
    for j, (src, _, fmt, _, tf) in enumerate(cols, 1):
        v = r[src]
        if pd.isna(v): v = None
        elif tf is not None: v = float(tf(v))
        elif isinstance(v, (int, float)): v = float(v)
        else: v = str(v)
        c = ws.cell(row=i, column=j, value=v); c.font = body; c.number_format = fmt
n = len(d) + 1
t = Table(displayName="AnalysisTable", ref=f"A1:{get_column_letter(len(cols))}{n}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
ws.add_table(t); ws.freeze_panes = "C2"

s = n + 2
ws.cell(row=s - 1, column=2, value="Summary (formulas over the table above)").font = Font(name=F, size=10, bold=True, italic=True)
summary = [
    ("Occupations", f"=COUNTA(A2:A{n})", "#,##0"),
    ("Total employment 2022 (thousands)", f"=SUM(D2:D{n})", "#,##0.0"),
    ("Total employment 2032 (thousands)", f"=SUM(E2:E{n})", "#,##0.0"),
    ("Projected change 2022–32 (%)", f"=D{s+2}/D{s+1}-1", "0.0%"),
    ("Employment-weighted AI exposure, human beta", f"=SUMPRODUCT(D2:D{n},O2:O{n})/D{s+1}", "0.000"),
    ("Jobs in occupations with human beta ≥ 0.5 (thousands)", f'=SUMIFS(D2:D{n},O2:O{n},">=0.5")', "#,##0.0"),
]
for k, (label, f, fmt) in enumerate(summary):
    ws.cell(row=s + k, column=2, value=label).font = Font(name=F, size=10, bold=True)
    c = ws.cell(row=s + k, column=4, value=f); c.font = body; c.number_format = fmt

ns = wb.create_sheet("Notes")
notes = [
    ("EC-426767 · Week 2 analysis table — Bancu Alexandru-Georgian", True),
    ("One row per BLS occupation (785 rows, 161.9M jobs = 98.4% of U.S. employment in 2022).", False),
    ("", False), ("Sources", True),
    ("Employment, projections, wages, education: BLS Employment Projections 2022–32, Table 1.7 (occupation_2023_final.xlsx, bundled in github.com/openai/GPTs-are-GPTs). https://www.bls.gov/emp/tables.htm", False),
    ("Median wage: from BLS OEWS May 2022; covers non-farm wage and salary workers only. Blank = not published by BLS (16 occupations).", False),
    ('AI exposure: Eloundou, Manning, Mishkin & Rock, "GPTs are GPTs" — occ_level.csv. https://github.com/openai/GPTs-are-GPTs', False),
    ("", False), ("Exposure definitions", True),
    ("alpha (E1) = share of an occupation's tasks where an LLM alone cuts task time by at least 50%.", False),
    ("beta = E1 + 0.5 × E2, where E2 = tasks exposed only with extra LLM-powered software. Main measure.", False),
    ("gamma = E1 + E2 (upper bound with full tooling).", False),
    ('"human" = rated by human annotators; "GPT-4" = rated by GPT-4.', False),
    ("", False), ("How the join was built", True),
    ("O*NET occupations (923) collapsed to 6-digit SOC by averaging sub-specialty scores (no weights published) → 798 codes.", False),
    ("773 matched exactly; 14 mapped to the BLS combined code (e.g. 13-1021/22/23 → 13-1020); 11 mapped by manual 2010→2018 SOC crosswalk (e.g. 25-9042/43 → 25-9045). Merged codes average their scores.", False),
    ('47 BLS occupations without an exposure score (mostly "all other" categories, 1.6% of jobs) are not included.', False),
    ("Percent columns are stored as fractions (0.05 displays as 5.0%).", False),
    ("Rebuild: python3 scripts/week2_analysis.py data/raw outputs && python3 scripts/make_excel.py outputs", False),
]
for i, (txt, bold) in enumerate(notes, 1):
    c = ns.cell(row=i, column=1, value=txt)
    c.font = Font(name=F, size=12 if i == 1 else 10, bold=bold)
    c.alignment = Alignment(wrap_text=True, vertical="top")
ns.column_dimensions["A"].width = 120
wb.save(out / "analysis_table_week2.xlsx")
print("saved", out / "analysis_table_week2.xlsx", "rows", n - 1)
