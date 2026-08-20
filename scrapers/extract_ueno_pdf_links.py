import csv
from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path("work/ueno_beneficios_agosto2026.pdf")
OUT = Path("work/ueno_pdf_links.csv")


def main():
    reader = PdfReader(str(PDF_PATH))
    rows = []
    for page_idx, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots") or []
        for annot_ref in annots:
            annot = annot_ref.get_object()
            action = annot.get("/A") or {}
            uri = action.get("/URI")
            if uri:
                rows.append({"Página PDF": page_idx, "URL": str(uri)})
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Página PDF", "URL"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} links -> {OUT}")
    for row in rows:
        print(row["Página PDF"], row["URL"])


if __name__ == "__main__":
    main()
