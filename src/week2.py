"""Load parameters and export results for the Week 2 projection."""

import argparse
import csv
import json
import math
import tempfile
from pathlib import Path
from zipfile import Path as ArchivePath

# Use the same cost model in direct CLI runs and test imports.
if __package__:
    from src.prototype import project_costs
else:
    from prototype import project_costs

DEFAULT_PARAMETERS = {
    "employees": 100,
    "replaced": 10,
    "annual_employee_cost": 30_000.0,
    "annual_ai_cost": 50_000.0,
    "implementation_cost": 100_000.0,
    "years": 10,
}

RESULT_COLUMNS = (
    "year",
    "baseline_cost",
    "scenario_cost",
    "savings",
    "cumul_baseline",
    "cumul_scenario",
    "cumul_savings",
)


def load_parameters(path: Path | ArchivePath) -> dict[str, int | float]:
    """Read parameter overrides from a JSON object."""
    try:
        with path.open(encoding="utf-8") as parameter_file:
            parameters = json.load(parameter_file)
    except (OSError, ValueError) as error:
        raise ValueError(f"Could not read parameter file {path}: {error}") from error

    if not isinstance(parameters, dict):
        raise ValueError(f"Parameter file {path} must contain a JSON object.")

    unknown = parameters.keys() - DEFAULT_PARAMETERS.keys()
    if unknown:
        raise ValueError(f"Unknown parameters in {path}: {', '.join(sorted(unknown))}")

    for name, value in parameters.items():
        if name in ("employees", "replaced", "years"):
            if type(value) is not int:
                raise ValueError(f"Parameter {name!r} in {path} must be an integer.")
        elif type(value) not in (int, float):
            raise ValueError(f"Parameter {name!r} in {path} must be a number.")

    return parameters


def run_projection(parameters: dict[str, int | float]) -> list[dict[str, int | float]]:
    """Run the prototype's cost model and validate the results before export."""
    try:
        projection = project_costs(**parameters)
    except OverflowError as error:
        raise ValueError("Inputs are too large to calculate finite results.") from error

    # Adding several finite annual costs can still overflow the totals.
    cumulative_columns = ("cumul_baseline", "cumul_scenario", "cumul_savings")
    if not all(math.isfinite(row[column]) for row in projection for column in cumulative_columns):
        raise ValueError("Inputs are too large to calculate finite cumulative results.")

    return projection


def export_results(projection: list[dict], path: Path, *, columns=RESULT_COLUMNS) -> None:
    """Save one row per projected year as a CSV file."""
    # Write the complete CSV beside its destination before replacing it.
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
        ) as output_file:
            temporary_path = Path(output_file.name)
            writer = csv.DictWriter(output_file, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(projection)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare workforce costs before and after AI replacement.",
        argument_default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--parameters", type=Path, metavar="PATH",
        help="Read model parameters and the projection horizon from a JSON file",
    )
    parser.add_argument(
        "--output", type=Path, metavar="PATH",
        help="Export annual and cumulative results to a CSV file",
    )
    parser.add_argument(
        "--employees", type=int,
        help=f"Initial number of employees (default: {DEFAULT_PARAMETERS['employees']})",
    )
    parser.add_argument(
        "--replaced", type=int,
        help=(
            "Employees replaced at the start of the projection "
            f"(default: {DEFAULT_PARAMETERS['replaced']})"
        ),
    )
    parser.add_argument(
        "--employee-cost", dest="annual_employee_cost", type=float,
        help=(
            "Total annual employer cost per employee in RON "
            f"(default: {DEFAULT_PARAMETERS['annual_employee_cost']:g})"
        ),
    )
    parser.add_argument(
        "--ai-cost", dest="annual_ai_cost", type=float,
        help=f"Total annual AI operating cost in RON (default: {DEFAULT_PARAMETERS['annual_ai_cost']:g})",
    )
    parser.add_argument(
        "--implementation-cost", type=float,
        help=f"One-time AI setup cost in RON (default: {DEFAULT_PARAMETERS['implementation_cost']:g})",
    )
    parser.add_argument(
        "--years", type=int,
        help=f"Number of years to project, 1-10 (default: {DEFAULT_PARAMETERS['years']})",
    )

    overrides = vars(parser.parse_args())
    parameter_path = overrides.pop("parameters", None)
    output_path = overrides.pop("output", None)

    try:
        file_parameters = load_parameters(parameter_path) if parameter_path else {}
        # File values override defaults, and explicit CLI options take precedence.
        parameters = DEFAULT_PARAMETERS | file_parameters | overrides
        projection = run_projection(parameters)
        if output_path is not None:
            if parameter_path is not None and output_path.resolve() == parameter_path.resolve():
                raise ValueError("Choose a different path for the results CSV and parameter file.")
            export_results(projection, output_path)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    args = argparse.Namespace(**parameters)
    print("\nEVIL CORP: First year workforce cost comparison")

    print("\nWorkforce")
    print(f"  Before AI: {args.employees} employees")
    print(f"  After AI:  {args.employees - args.replaced} employees")

    print("\nCost inputs")
    print(f"  Annual cost per employee:    {args.annual_employee_cost:>14,.2f} RON")
    print(f"  Annual AI operating cost:    {args.annual_ai_cost:>14,.2f} RON")
    print(f"  One-time implementation:     {args.implementation_cost:>14,.2f} RON")

    first_year = projection[0]
    print("\nResults")
    print(f"  Baseline annual labor cost:  {first_year['baseline_cost']:>14,.2f} RON")
    print(f"  First-year scenario cost:    {first_year['scenario_cost']:>14,.2f} RON")
    print(f"  First-year savings:          {first_year['savings']:>14,.2f} RON")

    final_year = projection[-1]
    print(f"\n{args.years}-Year Cumulative Totals")
    print(f"  Cumulative baseline cost:    {final_year['cumul_baseline']:>14,.2f} RON")
    print(f"  Cumulative scenario cost:    {final_year['cumul_scenario']:>14,.2f} RON")
    print(f"  Cumulative savings:          {final_year['cumul_savings']:>14,.2f} RON")
    if output_path is not None:
        print(f"\nExported yearly results to {output_path}")
    print()


if __name__ == "__main__":
    main()
