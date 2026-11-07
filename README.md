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

## Run

Requires Python 3.10 or later. No extra packages are needed.

Run with the default values:

```bash
python3 src/main.py
```

Change any inputs; omitted options keep their defaults:

```bash
python3 src/main.py --employees 100 --replaced 20
```

Show all available options:

```bash
python3 src/main.py --help
```

With the default inputs, baseline cost is 3,000,000 RON, first-year scenario cost
is 2,850,000 RON and savings are 150,000 RON.
