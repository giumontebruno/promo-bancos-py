const DATA_URL = "../public/promotions.json";
const DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
const BANKS = ["Todos", "ueno bank", "Itaú", "Continental", "Sudameris", "BNF", "Atlas", "Coop. Universitaria"];
const PREMIUM_CATEGORY = "Club Black";
const CATEGORY_GROUPS = [
  ["Todas", []],
  ["Supermercados", ["super", "mayorista", "delimarket", "stock", "real", "contimarket"]],
  ["Combustible", ["combustible", "estacion", "estaciones", "shell", "puma flota"]],
  ["Farmacias", ["farmacia", "farmacias", "perfumeria", "perfumerías"]],
  ["Gastronomía", ["gastronomia", "gastronomía", "cafeteria", "cafeterías", "heladeria", "heladerías"]],
  ["Tiendas", ["tienda", "tiendas", "moda", "indumentaria", "shopping", "shoppings", "joyeria", "joyerías", "joyas", "niños", "jugueteria", "jugueterías"]],
  ["Hogar y construcción", ["hogar", "construccion", "construcción", "ferreteria", "ferreterías", "muebleria", "mueblerías", "industrial"]],
  ["Tecnología", ["tecnologia", "tecnología", "electronica", "electrónica"]],
  ["Entretenimiento", ["entretenimiento", "eventos", "teatro", "clubes", "club", "deportes", "academia", "gym", "gimnasio", "pilates", "feria", "caza", "pesca"]],
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
  activeBank: "Todos",
  activeCategory: "Todas",
  activeDay: "hoy",
  query: "",
  uenoLevel: 5,
  collapsedSections: new Set(["Todos los dias", "Cuotas sin intereses todos los dias", "Otras ciudades"]),
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
};

const SECTION_SUBTITLES = {
  "Todos los dias": "Beneficios que podés usar cualquier día.",
  "Cuotas sin intereses todos los dias": "Opciones para pagar en cuotas sin interés.",
  "Otras ciudades": "Promos fuera de Asunción y Gran Asunción.",
};

const CATEGORY_ICONS = {
  Todas: "spark",
  Supermercados: "cart",
  Combustible: "fuel",
  Farmacias: "plus",
  Gastronomía: "fork",
  Tiendas: "bag",
  "Hogar y construcción": "home",
  Tecnología: "device",
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
  plus: '<path d="M12 5v14M5 12h14"/>',
  fork: '<path d="M7 4v8M10 4v8M7 8h3M9 12v8"/><path d="M16 4v16"/><path d="M16 4c2 1.5 3 3.5 3 6"/>',
  bag: '<path d="M6 9h12l-1 11H7L6 9z"/><path d="M9 9a3 3 0 0 1 6 0"/>',
  home: '<path d="M4 11l8-7 8 7"/><path d="M6 10v10h12V10"/><path d="M10 20v-6h4v6"/>',
  device: '<rect x="7" y="4" width="10" height="16" rx="2"/><path d="M11 17h2"/>',
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

function cleanSentence(value) {
  return String(value || "")
    .replace(/[•●]/g, "")
    .replace(/\bdel\s+([0-9]{4})\b/gi, "de $1")
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
    return "10% reintegro base; hasta 40% reintegro adicional ueno+ POWER";
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

  const parts = rawParts.length ? rawParts : [cleanBenefitLine(normalized)];
  return [...new Set(parts)].slice(0, 4);
}

function cleanBenefitLine(value) {
  let line = String(value || "").replace(/\s+/g, " ").trim();
  if (!line) return "";
  if (line.toLowerCase().includes("cuotas sin intereses") && line.toLowerCase().includes("aplica a todos los niveles")) {
    return "Cuotas sin intereses";
  }
  if (line.toLowerCase() === "cuotas_sin_intereses") return "Cuotas sin intereses";

  const quota = line.match(/(\d+)\s+cuotas?/i);
  if (quota) return `${quota[1]} cuotas`;

  const pct = line.match(/(\d{1,3}\s*%)/);
  if (pct) {
    const lower = line.toLowerCase();
    if (lower.includes("reintegro")) return `${pct[1].replace(/\s+/g, "")} reintegro`;
    if (lower.includes("descuento")) return `${pct[1].replace(/\s+/g, "")} descuento`;
    if (lower.includes("beneficio")) return `${pct[1].replace(/\s+/g, "")} beneficio`;
    return `${pct[1].replace(/\s+/g, "")} descuento`;
  }

  return line.replace(/^hasta\s+/i, "");
}

function getBenefitForSelectedUenoLevel(promo, level) {
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
    return sortPromotions(a, b);
  });

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
    `<button class="${state.activeBank === bank ? "active" : ""}" data-bank="${bank}" style="--tab-color:${getBankTheme(bank).main}">${escapeHtml(getBankLabel(bank))}</button>`
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

function renderIcon(name) {
  return `<svg class="chip-icon" viewBox="0 0 24 24" aria-hidden="true">${ICON_PATHS[name] || ICON_PATHS.star}</svg>`;
}

function render() {
  renderTabs();
  const base = state.promotions
    .filter(matchesBank)
    .filter(matchesCategory)
    .filter(matchesQuery)
    .filter((promo) => appliesToSelectedDay(promo, state.activeDay))
    .sort(sortPromotions);

  els.statusText.textContent = `Día activo: ${state.activeDay === "hoy" ? capitalize(getTodayInParaguay()) : capitalize(state.activeDay)}`;
  els.countText.textContent = `${base.length} promociones`;

  if (!base.length) {
    els.results.innerHTML = `<div class="empty">No encontramos promociones para estos filtros.</div>`;
    return;
  }

  els.results.innerHTML = sectionPromotions(base).map(([title, items, mode]) => {
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

function getCategories() {
  const categories = [...new Set(state.promotions
    .filter(matchesBank)
    .map(getPromoCategoryGroup)
    .filter(Boolean))]
    .sort((a, b) => getCategoryOrder(a) - getCategoryOrder(b) || a.localeCompare(b, "es"));
  const hasPremium = state.promotions.filter(matchesBank).some(hasPremiumVariant);
  return ["Todas", ...(hasPremium ? [PREMIUM_CATEGORY] : []), ...categories];
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

function sortPromotions(a, b) {
  return String(a.merchant_name || "").localeCompare(String(b.merchant_name || ""), "es");
}

function renderCard(promo, variant = null) {
  const theme = getBankTheme(promo.bank);
  const benefitLines = getBenefitLines(promo, variant);
  const categoryGroup = getPromoCategoryGroup(promo);
  const isPowerPromo = isUenoPowerPromo(promo);
  const isPremium = variant?.kind === "premium";
  const logoClass = `bank-logo-${normalizeDayName(promo.bank).replace(/[^a-z0-9]+/g, "-")}`;
  const premiumBadge = isPremium ? `<span class="premium-badge">${escapeHtml(variant.label)}</span>` : "";
  const powerBadge = isPowerPromo
    ? `<span class="power-badge" title="Promo ueno+ POWER"><img src="${escapeAttribute(bankThemes["ueno bank"].logo)}" alt="" />ueno+ POWER</span>`
    : "";
  return `
    <article class="promo-card ${isPowerPromo ? "ueno-power-card" : ""} ${isPremium ? "premium-card" : ""}" data-id="${promo.id}" style="--bank-main:${theme.main};--bank-soft:${theme.soft};--bank-card:${theme.card};--logo-bg:${theme.logoBg}">
      <div class="logo-box">${theme.logo ? `<img class="${escapeAttribute(logoClass)}" src="${escapeAttribute(theme.logo)}" alt="${escapeAttribute(getBankLabel(promo.bank))}" />` : ""}</div>
      <div class="promo-content">
        <div class="promo-card-head">
          <h3 class="store-name">${renderCategoryIcon(categoryGroup)}<span>${escapeHtml(getPromoTitle(promo))}</span></h3>
          ${premiumBadge || powerBadge}
        </div>
        <div class="benefit-lines">${benefitLines.map((line) => `<span>${escapeHtml(line)}</span>`).join("")}</div>
        <p class="bank-card-line">${escapeHtml(getBankLabel(promo.bank))} · ${escapeHtml(categoryGroup)}</p>
        <div class="meta">
          <div><strong>Día:</strong> ${escapeHtml(getDisplayDays(promo))}</div>
          <div><strong>Vigencia:</strong> ${escapeHtml(getCardValidity(promo))}</div>
        </div>
      </div>
    </article>
  `;
}

function openDetail(id) {
  const promo = state.promotions.find((item) => item.id === id);
  if (!promo) return;
  els.dialogContent.innerHTML = `
    <h2>${escapeHtml(getPromoTitle(promo))}</h2>
    <p class="benefit">${escapeHtml(getMainBenefit(promo))}</p>
    <div class="detail-list">
      ${isUenoPowerPromo(promo) ? `<div class="power-detail"><strong>Promo especial:</strong> ueno+ POWER. Puede requerir desbloqueo o criterios adicionales en la app de ueno.</div>` : ""}
      <div><strong>Banco:</strong> ${escapeHtml(promo.bank || "")}</div>
      <div><strong>Categoría:</strong> ${escapeHtml(promo.category || "")}</div>
      <div><strong>Comercios/locales:</strong> ${escapeHtml(promo.merchant_locations_or_group || promo.merchant_name || "")}</div>
      <div><strong>Días:</strong> ${escapeHtml(getDisplayDays(promo))}</div>
      <div><strong>Vigencia:</strong> ${escapeHtml(getDisplayValidity(promo))}</div>
      <div><strong>Topes y mínimos:</strong> ${escapeHtml(promo.caps_and_minimums || "No especificado")}</div>
      <div><strong>Reglas por nivel:</strong> ${escapeHtml(promo.level_rules || "No aplica")}</div>
      <div><strong>Condiciones:</strong> ${escapeHtml(cleanSentence(promo.raw_detail || promo.validity || "Ver bases y condiciones"))}</div>
      <div><a href="${escapeAttribute(promo.source_url || "#")}" target="_blank" rel="noreferrer">Ver bases y condiciones</a></div>
    </div>
  `;
  els.dialog.showModal();
}

async function loadPromotions() {
  els.statusText.textContent = "Actualizando promociones...";
  const response = await fetch(`${DATA_URL}?t=${Date.now()}`);
  if (!response.ok) throw new Error("No se pudo cargar promotions.json");
  state.promotions = await response.json();
  render();
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
  state.activeCategory = "Todas";
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
  render();
});

els.results.addEventListener("click", (event) => {
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
  if (card) openDetail(card.dataset.id);
});

els.closeDialog.addEventListener("click", () => els.dialog.close());
els.refreshButton.addEventListener("click", () => loadPromotions().catch((error) => {
  els.statusText.textContent = error.message;
}));

loadPromotions().catch((error) => {
  els.statusText.textContent = error.message;
  els.results.innerHTML = `<div class="empty">No se pudieron cargar las promociones.</div>`;
});
