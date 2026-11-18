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


def project_costs(
    employees,
    replaced,
    annual_employee_cost,
    annual_ai_cost,
    implementation_cost,
    years=10,
):
    if years < 1 or years > 10:
        raise ValueError("Years must be between 1 and 10")

    projection = []
    cumul_baseline = 0.0
    cumul_scenario = 0.0
    cumul_savings = 0.0

    for year in range(1, years + 1):
        yearly_setup = implementation_cost if year == 1 else 0.0
        baseline_cost, scenario_cost, savings = compare_costs(
            employees,
            replaced,
            annual_employee_cost,
            annual_ai_cost,
            yearly_setup,
        )
        cumul_baseline += baseline_cost
        cumul_scenario += scenario_cost
        cumul_savings += savings

        projection.append(
            {
                "year": year,
                "baseline_cost": baseline_cost,
                "scenario_cost": scenario_cost,
                "savings": savings,
                "cumul_baseline": cumul_baseline,
                "cumul_scenario": cumul_scenario,
                "cumul_savings": cumul_savings,
            }
        )

    return projection


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
    parser.add_argument(
        "--years", type=int, default=10,
        help="Number of years to project, 1-10 (default: 10)"
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
        projection = project_costs(
            args.employees,
            args.replaced,
            args.employee_cost,
            args.ai_cost,
            args.implementation_cost,
            years=args.years,
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

    final_year = projection[-1]
    print(f"\n{args.years}-Year Cumulative Totals")
    print(f"  Cumulative baseline cost:    {final_year['cumul_baseline']:>14,.2f} RON")
    print(f"  Cumulative scenario cost:    {final_year['cumul_scenario']:>14,.2f} RON")
    print(f"  Cumulative savings:          {final_year['cumul_savings']:>14,.2f} RON")
    print()


if __name__ == "__main__":
    main()