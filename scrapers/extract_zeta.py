"""Fail-closed Zeta source monitor; its current brochure has no stated validity.

The PDF below was discovered through the public Beneficios link on 2026-10-30,
not guessed from indexed historical files. Never import an undated brochure as
current discounts. A future parser needs dated terms and visual merchant mapping.
"""
try:
    from .bancop_solar_zeta_common import fetch,pdf_text,digest,export
except ImportError:
    from bancop_solar_zeta_common import fetch,pdf_text,digest,export
PAGE='https://www.zbanco.com.py/site?page=tarjetas'
BROCHURE='https://www.zbanco.com.py/uploads/55ba16aa-25d7-4192-9953-12a4c07d84c4.pdf'

def main():
    blob=fetch(BROCHURE).content
    text=pdf_text(blob)
    export('zeta',[],{'status':'blocked','coverage_complete':False,'source_page_url':PAGE,
        'brochure_url':BROCHURE,'sha256':digest(blob),'extracted_text_length':len(text),
        'reason':'Live JS catalog link needs rediscovery; linked brochure lacks explicit validity and merchant identities are logos. No current offers asserted.'})
if __name__=='__main__':main()
