# EC-426767 · Data Analysis (Weeks 1–4)

**Author:** Bancu Alexandru-Georgian, Data Analyst
**Project:** Human Replacement Profitability Study (EC-426767)

This folder holds all data-analyst work for November 2026: data sources, the analysis table, the checks of the team's parameter files, the scenario runs and the sensitivity analysis. Every number in `reports/` can be rebuilt from `data/` with the scripts in `scripts/`.

This folder is self-contained: it doesn't change or depend on anything in `src/`, `config/`, `results/` or `tests/`.

## Quick start

```bash
cd data-analysis
pip install -r requirements.txt
python run_all.py       # rebuilds everything in outputs/ (a few seconds; Windows, macOS, Linux)
```

Requires Python 3.10+, the same as the rest of the repository. Each script can also be run on its own (see the table below); run those commands from the `data-analysis` folder.

## Folder layout

```
data-analysis/
├── README.md
├── requirements.txt
├── run_all.py                  rebuilds every output (cross-platform)
├── data/
│   ├── raw/                    public source data (inputs)
│   └── team/
│       ├── round1/             Enache's first parameter + scenario files
│       └── round2/             "Parametrii noi.tura2" (latest)
├── scripts/                    analysis code
├── outputs/                    generated tables, results and run logs
└── reports/                    Week 1–4 deliverables (PDF)
```

## What each week did

| Week | Activity List tasks | Script(s) | Main outputs | Report |
| --- | --- | --- | --- | --- |
| 1 | Find 3–5 credible data sources; download one dataset and inspect its structure | `inspect_occ_level.py` | `week1_inspection_output.txt` | `Week1_Data_Sources_and_Inspection.pdf` |
| 2 | Descriptive statistics for the main employment variables; 2–3 preliminary charts | `week2_analysis.py`, `make_excel.py` | `analysis_table_week2.csv` / `.xlsx`, `tableA–C_*.csv` | `Week2_Descriptive_Statistics_and_Charts.pdf` |
| 3 | Compare baseline inputs with observed data; data- and parameter-quality report | `week3_checks.py`, `week3_checks_team.py`, `week3_checks_round2.py` | `week3_*_output.txt`, `week3_team_scenarios.csv`, `week3_round2_scenarios.csv` | `Week3_Baseline_vs_Observed_and_Quality_Report.pdf` |
| 4 | Run baseline and alternative scenarios; sensitivity analysis; external benchmarks | `week4_model.py` | `week4_scenarios.csv`, `week4_sensitivity.csv`, `week4_s2_by_group.csv` | `Week4_Scenarios_Sensitivity_and_Benchmarks.pdf` |

### Running scripts individually

| Script | Command | Reads | Writes |
| --- | --- | --- | --- |
| `inspect_occ_level.py` | `python3 scripts/inspect_occ_level.py data/raw/occ_level.csv data/raw/national_May2021_dl.csv` | exposure file, OEWS 2021 | prints the structure report |
| `week2_analysis.py` | `python3 scripts/week2_analysis.py data/raw outputs` | `occ_level.csv`, `occupation_2023_final.xlsx` | `analysis_table_week2.csv`, `tableA/B/C_*.csv`, `chart_scatter_data.csv` |
| `make_excel.py` | `python3 scripts/make_excel.py outputs` | `analysis_table_week2.csv` | `analysis_table_week2.xlsx` |
| `week3_checks.py` | `python3 scripts/week3_checks.py data/raw outputs` | analysis table, BLS Table 1.12 | prints the observed-evidence checks |
| `week3_checks_team.py` | `python3 scripts/week3_checks_team.py data/team/round1 outputs` | round-1 team files | `week3_team_scenarios.csv` |
| `week3_checks_round2.py` | `python3 scripts/week3_checks_round2.py data/team/round2 data/team/round1 outputs` | both rounds | `week3_round2_scenarios.csv` |
| `week4_model.py` | `python3 scripts/week4_model.py data/team/round2 outputs` | round-2 team files | `week4_scenarios.csv`, `week4_sensitivity.csv`, `week4_s2_by_group.csv` |

Order matters: `week2_analysis.py` must run before the Week 3 scripts, because they read `outputs/analysis_table_week2.csv`. `run_all.py` runs them in the right order.

## Key results

- **Week 2.** On average, 30.8% of a U.S. worker's tasks are exposed to AI (employment-weighted human beta = 0.308). 35.3M jobs (21.8%) are in occupations where at least half of tasks are exposed. Exposure is highest in computer, business and office work, and roughly doubles from the lowest- to the highest-paid jobs.
- **Week 3.** The team's parameter file reproduces the Week 2 data exactly, and its time-saved range matches the trial evidence. Three inputs fall short of observed data:
  - Labor cost is about 18% low (2022 wages).
  - S3 deployment is above every observed adoption level.
  - Moderate and high displacement are 5.6× and 11× the observed pace of AI-cited job cuts.

  Round 2 also showed S1 and S2 displace more jobs than their spare capacity allows.
- **Week 4.** S2 frees 2.31% of U.S. work hours, close to the 2.16% that workers report saving with generative AI. Capped at spare capacity, S2 displaces 1.87M jobs over five years and nets about $138bn/yr by year 5 (labor cost, not profit). Demand response is the most influential input: S2's year-5 net saving ranges from −$30bn to +$306bn across its 0–1 range.

## Important caveats

- **Week 4 uses its own implementation of the occupation-level calculator**, built from the definitions in the round-2 parameter file. The repository's current model (`src/prototype.py`, `src/week2.py`) is a different, company-level cost comparison in RON that does not read the team parameter file. When the developers add an occupation-level model, it should reproduce the freed-capacity columns of `week4_scenarios.csv` exactly. The financial layer (displacement, implementation, training) is my reading of settings the team marked "handoff only".
- **Currency:** all figures here are in **USD** (U.S. data), unlike the RON prototype in `src/`. Don't mix the two in one table.
- **Dollar figures are in 2022 wages × 1.43**, so they are understated by about 18%. Regenerate after downloading the May 2025 OEWS file.
- **All occupation-level data is U.S.** Romania appears only through the Eurostat adoption rate (5.2% of enterprises).
- **The benchmark comparisons in Week 4 are not a formal validation.** They show plausibility only.
- **Assumptions in Week 4:** 5-year horizon, full deployment from year 1, and cumulative displacement capped at spare capacity (uncapped results are also in `week4_scenarios.csv`).

## Data sources and licences

| File | Source | Licence / terms |
| --- | --- | --- |
| `data/raw/occ_level.csv` | Eloundou, Manning, Mishkin & Rock, *GPTs are GPTs*, [github.com/openai/GPTs-are-GPTs](https://github.com/openai/GPTs-are-GPTs) | MIT, © 2024 OpenAI; see `data/raw/LICENSE-GPTs-are-GPTs.txt` |
| `data/raw/occupation_2023_final.xlsx` | BLS Employment Projections 2022–32 ([bls.gov/emp](https://www.bls.gov/emp/tables.htm)), copy bundled in the repo above | U.S. government work, public domain |
| `data/raw/national_May2021_dl.csv` | BLS OEWS May 2021 national file ([bls.gov/oes](https://www.bls.gov/oes/tables.htm)), copy bundled in the repo above | U.S. government work, public domain |
| `data/team/round1/`, `data/team/round2/` | Enache Ionuț-Alexandru, parameter and scenario files (25 Nov 2026) | Team internal |

Observed figures used in Weeks 3–4 are typed into the scripts with their sources: BLS ECEC, BLS OEWS May 2025, Census BTOS, Eurostat, Challenger Gray & Christmas, St. Louis Fed Real-Time Population Survey, published productivity trials, Microsoft list prices and ATD. Full citations are in the Sources section of each report.
