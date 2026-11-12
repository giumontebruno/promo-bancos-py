const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('candidate account renderer keeps five synthetic favorites without storage or API writes',()=>{
 const source=fs.readFileSync('beta-web/app.js','utf8');
 const start=source.indexOf("window.addEventListener('beta-account', event => {");
 const end=source.indexOf('\n});',start)+4;
 let listener,renders=0;
 const account={favorites:Object.freeze(['fixture-a','fixture-b','fixture-c','fixture-d','fixture-e']),uenoLevel:2};
 const c={window:{addEventListener:(_name,callback)=>listener=callback},state:{},normalizeFavoriteIds:ids=>new Set(ids),syncFavoriteAlerts:()=>{},render:()=>renders++,loadStoredJson:()=>{throw Error('No storage reads expected for authenticated fixture');}};
 vm.createContext(c);vm.runInContext(source.slice(start,end),c);
 listener({detail:account});
 assert.deepEqual([...c.state.favorites],account.favorites);
 assert.equal(c.state.uenoLevel,2);assert.equal(renders,1);
 listener({detail:account});
 assert.equal(c.state.favorites.size,5);assert.equal(account.favorites.length,5);
});
test('read-only QA does not publish a candidate or change official routes',()=>{
 const build=fs.readFileSync('scripts/build.mjs','utf8');
 assert.doesNotMatch(build,/prepareOfficialCandidate|candidate\//);
 assert.match(build,/cp\('app-web', 'dist\/client\/app-web'/);
});
