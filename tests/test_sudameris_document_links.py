import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.dont_write_bytecode=True
from scrapers import sudameris_document_links as links
from scrapers import sudameris_campaigns as campaigns

def response(data,mime="application/pdf",code=200):
 r=Mock(status_code=code,headers={"Content-Type":mime},content=data);r.raise_for_status=Mock();return r
class LinkTests(unittest.TestCase):
 def test_extensionless_links_are_discovered_and_deduplicated(self):
  url="https://www.sudameris.com.py/descargas/documentos/concepcion-bases-y-condiciones"
  html=f'<a href="{url}">Bases</a><a href="{url}">Bases</a>'
  self.assertEqual(links.document_links(html,url),[url])
 def test_reject_html_even_when_url_or_mime_says_pdf(self):
  for data,mime in [(b"<html>404</html>","application/pdf"),(b"%PDF-1.7\n","text/html")]:
   s=Mock();s.get.return_value=response(data,mime)
   with self.assertRaisesRegex(ValueError,"non-PDF"):links.fetch_pdf("https://www.sudameris.com.py/descargas/documentos/example",s)
 def test_wrong_host_and_redirect_are_not_followed(self):
  s=Mock()
  with self.assertRaisesRegex(ValueError,"host"):links.fetch_pdf("https://www.sudamerispy.ad/descargas/documentos/encarnacion",s)
  s.get.assert_not_called()
  s.get.return_value=response(b"","text/html",302)
  with self.assertRaisesRegex(ValueError,"redirect"):links.fetch_pdf("https://www.sudameris.com.py/descargas/documentos/example",s)
  self.assertFalse(s.get.call_args.kwargs["allow_redirects"])
 def test_multidocument_north_cannot_silently_publish_first_city_only(self):
  row={"URL":"old-identity","URL fuente actual":"https://www.sudameris.com.py/personas/beneficios/zona-norte","Comercio/Promocion":"ZONA NORTE"}
  r=Mock(text='<a href="/descargas/documentos/one">One</a><a href="/descargas/documentos/two">Two</a>')
  with patch.object(campaigns.requests,"get",return_value=r),patch.object(campaigns,"merchant_rows") as parse:
   with self.assertRaisesRegex(ValueError,"per-city"):campaigns.expand_campaign(row)
   parse.assert_not_called()
 def test_single_document_preserves_old_identity_and_parser_dates(self):
  url="https://www.sudameris.com.py/descargas/documentos/example";identity="https://www.sudameris.com.py/storage/app/uploads/public/old.pdf"
  row={"URL":"oldpage","URL fuente actual":"https://www.sudameris.com.py/personas/beneficios/example","Comercio/Promocion":"TEST","Bases URL identidad":identity}
  source=Mock(text=f'<a href="{url}">Bases y Condiciones</a>')
  parsed=[{"URL":identity,"Vigencia":"Desde 2026-01-01 hasta 2026-12-31"}]
  with patch.object(campaigns.requests,"get",return_value=source),patch.object(campaigns,"fetch_pdf",return_value=b"pdf"),patch.object(campaigns,"merchant_rows",return_value=parsed) as parse:
   actual=campaigns.expand_campaign(row)
  parse.assert_called_once_with(b"pdf",identity,"TEST")
  self.assertEqual(actual[0]["URL"],identity)
  self.assertEqual(actual[0]["Vigencia"],"Desde 2026-01-01 hasta 2026-12-31")
if __name__=="__main__":unittest.main()
