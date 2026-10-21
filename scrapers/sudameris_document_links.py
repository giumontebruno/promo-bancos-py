"""Helper: discover linked official documents; verify before parsing."""
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import requests

OFFICIAL_HOSTS={"sudameris.com.py","www.sudameris.com.py"}
def document_links(html,base_url):
    """Return all candidate links, including malformed hosts for visible diagnostics."""
    found=[]
    for a in BeautifulSoup(html,"html.parser").select("a[href]"):
        url=urljoin(base_url,a["href"])
        path=urlparse(url).path.lower()
        if path.endswith(".pdf") or path.startswith("/descargas/documentos/"):
            if url not in found:found.append(url)
    return found

def fetch_pdf(url,session=requests):
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in OFFICIAL_HOSTS or parsed.username or parsed.password:
        raise ValueError("Unexpected Sudameris document host; review original link: "+url)
    response=session.get(url,timeout=45,allow_redirects=False)
    # Never follow a redirect to an unrelated host implicitly.
    if 300<=response.status_code<400:
        raise ValueError("Sudameris document redirect requires review: "+url)
    response.raise_for_status()
    mime=response.headers.get("Content-Type","").split(";",1)[0].strip().lower()
    if mime not in {"application/pdf","application/octet-stream"}:
        raise ValueError("Sudameris document has non-PDF content type: "+mime)
    if not response.content.lstrip().startswith(b"%PDF-"):
        raise ValueError("Sudameris document has non-PDF content bytes: "+url)
    return response.content
