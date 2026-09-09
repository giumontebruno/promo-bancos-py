(function (root) {
  const TOKEN_KEY = 'paybackPy.deviceToken';
  const ENABLED_KEY = 'paybackPy.pushEnabled';
  let endpointPromise;
  async function endpoint() {
    if (!endpointPromise) endpointPromise = fetch('./notifications-config.json', { cache: 'no-store', signal: AbortSignal.timeout(12000) }).then(async response => {
      if (!response.ok) throw new Error('Los avisos todavía no están disponibles.');
      const config = await response.json();
      const url = new URL(config.serviceUrl);
      if (url.protocol !== 'https:') throw new Error('El servicio de avisos no está disponible.');
      return url.origin;
    }).catch(error => { endpointPromise = null; throw error; });
    return endpointPromise;
  }
  function token() {
    let value = localStorage.getItem(TOKEN_KEY);
    if (!value) {
      value = [...crypto.getRandomValues(new Uint8Array(32))].map(n => n.toString(16).padStart(2, '0')).join('');
      localStorage.setItem(TOKEN_KEY, value);
    }
    return value;
  }
  function supported() { return 'serviceWorker' in navigator && 'PushManager' in root && 'Notification' in root; }
  function enabled() { return localStorage.getItem(ENABLED_KEY) === 'true'; }
  function registrationReady() {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('No pudimos preparar los avisos. Recargá la app e intentá nuevamente.')), 12000);
      navigator.serviceWorker.ready.then(value => { clearTimeout(timer); resolve(value); }, error => { clearTimeout(timer); reject(error); });
    });
  }
  async function sync(favorites, uenoLevel) {
    if (!enabled() || !supported()) return;
    const registration = await registrationReady();
    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) { localStorage.removeItem(ENABLED_KEY); return; }
    const response = await fetch((await endpoint()) + '/api/push/device', {
      method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token() },
      body: JSON.stringify({ subscription: subscription.toJSON(), favorites: [...favorites].slice(0, 100), uenoLevel }),
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) throw new Error('No pudimos sincronizar tus avisos. Intentá nuevamente.');
  }
  async function enable(favorites, uenoLevel) {
    if (!supported()) throw new Error('Para recibir avisos en iPhone, agregá Payback a la pantalla de inicio y abrila desde allí.');
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Los avisos están desactivados en los permisos de este navegador.');
    const response = await fetch((await endpoint()) + '/api/push/config', { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error('El servicio de avisos no está disponible.');
    const config = await response.json();
    if (!config.enabled || !config.publicKey) throw new Error('El servicio de avisos está en preparación.');
    const registration = await registrationReady();
    const decoded = atob(config.publicKey.replace(/-/g, '+').replace(/_/g, '/'));
    const applicationServerKey = Uint8Array.from(decoded, c => c.charCodeAt(0));
    await registration.pushManager.getSubscription() || await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey });
    localStorage.setItem(ENABLED_KEY, 'true');
    try { await sync(favorites, uenoLevel); } catch (error) { localStorage.removeItem(ENABLED_KEY); throw error; }
  }
  async function disable() {
    const response = await fetch((await endpoint()) + '/api/push/device', {
      method: 'DELETE', headers: { Authorization: 'Bearer ' + token() }, signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) throw new Error('No se pudieron desactivar los avisos. Intentá nuevamente.');
    const registration = await registrationReady();
    const subscription = await registration.pushManager.getSubscription();
    await subscription?.unsubscribe();
    localStorage.removeItem(ENABLED_KEY);
  }
  root.PaybackPush = { enable, disable, sync, enabled, supported };
})(globalThis);
