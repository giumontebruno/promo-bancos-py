import { build } from 'esbuild';
import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
await mkdir('dist/server', { recursive: true });
// Embed the original artwork so the favicon's circular clipping works standalone.
const faviconArtwork = await readFile('app-web/assets/logos/payback-py-icon-192.png');
await writeFile('app-web/assets/logos/payback-py-favicon.svg', `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><defs><clipPath id="circle"><circle cx="96" cy="96" r="95"/></clipPath></defs><image width="192" height="192" clip-path="url(#circle)" href="data:image/png;base64,${faviconArtwork.toString('base64')}"/></svg>`);
await build({ entryPoints: ['app-web/beta-client.js'], bundle: true, format: 'iife', platform: 'browser', target: 'es2022', outfile: 'app-web/beta-bundle.js', minify: true });
await build({ entryPoints: ['server/index.js'], bundle: true, format: 'esm', platform: 'browser', target: 'es2022', outfile: 'dist/server/index.js' });
await cp('app-web', 'dist/client/app-web', { recursive: true });
await cp('public', 'dist/client/public', { recursive: true });
await writeFile('dist/client/index.html', '<!doctype html><html lang="es"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=https://giumontebruno.github.io/promo-bancos-py/app-web/"><title>Payback PY</title><a href="https://giumontebruno.github.io/promo-bancos-py/app-web/">Payback PY</a></html>');
await mkdir('dist/.openai', { recursive: true });
await cp('.openai/hosting.json', 'dist/.openai/hosting.json');
await cp('drizzle', 'dist/.openai/drizzle', { recursive: true });
console.log('Built Payback PY and notification service.');
