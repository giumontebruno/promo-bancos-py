const {test} = require('node:test');
const assert = require('node:assert/strict');
const {mkdtempSync,rmSync,readFileSync,writeFileSync} = require('node:fs');
const {tmpdir} = require('node:os');
const {join,resolve} = require('node:path');
const {execFileSync,spawnSync} = require('node:child_process');

test('guard allows unchanged main but blocks any advancement without rebasing',()=>{
 const dir=mkdtempSync(join(tmpdir(),'payback-revision-'));
 const origin=join(dir,'origin'), checkout=join(dir,'checkout');
 const script=resolve('scripts/guard-refresh-revision.mjs');
 const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 try{
  git(dir,'init','-b','main',origin);
  git(origin,'config','user.email','test@example.invalid');git(origin,'config','user.name','Test');
  git(origin,'commit','--allow-empty','-m','baseline');git(dir,'clone',origin,checkout);
  const initial=git(checkout,'rev-parse','HEAD');
  const output=join(dir,'result');
  const run=()=>spawnSync(process.execPath,[script],{cwd:checkout,env:{...process.env,GITHUB_OUTPUT:output,GITHUB_STEP_SUMMARY:''}});
  assert.equal(run().status,0);
  git(origin,'commit','--allow-empty','-m','newer main');
  assert.equal(run().status,1);
  assert.equal(git(checkout,'rev-parse','HEAD'),initial);
  assert.match(readFileSync(output,'utf8'),/current=true\ncurrent=false\n/);
  git(checkout,'remote','set-url','origin',join(dir,'missing-origin'));
  assert.equal(run().status,1);
 }finally{rmSync(dir,{recursive:true,force:true});}
});

test('workflow requires both data safety and current revision, with no checkout/pull reset',()=>{
 const workflow=readFileSync('.github/workflows/refresh-promotions.yml','utf8');
 assert.match(workflow,/if: steps\.health\.outputs\.safe_to_commit == 'true' && steps\.revision\.outputs\.current == 'true'/);
 assert.match(workflow,/skip_fetch: true/);assert.match(workflow,/skip_checkout: true/);
 assert.match(workflow,/steps\.revision\.outcome != 'success'/);
});
