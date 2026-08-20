import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    ["scrapers/extract_sudameris.py"],
    ["scrapers/build_sudameris_table.py"],
    ["scrapers/extract_itau.py"],
    ["scrapers/extract_bnf.py"],
    ["scrapers/extract_continental.py"],
    ["scrapers/extract_ueno.py"],
    ["scrapers/extract_ueno_pdf_links.py"],
    ["scrapers/enrich_ueno_from_bases.py"],
    ["promo_backend/normalize.py"],
]


def run_step(script):
    print(f"Running {script}")
    subprocess.run([sys.executable, script], cwd=ROOT, check=True)


def main():
    for step in STEPS:
        run_step(step[0])
    print("Promotion database refresh complete.")


if __name__ == "__main__":
    main()
