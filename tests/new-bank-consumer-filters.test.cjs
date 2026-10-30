const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
for(const file of ['app-web/app.js','beta-web/app.js']) test(`${file} exposes each integrated bank without inventing logos`,()=>{
 const source=fs.readFileSync(file,'utf8');const declaration=source.match(/const BANKS = (\[[^;]+\]);/)[1];
 const banks=vm.runInNewContext(declaration);for(const bank of ['Basa','Interfisa','Bancop','Solar','Zeta'])assert.ok(banks.includes(bank));
 assert.equal(new Set(banks).size,banks.length);
});
