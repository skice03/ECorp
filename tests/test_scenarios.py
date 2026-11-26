import csv
import io
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from src.scenarios import PACKAGE, ROOT, SCENARIOS
from src.week2 import RESULT_COLUMNS


class ScenarioIntegrationTests(unittest.TestCase):
    def simulate(self, output, *options):
        subprocess.run(
            [sys.executable, "-B", str(ROOT / "src/scenarios.py"), "--output", str(output), *options],
            check=True,
            capture_output=True,
        )
        return list(csv.DictReader(io.StringIO(output.read_text(encoding="utf-8"))))

    def test_reproduces_enache_annual_results_and_paper(self):
        table = "EC426767_Enache_Research/results/tables/EC426767_Annual_Results.csv"
        with ZipFile(PACKAGE) as archive:
            expected = list(csv.DictReader(io.StringIO(archive.read(table).decode("utf-8-sig"))))
        with TemporaryDirectory() as tmp:
            rows = self.simulate(Path(tmp) / "all.csv")
        self.assertEqual(len(rows), 20)
        self.assertEqual(len(expected), len(rows))
        for actual, reference in zip(rows, expected):
            self.assertEqual((actual["scenario"], actual["year"]), (reference["scenario"], reference["year"]))
            for field in RESULT_COLUMNS[1:]:
                # Different floating-point summation orders at a scale of 300 trillion RON.
                self.assertAlmostEqual(float(actual[field]), float(reference[field]), delta=0.25)
        # Initial headcount reductions and five-year savings (RON billion) from Bianca's Table 1.
        published = [(0, 0.000), (0, -114.793), (759642, 690.292), (1619315, 434.427)]
        for scenario, (replaced, savings) in zip(SCENARIOS, published):
            final, = [row for row in rows if row["scenario"] == scenario and row["year"] == "5"]
            self.assertEqual(int(final["employees"]), 161931500)
            self.assertEqual(int(final["replaced_at_start"]), replaced)
            self.assertEqual(round(float(final["cumul_savings"]) / 1e9, 3), savings)

    def test_single_scenario_matches_full_run_and_repeats_exactly(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "simulation.csv"
            all_rows = self.simulate(path)
            selected = self.simulate(path, "--scenario", "S2")
            self.assertEqual(selected, [row for row in all_rows if row["scenario"] == "S2"])
            first = path.read_bytes()
            self.simulate(path, "--scenario", "S2")
            self.assertEqual(path.read_bytes(), first)
