const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const path of ['app-web/app.js','beta-web/app.js']){
 const source=fs.readFileSync(path,'utf8');
 test(`${path}: missing legacy favorite keeps saved ID, no invented migration`,()=>{
  const ctx={Set,state:{favorites:new Set(['legacy-unavailable']),favoriteAliases:{},promotions:[]}};
  vm.runInNewContext(source.slice(source.indexOf('function favoriteKey('),source.indexOf('function matchesSelectedDay(')),ctx);
  assert.equal(ctx.canonicalFavoriteId('legacy-unavailable'),'legacy-unavailable');
  assert.deepEqual([...ctx.normalizeFavoriteIds(ctx.state.favorites)],['legacy-unavailable']);
  assert.equal(ctx.state.favorites.size,1);
 });
 test(`${path}: empty favorites distinguish absent offers from never saved`,()=>{
  const start=source.indexOf('  if (!base.length) {');
  const end=source.indexOf('\n  els.results.innerHTML = (state.activeView',start);
  const ctx={base:[],hasQuery:false,escapeHtml:x=>x,state:{activeView:'favorites',favorites:new Set(['legacy-unavailable']),query:''},els:{results:{}}};
  vm.runInNewContext(`function renderEmpty(){${source.slice(start,end)}}`,ctx);
  ctx.renderEmpty();assert.match(ctx.els.results.innerHTML,/Tus favoritos siguen guardados/);assert.equal(ctx.state.favorites.size,1);
  ctx.state.favorites.clear();ctx.renderEmpty();assert.match(ctx.els.results.innerHTML,/Todavía no guardaste/);
  ctx.state.favorites.add('legacy-unavailable');ctx.state.activeView='search';ctx.renderEmpty();assert.match(ctx.els.results.innerHTML,/estos filtros/);assert.doesNotMatch(ctx.els.results.innerHTML,/siguen guardados/);
 });
}
