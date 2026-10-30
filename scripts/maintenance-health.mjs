import { readFile, writeFile, mkdir, appendFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { validateCatalog } from './publication-snapshot.mjs';

export const EXPECTED_SOURCES = ['GNB', 'Familiar', 'Sudameris', 'Itaú', 'BNF', 'Continental', 'Atlas', 'Coop. Universitaria', 'ueno bank', 'Basa', 'Interfisa', 'Bancop', 'Solar', 'Zeta'];
const NEW_SOURCES = new Set(['Basa', 'Interfisa', 'Bancop', 'Solar', 'Zeta']);

// Operational thresholds, not confirmation that any financial benefit is valid.
export function assessHealth({ manifest, promotions, sources, previous = [], now = new Date() }) {
  const errors = [], warnings = [];
  const ageHours = value => (now - Date.parse(value)) / 3600000;
  try { validateCatalog(manifest, promotions); } catch (error) { errors.push(error.message); }
  if (!Array.isArray(promotions) || !promotions.length) errors.push('Empty catalog; keep the previous published snapshot.');
  const rows = Array.isArray(promotions) ? promotions : [];
  if (previous.length && rows.length < previous.length * 0.5) errors.push('Catalog lost more than 50% of records; review before committing.');
  const generatedAge = ageHours(manifest?.generated_at);
  if (!Number.isFinite(generatedAge) || generatedAge < -1 || generatedAge > 36) errors.push('Catalog generation is invalid or older than 36 hours.');
  const sourceReport = EXPECTED_SOURCES.map(bank => {
    const source = sources?.[bank];
    const count = rows.filter(row => row.bank === bank).length;
    const priorCount = previous.filter(row => row.bank === bank).length;
    const explicitEmpty = NEW_SOURCES.has(bank) && !priorCount && count === 0 && source?.records === 0 && ['blocked', 'partial'].includes(source?.status) && source?.coverage_complete === false;
    if (!source || (!explicitEmpty && (!count || !Number.isInteger(source.records) || source.records <= 0))) errors.push(`${bank}: missing source health or empty data.`);
    if (priorCount && count < priorCount * 0.5) errors.push(`${bank}: lost more than 50% of records; review before committing.`);
    const checkedAge = ageHours(source?.checked_at);
    const fetchAge = ageHours(source?.last_successful_fetch_at || source?.checked_at);
    if (!Number.isFinite(fetchAge) || fetchAge < -1 || fetchAge > 36) warnings.push(`${bank}: no complete successful retrieval within 36 hours.`);
    const attemptAge = ageHours(source?.attempted_at || source?.checked_at);
    if (source?.status !== 'fetched') warnings.push(`${bank}: ${source?.status || 'missing'}; coverage is not complete.`);
    if (!Number.isFinite(checkedAge) || checkedAge < -1 || checkedAge > 72) warnings.push(`${bank}: no complete successful extraction within 72 hours.`);
    if (!Number.isFinite(attemptAge) || attemptAge < -1 || attemptAge > 36) warnings.push(`${bank}: no valid refresh attempt within 36 hours.`);
    return { bank, status: source?.status || 'missing', records: count, previous_records: priorCount, checked_at: source?.checked_at || null, last_successful_fetch_at: source?.last_successful_fetch_at || null, retrieval_status: source?.retrieval_status || 'legacy', attempted_at: source?.attempted_at || source?.checked_at || null };
  });
  const before = new Map(previous.map(row => [row.id, row]));
  const after = new Map(rows.map(row => [row.id, row]));
  return { checked_at: now.toISOString(), safe_to_commit: errors.length === 0, healthy: errors.length === 0 && warnings.length === 0, errors, warnings, catalog_generated_at: manifest?.generated_at, records: rows.length, changes: { added: rows.filter(row => !before.has(row.id)).length, removed: previous.filter(row => !after.has(row.id)).length, modified: rows.filter(row => before.has(row.id) && JSON.stringify(row) !== JSON.stringify(before.get(row.id))).length }, sources: sourceReport };
}

export function healthMarkdown(report) {
  return ['## Payback daily maintenance', '', `Catalog: ${report.catalog_generated_at || 'unavailable'} · ${report.records ?? 0} records`, `Data commit: ${report.safe_to_commit ? 'allowed (partial coverage may remain)' : 'BLOCKED — previous snapshot retained'}`, `Health: ${report.healthy ? 'passed' : 'attention required'}`, '', ...(report.changes ? [`Records added: ${report.changes.added}; modified: ${report.changes.modified}; removed: ${report.changes.removed}. Removed does not necessarily mean expired.`, ''] : []), ...report.errors.map(value => `- ERROR: ${value}`), ...report.warnings.map(value => `- WARNING: ${value}`), '', 'last_successful_fetch_at tracks retrieval; checked_at tracks complete extraction/review, neither guarantees offer validity. Schedule delivery can be delayed. See promotion-audit for source timestamps and details.', ''].join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  let report;
  try {
    const read = async path => JSON.parse(await readFile(path, 'utf8'));
    if (process.env.REFRESH_STARTED_AT) {
      const refresh = await read('outputs/refresh_report.json');
      if (!(Date.parse(refresh.completed_at) >= Date.parse(process.env.REFRESH_STARTED_AT))) throw new Error('Refresh did not finish normalization in this run; previous report is not evidence.');
    }
    report = assessHealth({ manifest: await read('public/manifest.json'), promotions: await read('public/promotions.json'), sources: await read('public/source_status.json'), previous: await read(process.argv[2]) });
  } catch (error) {
    report = { checked_at: new Date().toISOString(), safe_to_commit: false, healthy: false, errors: [`Unable to validate snapshot: ${error.message}`], warnings: [] };
  }
  await mkdir('outputs', { recursive: true });
  await writeFile('outputs/maintenance_report.json', JSON.stringify(report, null, 2) + '\n');
  const markdown = healthMarkdown(report);
  await writeFile('outputs/maintenance_summary.md', markdown);
  if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY, markdown);
  if (process.env.GITHUB_OUTPUT) await appendFile(process.env.GITHUB_OUTPUT, `safe_to_commit=${report.safe_to_commit}\nhealthy=${report.healthy}\n`);
  console.log(markdown);
  if (!report.healthy) process.exitCode = 1;
}
