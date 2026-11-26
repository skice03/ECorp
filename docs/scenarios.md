# Running and interpreting the workforce-cost simulations

Use Python 3.10 or later and run the commands below from the ECorp repository root.
All four weeks’ command-line tools use the Python standard library.

| Week | Command | What to look for |
| --- | --- | --- |
| 1 | `python3 src/prototype.py` | A hypothetical company starts with 100 employees and replaces 10. The console shows 150,000 RON in first-year savings. Use `--help` to see the adjustable inputs. |
| 2 | `python3 src/week2.py --parameters config/example_parameters.json --years 5 --output results/week2.csv` | Run one configuration and export five annual rows. The example file sets ten years and the command overrides it to five. The last row gives 1,150,000 RON in cumulative savings. |
| 3 | `python3 src/scenarios.py --scenario S2 --output results/s2.csv` | Load the data team’s 22 moderate-scenario cohort files directly from the ZIP, project each cohort, and sum their results by year. |
| 4 | `python3 src/scenarios.py` | Run S0–S3 and write 20 annual rows to `results/scenarios.csv`. The last year of each scenario gives its five-year totals. |

For a custom company simulation, copy `config/example_parameters.json`, edit the six values, and pass the copy to the week 2 command. Set `employees` and `replaced` to headcounts, `annual_employee_cost` to RON per person per year, `annual_ai_cost` to the **total** yearly AI budget, `implementation_cost` to the **total** one-time setup budget, and `years` to 1–10. Command-line overrides take precedence over the file. Choose a new output filename to keep previous results.

## Technical description for the paper

Enache’s handoff groups 785 U.S. occupations into 22 major occupational groups representing 161,931,500 jobs. It expresses U.S. wage proxies in RON using a 1.43 employer-cost multiplier and 4.6885 RON per USD. The JSON inputs already incorporate the scenario assumptions about exposure, deployment, redeployment, replacement and budgets. Each scenario uses a fixed initial replacement count for each group throughout five years.

For each group and year, baseline cost equals initial employees times annual employer cost per employee. Scenario cost equals remaining employees times that same unit cost, plus the annual AI budget. Year one also includes the initial integration and training budget. Savings equal baseline cost minus scenario cost. The runner sums the 22 group projections for each year. Identical inputs produce identical outputs. The calculation uses no sampling, seed or iteration count.

Each CSV row identifies its scenario and year. `employees` and `replaced_at_start` repeat the initial counts. `baseline_cost`, `scenario_cost` and `savings` cover that year in RON. Columns starting with `cumul_` cover year one through the row’s year. Negative savings mean the scenario costs more. Read the final cumulative value once per scenario.

| Scenario | Initially replaced | Year 1 savings, RON bn | Five-year savings, RON bn |
| --- | ---: | ---: | ---: |
| S0 · No deployment | 0 | 0.000 | 0.000 |
| S1 · Low deployment | 0 | −38.264 | −114.793 |
| S2 · Moderate deployment | 759,642 | 79.310 | 690.292 |
| S3 · High deployment | 1,619,315 | −51.924 | 434.427 |

S1 pays for AI while retaining the workforce. S3’s upfront costs exceed its first-year payroll savings. S2 has the largest five-year cost saving among these four cases. The model holds revenue and output constant. These estimates cover workforce costs under the specified assumptions and cannot establish a company’s profit-maximizing headcount.

## Sources and verification

The runner reads the six-field JSON files under `ECorp/config/enache/S0` through `S3` inside Enache’s committed archive. Bancu’s separate analysis uses USD and different displacement assumptions. Bianca’s Table 1 reports the RON scenarios shown above. [Enache’s inputs and reference outputs](../EC426767_Enache_Research_Deliverable.zip) · [Bianca’s research report](../SPM_Research_Report_Weeks_1-4.docx) · [Bancu’s methodology](../data-analysis/README.md)

Run `python3 -m unittest discover -s tests -v` to check the original CLI, all four scenarios against Enache’s annual reference table, the published five-year savings and initial replacement counts, and byte-identical repeat runs for S2. The comparison allows 0.25 RON for floating-point summation differences on costs above 300 trillion RON.
