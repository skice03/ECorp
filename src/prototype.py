import argparse
import math

def compare_costs(
    employees, replaced, annual_employee_cost, annual_ai_cost, implementation_cost
):
    # Validate employee counts and costs
    if employees < 0 or replaced < 0 or replaced > employees:
        raise ValueError("Replaced employees must be between 0 and total employees")

    costs = (annual_employee_cost, annual_ai_cost, implementation_cost)

    if any(not math.isfinite(cost) or cost < 0 for cost in costs):
        raise ValueError("Costs must be finite, non-negative numbers")

    # Calculate costs before and after replacement
    baseline_cost = employees * annual_employee_cost
    remaining_labor_cost = (employees - replaced) * annual_employee_cost
    scenario_cost = remaining_labor_cost + annual_ai_cost + implementation_cost

    if not all(math.isfinite(value) for value in (baseline_cost, scenario_cost)):
        raise ValueError("Inputs are too large to calculate finite results.")

    savings = baseline_cost - scenario_cost

    return baseline_cost, scenario_cost, savings


def main():
    parser = argparse.ArgumentParser(
        description="Compare first-year workforce costs before and after AI replacement."
    )

    parser.add_argument(
        "--employees", type=int, default=100,
        help="Initial number of employees (default: 100)"
    )
    parser.add_argument(
        "--replaced", type=int, default=10,
        help="Employees replaced at the start of the year (default: 10)"
    )
    parser.add_argument(
        "--employee-cost", type=float, default=30000,
        help="Total annual employer cost per employee in RON (default: 30000)"
    )
    parser.add_argument(
        "--ai-cost", type=float, default=50000,
        help="Total annual AI operating cost in RON (default: 50000)"
    )
    parser.add_argument(
        "--implementation-cost", type=float, default=100000,
        help="One-time AI setup cost in RON (default: 100000)"
    )

    args = parser.parse_args()

    try:
        baseline, scenario, savings = compare_costs(
            args.employees,
            args.replaced,
            args.employee_cost,
            args.ai_cost,
            args.implementation_cost,
        )
    except ValueError as error:
        parser.error(str(error))

    print("\nEVIL CORP: First year workforce cost comparison")

    print("\nWorkforce")
    print(f"  Before AI: {args.employees} employees")
    print(f"  After AI:  {args.employees - args.replaced} employees")

    print("\nCost inputs")
    print(f"  Annual cost per employee:    {args.employee_cost:>14,.2f} RON")
    print(f"  Annual AI operating cost:    {args.ai_cost:>14,.2f} RON")
    print(f"  One-time implementation:     {args.implementation_cost:>14,.2f} RON")

    print("\nResults")
    print(f"  Baseline annual labor cost:  {baseline:>14,.2f} RON")
    print(f"  First-year scenario cost:    {scenario:>14,.2f} RON")
    print(f"  First-year savings:          {savings:>14,.2f} RON")
    print()

if __name__ == "__main__":
    main()