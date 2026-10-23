export function mergeOfficialFavorites(local, official) {
 const clean = values => [...new Set((Array.isArray(values)?values:[]).filter(x=>typeof x==='string' && x.length>0 && x.length<=160))];
 const imported = new Set(clean(local.importedOfficial));
 const additions = clean(official).filter(id=>!imported.has(id));
 return {...local, favorites:clean([...clean(local.favorites),...additions]), importedOfficial:clean([...imported,...clean(official)])};
}
