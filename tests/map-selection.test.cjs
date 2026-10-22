const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app-web/app.js', 'utf8');
const points = [{place:{name:'A',lat:-25.3,lng:-57.6},promos:[],banks:[]}, {place:{name:'B',lat:-25.4,lng:-57.7},promos:[],banks:[]}];
function harness(provider, location = null) {
  const maps = [], markers = [], timers = [];
  class MapMock {
    constructor(el, options) { this.zoom=options.zoom; this.center=options.center; this.fits=0; maps.push(this); }
    getZoom(){return this.zoom;}
    setZoom(z){this.zoom=z;}
    setView(center,zoom){this.center=center;this.zoom=zoom;return this;}
    fitBounds(){this.fits++;this.zoom=9;}
    remove(){}
    invalidateSize(){}
  }
  class MarkerMock {
    constructor(options){this.position=options.position;markers.push(this);}
    addListener(type,fn){this[type]=fn;}
    on(type,fn){this[type]=fn;return this;}
    addTo(){return this;}
    getPosition(){return this.position;}
    remove(){}
    setMap(){}
  }
  const element={};
  const c={state:{location,activeView:'nearby',locationsLoaded:true},nearbyMapState:{markers:[],googleMarkers:[],renderId:0},
    document:{querySelector:()=>element},window:{clearTimeout(){},setTimeout(fn){timers.push(fn);}},setMapProviderStatus:()=>{},
    getPointKey:i=>i?.place.name,getMapVisiblePoints:p=>p,getGoogleMarkerIcon:()=>({}),
    getPointPrimaryPromo:()=>null,getBankTheme:()=>({main:'red'}),getDominantPromoCategory:()=> 'test',CATEGORY_ICONS:{test:'test'},ICON_PATHS:{test:''},escapeAttribute:s=>s,isSelectedPoint:()=>false};
  c.window.google={maps:{Map:MapMock,Marker:MarkerMock,LatLngBounds:class {extend(){} isEmpty(){return false;}},SymbolPath:{CIRCLE:0},event:{addListenerOnce:(m,e,fn)=>timers.push(fn)}}};
  c.window.L={map:(el,o)=>new MapMock(el,o),marker:(pos,o)=>new MarkerMock({position:pos}),circleMarker:(pos)=>new MarkerMock({position:pos}),divIcon:o=>o,latLngBounds:x=>x,tileLayer:()=>({on(){return this;},addTo(){}})};
  function load(a,b){vm.runInNewContext(source.slice(source.indexOf(`function ${a}(`),source.indexOf(`function ${b}(`)),c);}
  load('cleanupNearbyMaps','getGoogleMarkerIcon');
  load('renderLeafletNearbyMap','getDominantPromoCategory');
  load('renderNearbyView','getNearbyActiveFilterText');
  Object.assign(c,{els:{results:{},statusText:{},countText:{}},getNearbyPromoPoints:()=>points,KNOWN_LOCAL_POINTS:[],renderIcon:()=>'',renderNearbySelectedPlace:()=>'',renderNearbyPlaceButton:()=>'',hydrateNearbyMap:(p,selected,focus)=>c[provider](p,selected,focus)});
  return {c,maps,markers,timers};
}
for (const provider of ['renderGoogleNearbyMap','renderLeafletNearbyMap']) {
  for (const zoom of [10,18]) for (const location of [null,{lat:-25,lng:-57}]) {
    test(`${provider}: shop click at zoom ${zoom}, GPS ${!!location}, retains focus through rerender`,()=>{
      const {c,maps,markers,timers}=harness(provider,location);
      c.renderNearbyView();
      assert.equal(maps.at(-1).fits,1,'initial overview fits all points');
      maps.at(-1).zoom=zoom;
      markers[1].click();
      const selected=maps.at(-1);
      assert.equal(selected.zoom,Math.max(16,zoom));
      assert.equal(selected.fits,0,'selection never fits the global bounds');
      assert.equal(c.state.activePlaceName,'B');
      const center=selected.center;
      assert.equal(Array.isArray(center)?center[0]:center.lat,points[1].place.lat);
      assert.equal(Array.isArray(center)?center[1]:center.lng,points[1].place.lng);
      timers.forEach(fn=>fn());
      assert.equal(selected.zoom,Math.max(16,zoom),'delayed callbacks cannot reset selection');
      c.renderNearbyView();
      assert.equal(maps.at(-1).fits,1,'normal filter render still fits results');
    });
  }
}

for (const provider of ['renderGoogleNearbyMap','renderLeafletNearbyMap']) {
  test(`${provider}: list selection without map and obsolete selection`,()=>{
    const {c,maps}=harness(provider);
    c.selectNearbyPlace('B');
    assert.equal(maps.at(-1).zoom,16);
    assert.equal(maps.at(-1).fits,0);
    c.selectNearbyPlace('filtered-out');
    assert.equal(maps.at(-1).fits,1,'missing selected shop does not focus a replacement shop');
  });
}
test('Google to Leaflet fallback carries the selection and honors tile zoom limit',async()=>{
  const {c,maps}=harness('renderGoogleNearbyMap');
  vm.runInNewContext(source.slice(source.indexOf('async function hydrateNearbyMap('),source.indexOf('function getGoogleMapsApiKey(')),c);
  c.ensureGoogleMaps=async()=>true;
  c.getMapProvider=()=>({leaflet:async()=>true});
  c.renderGoogleNearbyMap=()=>{throw new Error('Google unavailable');};
  await c.hydrateNearbyMap(points,points[1].place,{pointKey:'B',zoom:20});
  assert.equal(maps.at(-1).zoom,19);
  assert.equal(maps.at(-1).fits,0);
});
test('late provider completion cannot overwrite a newer selection',async()=>{
  const {c,maps}=harness('renderGoogleNearbyMap');
  vm.runInNewContext(source.slice(source.indexOf('async function hydrateNearbyMap('),source.indexOf('function getGoogleMapsApiKey(')),c);
  let resolve;
  c.ensureGoogleMaps=()=>new Promise(r=>{resolve=r;});
  const pending=c.hydrateNearbyMap(points,points[0].place,{pointKey:'A',zoom:16});
  c.nearbyMapState.renderId++;
  resolve(true);
  await pending;
  assert.equal(maps.length,0);
});
test('late Google authorization failure retains shop focus during fallback',()=>{
  const {c,maps}=harness('renderGoogleNearbyMap');
  let failure;
  c.window.PaybackMapProvider={create:options=>{failure=options.onGoogleFailure;return {};}};
  c.getGoogleMapsApiKey=()=>'';
  vm.runInNewContext(source.slice(source.indexOf('function getMapProvider('),source.indexOf('function setMapProviderStatus(')),c);
  c.getMapProvider();
  c.selectNearbyPlace('B');
  maps.at(-1).zoom=18;
  c.hydrateNearbyMap=(p,selected,focus)=>c.renderLeafletNearbyMap(p,selected,focus);
  failure();
  assert.equal(maps.at(-1).zoom,18);
  assert.equal(maps.at(-1).fits,0);
  assert.equal(maps.at(-1).center[0],points[1].place.lat);
  c.renderNearbyView();
  assert.equal(c.nearbyMapState.selection,null,'filter render clears selection camera intent');
});
