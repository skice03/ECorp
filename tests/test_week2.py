import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.week2 import DEFAULT_PARAMETERS, load_parameters, run_projection

WEEK2_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "week2.py"


class ParameterFileTests(unittest.TestCase):
    def test_loads_numeric_overrides(self):
        parameters = {"employees": 50, "annual_employee_cost": 30_000.50, "years": 3}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "parameters.json"
            path.write_text(json.dumps(parameters), encoding="utf-8")
            self.assertEqual(load_parameters(path), parameters)

    def test_rejects_invalid_parameter_files(self):
        invalid_files = (
            ("{", "Could not read parameter file"),
            ("[]", "must contain a JSON object"),
            ('{"yaers": 3}', "Unknown parameters"),
            ('{"employees": true}', "must be an integer"),
            ('{"years": 2.5}', "must be an integer"),
            ('{"annual_ai_cost": "50000"}', "must be a number"),
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "parameters.json"
            for contents, message in invalid_files:
                with self.subTest(contents=contents):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_parameters(path)
            with self.assertRaisesRegex(ValueError, "Could not read parameter file"):
                load_parameters(Path(directory) / "missing.json")


class ProjectionTests(unittest.TestCase):
    def test_implementation_cost_is_charged_in_year_one(self):
        first_year, second_year = run_projection(DEFAULT_PARAMETERS | {"years": 2})

        self.assertEqual(first_year["baseline_cost"], 3_000_000)
        self.assertEqual(first_year["scenario_cost"], 2_850_000)
        self.assertEqual(first_year["savings"], 150_000)
        self.assertEqual(second_year["baseline_cost"], 3_000_000)
        self.assertEqual(second_year["scenario_cost"], 2_750_000)
        self.assertEqual(second_year["savings"], 250_000)
        self.assertEqual(second_year["cumul_savings"], 400_000)

    def test_rejects_invalid_simulation_inputs(self):
        invalid_inputs = (
            ({"employees": 10, "replaced": 11}, "Replaced employees"),
            ({"annual_employee_cost": -1}, "Costs must be finite, non-negative"),
            ({"annual_ai_cost": float("nan")}, "Costs must be finite, non-negative"),
            ({"years": 0}, "Years must be between 1 and 10"),
            ({"years": 11}, "Years must be between 1 and 10"),
            (
                {"employees": 1, "replaced": 0, "annual_employee_cost": 1e308, "years": 2},
                "finite cumulative results",
            ),
        )
        for arguments, message in invalid_inputs:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(ValueError, message):
                    run_projection(DEFAULT_PARAMETERS | arguments)


class CommandLineTests(unittest.TestCase):
    def run_week2(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(WEEK2_SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exports_annual_and_cumulative_results_with_overrides(self):
        with TemporaryDirectory() as directory:
            parameters = Path(directory) / "parameters.json"
            output = Path(directory) / "results.csv"
            parameters.write_text(
                json.dumps({"employees": 50, "replaced": 5, "annual_ai_cost": 40_000, "years": 2}),
                encoding="utf-8",
            )
            # Override the headcount while keeping the horizon and AI cost from the file.
            run = self.run_week2(
                "--parameters", str(parameters), "--employees", "60", "--output", str(output)
            )
            self.assertEqual(run.returncode, 0, run.stderr)

            with output.open(encoding="utf-8", newline="") as output_file:
                rows = list(csv.DictReader(output_file))

        self.assertEqual([row["year"] for row in rows], ["1", "2"])
        self.assertEqual(float(rows[0]["savings"]), 10_000)
        self.assertEqual(
            {name: float(value) for name, value in rows[1].items()},
            {
                "year": 2,
                "baseline_cost": 1_800_000,
                "scenario_cost": 1_690_000,
                "savings": 110_000,
                "cumul_baseline": 3_600_000,
                "cumul_scenario": 3_480_000,
                "cumul_savings": 120_000,
            },
        )

    def test_invalid_input_leaves_existing_results_intact(self):
        with TemporaryDirectory() as directory:
            parameters = Path(directory) / "parameters.json"
            output = Path(directory) / "results.csv"
            parameters.write_text('{"employees": 4, "replaced": 5}', encoding="utf-8")
            output.write_text("Existing results\n", encoding="utf-8")

            run = self.run_week2("--parameters", str(parameters), "--output", str(output))

            self.assertEqual(run.returncode, 2)
            self.assertIn("Replaced employees", run.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "Existing results\n")

    def test_export_cannot_overwrite_the_parameter_file(self):
        with TemporaryDirectory() as directory:
            parameters = Path(directory) / "parameters.json"
            contents = '{"years": 1}'
            parameters.write_text(contents, encoding="utf-8")

            run = self.run_week2("--parameters", str(parameters), "--output", str(parameters))

            self.assertEqual(run.returncode, 2)
            self.assertIn("Choose a different path", run.stderr)
            self.assertEqual(parameters.read_text(encoding="utf-8"), contents)


if __name__ == "__main__":
    unittest.main()
