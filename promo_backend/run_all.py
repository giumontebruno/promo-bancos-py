import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    ("scrapers/extract_sudameris.py", False),
    ("scrapers/build_sudameris_table.py", False),
    ("scrapers/extract_itau.py", False),
    ("scrapers/extract_bnf.py", False),
    ("scrapers/extract_continental.py", False),
    ("scrapers/extract_atlas.py", False),
    ("scrapers/extract_universitaria.py", False),
    ("scrapers/extract_ueno.py", False),
    ("scrapers/extract_ueno_pdf_links.py", False),
    ("scrapers/enrich_ueno_from_bases.py", False),
    ("promo_backend/normalize.py", True),
]


def run_step(script, required):
    print(f"Running {script}")
    completed = subprocess.run([sys.executable, script], cwd=ROOT, check=False)
    if completed.returncode and required:
        completed.check_returncode()
    return completed.returncode


def main():
    failures = []
    for script, required in STEPS:
        returncode = run_step(script, required)
        if returncode:
            failures.append((script, returncode))
            print(f"WARNING: {script} failed with exit code {returncode}. Continuing with existing data.")
    if failures:
        print("Refresh completed with scraper warnings:")
        for script, returncode in failures:
            print(f"- {script}: exit code {returncode}")
    print("Promotion database refresh complete.")


if __name__ == "__main__":
    main()
