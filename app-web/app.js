const DATA_URL = "../public/promotions.json";
const DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
const BANKS = ["Todos", "ueno bank", "Itaú", "Continental", "Sudameris", "BNF"];

const state = {
  promotions: [],
  activeBank: "Todos",
  activeDay: "hoy",
  query: "",
  uenoLevel: 5,
};

const bankThemes = {
  "ueno bank": { main: "#007a53", soft: "#dcf6eb" },
  "Itaú": { main: "#ec7000", soft: "#fff0df" },
  "Continental": { main: "#9f1736", soft: "#fde8ee" },
  "Sudameris": { main: "#0057a8", soft: "#e4f0ff" },
  "BNF": { main: "#004b8d", soft: "#e3effa" },
};

const els = {
  bankTabs: document.querySelector("#bankTabs"),
  dayTabs: document.querySelector("#dayTabs"),
  searchInput: document.querySelector("#searchInput"),
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

function inferPromotionDaysFromText(promo) {
  const existing = (promo.promotion_days || []).map(normalizeDayName).filter(Boolean);
  if (existing.length) return existing;

  const text = normalizeDayName(`${promo.day_text || ""} ${promo.validity || ""}`);
  if (!text || text.includes("no especificado")) return [];
  if (text.includes("todos los dias") || text.includes("todos los días")) return [...DAYS];

  const found = DAYS.filter((day) => text.includes(normalizeDayName(day)));
  const range = inferDayRange(text);
  return [...new Set([...found, ...range])];
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
  return bankThemes[bank] || { main: "#334155", soft: "#eef2f7" };
}

function getMainBenefit(promo) {
  if (promo.bank === "ueno bank") {
    return getBenefitForSelectedUenoLevel(promo, state.uenoLevel);
  }
  const pct = (promo.percentages || [])[0];
  if (pct && promo.benefit_summary?.toLowerCase().includes(pct.toLowerCase())) return promo.benefit_summary;
  return [pct, promo.benefit_type].filter(Boolean).join(" ") || promo.benefit_summary || "Ver detalle";
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

function getPromoTitle(promo) {
  const merchant = promo.merchant_name || promo.category || "Promoción";
  return `${merchant} - ${getMainBenefit(promo)}`;
}

function appliesToSelectedDay(promo, selectedDay) {
  const day = selectedDay === "hoy" ? getTodayInParaguay() : selectedDay;
  if (selectedDay === "hoy" && !passesOrdinalDayRule(promo, day)) return false;
  return inferPromotionDaysFromText(promo).includes(day);
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

function sectionPromotions(promos) {
  const exact = [];
  const everydayDiscounts = [];
  const everydayInstallments = [];

  promos.forEach((promo) => {
    const everyDay = isEveryDayPromotion(promo);
    if (everyDay && isInstallmentsOnly(promo)) {
      everydayInstallments.push(promo);
    } else if (everyDay) {
      everydayDiscounts.push(promo);
    } else {
      exact.push(promo);
    }
  });

  return [
    ["Promos de hoy", exact],
    ["Todos los dias con descuento o reintegro", everydayDiscounts],
    ["Cuotas sin intereses todos los dias", everydayInstallments],
  ].filter(([, items]) => items.length);
}

function renderTabs() {
  els.bankTabs.innerHTML = BANKS.map((bank) => (
    `<button class="${state.activeBank === bank ? "active" : ""}" data-bank="${bank}">${bank}</button>`
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

function render() {
  renderTabs();
  const base = state.promotions
    .filter(matchesBank)
    .filter(matchesQuery)
    .filter((promo) => appliesToSelectedDay(promo, state.activeDay))
    .sort(sortPromotions);

  els.statusText.textContent = `Dia activo: ${state.activeDay === "hoy" ? capitalize(getTodayInParaguay()) : capitalize(state.activeDay)}`;
  els.countText.textContent = `${base.length} promociones`;

  if (!base.length) {
    els.results.innerHTML = `<div class="empty">No encontramos promociones para estos filtros.</div>`;
    return;
  }

  els.results.innerHTML = sectionPromotions(base).map(([title, items]) => `
    <section>
      <h2 class="section-title">${title}</h2>
      <div class="grid">${items.map(renderCard).join("")}</div>
    </section>
  `).join("");
}

function sortPromotions(a, b) {
  return String(a.merchant_name || "").localeCompare(String(b.merchant_name || ""), "es");
}

function renderCard(promo) {
  const theme = getBankTheme(promo.bank);
  return `
    <article class="promo-card" data-id="${promo.id}" style="--bank-main:${theme.main};--bank-soft:${theme.soft}">
      <h3 class="promo-title">${escapeHtml(getPromoTitle(promo))}</h3>
      <div class="bank-line">
        <span class="pill">${escapeHtml(promo.bank || "Banco")}</span>
        <span class="pill">${escapeHtml(promo.category || "Categoria")}</span>
      </div>
      <div class="meta">
        <div><strong>Dia:</strong> ${escapeHtml(promo.day_text || promo.validity || "No especificado")}</div>
        <div><strong>Vigencia:</strong> ${escapeHtml(promo.validity || "Ver bases")}</div>
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
      <div><strong>Banco:</strong> ${escapeHtml(promo.bank || "")}</div>
      <div><strong>Categoria:</strong> ${escapeHtml(promo.category || "")}</div>
      <div><strong>Comercios/locales:</strong> ${escapeHtml(promo.merchant_locations_or_group || promo.merchant_name || "")}</div>
      <div><strong>Dias:</strong> ${escapeHtml(promo.day_text || "")}</div>
      <div><strong>Vigencia:</strong> ${escapeHtml(promo.validity || "")}</div>
      <div><strong>Topes y minimos:</strong> ${escapeHtml(promo.caps_and_minimums || "No especificado")}</div>
      <div><strong>Reglas por nivel:</strong> ${escapeHtml(promo.level_rules || "No aplica")}</div>
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
  const bank = event.target?.dataset?.bank;
  if (!bank) return;
  state.activeBank = bank;
  render();
});

els.dayTabs.addEventListener("click", (event) => {
  const day = event.target?.dataset?.day;
  if (!day) return;
  state.activeDay = day;
  render();
});

els.uenoLevelPanel.addEventListener("click", (event) => {
  const level = Number(event.target?.dataset?.level);
  if (!level) return;
  state.uenoLevel = level;
  render();
});

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

els.results.addEventListener("click", (event) => {
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
