import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const DATA_FILES = ['manifest.json', 'promotions.json', 'source_status.json', 'locations.json'];
export const sha256 = value => createHash('sha256').update(value).digest('hex');

export function validateCatalog(manifest, promotions) {
  if (!Number.isFinite(Date.parse(manifest.generated_at))) throw new Error('Invalid catalog generation timestamp');
  if (!Array.isArray(promotions) || manifest.promotion_count !== promotions.length) throw new Error('Manifest/catalog record count mismatch');
  const ids = promotions.map(p => p.id);
  if (ids.some(id => !id) || new Set(ids).size !== ids.length) throw new Error('Missing or duplicate promotion IDs');
}

// Proves packaging identity, not bank accuracy or eligibility of any offer.
export async function stampSnapshot(sourceDir, publishedDir, revision = process.env.PAYBACK_BUILD_REVISION || process.env.GITHUB_SHA || 'local') {
  const files = {};
  for (const name of DATA_FILES) {
    const source = await readFile(resolve(sourceDir, name));
    const published = await readFile(resolve(publishedDir, 'public', name));
    if (sha256(source) !== sha256(published)) throw new Error(`Published copy differs: ${name}`);
    files[name] = { sha256: sha256(source), bytes: source.length };
  }
  const manifest = JSON.parse(await readFile(resolve(sourceDir, 'manifest.json'), 'utf8'));
  const promotions = JSON.parse(await readFile(resolve(sourceDir, 'promotions.json'), 'utf8'));
  validateCatalog(manifest, promotions);
  const result = { schema_version: 1, revision, built_at: new Date().toISOString(), catalog_generated_at: manifest.generated_at, promotion_count: promotions.length, files };
  await writeFile(resolve(publishedDir, 'publication.json'), JSON.stringify(result, null, 2) + '\n');
  return result;
}

export async function verifyPublished(baseUrl, expected, fetcher = fetch) {
  const base = new URL(baseUrl);
  if (base.protocol !== 'https:') throw new Error('Publication verification requires HTTPS');
  const read = async path => {
    const url = new URL(path, base.href.endsWith('/') ? base : base.href + '/');
    url.searchParams.set('publication_check', `${expected.revision}-${Date.now()}`);
    const response = await fetcher(url, { cache: 'no-store', signal: AbortSignal.timeout(20000) });
    if (!response.ok) throw new Error(`Published ${path}: HTTP ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
  };
  const actual = JSON.parse((await read('publication.json')).toString('utf8'));
  if (actual.revision !== expected.revision || actual.catalog_generated_at !== expected.catalog_generated_at || actual.promotion_count !== expected.promotion_count) throw new Error('Published snapshot is not the expected deployment');
  for (const name of DATA_FILES) {
    if (sha256(await read(`public/${name}`)) !== expected.files[name].sha256) throw new Error(`Published data differs: ${name}`);
  }
  return { revision: actual.revision, catalog_generated_at: actual.catalog_generated_at, promotion_count: actual.promotion_count };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const [command, first, second] = process.argv.slice(2);
  if (command !== 'verify' || !first || !second) throw new Error('Usage: node scripts/publication-snapshot.mjs verify HTTPS_BASE_URL EXPECTED_PUBLICATION_JSON');
  const expected = JSON.parse(await readFile(second, 'utf8'));
  let lastError;
  for (let attempt = 0; attempt < 6; attempt++) {
    try { console.log(JSON.stringify(await verifyPublished(first, expected))); lastError = null; break; }
    catch (error) { lastError = error; if (attempt < 5) await new Promise(resolve => setTimeout(resolve, 10000)); }
  }
  if (lastError) throw lastError;
}
