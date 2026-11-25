"""Rebuild every data-analysis output from the raw data and team files.

Works on Windows, macOS and Linux. Run from anywhere:
    python run_all.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

STEPS = [  # (script, arguments, log file or None)
    ("inspect_occ_level.py", ["data/raw/occ_level.csv", "data/raw/national_May2021_dl.csv"], "week1_inspection_output.txt"),
    ("week2_analysis.py", ["data/raw", "outputs"], "week2_output.txt"),
    ("make_excel.py", ["outputs"], None),
    ("week3_checks.py", ["data/raw", "outputs"], "week3_output.txt"),
    ("week3_checks_team.py", ["data/team/round1", "outputs"], "week3_team_output.txt"),
    ("week3_checks_round2.py", ["data/team/round2", "data/team/round1", "outputs"], "week3_round2_output.txt"),
    ("week4_model.py", ["data/team/round2", "outputs"], "week4_output.txt"),
]

for script, args, log in STEPS:
    print(f"running {script} ...")
    result = subprocess.run([sys.executable, str(HERE / "scripts" / script), *args],
                            cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(f"{script} failed:\n{result.stderr}")
    if log:
        (OUT / log).write_text(result.stdout, encoding="utf-8")

print("Done. Results are in outputs/")
