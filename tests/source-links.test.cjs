const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('source links reject executable schemes while preserving official URLs',()=>{
 const source=fs.readFileSync('app-web/app.js','utf8');
 const ctx={URL,location:{href:'https://example.test/app/'}};
 vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('function safeSourceUrl('),source.indexOf('function escapeHtml(')),ctx);
 for(const value of ['javascript:alert(1)','JaVaScRiPt:alert(1)','\njavascript:alert(1)','data:text/html,<script>alert(1)</script>','vbscript:msgbox(1)'])assert.equal(ctx.safeSourceUrl(value),'#');
 assert.equal(ctx.safeSourceUrl('https://www.sudameris.com.py/descargas/documentos/example.pdf'),'https://www.sudameris.com.py/descargas/documentos/example.pdf');
});
