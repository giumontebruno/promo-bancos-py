const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const create=require('../app-web/map-provider.js');
function fixture(){
 const timers=new Map(),scripts=[];let id=0;
 const win={setTimeout:f=>{timers.set(++id,f);return id},clearTimeout:i=>timers.delete(i)};
 const doc={createElement:()=>({remove(){this.removed=true}}),head:{appendChild:s=>scripts.push(s)}};
 const provider=create({window:win,document:doc,getGoogleKey:()=> 'test-key',timeoutMs:8000});
 return {win,provider,scripts,timers,expire(){for(const [i,f]of [...timers]){timers.delete(i);f()}}};
}
test('Google missing callback is bounded; late callback cannot resolve the failed attempt',async()=>{
 const f=fixture(),result=f.provider.google(),script=f.scripts[0];
 const callback=new URL(script.src).searchParams.get('callback');
 f.expire();assert.equal(await result,false);assert.equal(script.removed,true);
 assert.doesNotThrow(()=>f.win[callback]());
 assert.equal(await result,false);
});
test('Google ready callback resolves once and reuses loaded API',async()=>{
 const f=fixture(),result=f.provider.google();f.win.google={maps:{Map:function(){}}};
 f.win[new URL(f.scripts[0].src).searchParams.get('callback')]();
 assert.equal(await result,true);assert.equal(await f.provider.google(),true);assert.equal(f.scripts.length,1);assert.equal(f.timers.size,0);
});
test('failure of both providers is retryable rather than permanently cached',async()=>{
 const f=fixture();let g=f.provider.google();f.scripts.at(-1).onerror();assert.equal(await g,false);
 let l=f.provider.leaflet();f.scripts.at(-1).onerror();assert.equal(await l,false);
 f.provider.retry();g=f.provider.google();f.scripts.at(-1).onerror();await g;
 l=f.provider.leaflet();f.win.L={map:function(){}};f.scripts.at(-1).onload();assert.equal(await l,true);
 assert.equal(f.scripts.length,4);
});
test('Google auth failure triggers fallback even after the API callback',async()=>{
 const f=fixture();let failures=0;const p=create({window:f.win,document:{createElement:()=>({remove(){}}),head:{appendChild:s=>f.scripts.push(s)}},getGoogleKey:()=> 'test',onGoogleFailure:()=>failures++});
 const ready=p.google();f.win.google={maps:{Map:function(){}}};f.win[new URL(f.scripts[0].src).searchParams.get('callback')]();assert.equal(await ready,true);
 f.win.gm_authFailure();assert.equal(await p.google(),false);assert.equal(failures,1);
});
const source=fs.readFileSync('app-web/app.js','utf8');
test('navigation away and replacement of map DOM cancel stale rendering',async()=>{
 let resolve,draws=0,element={};
 const c={state:{activeView:'nearby'},nearbyMapState:{renderId:1},document:{querySelector:()=>element},ensureGoogleMaps:()=>new Promise(r=>resolve=r),setMapProviderStatus:()=>{},renderGoogleNearbyMap:()=>draws++,cleanupNearbyMaps:()=>{}};
 vm.runInNewContext(source.slice(source.indexOf('async function hydrateNearbyMap('),source.indexOf('function getGoogleMapsApiKey(')),c);
 const first=c.hydrateNearbyMap([],{});c.state.activeView='today';resolve(true);await first;assert.equal(draws,0);
 c.state.activeView='nearby';const second=c.hydrateNearbyMap([],{});element={};resolve(true);await second;assert.equal(draws,0);
 const third=c.hydrateNearbyMap([],{});resolve(true);await third;assert.equal(draws,1);
});
test('branches load while GPS remains pending and concurrent requests share one fetch',async()=>{
 let finishFetch,fetches=0,gps=0;
 const c={state:{activeView:'nearby'},LOCATIONS_URL:'/locations',fetch:()=>{fetches++;return new Promise(r=>finishFetch=r)},render:()=>{},requestLocation:()=>gps++};
 vm.runInNewContext(source.slice(source.indexOf('async function requestNearbyLocationAutomatically('),source.indexOf('async function exploreNearbyManually(')),c);
 vm.runInNewContext(source.slice(source.indexOf('async function loadLocations('),source.indexOf('function toggleFavorite(')),c);
 await c.requestNearbyLocationAutomatically();const concurrent=c.loadLocations();assert.equal(fetches,1);assert.equal(gps,1);
 finishFetch({ok:true,json:async()=>({locations:[]})});await concurrent;
 assert.equal(c.state.locationsLoaded,true);assert.equal(c.state.locationsPromise,null);
});
