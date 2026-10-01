"""Expose current UENO category pages to the terms enrichment pipeline."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "work/ueno_monthly_sources.json"
OUT = ROOT / "work/ueno_pdf_links.csv"


def main():
    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    rows = [{"Página PDF": source["index"], "URL": source["page_url"]} for source in sources]
    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Página PDF", "URL"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"UENO: {len(rows)} category links -> {OUT}")


if __name__ == "__main__":
    main()
