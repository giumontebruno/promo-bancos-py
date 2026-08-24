# Payback PY - Continuar desde otra PC

Este archivo resume el estado del proyecto para poder abrir un chat nuevo desde otra computadora y continuar sin depender de la conversación original.

## Proyecto

- Repositorio: https://github.com/giumontebruno/promo-bancos-py
- App publicada: https://giumontebruno.github.io/promo-bancos-py/app-web/
- Objetivo: app personal, luego comercializable, para consultar promociones bancarias de Paraguay en un solo lugar.

## Estado actual

- La app web esta publicada en GitHub Pages.
- Marca actual: Payback PY.
- Slogan: "Te devuelve mas".
- Branding oscuro, elegante, con crema/dorado como acento.
- Logo principal usado en el header: `app-web/assets/logos/payback-py-wordmark.png`.
- Iconos de app: `app-web/assets/logos/payback-py-icon-192.png` y `app-web/assets/logos/payback-py-icon-512.png`.
- Bancos actuales: UENO, Itau, Continental, Sudameris, BNF, Atlas, Coop. Universitaria.

## Criterios importantes de la app

- Las promociones vencidas no deben mostrarse bajo ningun caso.
- En "Hoy" se priorizan promociones puntuales del dia, ordenadas por mayor descuento/reintegro.
- Las promociones de todos los dias se muestran despues.
- Las cuotas sin intereses se muestran mas abajo que los descuentos/reintegros.
- Si un banco esta seleccionado, debe mantenerse al cambiar categoria o dia.
- Los filtros no deben obligar a desplazamiento horizontal; deben verse todos.
- En UENO, el selector debe decir "Nivel 1", "Nivel 2", etc. y adaptar beneficios/topes al nivel elegido.
- "Beneficios del mes" no es un comercio; las tarjetas deben representar locales/comercios reales.
- Las tarjetas premium van separadas de las tarjetas normales. Ejemplos: Itau Black, UENO Black, Continental Privilege, Mastercard Black/Visa Infinite cuando corresponda.
- Los textos deben estar normalizados: no copiar mayusculas/minusculas desordenadas de PDFs.

## Modulo Cerca

Objetivo: que el usuario pueda ver promociones cercanas como un mapa tipo Airbnb.

Estado actual:

- Usa Google Maps si hay API key configurada y Leaflet como fallback.
- Carga ubicaciones desde `public/locations.json`.
- Lista ubicaciones cercanas, no grupos abstractos.
- Si una ubicacion tiene promos de mas de un banco, muestra un numerito con la cantidad de bancos.
- El color del punto corresponde al banco con el mejor beneficio detectado.
- Las promos del local seleccionado se separan en:
  - Promos de hoy
  - Todos los dias
  - Cuotas sin intereses
  - Otras promos
- Los puntos con promos puntuales de hoy tienen un glow dorado leve.

Pendiente en Cerca:

- Mejorar la calidad de geolocalizacion por comercio/sucursal en Asuncion y Gran Asuncion.
- Cruzar nombres, ciudades y direcciones con Google Places para ubicar locales exactos.
- Evitar puntos duplicados o demasiado cercanos cuando representan el mismo local.
- Mejorar navegacion y densidad de marcadores cuando hay muchos puntos juntos.

## Datos y scraping

Fuentes trabajadas:

- Sudameris
- Itau
- Continental
- UENO
- BNF
- Atlas
- Coop. Universitaria

Reglas:

- Cada promocion debe cruzarse con bases y condiciones cuando existan.
- Extraer: comercio, banco, categoria, beneficio, dias, vigencia, topes, minimos, tarjetas aplicables, tarjetas excluidas, reglas por nivel, condiciones relevantes y URL/fuente.
- Para UENO, todos los comercios pueden tener beneficios por niveles; respetar el nivel seleccionado.
- Para BNF, muchas promos agrupan comercios por categoria; mostrar cantidad de locales y principales comercios cuando aplique.
- Fuente debe mostrar fecha de ultima actualizacion.

Automatizacion deseada:

- Reescaneo semanal preferentemente los viernes.
- Si termina el mes, actualizar el dia 1 del mes, idealmente entre 00:00 y 05:00.
- Todavia conviene revisar si el workflow programado quedo activo y funcionando.

## Para continuar desde otra PC

1. Clonar el repo:

```bash
git clone https://github.com/giumontebruno/promo-bancos-py.git
cd promo-bancos-py
```

2. Abrir el proyecto con Codex/ChatGPT Work.

3. En el nuevo chat, pegar este mensaje:

```text
Estoy continuando el proyecto Payback PY desde otra PC.
Usa el repo actual y lee CONTINUAR_DESDE_OTRA_PC.md para entender el estado del proyecto, criterios de diseño, scraping y pendientes.
Primero revisa el estado del repo y luego seguimos con los ajustes que te indique.
```

4. Si hay claves privadas o API keys para scraping/backend, configurarlas localmente. No subir claves privadas al repo.

## Archivos principales

- App web: `app-web/index.html`, `app-web/app.js`, `app-web/styles.css`
- Manifest/PWA: `app-web/manifest.webmanifest`, `app-web/sw.js`
- Datos de promociones: `public/promotions.json`
- Datos de ubicaciones: `public/locations.json`
- Scrapers: `scrapers/`
- Backend auxiliar: `promo_backend/`

