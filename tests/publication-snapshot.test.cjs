const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const os=require('node:os');
const lib=()=>import('../scripts/publication-snapshot.mjs');

test('publication validates counts and IDs instead of trusting a fresh timestamp',async()=>{
 const {validateCatalog}=await lib();
 const m={generated_at:'2026-10-30T00:00:00Z',promotion_count:1};
 assert.doesNotThrow(()=>validateCatalog(m,[{id:'a'}]));
 assert.throws(()=>validateCatalog(m,[]),/count mismatch/);
 assert.throws(()=>validateCatalog({...m,promotion_count:2},[{id:'a'},{id:'a'}]),/duplicate/);
 assert.throws(()=>validateCatalog({...m,generated_at:'today'},[{id:'a'}]),/timestamp/);
});

test('build stamps only byte-identical copies and detects stale packaging',async()=>{
 const {stampSnapshot,DATA_FILES}=await lib();const root=await fs.mkdtemp(path.join(os.tmpdir(),'payback-publication-'));
 try {
  const source=path.join(root,'source'),out=path.join(root,'dist');await fs.mkdir(source);await fs.mkdir(path.join(out,'public'),{recursive:true});
  const payloads={'manifest.json':{generated_at:'2026-10-30T00:00:00Z',promotion_count:1},'promotions.json':[{id:'a'}],'source_status.json':{banks:[{status:'failed',checked_at:'2026-10-20'}]},'locations.json':{locations:[]}};
  for(const name of DATA_FILES){const bytes=JSON.stringify(payloads[name]);await fs.writeFile(path.join(source,name),bytes);await fs.writeFile(path.join(out,'public',name),bytes);}
  const stamp=await stampSnapshot(source,out,'revision-a');assert.equal(stamp.promotion_count,1);assert.equal(stamp.revision,'revision-a');
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(out,'publication.json'),'utf8')),stamp);
  await fs.writeFile(path.join(out,'public/promotions.json'),'[]');await assert.rejects(stampSnapshot(source,out,'revision-a'),/copy differs/);
 } finally {await fs.rm(root,{recursive:true,force:true});}
});

test('post-deploy check rejects stale CDN data even with new publication metadata',async()=>{
 const {verifyPublished,DATA_FILES,sha256}=await lib();const bytes=Buffer.from('{}');const expected={revision:'new',catalog_generated_at:'2026-10-30T00:00:00Z',promotion_count:1,files:Object.fromEntries(DATA_FILES.map(f=>[f,{sha256:sha256(bytes)}]))};
 const fetcher=async url=>({ok:true,status:200,arrayBuffer:async()=>url.pathname.endsWith('/publication.json')?Buffer.from(JSON.stringify(expected)):bytes});
 assert.equal((await verifyPublished('https://example.org/payback/',expected,fetcher)).revision,'new');
 const stale=async url=>({ok:true,status:200,arrayBuffer:async()=>url.pathname.endsWith('/publication.json')?Buffer.from(JSON.stringify(expected)):Buffer.from('[]')});
 await assert.rejects(verifyPublished('https://example.org/payback/',expected,stale),/Published data differs/);
 const old=async()=>({ok:true,status:200,arrayBuffer:async()=>Buffer.from(JSON.stringify({...expected,revision:'old'}))});
 await assert.rejects(verifyPublished('https://example.org/payback/',expected,old),/not the expected/);
 await assert.rejects(verifyPublished('http://example.org',expected,fetcher),/HTTPS/);
});

test('Pages workflow pins trusted main and verifies catalog after deployment',async()=>{
 const yml=await fs.readFile(path.join(__dirname,'../.github/workflows/deploy-pages.yml'),'utf8');
 assert.match(yml,/head_repository.full_name == github.repository/);assert.match(yml,/head_branch == 'main'/);assert.match(yml,/ref: main/);assert.match(yml,/PAYBACK_BUILD_REVISION=\$\(git rev-parse HEAD\)/);
 assert.ok(yml.indexOf('publication-snapshot.mjs verify')>yml.indexOf('uses: actions/deploy-pages@v4'));
});
