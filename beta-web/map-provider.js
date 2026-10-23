(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else root.PaybackMapProvider = { create: factory };
})(typeof window === 'undefined' ? globalThis : window, function createMapProvider(options) {
  const win = options.window;
  const doc = options.document;
  const timeout = options.timeoutMs || 8000;
  let googlePromise = null, leafletPromise = null, serial = 0, googleFailed = false;
  let rejectGoogle = null;
  const hasGoogle = () => typeof win.google?.maps?.Map === 'function' && !googleFailed;
  const hasLeaflet = () => typeof win.L?.map === 'function';
  function load(url, ready, callback) {
    return new Promise(resolve => {
      const script = doc.createElement('script');
      let settled = false;
      const finish = success => {
        if (settled) return;
        settled = true;
        win.clearTimeout(timer);
        script.onerror = script.onload = null;
        if (callback) win[callback] = () => {}; // A late response must be harmless.
        if (!success) script.remove();
        resolve(success);
      };
      const timer = win.setTimeout(() => finish(false), timeout);
      if (callback) {
        win[callback] = () => finish(ready());
        rejectGoogle = () => finish(false);
      } else script.onload = () => finish(ready());
      script.onerror = () => finish(false);
      script.src = url;
      script.async = true;
      doc.head.appendChild(script);
    });
  }
  win.gm_authFailure = () => {
    if (googleFailed) return;
    googleFailed = true;
    rejectGoogle?.();
    options.onGoogleFailure?.();
  };
  return {
    google() {
      if (googleFailed) return Promise.resolve(false);
      if (hasGoogle()) return Promise.resolve(true);
      const key = options.getGoogleKey();
      if (!key) return Promise.resolve(false);
      if (!googlePromise) {
        const callback = `paybackGoogleMapsReady${Date.now()}_${++serial}`;
        googlePromise = load(`https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&callback=${callback}`, hasGoogle, callback);
      }
      return googlePromise;
    },
    leaflet() {
      if (hasLeaflet()) return Promise.resolve(true);
      if (!leafletPromise) leafletPromise = load('./vendor/leaflet/leaflet.js', hasLeaflet);
      return leafletPromise;
    },
    retry() {
      googlePromise = leafletPromise = null;
      googleFailed = false;
    },
  };
});
