const DATA_URL = "../public/promotions.json";
const MANIFEST_URL = "../public/manifest.json";
const LOCATIONS_URL = "../public/locations.json";
const STORAGE_KEYS = {
  user: "paybackPy.user",
  favorites: "paybackPy.favorites",
  alertPrefs: "paybackPy.alertPrefs",
};
const DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
const BANKS = ["Todos", "ueno bank", "Itaú", "Continental", "Sudameris", "BNF", "Atlas", "Coop. Universitaria"];
const PREMIUM_CATEGORY = "Club Black";
const KNOWN_PLACES = [
  { name: "Shopping del Sol", lat: -25.28288, lng: -57.56706, terms: ["del sol", "delsol", "shopping del sol", "shopping delsol"] },
  { name: "Paseo La Galería", lat: -25.2819, lng: -57.5638, terms: ["paseo la galeria", "paseo la galería", "la galeria", "la galería", "paseo galeria"] },
  { name: "Shopping Mariscal", lat: -25.2964, lng: -57.5814, terms: ["shopping mariscal", "mariscal", "gastro mariscal", "shopping mariscal lopez", "shopping mariscal lópez"] },
  { name: "Pinedo Shopping", lat: -25.32396, lng: -57.52098, terms: ["pinedo", "pinedo shopping", "shopping pinedo"] },
  { name: "Shopping Mariano", lat: -25.2076, lng: -57.5323, terms: ["shopping mariano", "mariano", "shopping mariano roque alonso"] },
  { name: "Multiplaza", lat: -25.29831, lng: -57.55011, terms: ["multiplaza", "shopping multiplaza"] },
  { name: "Villa Morra", lat: -25.29338, lng: -57.58125, terms: ["villa morra", "villamorra", "shopping villa morra", "shopping villamorra"] },
];
const KNOWN_LOCAL_POINTS = [
  ...KNOWN_PLACES,
  { name: "CIT", lat: -25.28935, lng: -57.60074, terms: ["club internacional de tenis", "cit", "tl sports cit", "provisión cars cit", "provision cars cit", "asismed sucursal cit"] },
  { name: "Asunción Tenis Club", lat: -25.2871, lng: -57.6087, terms: ["asuncion tenis club", "asunción tenis club"] },
  { name: "Club Cerro Porteño", lat: -25.2979, lng: -57.6591, terms: ["cerro porteño", "cerro porteno", "club cerro porteño"] },
  { name: "Club Olimpia", lat: -25.2912, lng: -57.6426, terms: ["club olimpia", "olimpia"] },
  { name: "Distrito Perseverancia", lat: -25.28763, lng: -57.58251, terms: ["distrito perseverancia", "perseverancia"] },
  { name: "Casa Rica Molas López", lat: -25.27381, lng: -57.57173, terms: ["casa rica molas", "molas lópez", "molas lopez"] },
  { name: "Superseis Los Laureles", lat: -25.2998, lng: -57.5706, terms: ["los laureles", "superseis los laureles"] },
];
const CATEGORY_GROUPS = [
  ["Todas", []],
  ["Supermercados", ["super", "mayorista", "delimarket", "stock", "real", "contimarket"]],
  ["Combustible", ["combustible", "estacion", "estaciones", "shell", "puma flota"]],
  ["Farmacias", ["farmacia", "farmacias", "perfumeria", "perfumerías"]],
  ["Gastronomía", ["gastronomia", "gastronomía", "cafeteria", "cafeterías", "heladeria", "heladerías"]],
  ["Tiendas", ["tienda", "tiendas", "moda", "indumentaria", "shopping", "shoppings", "joyeria", "joyerías", "joyas", "niños", "jugueteria", "jugueterías"]],
  ["Hogar y construcción", ["hogar", "construccion", "construcción", "ferreteria", "ferreterías", "muebleria", "mueblerías", "industrial"]],
  ["Tecnología", ["tecnologia", "tecnología", "electronica", "electrónica"]],
  ["Clubes sociales", ["clubes", "deportes y clubes", "club social", "club deportivo", "country club", "centro social", "cit", "club internacional de tenis", "asuncion tenis club", "asunción tenis club", "cerro porteño", "cerro porteno", "olimpia"]],
  ["Entretenimiento", ["entretenimiento", "eventos", "teatro", "deportes", "academia", "gym", "gimnasio", "pilates", "feria", "caza", "pesca"]],
  ["Viajes", ["viaje", "viajes", "turismo", "hoteles", "hotel", "cabaña", "cabañas", "aéreas", "aereas"]],
  ["Salud y belleza", ["salud", "belleza", "peluqueria", "peluquerías", "spa", "spas", "veterinaria", "veterinarias"]],
  ["Servicios", ["educacion", "educación", "seguros", "municipalidades", "juridicos", "jurídicos", "inmobiliarias", "vehículos", "vehiculos"]],
  ["Especiales", ["beneficios del mes", "primera compra", "privilege", "promociones especiales", "cuotas", "tarjetas", "últimos días", "ultimos dias", "varios", "otros", "sin categoría"]],
];
const METRO_AREA_TERMS = [
  "asuncion",
  "gran asuncion",
  "fernando de la mora",
  "san lorenzo",
  "luque",
  "lambare",
  "lambare",
  "mariano roque alonso",
  "limpio",
  "capiata",
  "nemby",
  "ñemby",
  "san antonio",
  "villa elisa",
  "villa hayes",
  "ypane",
  "yaguaron",
  "aregua",
  "itaugua",
];
const OTHER_CITY_TERMS = [
  "ciudad del este",
  "encarnacion",
  "caaguazu",
  "coronel oviedo",
  "concepcion",
  "itapua",
  "pilar",
  "paraguari",
  "san bernardino",
  "villarrica",
  "hohenau",
  "hernandarias",
  "presidente franco",
  "maria auxiliadora",
  "obligado",
  "colonias unidas",
  "bella vista",
  "capitan meza",
  "santa rita",
  "minga guazu",
  "curuguaty",
  "salto del guaira",
  "san ignacio",
  "misiones",
  "caazapa",
  "caaguazu",
  "cordillera",
  "alto parana",
  "neembucu",
  "ñeembucu",
  "guaira",
  "canindeyu",
  "concepcion",
];

const state = {
  promotions: [],
  locations: [],
  locationsUpdated: "",
  activeView: "today",
  activeBank: "Todos",
  activeCategory: "Todas",
  activeDay: "hoy",
  query: "",
  uenoLevel: 5,
  location: null,
  locationStatus: "idle",
  activePlaceName: "",
  user: loadStoredJson(STORAGE_KEYS.user, null),
  favorites: new Set(loadStoredJson(STORAGE_KEYS.favorites, [])),
  alertPrefs: loadStoredJson(STORAGE_KEYS.alertPrefs, { today: true, favorites: true }),
  collapsedSections: new Set(["Todos los dias", "Cuotas sin intereses todos los dias", "Otras ciudades"]),
  lastUpdated: "",
};

const bankThemes = {
  "ueno bank": { main: "#2bd98e", soft: "#e2f8ef", card: "#f3fcf8", logo: "./assets/logos/ueno-icon-official.svg", logoBg: "#062017" },
  "Itaú": { main: "#ec7000", soft: "#fff0df", card: "#fff8f0", logo: "./assets/logos/itau-official.svg", logoBg: "#ec7000" },
  "Continental": { main: "#082a63", soft: "#e5edf8", card: "#f4f8fe", logo: "./assets/logos/continental-official.png", logoBg: "#e7ebf0" },
  "Sudameris": { main: "#ff0000", soft: "#ffe5e5", card: "#fff7f7", logo: "./assets/logos/sudameris.svg", logoBg: "#ff0000" },
  "BNF": { main: "#b08a2e", soft: "#f4eddd", card: "#fbfaf6", logo: "./assets/logos/bnf-official.png", logoBg: "#d9d1bf" },
  "Atlas": { main: "#a41f35", soft: "#f7e6ea", card: "#fff6f8", logo: "./assets/logos/atlas-official.svg", logoBg: "#631421" },
  "Coop. Universitaria": { main: "#4c1d95", soft: "#ede9fe", card: "#f7f2ff", logo: "./assets/logos/universitaria-official.png", logoBg: "#f1ecff" },
};

const BANK_LABELS = {
  "ueno bank": "UENO",
  "Coop. Universitaria": "Universitaria",
};

const SECTION_LABELS = {
  "Todos los dias": "Siempre activas",
  "Cuotas sin intereses todos los dias": "Financiación",
  "Otras ciudades": "Explorar interior",
  "Mejor opción hoy": "Mejor opción hoy",
  "Otras opciones": "Otras opciones",
  "Hoy te conviene": "Hoy te conviene",
  "Disponible hoy": "Disponible hoy",
  "Mayor ahorro hoy": "Mayor ahorro hoy",
  "Cuotas sin intereses": "Cuotas sin intereses",
};

const SECTION_SUBTITLES = {
  "Todos los dias": "Beneficios que podés usar cualquier día.",
  "Cuotas sin intereses todos los dias": "Opciones para pagar en cuotas sin interés.",
  "Otras ciudades": "Promos fuera de Asunción y Gran Asunción.",
  "Mejor opción hoy": "La tarjeta que más conviene para esta búsqueda.",
  "Otras opciones": "Alternativas disponibles para comparar.",
  "Hoy te conviene": "Beneficios destacados para usar hoy.",
  "Disponible hoy": "Promos activas para usar ahora mismo.",
  "Mayor ahorro hoy": "Ordenado por ahorro máximo estimado.",
  "Cuotas sin intereses": "Financiación separada de reintegros y descuentos.",
};

const CATEGORY_ICONS = {
  Todas: "spark",
  Supermercados: "cart",
  Combustible: "fuel",
  Farmacias: "pill",
  Gastronomía: "fork",
  Tiendas: "bag",
  "Hogar y construcción": "home",
  Tecnología: "device",
  "Clubes sociales": "users",
  Entretenimiento: "ticket",
  Viajes: "plane",
  "Salud y belleza": "heart",
  Servicios: "briefcase",
  Especiales: "star",
  [PREMIUM_CATEGORY]: "crown",
};

const ICON_PATHS = {
  spark: '<path d="M12 3l1.6 5.1L19 10l-5.4 1.9L12 17l-1.6-5.1L5 10l5.4-1.9L12 3z"/>',
  cart: '<path d="M5 6h2l1.4 8.2h8.3L19 8H8"/><circle cx="10" cy="18" r="1.4"/><circle cx="16" cy="18" r="1.4"/>',
  fuel: '<path d="M6 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><path d="M8 9h7"/><path d="M18 7l2 2v7a2 2 0 0 1-4 0v-4"/><path d="M4 21h15"/>',
  pill: '<path d="M10.5 20.5a5 5 0 0 1-7-7l7-7a5 5 0 0 1 7 7l-7 7z"/><path d="M8 9l7 7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  fork: '<path d="M7 4v8M10 4v8M7 8h3M9 12v8"/><path d="M16 4v16"/><path d="M16 4c2 1.5 3 3.5 3 6"/>',
  bag: '<path d="M6 9h12l-1 11H7L6 9z"/><path d="M9 9a3 3 0 0 1 6 0"/>',
  home: '<path d="M4 11l8-7 8 7"/><path d="M6 10v10h12V10"/><path d="M10 20v-6h4v6"/>',
  device: '<rect x="7" y="4" width="10" height="16" rx="2"/><path d="M11 17h2"/>',
  users: '<path d="M16 11a4 4 0 1 0-8 0"/><path d="M4 20a8 8 0 0 1 16 0"/><path d="M18 8a3 3 0 0 1 2 5"/><path d="M6 8a3 3 0 0 0-2 5"/>',
  ticket: '<path d="M5 8h14v3a2 2 0 0 0 0 4v3H5v-3a2 2 0 0 0 0-4V8z"/><path d="M12 9v2M12 13v2M12 17v1"/>',
  plane: '<path d="M3 11l18-7-7 18-3-8-8-3z"/><path d="M11 14l4-4"/>',
  heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
  briefcase: '<path d="M7 8V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"/><rect x="4" y="8" width="16" height="11" rx="2"/><path d="M4 13h16"/>',
  star: '<path d="M12 4l2.4 5 5.6.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.6-.8L12 4z"/>',
  crown: '<path d="M5 18h14"/><path d="M6 15l1-8 5 4 5-4 1 8H6z"/><path d="M9 21h6"/>',
};

const els = {
  bankTabs: document.querySelector("#bankTabs"),
  dayTabs: document.querySelector("#dayTabs"),
  searchInput: document.querySelector("#searchInput"),
  categoryTabs: document.querySelector("#categoryTabs"),
  refreshButton: document.querySelector("#refreshButton"),
  statusText: document.querySelector("#statusText"),
  countText: document.querySelector("#countText"),
  results: document.querySelector("#results"),
  uenoLevelPanel: document.querySelector("#uenoLevelPanel"),
  bottomNav: document.querySelector("#bottomNav"),
  dialog: document.querySelector("#promoDialog"),
  dialogContent: document.querySelector("#dialogContent"),
  closeDialog: document.querySelector("#closeDialog"),
};

function normalizeDayName(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace("miercoles", "miércoles")
    .replace("sabado", "sábado")
    .trim();
}

function loadStoredJson(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function saveStoredJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getTodayInParaguay() {
  const text = new Intl.DateTimeFormat("es-PY", {
    weekday: "long",
    timeZone: "America/Asuncion",
  }).format(new Date());
  return normalizeDayName(text);
}

function getTodayLabel() {
  const parts = new Intl.DateTimeFormat("es-PY", {
    day: "numeric",
    month: "long",
    timeZone: "America/Asuncion",
    weekday: "long",
  }).formatToParts(new Date());
  const weekday = parts.find((part) => part.type === "weekday")?.value || getTodayInParaguay();
  const day = parts.find((part) => part.type === "day")?.value || "";
  const month = parts.find((part) => part.type === "month")?.value || "";
  return `Hoy ${normalizeDayName(weekday)} ${day} de ${month}`;
}

function inferPromotionDaysFromText(promo) {
  if (getMonthDays(promo).length) return [];

  const ordinalRules = getOrdinalWeekdayRules(promo);
  if (ordinalRules.length) return [...new Set(ordinalRules.map((rule) => rule.day))];

  const existing = (promo.promotion_days || []).map(normalizeDayName).filter(Boolean);
  if (existing.length) return existing;

  const text = normalizeDayName(`${promo.day_text || ""} ${promo.validity || ""}`);
  if (hasOpenDateRangeWithoutSpecificDay(text)) return [...DAYS];
  if (!text) return [];
  if (text.includes("todos los dias") || text.includes("todos los días")) return [...DAYS];

  const found = DAYS.filter((day) => text.includes(normalizeDayName(day)));
  const range = inferDayRange(text);
  if (!found.length && !range.length && text.includes("no especificado")) return [];
  return [...new Set([...found, ...range])];
}

function hasOpenDateRangeWithoutSpecificDay(text) {
  const hasRange = /\b(del|desde)\b.+\b(al|hasta)\b/.test(text);
  if (!hasRange) return false;
  return !DAYS.some((day) => text.includes(normalizeDayName(day)));
}

function getDisplayDays(promo) {
  const monthDays = getMonthDays(promo);
  if (monthDays.length) return monthDays.map((day) => `${day} de cada mes`).join(", ");

  const ordinalRules = getOrdinalWeekdayRules(promo);
  if (ordinalRules.length) {
    return ordinalRules.map((rule) => `${ordinalLabel(rule.ordinal)} ${rule.day} de cada mes`).join(", ");
  }

  const days = inferPromotionDaysFromText(promo);
  if (isEveryDayPromotion(promo)) return "Todos los dias";
  if (!days.length) return "No especificado";
  return days.map(capitalize).join(", ");
}

function getOrdinalWeekdayRules(promo) {
  if (Array.isArray(promo.ordinal_weekdays) && promo.ordinal_weekdays.length) {
    return promo.ordinal_weekdays
      .map((rule) => ({ ordinal: Number(rule.ordinal), day: normalizeDayName(rule.day) }))
      .filter((rule) => rule.ordinal && DAYS.includes(rule.day));
  }

  const text = normalizeDayName(`${promo.day_text || ""} ${promo.validity || ""} ${promo.raw_detail || ""}`);
  const ordinalWords = {
    primer: 1,
    primero: 1,
    primera: 1,
    segundo: 2,
    segunda: 2,
    tercer: 3,
    tercero: 3,
    tercera: 3,
    cuarto: 4,
    cuarta: 4,
    ultimo: -1,
    ultima: -1,
  };
  const rules = [];
  const wordPattern = Object.keys(ordinalWords).join("|");
  const dayPattern = DAYS.map(normalizeDayName).join("|");
  const regexes = [
    new RegExp(`\\b(${wordPattern})\\s+((?:${dayPattern})(?:\\s+y\\s+(?:${dayPattern}))*)\\s+de\\s+cada\\s+mes\\b`, "g"),
    new RegExp(`\\bsolo\\s+el\\s+(${wordPattern})\\s+((?:${dayPattern})(?:\\s+y\\s+(?:${dayPattern}))*)\\b`, "g"),
  ];
  regexes.forEach((regex) => {
    for (const match of text.matchAll(regex)) {
      const ordinal = ordinalWords[match[1]];
      DAYS.forEach((day) => {
        if (match[2].includes(normalizeDayName(day))) rules.push({ ordinal, day });
      });
    }
  });
  return uniqueOrdinalRules(rules);
}

function uniqueOrdinalRules(rules) {
  const seen = new Set();
  return rules.filter((rule) => {
    const key = `${rule.ordinal}:${rule.day}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function ordinalLabel(ordinal) {
  if (ordinal === 1) return "Primer";
  if (ordinal === 2) return "Segundo";
  if (ordinal === 3) return "Tercer";
  if (ordinal === 4) return "Cuarto";
  if (ordinal === -1) return "Ultimo";
  return `${ordinal}°`;
}

function getMonthDays(promo) {
  if (Array.isArray(promo.month_days)) {
    return promo.month_days.map(Number).filter((day) => day >= 1 && day <= 31);
  }

  const text = normalizeDayName(`${promo.day_text || ""} ${promo.validity || ""} ${promo.raw_detail || ""}`);
  const found = [...text.matchAll(/\b(?:dia\s*)?([0-3]?\d)\s+de\s+cada\s+mes\b/g)]
    .map((match) => Number(match[1]))
    .filter((day) => day >= 1 && day <= 31);
  return [...new Set(found)];
}

function getDisplayValidity(promo) {
  const text = String(promo.validity || "").trim();
  if (!text || normalizeDayName(text).includes("no especificado")) return "Ver bases";

  const datePatterns = [
    /del\s+[0-9]{1,2}\s+al\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de\s+)?[0-9]{4})/i,
    /desde\s+el\s+[0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+al\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de\s+)?[0-9]{4})/i,
    /hasta\s+el\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de\s+)?[0-9]{4})/i,
    /hasta\s+el\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+del\s+[0-9]{4})/i,
    /hasta\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de\s+)?[0-9]{4})/i,
    /hasta\s+([0-9]{4}-[0-9]{2}-[0-9]{2})/i,
    /[0-9]{4}-[0-9]{2}-[0-9]{2}\s+hasta\s+([0-9]{4}-[0-9]{2}-[0-9]{2})/i,
    /hasta\s+el\s+([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})/i,
  ];
  for (const pattern of datePatterns) {
    const match = text.match(pattern);
    if (match) return `Hasta ${cleanSentence(match[1])}`;
  }
  return cleanSentence(text.replace(/^vigencia:\s*/i, ""));
}

function getCardValidity(promo) {
  const validity = getDisplayValidity(promo);
  if (validity.length <= 46) return validity;
  const text = cleanSentence(`${promo.validity || ""} ${promo.raw_detail || ""}`);
  const match = text.match(/vigente[^.]*?(?:hasta|al)\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de\s+)?[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})/i);
  if (match) return `Hasta ${cleanSentence(match[1])}`;
  return "Ver detalle";
}

function isActivePromotion(promo) {
  const endDate = getPromotionEndDate(promo);
  if (!endDate) return true;
  return endDate >= getTodayDateOnly();
}

function shouldShowPromotion(promo) {
  return isActivePromotion(promo) && isDisplayablePromotion(promo);
}

function isDisplayablePromotion(promo) {
  const text = normalizeDayName([
    promo.merchant_name,
    promo.benefit_summary,
    promo.benefit_type,
    promo.category,
    promo.merchant_locations_or_group,
    promo.caps_and_minimums,
    promo.level_rules,
    promo.raw_detail,
    promo.source_url,
  ].join(" "));

  if (text.includes("tyc-beneficios-ueno") || text.includes("programa de beneficios ueno+")) {
    return false;
  }

  const hasDiscountBenefit =
    /\d{1,3}\s*%/.test(text) ||
    text.includes("reintegro") ||
    text.includes("descuento") ||
    text.includes("cuotas sin interes") ||
    text.includes("cuotas sin intereses");
  const isOnlyPointsAction =
    text.includes("upys") &&
    !text.includes("reintegro") &&
    !text.includes("descuento") &&
    !text.includes("cuotas sin interes") &&
    !text.includes("cuotas sin intereses");

  return hasDiscountBenefit && !isOnlyPointsAction;
}

function getPromotionEndDate(promo) {
  const text = cleanSentence([
    promo.validity,
    promo.caps_and_minimums,
    promo.raw_detail,
  ].join(" "));
  const dates = extractEndDates(text);
  if (!dates.length) return null;
  return new Date(Math.max(...dates.map((date) => date.getTime())));
}

function extractEndDates(text) {
  const normalized = String(text || "");
  const patterns = [
    /\b(?:hasta|al)\s+el\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de|del)\s+[0-9]{4})/gi,
    /\b(?:hasta|al)\s+([0-9]{1,2}\s+de\s+[a-záéíóúñ]+\s+(?:de|del)\s+[0-9]{4})/gi,
    /\b(?:hasta|al)\s+el\s+([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})/gi,
    /\b(?:hasta|al)\s+([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})/gi,
    /\b(?:hasta|al)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})/gi,
    /\b[0-9]{4}-[0-9]{2}-[0-9]{2}\s+hasta\s+([0-9]{4}-[0-9]{2}-[0-9]{2})/gi,
  ];
  const dates = [];
  patterns.forEach((pattern) => {
    for (const match of normalized.matchAll(pattern)) {
      const parsed = parseDateText(match[1]);
      if (parsed) dates.push(parsed);
    }
  });
  return dates;
}

function parseDateText(value) {
  const text = normalizeDayName(value).replace(/\bdel\b/g, "de");
  const iso = text.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/);
  if (iso) return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]), 23, 59, 59);

  const slash = text.match(/^([0-9]{1,2})\/([0-9]{1,2})\/([0-9]{4})$/);
  if (slash) return new Date(Number(slash[3]), Number(slash[2]) - 1, Number(slash[1]), 23, 59, 59);

  const monthNames = {
    enero: 0,
    febrero: 1,
    marzo: 2,
    abril: 3,
    mayo: 4,
    junio: 5,
    julio: 6,
    agosto: 7,
    septiembre: 8,
    setiembre: 8,
    octubre: 9,
    noviembre: 10,
    diciembre: 11,
  };
  const words = text.match(/^([0-9]{1,2})\s+de\s+([a-zñ]+)\s+de\s+([0-9]{4})$/);
  if (!words || !(words[2] in monthNames)) return null;
  return new Date(Number(words[3]), monthNames[words[2]], Number(words[1]), 23, 59, 59);
}

function getTodayDateOnly() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Asuncion",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  return new Date(
    Number(parts.find((part) => part.type === "year")?.value),
    Number(parts.find((part) => part.type === "month")?.value) - 1,
    Number(parts.find((part) => part.type === "day")?.value),
    0,
    0,
    0
  );
}

function cleanSentence(value) {
  return String(value || "")
    .replace(/[•●]/g, "")
    .replace(/\bapple pay\b/gi, "Apple Pay")
    .replace(/\bgoogle pay\b/gi, "Google Pay")
    .replace(/\bmastercard\b/gi, "Mastercard")
    .replace(/\bueno bank\b/gi, "UENO")
    .replace(/\bueno\b/gi, "UENO")
    .replace(/\bapp UENO\b/g, "app UENO")
    .replace(/\bgpays?\b/gi, "Google Pay")
    .replace(/\bqr\b/gi, "QR")
    .replace(/\bpos\b/gi, "POS")
    .replace(/\bvpos\b/gi, "VPOS")
    .replace(/\bupay\b/gi, "Upay")
    .replace(/\bGs\b/g, "Gs.")
    .replace(/Gs\.\./g, "Gs.")
    .replace(/\bdel\s+([0-9]{4})\b/gi, "de $1")
    .replace(/\s*;\s*/g, "; ")
    .replace(/\s*,\s*/g, ", ")
    .replace(/\s+/g, " ")
    .replace(/\s+\./g, ".")
    .trim();
}

function inferDayRange(text) {
  const normalized = normalizeDayName(text);
  const ranges = [
    ["lunes a viernes", "lunes", "viernes"],
    ["lunes a miercoles", "lunes", "miércoles"],
    ["lunes a miércoles", "lunes", "miércoles"],
    ["martes a domingo", "martes", "domingo"],
    ["miercoles a sabado", "miércoles", "sábado"],
    ["miércoles a sábado", "miércoles", "sábado"],
  ];

  const matched = ranges.find(([needle]) => normalized.includes(normalizeDayName(needle)));
  if (!matched) return [];

  const start = DAYS.indexOf(matched[1]);
  const end = DAYS.indexOf(matched[2]);
  if (start === -1 || end === -1) return [];
  if (start <= end) return DAYS.slice(start, end + 1);
  return [...DAYS.slice(start), ...DAYS.slice(0, end + 1)];
}

function isEveryDayPromotion(promo) {
  const days = inferPromotionDaysFromText(promo);
  return DAYS.every((day) => days.includes(day));
}

function isInstallmentsOnly(promo) {
  const text = normalizeDayName(`${promo.benefit_summary || ""} ${promo.benefit_type || ""} ${promo.level_rules || ""}`);
  const hasInstallments = text.includes("cuota") || text.includes("sin interes") || text.includes("sin intereses");
  const hasDiscount = text.includes("descuento") || text.includes("reintegro");
  return hasInstallments && !hasDiscount;
}

function getBankTheme(bank) {
  return bankThemes[bank] || { main: "#334155", soft: "#eef2f7", card: "#ffffff", logo: "", logoBg: "#ffffff" };
}

function getBankLabel(bank) {
  return BANK_LABELS[bank] || bank || "Banco";
}

function isUenoPowerPromo(promo) {
  if (promo.bank !== "ueno bank") return false;
  if (Array.isArray(promo.special_flags) && promo.special_flags.includes("ueno_power")) return true;
  const text = normalizeDayName([
    promo.benefit_summary,
    promo.level_rules,
    promo.caps_and_minimums,
    promo.validity,
    promo.raw_detail,
  ].join(" "));
  return /ueno\s*\+\s*power|desbloquea\s+ueno|saldo promedio requerido/.test(text);
}

function getMainBenefit(promo, variant = null) {
  if (variant?.benefit) return variant.benefit;
  if (isUenoPowerPromo(promo)) {
    return getBenefitForSelectedUenoLevel(promo, state.uenoLevel);
  }
  if (promo.bank === "ueno bank") {
    return getBenefitForSelectedUenoLevel(promo, state.uenoLevel);
  }
  const pct = (promo.percentages || [])[0];
  if (pct && promo.benefit_summary?.toLowerCase().includes(pct.toLowerCase())) return promo.benefit_summary;
  return [pct, promo.benefit_type].filter(Boolean).join(" ") || promo.benefit_summary || "Ver detalle";
}

function getBenefitLines(promo, variant = null) {
  const text = String(getMainBenefit(promo, variant) || promo.benefit_summary || "Ver detalle");

  const normalized = text
    .replace(/hasta\s+(\d+)\s+cuotas?\s+sin\s+inter[eé]s(?:es)?/gi, "$1 cuotas")
    .replace(/(\d{1,3}\s*%)\s+de\s+/gi, "$1 ")
    .replace(/;/g, "|");

  const rawParts = normalized
    .split("|")
    .map((part) => cleanBenefitLine(part))
    .filter(Boolean);

  const compactParts = extractCompactBenefitLines(normalized);
  const parts = compactParts.length ? compactParts : rawParts.length ? rawParts : [cleanBenefitLine(normalized)];
  return [...new Set(parts)].slice(0, 1);
}

function getDisplayBenefit(promo, variant = null) {
  const lines = getBenefitLines(promo, variant);
  if (lines.length) return lines.join(" · ");
  return cleanBenefitLine(getMainBenefit(promo, variant)) || "Ver detalle";
}

function extractCompactBenefitLines(value) {
  const text = String(value || "");
  const lower = text.toLowerCase();
  if (lower.includes("cuotas sin intereses") && lower.includes("aplica a todos los niveles")) {
    return ["Cuotas sin intereses"];
  }

  const benefits = [];
  for (const match of text.matchAll(/(\d{1,3})\s*%[^|;,.]*/g)) {
    const segment = match[0].toLowerCase();
    if (segment.includes("tope") || segment.includes("mínim") || segment.includes("minim")) continue;
    if (segment.includes("reintegro")) benefits.push(`${match[1]}% reintegro`);
    else if (segment.includes("descuento")) benefits.push(`${match[1]}% descuento`);
    else benefits.push(`${match[1]}% ${promoBenefitWord(value)}`);
  }

  const quota = text.match(/(\d+)\s+cuotas?/i);
  if (!benefits.length && quota) benefits.push(`${quota[1]} cuotas`);
  return benefits;
}

function promoBenefitWord(value) {
  const lower = String(value || "").toLowerCase();
  if (lower.includes("reintegro")) return "reintegro";
  if (lower.includes("beneficio")) return "beneficio";
  return "descuento";
}

function cleanBenefitLine(value) {
  let line = String(value || "").replace(/\s+/g, " ").trim();
  line = line.replace(/^(\d{1,3})\s*%\s*;\s*(?=\1\s*%)/i, "");
  if (!line) return "";
  const lowerLine = line.toLowerCase();
  if (
    lowerLine.includes("tope") ||
    lowerLine.includes("monto mínimo") ||
    lowerLine.includes("monto minimo") ||
    lowerLine.includes("compra mensual") ||
    line.length > 42
  ) {
    return "";
  }
  if (lowerLine.includes("cuotas sin intereses") && lowerLine.includes("aplica a todos los niveles")) {
    return "Cuotas sin intereses";
  }
  if (lowerLine === "cuotas_sin_intereses") return "Cuotas sin intereses";

  const quota = line.match(/(\d+)\s+cuotas?/i);
  if (quota) return `${quota[1]} cuotas`;

  const pct = line.match(/(\d{1,3}\s*%)/);
  if (pct) {
    if (lowerLine.includes("reintegro")) return `${pct[1].replace(/\s+/g, "")} reintegro`;
    if (lowerLine.includes("descuento")) return `${pct[1].replace(/\s+/g, "")} descuento`;
    if (lowerLine.includes("beneficio")) return `${pct[1].replace(/\s+/g, "")} beneficio`;
    return `${pct[1].replace(/\s+/g, "")} descuento`;
  }

  return line.replace(/^hasta\s+/i, "");
}

function getBenefitForSelectedUenoLevel(promo, level) {
  const selected = getSelectedUenoLevelDetails(promo, level);
  if (selected?.percent) return `${selected.percent} ${promo.benefit_type || "reintegro"}`.trim();

  const rules = String(promo.level_rules || "");
  if (isInstallmentsOnly(promo) || rules.toLowerCase().includes("aplica a todos los niveles")) {
    return "Cuotas sin intereses - aplica a todos los niveles";
  }

  const escapedLevel = String(level).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`nivel\\s*${escapedLevel}\\D{0,20}(\\d{1,3})\\s*%`, "i");
  const match = rules.match(pattern);
  if (match) return `${match[1]}% ${promo.benefit_type || "reintegro"}`.trim();

  const percentages = promo.percentages || [];
  return percentages[0] ? `${percentages[0]} ${promo.benefit_type || ""}`.trim() : promo.benefit_summary || "Ver detalle";
}

function getSelectedUenoLevelDetails(promo, level) {
  if (promo.bank !== "ueno bank") return null;
  if (isInstallmentsOnly(promo)) return null;

  const rules = normalizeDayName(promo.level_rules || "");
  const escapedLevel = String(level).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pctMatch = rules.match(new RegExp(`nivel\\s*${escapedLevel}\\D{0,24}(\\d{1,3})\\s*%`, "i"));
  const percent = pctMatch ? `${pctMatch[1]}%` : "";
  if (!percent) return null;

  const caps = extractUenoLevelCaps(promo, level, percent);
  return { level, percent, ...caps };
}

function extractUenoLevelCaps(promo, level, percent) {
  const capsText = cleanSentence(promo.caps_and_minimums || "");
  const levelBlock = capsText.match(new RegExp(`nivel\\s*${level}[^;]*(?:;|$)`, "i"))?.[0] || "";
  const amountsFromBlock = extractGuaraniAmounts(levelBlock);
  if (amountsFromBlock.length) {
    return {
      purchaseCap: amountsFromBlock[0] || "",
      refundCap: amountsFromBlock[1] || "",
      capLabel: levelBlock.toLowerCase().includes("semanal") ? "Semanal" : "Durante vigencia",
    };
  }

  const allAmounts = extractGuaraniAmounts(capsText);
  const levelOrder = extractUenoLevelOrder(promo);
  const position = levelOrder.indexOf(Number(level));
  if (position >= 0 && allAmounts.length >= (position + 1) * 2) {
    return {
      purchaseCap: allAmounts[position * 2] || "",
      refundCap: allAmounts[position * 2 + 1] || "",
      capLabel: "Durante vigencia",
    };
  }

  const rawText = cleanSentence(promo.raw_detail || "");
  const rawPattern = new RegExp(`(?:nivel\\s*)?${level}\\s+${percent.replace("%", "\\s*%")}\\s+Gs\\.?\\s*([0-9.]+)(?:\\s+Gs\\.?\\s*([0-9.]+))?`, "i");
  const rawMatch = rawText.match(rawPattern);
  if (rawMatch) {
    return {
      purchaseCap: `Gs. ${rawMatch[1]}`,
      refundCap: rawMatch[2] ? `Gs. ${rawMatch[2]}` : "",
      capLabel: "Durante vigencia",
    };
  }

  return { purchaseCap: "", refundCap: "", capLabel: "" };
}

function extractUenoLevelOrder(promo) {
  const matches = [...normalizeDayName(promo.level_rules || "").matchAll(/nivel\s*([1-5])\D{0,24}\d{1,3}\s*%/g)]
    .map((match) => Number(match[1]));
  return matches.length ? matches : [5, 4, 3, 2, 1];
}

function extractGuaraniAmounts(text) {
  return [...String(text || "").matchAll(/Gs\.?\s*([0-9]+(?:\.[0-9]{3})*)/gi)]
    .map((match) => `Gs. ${match[1]}`);
}

function getPromoVariants(promo) {
  if (isUenoPowerPromo(promo)) return [null];

  const baseBenefit = getBaseBenefitForPremiumPromo(promo);
  const basePercent = percentNumber(baseBenefit);
  const variants = [{ kind: "base", label: "", benefit: baseBenefit }];
  const text = normalizeDayName(`${promo.benefit_summary || ""} ${promo.level_rules || ""} ${promo.caps_and_minimums || ""} ${promo.raw_detail || ""}`);
  const premium = [];
  const privilegePct = percentNear(text, ["privilege", "privilegio"]);
  if (privilegePct && percentNumber(privilegePct) > basePercent) {
    premium.push({ kind: "premium", label: "Privilege", benefit: `${privilegePct} reintegro` });
  }

  const blackPct = percentNear(text, ["black", "infinite", "visa infinite", "amex platinum", "personal bank", "ueno black"]);
  if (blackPct && blackPct !== privilegePct && percentNumber(blackPct) > basePercent) {
    const label = promo.bank === "ueno bank" ? "UENO Black" : promo.bank === "Itaú" ? "Black / Infinite" : "Black / Infinite";
    premium.push({ kind: "premium", label, benefit: `${blackPct} reintegro` });
  }

  const uniquePremium = premium.filter((item, index, list) => (
    list.findIndex((other) => other.label === item.label && other.benefit === item.benefit) === index
  ));
  return uniquePremium.length ? [...variants, ...uniquePremium] : [null];
}

function getVariantByKey(promo, key) {
  const variants = getPromoVariants(promo);
  if (!key) return variants[0] || null;
  return variants.find((variant, index) => String(index) === String(key) || variant?.label === key) || variants[0] || null;
}

function hasPremiumVariant(promo) {
  return getPromoVariants(promo).some((variant) => variant?.kind === "premium");
}

function percentNumber(value) {
  const match = String(value || "").match(/(\d{1,3})\s*%/);
  return match ? Number(match[1]) : 0;
}

function getBaseBenefitForPremiumPromo(promo) {
  const text = normalizeDayName(`${promo.benefit_summary || ""} ${promo.raw_detail || ""}`);
  const baseMatch = text.match(/(?:clasica|clásica|oro|dinelco|todas las tarjetas|tarjetas de credito itau|tarjetas de crédito itau)[^.%]{0,90}(\d{1,3})\s*%|(\d{1,3})\s*%[^.%]{0,90}(?:clasica|clásica|oro|dinelco|todas las tarjetas|tarjetas de credito itau|tarjetas de crédito itau)/i);
  const basePct = baseMatch?.[1] || baseMatch?.[2];
  if (basePct) return `${basePct}% ${promo.benefit_type || "reintegro"}`.trim();
  const percentages = (promo.percentages || []).map((pct) => pct.replace(/\s+/g, ""));
  if (percentages.length >= 2) return `${percentages.at(-1)} ${promo.benefit_type || "reintegro"}`.trim();
  return null;
}

function percentNear(text, needles) {
  const normalizedNeedles = needles.map(normalizeDayName);
  const percentages = [];
  normalizedNeedles.forEach((needle) => {
    const patternBefore = new RegExp(`(\\d{1,3})\\s*%[^.]{0,130}${needle}`, "gi");
    const patternAfter = new RegExp(`${needle}[^.]{0,130}(\\d{1,3})\\s*%`, "gi");
    for (const match of text.matchAll(patternBefore)) percentages.push(Number(match[1]));
    for (const match of text.matchAll(patternAfter)) percentages.push(Number(match[1]));
  });
  if (!percentages.length) return "";
  return `${Math.max(...percentages)}%`;
}

function getPromoTitle(promo) {
  return promo.merchant_name || promo.category || "Promoción";
}

function appliesToSelectedDay(promo, selectedDay) {
  const monthDays = getMonthDays(promo);
  if (monthDays.length) {
    return selectedDay === "hoy" && monthDays.includes(getParaguayMonthDay());
  }

  const ordinalRules = getOrdinalWeekdayRules(promo);
  if (ordinalRules.length) {
    return selectedDay === "hoy" && ordinalRules.some((rule) => isTodayOrdinalWeekday(rule));
  }

  const day = selectedDay === "hoy" ? getTodayInParaguay() : selectedDay;
  if (selectedDay === "hoy" && !passesOrdinalDayRule(promo, day)) return false;
  return inferPromotionDaysFromText(promo).includes(day);
}

function isTodayOrdinalWeekday(rule) {
  const today = getTodayInParaguay();
  if (rule.day !== today) return false;
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Asuncion",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const year = Number(parts.find((part) => part.type === "year")?.value);
  const month = Number(parts.find((part) => part.type === "month")?.value);
  const date = Number(parts.find((part) => part.type === "day")?.value);
  return date === getOrdinalDayOfMonthDate(year, month, rule.day, rule.ordinal);
}

function getParaguayMonthDay() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    timeZone: "America/Asuncion",
  }).formatToParts(new Date());
  return Number(parts.find((part) => part.type === "day")?.value);
}

function passesOrdinalDayRule(promo, day) {
  const text = normalizeDayName(`${promo.day_text || ""} ${promo.validity || ""}`);
  const firstNeedles = [`primer ${normalizeDayName(day)}`, `primeros ${normalizeDayName(day)}`];
  const onlyFirst = firstNeedles.some((needle) => text.includes(needle));
  if (!onlyFirst) return true;

  const now = new Date();
  const paraguayParts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Asuncion",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const year = Number(paraguayParts.find((part) => part.type === "year")?.value);
  const month = Number(paraguayParts.find((part) => part.type === "month")?.value);
  const date = Number(paraguayParts.find((part) => part.type === "day")?.value);
  return date === getFirstDayOfMonthDate(year, month, day);
}

function getFirstDayOfMonthDate(year, month, day) {
  return getOrdinalDayOfMonthDate(year, month, day, 1);
}

function getOrdinalDayOfMonthDate(year, month, day, ordinal) {
  const matches = [];
  const lastDate = new Date(Date.UTC(year, month, 0, 12, 0, 0)).getUTCDate();
  for (let date = 1; date <= lastDate; date += 1) {
    const candidate = new Date(Date.UTC(year, month - 1, date, 12, 0, 0));
    const candidateDay = new Intl.DateTimeFormat("es-PY", {
      weekday: "long",
      timeZone: "America/Asuncion",
    }).format(candidate);
    if (normalizeDayName(candidateDay) === normalizeDayName(day)) matches.push(date);
  }
  if (ordinal === -1) return matches.at(-1) || -1;
  return matches[ordinal - 1] || -1;
}

function getFirstDayOfMonthDateLegacy(year, month, day) {
  for (let date = 1; date <= 7; date += 1) {
    const candidate = new Date(Date.UTC(year, month - 1, date, 12, 0, 0));
    const candidateDay = new Intl.DateTimeFormat("es-PY", {
      weekday: "long",
      timeZone: "America/Asuncion",
    }).format(candidate);
    if (normalizeDayName(candidateDay) === normalizeDayName(day)) return date;
  }
  return -1;
}

function matchesQuery(promo) {
  const query = normalizeDayName(state.query);
  if (!query) return true;
  const haystack = normalizeDayName([
    promo.merchant_name,
    promo.category,
    promo.bank,
    promo.benefit_summary,
    promo.caps_and_minimums,
    promo.level_rules,
    promo.merchant_locations_or_group,
  ].join(" "));
  return haystack.includes(query);
}

function matchesBank(promo) {
  if (state.activeBank === "Todos") return true;
  return promo.bank === state.activeBank;
}

function matchesCategory(promo) {
  if (state.activeCategory === "Todas") return true;
  if (state.activeCategory === PREMIUM_CATEGORY) return hasPremiumVariant(promo);
  return getPromoCategoryGroup(promo) === state.activeCategory;
}

function sectionPromotions(promos) {
  const todaySpecific = [];
  const everydayDiscounts = [];
  const everydayInstallments = [];
  const otherCities = [];
  const selectedDay = state.activeDay === "hoy" ? getTodayInParaguay() : state.activeDay;

  promos.forEach((promo) => {
    if (isOtherCitiesOnly(promo)) {
      otherCities.push(promo);
      return;
    }
    const everyDay = isEveryDayPromotion(promo);
    if (everyDay && isInstallmentsOnly(promo)) {
      everydayInstallments.push(promo);
    } else if (everyDay) {
      everydayDiscounts.push(promo);
    } else {
      todaySpecific.push(promo);
    }
  });

  todaySpecific.sort((a, b) => {
    const aExclusive = isExclusiveToDay(a, selectedDay) ? -1 : 1;
    const bExclusive = isExclusiveToDay(b, selectedDay) ? -1 : 1;
    if (aExclusive !== bExclusive) return aExclusive - bExclusive;
    return sortByDayDisplayPriority(a, b);
  });
  everydayDiscounts.sort(sortByDayDisplayPriority);
  everydayInstallments.sort(sortByDayDisplayPriority);
  otherCities.sort(sortByDayDisplayPriority);

  const sections = [
    [state.activeDay === "hoy" ? getTodayLabel() : capitalize(selectedDay), todaySpecific, "featured"],
    ["Todos los dias", everydayDiscounts],
    ["Cuotas sin intereses todos los dias", everydayInstallments],
    ["Otras ciudades", otherCities],
  ];

  return sections.filter((section, index) => index === 0 || section[1].length);
}

function isOtherCitiesOnly(promo) {
  const primaryText = normalizeDayName([
    promo.merchant_name,
    promo.merchant_locations_or_group,
  ].join(" "));
  if (primaryText) {
    if (METRO_AREA_TERMS.some((term) => primaryText.includes(normalizeDayName(term)))) return false;
    if (OTHER_CITY_TERMS.some((term) => primaryText.includes(normalizeDayName(term)))) return true;
  }

  const detailText = normalizeDayName(promo.raw_detail || "");
  const hasLocationList = /sucursales|locales adherid|estaciones adherid|agencias adherid/.test(detailText);
  if (!hasLocationList) return false;
  if (METRO_AREA_TERMS.some((term) => detailText.includes(normalizeDayName(term)))) return false;
  return OTHER_CITY_TERMS.some((term) => detailText.includes(normalizeDayName(term)));
}

function isExclusiveToDay(promo, day) {
  const days = inferPromotionDaysFromText(promo);
  return days.length === 1 && days[0] === day;
}

function renderTabs() {
  els.bankTabs.innerHTML = BANKS.map((bank) => (
    `<button class="${state.activeBank === bank ? "active" : ""}" data-bank="${bank}" style="${getBankTabStyle(bank)}">${escapeHtml(getBankLabel(bank))}</button>`
  )).join("");

  const categories = getCategories();
  els.categoryTabs.innerHTML = categories.map((category) => (
    `<button class="${state.activeCategory === category ? "active" : ""} ${category === PREMIUM_CATEGORY ? "premium-filter" : ""}" data-category="${escapeAttribute(category)}">${renderIcon(CATEGORY_ICONS[category] || "star")}${escapeHtml(category)}</button>`
  )).join("");

  const days = [["hoy", "Hoy"], ...DAYS.map((day) => [day, capitalize(day)])];
  els.dayTabs.innerHTML = days.map(([value, label]) => (
    `<button class="${state.activeDay === value ? "active" : ""}" data-day="${value}">${label}</button>`
  )).join("");

  els.uenoLevelPanel.classList.toggle("hidden", state.activeBank !== "ueno bank");
  els.uenoLevelPanel.innerHTML = `<span class="label">Nivel ueno</span>` + [1, 2, 3, 4, 5].map((level) => (
    `<button class="${state.uenoLevel === level ? "active" : ""}" data-level="${level}">Nivel ${level}</button>`
  )).join("");
}

function getBankTabStyle(bank) {
  if (bank === "Todos") return "--tab-color:#f7f1e3;--tab-fill:#f7f1e3;--tab-text:#071124;";
  const theme = getBankTheme(bank);
  return `--tab-color:${theme.main};--tab-fill:${theme.main};--tab-text:#ffffff;`;
}

function renderIcon(name) {
  return `<svg class="chip-icon" viewBox="0 0 24 24" aria-hidden="true">${ICON_PATHS[name] || ICON_PATHS.star}</svg>`;
}

function render() {
  renderTabs();
  renderBottomNav();

  if (state.activeView === "alerts") {
    renderAlertsView();
    return;
  }
  if (state.activeView === "nearby") {
    renderNearbyView();
    return;
  }

  const base = state.promotions
    .filter(matchesBank)
    .filter(matchesCategory)
    .filter(matchesQuery)
    .filter(matchesActiveView)
    .filter((promo) => state.query.trim() ? true : matchesSelectedDay(promo))
    .sort(sortByDayDisplayPriority);

  const hasQuery = Boolean(state.query.trim());
  els.statusText.textContent = state.activeView === "favorites"
    ? "Tus promociones guardadas"
    : hasQuery
      ? `Resultados para "${state.query.trim()}"`
      : `Día activo: ${state.activeDay === "hoy" ? capitalize(getTodayInParaguay()) : capitalize(state.activeDay)}`;
  els.countText.textContent = `${base.length} ${hasQuery ? "promociones activas" : "promociones"}`;

  if (!base.length) {
    els.results.innerHTML = state.activeView === "favorites"
      ? `<div class="empty">Todavía no guardaste favoritos. Tocá el corazón en una promo para verla acá.</div>`
      : hasQuery
        ? `<div class="empty">No encontramos beneficios activos para "${escapeHtml(state.query.trim())}".</div>`
        : `<div class="empty">No encontramos promociones para estos filtros.</div>`;
    return;
  }

  els.results.innerHTML = buildResultSections(base).map(([title, items, mode]) => {
    const isCollapsed = state.collapsedSections.has(title);
    return `
    <section class="${mode === "featured" ? "featured-section" : ""} ${isCollapsed ? "collapsed" : ""}" data-section="${escapeAttribute(title)}">
      <button class="section-toggle" type="button" data-section-toggle="${escapeAttribute(title)}" aria-expanded="${String(!isCollapsed)}">
        <span class="chevron" aria-hidden="true"></span>
        <span class="section-copy">
          <span class="section-title">${escapeHtml(SECTION_LABELS[title] || title)}</span>
          ${SECTION_SUBTITLES[title] ? `<span class="section-subtitle">${escapeHtml(SECTION_SUBTITLES[title])}</span>` : ""}
        </span>
        <span class="section-count">${items.length}</span>
      </button>
      ${isCollapsed ? "" : items.length ? `<div class="grid">${items.flatMap((promo) => getPromoVariants(promo).map((variant) => renderCard(promo, variant))).join("")}</div>` : `<div class="empty compact">No hay promociones exclusivas para este día con estos filtros.</div>`}
    </section>
  `;
  }).join("");
}

function buildResultSections(promos) {
  if (state.query.trim()) return buildSearchSections(promos);
  if (state.activeView === "today" && state.activeBank === "Todos" && state.activeCategory === "Todas") {
    return buildHomeSections(promos);
  }
  return sectionPromotions(promos);
}

function buildSearchSections(promos) {
  const today = promos
    .filter((promo) => !isEveryDayPromotion(promo) && appliesToSelectedDay(promo, "hoy"))
    .sort(sortByDayDisplayPriority);
  const seen = new Set(today.map((promo) => promo.id));
  const daySections = DAYS.map((day) => [
    capitalize(day),
    promos
      .filter((promo) => !seen.has(promo.id) && !isEveryDayPromotion(promo) && appliesToSelectedDay(promo, day))
      .sort(sortByDayDisplayPriority),
  ]).filter(([, items]) => items.length);
  daySections.forEach(([, items]) => items.forEach((promo) => seen.add(promo.id)));

  const everydayDiscounts = promos
    .filter((promo) => !seen.has(promo.id) && isEveryDayPromotion(promo) && !isInstallmentsOnly(promo))
    .sort(sortByDayDisplayPriority);
  everydayDiscounts.forEach((promo) => seen.add(promo.id));

  const everydayInstallments = promos
    .filter((promo) => !seen.has(promo.id) && isEveryDayPromotion(promo) && isInstallmentsOnly(promo))
    .sort(sortByDayDisplayPriority);
  everydayInstallments.forEach((promo) => seen.add(promo.id));

  const remaining = promos.filter((promo) => !seen.has(promo.id)).sort(sortByDayDisplayPriority);

  return [
    ["Disponible hoy", today, "featured"],
    ...daySections,
    ["Todos los dias", everydayDiscounts],
    ["Cuotas sin intereses todos los dias", everydayInstallments],
    ["Otras opciones", remaining],
  ].filter((section, index) => index === 0 || section[1].length);
}

function buildHomeSections(promos) {
  const today = state.activeDay === "hoy" ? getTodayInParaguay() : state.activeDay;
  const ranked = [...promos].sort((a, b) => {
    const aExclusive = isExclusiveToDay(a, today) ? -1 : 1;
    const bExclusive = isExclusiveToDay(b, today) ? -1 : 1;
    if (aExclusive !== bExclusive) return aExclusive - bExclusive;
    return sortByDayDisplayPriority(a, b);
  });
  const seen = new Set();
  const takeUnique = (items, count) => {
    const selected = [];
    items.forEach((promo) => {
      if (selected.length >= count || seen.has(promo.id)) return;
      seen.add(promo.id);
      selected.push(promo);
    });
    return selected;
  };
  const todayBest = takeUnique(ranked.filter((promo) => !isInstallmentsOnly(promo)), 5);
  const maxSavings = takeUnique(ranked.filter((promo) => getEstimatedSavings(promo).refundCap > 0), 8);
  const installments = takeUnique(ranked.filter(isInstallmentsOnly), 8);
  const remaining = ranked.filter((promo) => !seen.has(promo.id));
  return [
    ["Hoy te conviene", todayBest, "featured"],
    ["Mayor ahorro hoy", maxSavings],
    ["Cuotas sin intereses", installments],
    ["Otras opciones", remaining],
  ].filter((section) => section[1].length);
}

function matchesActiveView(promo) {
  if (state.activeView !== "favorites") return true;
  return state.favorites.has(promo.id);
}

function matchesSelectedDay(promo) {
  if (state.activeView === "favorites") return true;
  return appliesToSelectedDay(promo, state.activeDay);
}

function renderBottomNav() {
  els.bottomNav.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.activeView);
  });
}

function renderAlertsView() {
  els.statusText.textContent = state.user?.name ? `Perfil: ${state.user.name}` : "Perfil local";
  els.countText.textContent = `${state.favorites.size} favoritos`;
  els.results.innerHTML = `
    <section class="profile-panel">
      <div class="profile-card">
        <span class="profile-logo"><img src="./assets/logos/payback-py.svg" alt="" /></span>
        <div>
          <h2>${state.user?.name ? `Hola, ${escapeHtml(state.user.name)}` : "Activá tu perfil Payback"}</h2>
          <p>Guardamos tus favoritos y preferencias en este teléfono.</p>
        </div>
      </div>
      <form id="profileForm" class="profile-form">
        <label>
          Nombre
          <input name="name" type="text" placeholder="Tu nombre" value="${escapeAttribute(state.user?.name || "")}" />
        </label>
        <label class="check-row">
          <input name="today" type="checkbox" ${state.alertPrefs.today ? "checked" : ""} />
          Avisarme por promociones del día
        </label>
        <label class="check-row">
          <input name="favorites" type="checkbox" ${state.alertPrefs.favorites ? "checked" : ""} />
          Priorizar mis comercios favoritos
        </label>
        <button type="submit">Guardar perfil</button>
      </form>
      <div class="profile-note">
        Esta primera versión guarda todo en tu teléfono. Cuando avancemos a cuenta online, tus favoritos podrán sincronizarse entre dispositivos.
      </div>
    </section>
  `;
}

function renderNearbyView() {
  const points = getNearbyPromoPoints();
  const selectedPoint = points.find((item) => item.place.name === state.activePlaceName) || points[0];
  const selectedPlace = selectedPoint?.place || KNOWN_LOCAL_POINTS[0];
  const selectedDistance = selectedPoint?.distance || 0;
  const promos = selectedPoint?.promos || [];
  const geocodedCount = state.locations.filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng)).length;
  els.statusText.textContent = state.location
    ? `Cerca de ${selectedPlace.name}`
    : "Radar de locales";
  els.countText.textContent = `${points.reduce((sum, item) => sum + item.promos.length, 0)} promos ubicables`;
  els.results.innerHTML = `
    <section class="nearby-panel">
      <div class="nearby-hero">
        <div>
          <span class="nearby-kicker">Ubicación</span>
          <h2>${state.location ? escapeHtml(selectedPlace.name) : "Promos cerca tuyo"}</h2>
          <p>${state.location ? `Aprox. ${formatDistance(selectedDistance)} de tu ubicación.` : "Activá tu ubicación o elegí un punto del mapa para ver locales con promociones."}</p>
        </div>
        <button type="button" class="location-button" data-location-action="detect">${state.locationStatus === "loading" ? "Buscando..." : "Usar mi ubicación"}</button>
      </div>
      <div class="mini-map local-radar" aria-label="Mapa de referencia">
        ${points.slice(0, 40).map((item) => renderMapMarker(item, selectedPlace)).join("")}
      </div>
      <div class="place-list">
        ${points.slice(0, 12).map((item) => `<button type="button" data-place-name="${escapeAttribute(item.place.name)}" class="${item.place.name === selectedPlace.name ? "active" : ""}"><strong>${escapeHtml(item.place.name)}</strong><span>${state.location ? formatDistance(item.distance) : `${item.promos.length} promos`}</span></button>`).join("")}
      </div>
      ${promos.length ? `<div class="nearby-note">Mostrando promos asociadas a <strong>${escapeHtml(selectedPlace.name)}</strong>. ${geocodedCount ? `${geocodedCount} locales tienen coordenadas reales o aproximadas por ciudad.` : "El mapa usa puntos de referencia mientras se completa la base geolocalizada."}</div><div class="grid nearby-grid">${promos.slice(0, 20).flatMap((promo) => getPromoVariants(promo).map((variant) => renderCard(promo, variant))).join("")}</div>` : `<div class="empty">Todavía no tenemos promociones geolocalizadas para esta zona. El siguiente paso es enriquecer la base con dirección, latitud y longitud por local.</div>`}
    </section>
  `;
}

function renderMapMarker(item, selectedPlace) {
  const firstPromo = item.promos[0];
  const theme = getBankTheme(firstPromo?.bank);
  const bankCount = new Set(item.promos.map((promo) => promo.bank)).size;
  const sourceLabel = item.place.geocode_source === "city_approximation" ? "zona aproximada" : "ubicación";
  const title = `${item.place.name}${item.place.address ? ` · ${item.place.address}` : ""} · ${item.promos.length} promos · ${sourceLabel}`;
  return `<button type="button" data-place-name="${escapeAttribute(item.place.name)}" class="map-marker ${item.place.geocode_source === "city_approximation" ? "approximate" : ""} ${item.place.name === selectedPlace.name ? "active" : ""}" style="--x:${getMapX(item.place.lng)}%;--y:${getMapY(item.place.lat)}%;--marker-color:${theme.main};" title="${escapeAttribute(title)}"><span>${bankCount > 1 ? item.promos.length : getBankLabel(firstPromo?.bank).slice(0, 1)}</span></button>`;
}

function getNearbyPromoPoints() {
  const dynamicPoints = state.locations
    .filter((place) => Number.isFinite(place.lat) && Number.isFinite(place.lng))
    .map((place) => {
      const promos = getPromotionsForLocation(place);
      return {
        place,
        promos,
        distance: state.location ? distanceKm(state.location.lat, state.location.lng, place.lat, place.lng) : 0,
      };
    })
    .filter((item) => item.promos.length);
  const knownPoints = KNOWN_LOCAL_POINTS
    .map((place) => {
      const promos = getPromotionsForPlace(place);
      return {
        place,
        promos,
        distance: state.location ? distanceKm(state.location.lat, state.location.lng, place.lat, place.lng) : 0,
      };
    })
    .filter((item) => item.promos.length);
  const pointsByName = new Map();
  [...dynamicPoints, ...knownPoints].forEach((item) => {
    const key = normalizeDayName([item.place.name, item.place.address, item.place.city].join(" "));
    if (!pointsByName.has(key) || item.promos.length > pointsByName.get(key).promos.length) {
      pointsByName.set(key, item);
    }
  });
  return [...pointsByName.values()].sort((a, b) => {
    if (state.location && a.distance !== b.distance) return a.distance - b.distance;
    return b.promos.length - a.promos.length;
  });
}

function getNearbyPlaces() {
  const withDistance = KNOWN_PLACES.map((place) => ({
    place,
    distance: state.location ? distanceKm(state.location.lat, state.location.lng, place.lat, place.lng) : 0,
  }));
  return withDistance.sort((a, b) => a.distance - b.distance);
}

function getPromotionsForPlace(place) {
  return state.promotions.filter((promo) => {
    if (!shouldShowPromotion(promo)) return false;
    const text = normalizeDayName([
      promo.merchant_name,
      promo.category,
      promo.merchant_locations_or_group,
      promo.caps_and_minimums,
      promo.raw_detail,
    ].join(" "));
    return place.terms.some((term) => text.includes(normalizeDayName(term)));
  });
}

function getPromotionsForLocation(place) {
  const merchant = normalizeDayName(place.merchant_name || place.name);
  const category = normalizeDayName(place.category);
  const bank = normalizeDayName(place.bank);
  return state.promotions.filter((promo) => {
    if (!shouldShowPromotion(promo)) return false;
    const promoBank = normalizeDayName(promo.bank);
    if (bank && bank !== "varios" && promoBank !== bank) return false;
    const promoCategory = normalizeDayName(getPromoCategoryGroup(promo));
    const promoText = normalizeDayName([
      promo.merchant_name,
      promo.category,
      promo.merchant_locations_or_group,
      promo.raw_detail,
    ].join(" "));
    if (merchant && promoText.includes(merchant)) return true;
    if (category && promoCategory === normalizeDayName(category)) return true;
    return false;
  }).slice(0, 10);
}

function distanceKm(lat1, lng1, lat2, lng2) {
  const earth = 6371;
  const dLat = toRadians(lat2 - lat1);
  const dLng = toRadians(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLng / 2) ** 2;
  return earth * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function toRadians(value) {
  return value * Math.PI / 180;
}

function formatDistance(value) {
  if (!value) return "0 km";
  if (value < 1) return `${Math.round(value * 1000)} m`;
  return `${value.toFixed(1)} km`;
}

function getMapX(lng) {
  const min = -57.59;
  const max = -57.51;
  return Math.min(92, Math.max(8, ((lng - min) / (max - min)) * 84 + 8));
}

function getMapY(lat) {
  const min = -25.33;
  const max = -25.20;
  return Math.min(88, Math.max(12, (1 - ((lat - min) / (max - min))) * 76 + 12));
}

function requestLocation() {
  if (!navigator.geolocation) {
    state.locationStatus = "unsupported";
    render();
    return;
  }
  state.locationStatus = "loading";
  render();
  navigator.geolocation.getCurrentPosition((position) => {
    state.location = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
    };
    state.locationStatus = "ready";
    render();
  }, () => {
    state.locationStatus = "denied";
    render();
  }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 });
}

function toggleFavorite(id) {
  if (!id) return;
  if (state.favorites.has(id)) {
    state.favorites.delete(id);
  } else {
    state.favorites.add(id);
  }
  saveStoredJson(STORAGE_KEYS.favorites, [...state.favorites]);
  render();
}

function getCategories() {
  const categories = [...new Set(state.promotions
    .filter(matchesBank)
    .map(getPromoCategoryGroup)
    .filter(Boolean))]
    .sort((a, b) => getCategoryOrder(a) - getCategoryOrder(b) || a.localeCompare(b, "es"));
  const hasPremium = state.promotions.filter(matchesBank).some(hasPremiumVariant);
  const visible = ["Todas", ...(hasPremium ? [PREMIUM_CATEGORY] : []), ...categories];
  if (state.activeCategory !== "Todas" && !visible.includes(state.activeCategory)) {
    visible.push(state.activeCategory);
  }
  return visible;
}

function getPromoCategoryGroup(promo) {
  const normalized = normalizeDayName([
    promo.category,
    promo.merchant_name,
    promo.merchant_locations_or_group,
  ].join(" "));
  const found = CATEGORY_GROUPS.find(([group, needles]) => (
    group !== "Todas" && needles.some((needle) => normalized.includes(normalizeDayName(needle)))
  ));
  return found ? found[0] : "Especiales";
}

function getCategoryOrder(category) {
  const index = CATEGORY_GROUPS.findIndex(([group]) => group === category);
  return index === -1 ? 999 : index;
}

function renderCategoryIcon(category) {
  const iconKey = CATEGORY_ICONS[category] || CATEGORY_ICONS.Especiales;
  const path = ICON_PATHS[iconKey] || ICON_PATHS.star;
  return `<span class="store-category-icon" title="${escapeAttribute(category)}" aria-hidden="true"><svg viewBox="0 0 24 24">${path}</svg></span>`;
}

function renderUenoLevelCaps(details) {
  const items = [
    details.purchaseCap ? `Compra ${details.purchaseCap}` : "",
    details.refundCap ? `Reintegro ${details.refundCap}` : "",
  ].filter(Boolean);
  if (!items.length) return "";
  return `<div class="level-caps">${items.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>`;
}

function sortPromotions(a, b) {
  return String(a.merchant_name || "").localeCompare(String(b.merchant_name || ""), "es");
}

function sortByBenefitValue(a, b) {
  const aSavings = getEstimatedSavings(a);
  const bSavings = getEstimatedSavings(b);
  if (bSavings.refundCap !== aSavings.refundCap) return bSavings.refundCap - aSavings.refundCap;
  if (bSavings.percent !== aSavings.percent) return bSavings.percent - aSavings.percent;
  if (Number(isInstallmentsOnly(a)) !== Number(isInstallmentsOnly(b))) {
    return Number(isInstallmentsOnly(a)) - Number(isInstallmentsOnly(b));
  }
  return sortPromotions(a, b);
}

function sortByDayDisplayPriority(a, b) {
  const aInstallmentsOnly = Number(isInstallmentsOnly(a));
  const bInstallmentsOnly = Number(isInstallmentsOnly(b));
  if (aInstallmentsOnly !== bInstallmentsOnly) return aInstallmentsOnly - bInstallmentsOnly;
  return sortByBenefitValue(a, b);
}

function getEstimatedSavings(promo, amount = null) {
  const level = getSelectedUenoLevelDetails(promo, state.uenoLevel);
  const percent = percentNumber(level?.percent || getMainBenefit(promo) || promo.benefit_summary);
  const amounts = extractGuaraniAmounts(`${promo.caps_and_minimums || ""} ${promo.raw_detail || ""}`).map(moneyToNumber).filter(Boolean);
  const purchaseCap = moneyToNumber(level?.purchaseCap) || inferPurchaseCap(promo, amounts);
  const explicitRefundCap = moneyToNumber(level?.refundCap) || inferRefundCap(promo, amounts, purchaseCap, percent);
  const spend = amount ? Math.max(0, Number(amount)) : purchaseCap;
  const calculated = percent && spend ? Math.round(spend * percent / 100) : 0;
  const refundCap = explicitRefundCap || calculated;
  const estimated = amount ? (explicitRefundCap ? Math.min(calculated, explicitRefundCap) : calculated) : refundCap;
  return { percent, purchaseCap, refundCap: estimated || 0, explicitRefundCap };
}

function getDetailRows(promo, variant = null) {
  const rawDetail = cleanSentence(promo.raw_detail || promo.validity || "");
  const rows = [
    ["Banco", promo.bank || ""],
    ["Categoría", promo.category || ""],
    ["Comercios/locales", getMerchantDetail(promo), "merchants"],
    ["Días", getDisplayDays(promo)],
    ["Fecha", getDisplayValidity(promo)],
    ["Reintegro o descuento", getDisplayBenefit(promo, variant)],
    ["Tarjetas que aplican", formatDetailText(extractApplicableCards(promo, variant))],
    ["Tarjetas excluidas", formatDetailText(extractExcludedCards(promo))],
    ["Topes y mínimos", formatCapsText(promo, variant), "caps"],
    ["Reglas por nivel", promo.level_rules || "", "levels"],
    ["Info adicional importante", extractAdditionalInfo(promo, rawDetail, variant)],
  ];
  return rows.filter(([, value]) => cleanSentence(value));
}

function getMerchantDetail(promo) {
  const group = cleanSentence(promo.merchant_locations_or_group || promo.merchant_name || "");
  if (!group) return "";
  const count = extractMerchantCount(promo);
  const brands = extractMerchantBrands(promo);
  if (count || brands.length > 3) {
    const intro = count ? `${count} locales adheridos.` : "Locales adheridos.";
    const names = brands.length ? ` Principales comercios: ${brands.slice(0, 10).join("; ")}.` : "";
    return `${intro}${names}`;
  }
  return group;
}

function extractMerchantCount(promo) {
  const text = cleanSentence(`${promo.merchant_locations_or_group || ""} ${promo.raw_detail || ""}`);
  const match = text.match(/\b(\d{2,5})\s+locales?\b/i);
  return match ? Number(match[1]) : 0;
}

function extractMerchantBrands(promo) {
  const source = cleanSentence(`${promo.merchant_locations_or_group || ""} ${promo.raw_detail || ""}`);
  const explicit = source.match(/Marcas\/comercios:\s*([^.|]+)/i)?.[1] || "";
  const names = explicit
    ? explicit.split(";").map(formatBrandName)
    : [...source.matchAll(/Listado de locales de\s+(.+?)\s+adheridos/gi)].map((match) => formatBrandName(match[1]));
  return [...new Set(names.filter(Boolean))].slice(0, 12);
}

function formatBrandName(value) {
  return cleanSentence(value)
    .replace(/\bASISMED\b/g, "ASISMED")
    .replace(/\bDRUGSTORE\b/g, "Drugstore")
    .replace(/\bFARMACIAS\b/g, "Farmacias")
    .replace(/\bFARMACIA\b/g, "Farmacia")
    .replace(/\bCATEDRAL\b/g, "Catedral")
    .replace(/\bVICENTE SCAVONE\b/g, "Vicente Scavone")
    .replace(/\bFARMACENTER\b/g, "Farmacenter")
    .replace(/\bFARMA KOKE\b/g, "Farma Koke")
    .replace(/\bSANTA VICTORIA\b/g, "Santa Victoria");
}

function extractApplicableCards(promo, variant = null) {
  const text = cleanSentence([promo.raw_detail, promo.benefit_summary].join(" "));
  if (variant?.kind === "premium") {
    if (/privilege|privilegio/i.test(variant.label)) return "Tarjetas Continental Privilege";
    if (/mastercard black|visa infinite|amex platinum|personal bank|premium/i.test(text)) {
      return "Tarjetas premium indicadas en bases: Mastercard Black, Visa Infinite o equivalentes";
    }
  }
  if (variant?.kind === "base" && promo.bank === "Sudameris") return "Tarjetas de crédito Sudameris";
  const explicit = text.match(/(?:aplica exclusivamente para compras realizadas con|con|pagando con|válido con|valido con)\s+(?:tu\s+)?(?:tarjeta|tarjetas|tarjetas físicas)[^.]+/i)?.[0];
  if (explicit) {
    return cleanSentence(explicit.replace(/^(?:aplica exclusivamente para compras realizadas con|con|pagando con|válido con|valido con)\s+/i, ""));
  }
  const cards = text.match(/\b(?:visa|mastercard|mc|cabal|oro|premium|black|platinum|infinite|signature|cl[aá]sica|prepaga|albirroja)[^.;)]*/gi);
  return cards ? cleanSentence([...new Set(cards.map((card) => cleanSentence(card)))].join("; ")) : "No especificado";
}

function extractExcludedCards(promo) {
  const text = cleanSentence([promo.raw_detail, promo.validity].join(" "));
  const match = text.match(/(?:no aplica|se excluyen|quedan excluidas?)[^.]+/i);
  return match ? cleanSentence(match[0]) : "No especificado";
}

function extractCapsText(text) {
  const matches = String(text || "").match(/(?:tope|m[ií]nimo|monto m[ií]nimo|l[ií]mite)[^.]+/gi);
  return matches ? cleanSentence([...new Set(matches)].join("; ")) : "";
}

function formatCapsText(promo, variant = null) {
  const text = cleanSentence(`${promo.caps_and_minimums || ""} ${promo.raw_detail || ""}`);
  if (!text || normalizeDayName(text).includes("no especificado")) return "No especificado";
  const scoped = getVariantScopedText(promo, variant);
  if (scoped) return scoped;
  const amounts = extractGuaraniAmounts(text);
  const parts = [];
  const purchase = text.match(/tope de compra[^.]*?Gs\.?\s*([0-9.]+)/i);
  const refund = text.match(/tope de reintegro[^.]*?Gs\.?\s*([0-9.]+)/i);
  const minimum = text.match(/(?:monto|mínimo|minimo)[^.]*?Gs\.?\s*([0-9.]+)/i);
  if (minimum) parts.push(`Compra mínima: Gs. ${minimum[1]}.`);
  if (purchase) parts.push(`Tope de compra: Gs. ${purchase[1]}.`);
  if (refund) parts.push(`Tope de reintegro: Gs. ${refund[1]}.`);
  if (!purchase && amounts[0]) parts.push(`Tope de compra: ${amounts[0]}.`);
  if (!refund && amounts[1]) parts.push(`Tope de reintegro: ${amounts[1]}.`);
  if (/no se multiplicar[aá]\s+por\s+sucursal/i.test(text)) {
    parts.push("El tope aplica por marca/comercio adherido y no se multiplica por sucursal.");
  }
  if (/mensual/i.test(text) && parts.length) {
    parts[0] = parts[0].replace("Tope de compra:", "Tope mensual de compra:");
  }
  return parts.length ? parts.join(" ") : formatDetailText(text).slice(0, 240);
}

function extractAdditionalInfo(promo, rawDetail, variant = null) {
  const scoped = getVariantScopedText(promo, variant);
  if (scoped) return "Ver promoción original para bases completas.";
  const important = [];
  const source = cleanSentence(rawDetail);
  const withoutKnown = source
    .replace(/(?:con|pagando con|válido con|valido con)\s+(?:tu\s+)?(?:tarjeta|tarjetas)[^.]+/gi, "")
    .replace(/(?:no aplica|se excluyen|quedan excluidas?)[^.]+/gi, "")
    .replace(/(?:tope|m[ií]nimo|monto m[ií]nimo|l[ií]mite)[^.]+/gi, "");
  const sentences = withoutKnown.split(".").map(cleanSentence).filter(Boolean);
  sentences.slice(0, 3).forEach((sentence) => important.push(sentence));
  if (promo.source_url) important.push("Ver promoción original para bases completas.");
  return cleanSentence(important.join(". "));
}

function formatDetailText(value) {
  let text = cleanSentence(value);
  text = text
    .replace(/,\./g, ".")
    .replace(/\s+\./g, ".")
    .replace(/\btarjetas de crédito de Sudameris\b/gi, "Tarjetas de crédito Sudameris")
    .replace(/\btarjetas de crédito Sudameris\b/gi, "Tarjetas de crédito Sudameris")
    .replace(/\btarjetas de crédito Continental\b/gi, "Tarjetas de crédito Continental")
    .replace(/\btarjeta de crédito visa bnf\b/gi, "Tarjeta de crédito Visa BNF")
    .replace(/\bvisa\b/gi, "Visa")
    .replace(/\bmastercard\b/gi, "Mastercard")
    .replace(/\bpersonal bank\b/gi, "Personal Bank")
    .replace(/\bamex platinum\b/gi, "Amex Platinum")
    .replace(/\breintegro directo en extracto\b/gi, "reintegro directo en extracto")
    .replace(/^tarjetas físicas/i, "Tarjetas físicas")
    .replace(/^tope de/i, "Tope de")
    .replace(/^monto mínimo/i, "Monto mínimo")
    .replace(/^no aplica/i, "No aplica")
    .replace(/^se excluyen/i, "Se excluyen")
    .replace(/\bcredito\b/gi, "crédito")
    .replace(/\bclasica\b/gi, "Clásica")
    .replace(/\bduo\b/gi, "Dúo")
    .replace(/\balbirroja\b/gi, "Albirroja")
    .replace(/\bblack\b/gi, "Black")
    .replace(/\bultra Black\b/g, "Ultra Black");
  return text;
}

function getVariantScopedText(promo, variant = null) {
  if (!variant || !promo.raw_detail) return "";
  const percent = percentNumber(variant.benefit);
  if (!percent) return "";
  const premiumTerms = /black|infinite|platinum|premium|privilege|privilegio|personal bank|mastercard black|visa infinite|amex platinum/i;
  const sentences = cleanSentence(promo.raw_detail)
    .split(".")
    .map(formatDetailText)
    .filter(Boolean);
  if (!sentences.some((sentence) => premiumTerms.test(sentence))) return "";
  const selected = sentences.filter((sentence) => {
    const hasPercent = new RegExp(`\\b${percent}\\s*%`).test(sentence);
    const isPremium = premiumTerms.test(sentence);
    if (variant.kind === "premium") return hasPercent && isPremium;
    if (variant.kind === "base") return hasPercent && !isPremium;
    return false;
  });
  return selected.slice(0, 2).join(". ");
}

function parseLevelRows(promo) {
  const rules = normalizeDayName(promo.level_rules || "");
  const rawText = cleanSentence(`${promo.raw_detail || ""} ${promo.caps_and_minimums || ""}`);
  const rows = [];
  const seen = new Set();
  for (const match of rules.matchAll(/nivel\s*([1-5])\D{0,24}(\d{1,3})\s*%/g)) {
    const level = Number(match[1]);
    const percent = `${match[2]}%`;
    if (seen.has(level)) continue;
    seen.add(level);
    const caps = extractUenoLevelCaps(promo, level, percent);
    const rawPattern = new RegExp(`nivel\\s*${level}\\s+${percent.replace("%", "\\s*%")}\\s+Gs\\.?\\s*([0-9.]+)(?:\\s+Gs\\.?\\s*([0-9.]+))?`, "i");
    const rawMatch = rawText.match(rawPattern);
    rows.push({
      level,
      percent,
      purchaseCap: caps.purchaseCap || (rawMatch ? `Gs. ${rawMatch[1]}` : ""),
      refundCap: caps.refundCap || (rawMatch?.[2] ? `Gs. ${rawMatch[2]}` : ""),
    });
  }
  return rows.sort((a, b) => b.level - a.level);
}

function renderLevelTable(promo) {
  const rows = parseLevelRows(promo);
  if (!rows.length) return "";
  return `
    <div class="level-table" role="table" aria-label="Reglas por nivel">
      <div class="level-table-head" role="row">
        <span>Nivel</span><span>Beneficio</span><span>Compra</span><span>Reintegro</span>
      </div>
      ${rows.map((row) => `
        <div class="level-table-row ${Number(row.level) === Number(state.uenoLevel) ? "active" : ""}" role="row">
          <span>Nivel ${row.level}</span>
          <strong>${escapeHtml(row.percent)}</strong>
          <span>${escapeHtml(row.purchaseCap || "-")}</span>
          <span>${escapeHtml(row.refundCap || "-")}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderDetailRows(promo, variant = null) {
  return getDetailRows(promo, variant).map(([label, value, type]) => `
    <div class="detail-row">
      <span>${escapeHtml(label)}</span>
      ${type === "levels" ? renderLevelTable(promo) : renderDetailValue(value, type)}
    </div>
  `).join("");
}

function renderDetailValue(value, type) {
  if (type === "merchants") {
    return `
      <strong>${escapeHtml(formatDetailText(value))}</strong>
      <button class="detail-inline-action" type="button" data-scroll-source>Ver más locales</button>
    `;
  }
  if (type === "caps") return `<strong class="detail-readable">${escapeHtml(formatDetailText(value))}</strong>`;
  return `<strong>${escapeHtml(formatDetailText(value))}</strong>`;
}

function formatLastUpdated() {
  const value = state.lastUpdated ? new Date(state.lastUpdated) : null;
  if (!value || Number.isNaN(value.getTime())) return "";
  return new Intl.DateTimeFormat("es-PY", {
    timeZone: "America/Asuncion",
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  }).format(value);
}

function inferPurchaseCap(promo, amounts) {
  const text = normalizeDayName(promo.caps_and_minimums || "");
  if (!amounts.length) return 0;
  if (text.includes("tope de reintegro") || text.includes("reintegro maximo")) {
    return amounts.length >= 2 ? amounts[0] : 0;
  }
  return amounts[0] || 0;
}

function inferRefundCap(promo, amounts, purchaseCap, percent) {
  const text = normalizeDayName(promo.caps_and_minimums || "");
  if (text.includes("tope de reintegro") || text.includes("reintegro maximo")) {
    return amounts.length >= 2 ? amounts[1] : amounts[0] || 0;
  }
  if (purchaseCap && percent) return Math.round(purchaseCap * percent / 100);
  return 0;
}

function moneyToNumber(value) {
  const match = String(value || "").match(/([0-9]+(?:\.[0-9]{3})*)/);
  return match ? Number(match[1].replace(/\./g, "")) : 0;
}

function formatGuarani(value) {
  const number = Math.round(Number(value || 0));
  if (!number) return "";
  return `Gs. ${number.toLocaleString("es-PY")}`;
}

function renderCard(promo, variant = null) {
  const theme = getBankTheme(promo.bank);
  const benefitLines = getBenefitLines(promo, variant);
  const categoryGroup = getPromoCategoryGroup(promo);
  const isPowerPromo = isUenoPowerPromo(promo);
  const isPremium = variant?.kind === "premium";
  const isFavorite = state.favorites.has(promo.id);
  const levelDetails = getSelectedUenoLevelDetails(promo, state.uenoLevel);
  const savings = getEstimatedSavings(promo);
  const savingsLabel = savings.refundCap ? `Ahorro max. ${formatGuarani(savings.refundCap)}` : "";
  const logoClass = `bank-logo-${normalizeDayName(promo.bank).replace(/[^a-z0-9]+/g, "-")}`;
  const premiumBadge = isPremium ? `<span class="premium-badge">${escapeHtml(variant.label)}</span>` : "";
  const powerBadge = isPowerPromo
    ? `<span class="power-badge" title="Promo ueno+ POWER"><img src="${escapeAttribute(bankThemes["ueno bank"].logo)}" alt="" />ueno+ POWER</span>`
    : "";
  return `
    <article class="promo-card ${isPowerPromo ? "ueno-power-card" : ""} ${isPremium ? "premium-card" : ""}" data-id="${promo.id}" data-variant="${escapeAttribute(String(getPromoVariants(promo).indexOf(variant)))}" style="--bank-main:${theme.main};--bank-soft:${theme.soft};--bank-card:${theme.card};--logo-bg:${theme.logoBg}">
      <div class="logo-box">${theme.logo ? `<img class="${escapeAttribute(logoClass)}" src="${escapeAttribute(theme.logo)}" alt="${escapeAttribute(getBankLabel(promo.bank))}" />` : ""}</div>
      <div class="promo-content">
        <div class="promo-card-head">
          <div>
            <div class="benefit-lines primary-benefit">${benefitLines.map((line) => `<span>${escapeHtml(line)}</span>`).join("")}</div>
            <h3 class="store-name">${renderCategoryIcon(categoryGroup)}<span>${escapeHtml(getPromoTitle(promo))}</span></h3>
          </div>
          <div class="card-actions">
            ${premiumBadge || powerBadge}
            <button class="favorite-toggle ${isFavorite ? "active" : ""}" type="button" data-favorite-id="${escapeAttribute(promo.id)}" title="${isFavorite ? "Quitar de favoritos" : "Guardar favorito"}" aria-label="${isFavorite ? "Quitar de favoritos" : "Guardar favorito"}">${isFavorite ? "♥" : "♡"}</button>
          </div>
        </div>
        ${savingsLabel ? `<div class="savings-line">${escapeHtml(savingsLabel)}</div>` : ""}
        ${levelDetails ? renderUenoLevelCaps(levelDetails) : ""}
        <p class="bank-card-line">${escapeHtml(getBankLabel(promo.bank))} · ${escapeHtml(categoryGroup)}</p>
        <div class="meta">
          <div><strong>Día:</strong> ${escapeHtml(getDisplayDays(promo))}</div>
          <div><strong>Vigencia:</strong> ${escapeHtml(getCardValidity(promo))}</div>
        </div>
      </div>
    </article>
  `;
}

function openDetail(id, variantKey = "") {
  const promo = state.promotions.find((item) => item.id === id);
  if (!promo) return;
  const variant = getVariantByKey(promo, variantKey);
  const isFavorite = state.favorites.has(promo.id);
  const levelDetails = getSelectedUenoLevelDetails(promo, state.uenoLevel);
  const savings = getEstimatedSavings(promo);
  els.dialogContent.innerHTML = `
    <h2>${escapeHtml(getPromoTitle(promo))}</h2>
    ${variant?.kind === "premium" ? `<span class="premium-badge detail-premium">${escapeHtml(variant.label)}</span>` : ""}
    <p class="benefit">${escapeHtml(getDisplayBenefit(promo, variant))}</p>
    ${savings.refundCap ? `<div class="detail-saving"><span>Ahorro máximo estimado</span><strong>${escapeHtml(formatGuarani(savings.refundCap))}</strong></div>` : ""}
    <button class="detail-favorite ${isFavorite ? "active" : ""}" type="button" data-favorite-id="${escapeAttribute(promo.id)}">${isFavorite ? "♥ Guardado en favoritos" : "♡ Guardar en favoritos"}</button>
    <div class="calculator" data-calculator-id="${escapeAttribute(promo.id)}">
      <label>¿Cuánto vas a gastar?
        <input type="number" inputmode="numeric" min="0" step="1000" placeholder="Ej: 500000" />
      </label>
      <div class="calculator-result">Ingresá un monto para calcular tu ahorro.</div>
    </div>
    <div class="detail-list">
      ${isUenoPowerPromo(promo) ? `<div class="power-detail"><strong>Promo especial:</strong> ueno+ POWER. Puede requerir desbloqueo o criterios adicionales en la app de ueno.</div>` : ""}
      ${levelDetails ? `<div><strong>Nivel UENO seleccionado:</strong> Nivel ${state.uenoLevel} · ${escapeHtml(levelDetails.percent)}${levelDetails.purchaseCap ? ` · Compra ${escapeHtml(levelDetails.purchaseCap)}` : ""}${levelDetails.refundCap ? ` · Reintegro ${escapeHtml(levelDetails.refundCap)}` : ""}</div>` : ""}
      ${renderDetailRows(promo, variant)}
      <div class="detail-row"><span>Fuente</span><strong>${escapeHtml(promo.bank || "Banco")} · Datos actualizados automáticamente${formatLastUpdated() ? ` · ${escapeHtml(formatLastUpdated())}` : ""}</strong></div>
      <div id="detailSourceLink"><a href="${escapeAttribute(promo.source_url || "#")}" target="_blank" rel="noreferrer">Ver bases y condiciones</a></div>
    </div>
  `;
  els.dialog.showModal();
}

async function loadPromotions() {
  els.statusText.textContent = "Actualizando promociones...";
  els.results.innerHTML = renderSkeletons();
  const [response, manifestResponse, locationsResponse] = await Promise.all([
    fetch(`${DATA_URL}?t=${Date.now()}`),
    fetch(`${MANIFEST_URL}?t=${Date.now()}`).catch(() => null),
    fetch(`${LOCATIONS_URL}?t=${Date.now()}`).catch(() => null),
  ]);
  if (!response.ok) throw new Error("No se pudo cargar promotions.json");
  if (manifestResponse?.ok) {
    const manifest = await manifestResponse.json();
    state.lastUpdated = manifest.generated_at || "";
  }
  state.promotions = (await response.json()).filter(shouldShowPromotion);
  if (locationsResponse?.ok) {
    const payload = await locationsResponse.json();
    state.locationsUpdated = payload.generated_at || "";
    state.locations = (payload.locations || []).map((item) => ({
      ...item,
      name: [item.merchant_name, item.address].filter(Boolean).join(" · "),
      lat: item.lat === null || item.lat === "" ? null : Number(item.lat),
      lng: item.lng === null || item.lng === "" ? null : Number(item.lng),
      terms: [item.merchant_name, item.address, item.city].filter(Boolean),
    }));
  }
  render();
}

function renderSkeletons() {
  return `<div class="skeleton-list">${[1, 2, 3].map(() => `
    <article class="skeleton-card">
      <span></span>
      <div><i></i><i></i><i></i></div>
    </article>
  `).join("")}</div>`;
}

function capitalize(value) {
  return String(value || "").charAt(0).toUpperCase() + String(value || "").slice(1);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

els.bankTabs.addEventListener("click", (event) => {
  const bank = event.target.closest("button")?.dataset?.bank;
  if (!bank) return;
  state.activeBank = bank;
  render();
});

els.categoryTabs.addEventListener("click", (event) => {
  const category = event.target.closest("button")?.dataset?.category;
  if (!category) return;
  state.activeCategory = category;
  render();
});

els.dayTabs.addEventListener("click", (event) => {
  const day = event.target.closest("button")?.dataset?.day;
  if (!day) return;
  state.activeDay = day;
  render();
});

els.uenoLevelPanel.addEventListener("click", (event) => {
  const level = Number(event.target.closest("button")?.dataset?.level);
  if (!level) return;
  state.uenoLevel = level;
  render();
});

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  if (state.activeView === "alerts") state.activeView = "search";
  render();
});

els.results.addEventListener("click", (event) => {
  const locationButton = event.target.closest("[data-location-action]");
  if (locationButton) {
    requestLocation();
    return;
  }

  const placeButton = event.target.closest("[data-place-name]");
  if (placeButton) {
    state.activePlaceName = placeButton.dataset.placeName;
    renderNearbyView();
    return;
  }

  const favoriteButton = event.target.closest("[data-favorite-id]");
  if (favoriteButton) {
    event.preventDefault();
    event.stopPropagation();
    toggleFavorite(favoriteButton.dataset.favoriteId);
    return;
  }

  const toggle = event.target.closest("[data-section-toggle]");
  if (toggle) {
    const title = toggle.dataset.sectionToggle;
    if (state.collapsedSections.has(title)) {
      state.collapsedSections.delete(title);
    } else {
      state.collapsedSections.add(title);
    }
    render();
    return;
  }

  const card = event.target.closest(".promo-card");
  if (card) openDetail(card.dataset.id, card.dataset.variant);
});

els.results.addEventListener("submit", (event) => {
  const form = event.target.closest("#profileForm");
  if (!form) return;
  event.preventDefault();
  const formData = new FormData(form);
  const name = String(formData.get("name") || "").trim();
  state.user = name ? { name } : null;
  state.alertPrefs = {
    today: formData.has("today"),
    favorites: formData.has("favorites"),
  };
  saveStoredJson(STORAGE_KEYS.user, state.user);
  saveStoredJson(STORAGE_KEYS.alertPrefs, state.alertPrefs);
  render();
});

els.dialogContent.addEventListener("click", (event) => {
  const sourceButton = event.target.closest("[data-scroll-source]");
  if (sourceButton) {
    const sourceLink = els.dialogContent.querySelector("#detailSourceLink");
    sourceLink?.scrollIntoView({ behavior: "smooth", block: "center" });
    sourceLink?.classList.remove("pulse-source");
    window.setTimeout(() => sourceLink?.classList.add("pulse-source"), 80);
    window.setTimeout(() => sourceLink?.classList.remove("pulse-source"), 1800);
    return;
  }
  const favoriteButton = event.target.closest("[data-favorite-id]");
  if (!favoriteButton) return;
  toggleFavorite(favoriteButton.dataset.favoriteId);
  els.dialog.close();
});

els.dialogContent.addEventListener("input", (event) => {
  const input = event.target.closest(".calculator input");
  if (!input) return;
  const wrapper = input.closest("[data-calculator-id]");
  const promo = state.promotions.find((item) => item.id === wrapper?.dataset?.calculatorId);
  const output = wrapper?.querySelector(".calculator-result");
  if (!promo || !output) return;
  const amount = Number(input.value || 0);
  if (!amount) {
    output.textContent = "Ingresá un monto para calcular tu ahorro.";
    return;
  }
  const savings = getEstimatedSavings(promo, amount);
  const capText = savings.explicitRefundCap && Math.round(amount * savings.percent / 100) > savings.explicitRefundCap
    ? " porque alcanzaste el tope."
    : ".";
  output.innerHTML = `Recibís <strong>${escapeHtml(formatGuarani(savings.refundCap))}</strong>${capText}`;
});

els.bottomNav.addEventListener("click", (event) => {
  const view = event.target.closest("button")?.dataset?.view;
  if (!view) return;
  state.activeView = view;
  if (view === "today") {
    state.activeDay = "hoy";
  }
  if (view === "search") {
    requestAnimationFrame(() => {
      els.searchInput.focus();
      els.searchInput.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }
  render();
});

els.closeDialog.addEventListener("click", () => els.dialog.close());
els.refreshButton.addEventListener("click", () => loadPromotions().catch((error) => {
  els.statusText.textContent = error.message;
}));

loadPromotions().catch((error) => {
  els.statusText.textContent = error.message;
  els.results.innerHTML = `<div class="empty">No se pudieron cargar las promociones.</div>`;
});
