"""Extract text from GNB terms downloaded through the official website in Chrome."""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path("D:/promos bancos py/gnb-source-pdfs")
MANIFEST = ROOT / "data/gnb_pdf_manifest_2026-09-22.json"
OUTPUT = ROOT / "data/gnb_pdf_text_2026-09-22.json"


def main():
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = list(dict.fromkeys(card["pdf"] for card in manifest))
    documents = {}
    for relative_path in paths:
        match = re.search(r"imagenes/(\d+)_", relative_path)
        if not match:
            raise ValueError(f"Unexpected GNB PDF path: {relative_path}")
        file_id = match.group(1)
        path = PDF_DIR / f"{file_id}.pdf"
        if not path.exists():
            documents[file_id] = {"url": f"https://www.beneficiosbancognb.com.py/{relative_path}", "error": "missing_download"}
            continue
        content = path.read_bytes()
        if not content.startswith(b"%PDF-"):
            documents[file_id] = {"url": f"https://www.beneficiosbancognb.com.py/{relative_path}", "error": "not_pdf"}
            continue
        try:
            reader = PdfReader(path)
            pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
            text = "\n\n".join(pages)
            documents[file_id] = {
                "url": f"https://www.beneficiosbancognb.com.py/{relative_path}",
                "sha256": hashlib.sha256(content).hexdigest(),
                "pages": len(pages),
                "text": text,
                "error": "image_only_or_empty" if len(text.strip()) < 80 else "",
            }
        except Exception as error:
            documents[file_id] = {"url": f"https://www.beneficiosbancognb.com.py/{relative_path}", "error": type(error).__name__}
    result = {"extracted_at": datetime.now(timezone.utc).isoformat(), "documents": documents}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = {file_id: doc["error"] for file_id, doc in documents.items() if doc.get("error")}
    print(f"GNB PDF text: {len(documents)} documents, {len(errors)} extraction issues: {errors}")


if __name__ == "__main__":
    main()
