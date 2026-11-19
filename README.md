# E Corp

A university group project studying how replacing employees with AI affects
company costs and profitability.

## Team

| Team member | Role | Responsibilities |
| --- | --- | --- |
| Barbu David-Constantin | Project Manager | Coordinate the team, tasks and project timeline. |
| Copcă-Mare Bianca-Giorgiana | Research Analyst | Review existing research and prepare the research paper. |
| Bancu Alexandru-Georgian | Data Analyst | Find datasets and analyse the collected data. |
| Enache Ionuț-Alexandru | Data Analyst | Define model parameters, assumptions and scenarios. |
| Cipu Marinel | Software Developer | Set up the repository and develop the prototype, input handling and results output. |
| Dan Ela | Software Developer | Compare simulation approaches and develop the model logic. |

## Week 1 prototype

The Python prototype compares annual labor costs before replacement with the
first-year costs after replacing a chosen number of employees with AI.

Inputs: total employees, employees replaced, annual employer cost per employee,
total annual AI operating cost and one-time implementation cost.

Outputs: baseline cost, first-year scenario cost and savings. Positive savings
mean lower costs; negative savings mean higher costs.

All costs are in RON. The inputs are hypothetical, and company output and revenue
are assumed unchanged. This is an initial cost comparison, not the final simulation.

### Run the prototype

Requires Python 3.10 or later. No extra packages are needed.

Run with the default values:

```bash
python3 src/prototype.py
```

Change any inputs; omitted options keep their defaults:

```bash
python3 src/prototype.py --employees 100 --replaced 20 --years 5
```

Show all available options:

```bash
python3 src/prototype.py --help
```

## Week 2

The Week 2 script uses the prototype's cost model, loads JSON parameters, and
exports annual and cumulative results to CSV. Set the projection horizon to
1–10 years in the JSON file or use `--years` to override it.

Run the five-year example from the repository root.

```bash
python3 src/week2.py --parameters config/example_parameters.json --years 5 --output results/week2.csv
```

Run the tests for input validation, CSV output, and the one-time setup cost.

```bash
python3 -m unittest discover -s tests
```

The example uses hypothetical costs in RON. [Sample CSV](results/week2.csv) · [Week 2 guide](docs/week2.md)

## Streamlit web interface

Requires streamlit, pandas, plotly.

```bash
pip install streamlit pandas plotly
```

Open the dashboard:

```bash
streamlit run src/app.py
```

With the default inputs, baseline annual cost is 3,000,000 RON, first-year scenario cost is 2,850,000 RON, and first-year savings are 150,000 RON (with 250,000 RON/year in savings from Year 2 onward). Over 10 years, cumulative baseline cost is 30,000,000 RON, cumulative scenario cost is 27,600,000 RON, and total cumulative savings reach 2,400,000 RON.
