import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

// Publication-only overlay. Source evidence, terms and IDs remain intact.
// To reactivate a bank, remove it from public/promotion-suspensions.json and build.
export function applySuspensions(promotions, banks) {
  const suspended = new Set(banks.map(bank => bank.trim().toLowerCase()));
  return promotions.map(promo => {
    const next = { ...promo };
    const previous = next.publication_suspension;
    if (previous) {
      if (previous.had_source_verification) next.source_verification = previous.source_verification;
      else delete next.source_verification;
      delete next.publication_suspension;
    }
    if (suspended.has(String(next.bank || '').trim().toLowerCase())) {
      next.publication_suspension = {
        had_source_verification: Object.hasOwn(next, 'source_verification'),
        source_verification: next.source_verification ?? null,
      };
      // Both existing clients already exclude this state, including cached app code.
      next.source_verification = 'unconfirmed';
    }
    return next;
  });
}

export async function prepareSuspensions(publicDir) {
  const policy = JSON.parse(await readFile(resolve(publicDir, 'promotion-suspensions.json'), 'utf8'));
  if (!Array.isArray(policy.banks) || policy.banks.some(bank => typeof bank !== 'string' || !bank.trim())) {
    throw new Error('Invalid promotion suspension policy');
  }
  const path = resolve(publicDir, 'promotions.json');
  const promotions = JSON.parse(await readFile(path, 'utf8'));
  const next = applySuspensions(promotions, policy.banks);
  if (JSON.stringify(next) !== JSON.stringify(promotions)) {
    await writeFile(path, JSON.stringify(next, null, 2));
    const manifestPath = resolve(publicDir, 'manifest.json');
    const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
    manifest.generated_at = new Date().toISOString();
    await writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  }
  return next.filter(promo => promo.publication_suspension).length;
}
