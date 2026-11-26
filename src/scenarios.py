"""Run Enache's four occupational scenarios using the Week 2 projection."""

import argparse
import math
from pathlib import Path
from zipfile import BadZipFile, Path as ArchivePath, ZipFile

if __package__:
    from .week2 import DEFAULT_PARAMETERS, RESULT_COLUMNS, export_results, load_parameters, run_projection
else:
    from week2 import DEFAULT_PARAMETERS, RESULT_COLUMNS, export_results, load_parameters, run_projection

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "EC426767_Enache_Research_Deliverable.zip"
CONFIG_ROOT = "EC426767_Enache_Research/ECorp/config/enache"
SCENARIOS = ("S0", "S1", "S2", "S3")
# The handoff contains the 22 major occupational groups from SOC 11 through SOC 53.
SOC_GROUPS = range(11, 54, 2)
OUTPUT_COLUMNS = ("scenario", "employees", "replaced_at_start", *RESULT_COLUMNS)


def scenario_rows(archive: ZipFile, scenario: str) -> list[dict]:
    projections = []
    employees = replaced = 0
    for group in SOC_GROUPS:
        member = f"{CONFIG_ROOT}/{scenario}/EC426767_{scenario}_SOC{group}.json"
        source = ArchivePath(archive, member)
        parameters = load_parameters(source)
        missing = DEFAULT_PARAMETERS.keys() - parameters.keys()
        if missing:
            raise ValueError(f"{member} is missing {', '.join(sorted(missing))}")
        try:
            projection = run_projection(parameters)
        except ValueError as error:
            raise ValueError(f"{member}: {error}") from error
        if projections and len(projection) != len(projections[0]):
            raise ValueError(f"{member} has a different projection horizon")
        projections.append(projection)
        employees += parameters["employees"]
        replaced += parameters["replaced"]

    rows = []
    for year, cohorts in enumerate(zip(*projections), start=1):
        totals = {key: math.fsum(row[key] for row in cohorts) for key in RESULT_COLUMNS if key != "year"}
        rows.append(dict(scenario=scenario, employees=employees, replaced_at_start=replaced, year=year, **totals))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, help="Run one scenario (default: all four)")
    parser.add_argument("--output", type=Path, default=ROOT / "results/scenarios.csv", help="Destination CSV")
    args = parser.parse_args()
    if args.output.resolve() == PACKAGE.resolve():
        parser.error("Choose an output path different from the input archive.")
    try:
        with ZipFile(PACKAGE) as archive:
            rows = []
            for scenario in (SCENARIOS if args.scenario is None else (args.scenario,)):
                rows.extend(scenario_rows(archive, scenario))
        export_results(rows, args.output, columns=OUTPUT_COLUMNS)
    except (BadZipFile, OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Wrote {len(rows)} annual scenario rows to {args.output}")


if __name__ == "__main__":
    main()
