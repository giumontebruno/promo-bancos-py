# Promo Bancos PY

Base automatizada de promociones bancarias de Paraguay para consumo desde una app Android.

## Fuentes iniciales

- Sudameris
- Itaú
- BNF
- Continental
- ueno bank

## Salidas para la app

Los archivos consumibles quedan en `public/`:

- `public/promotions.json`: lista normalizada de promociones.
- `public/promotions.csv`: misma base en CSV.
- `public/index_by_day.json`: ids de promociones agrupados por día.
- `public/index_by_category.json`: ids agrupados por categoría.
- `public/manifest.json`: fecha de generación, bancos, categorías y conteo.

## Automatización

El workflow `.github/workflows/refresh-promotions.yml` corre todos los días a las 04:00 de Paraguay, pero solo actualiza datos si:

- es viernes, o
- es el día 1 del mes.

También puede ejecutarse manualmente desde GitHub Actions.

## Ejecución local

```bash
pip install -r requirements.txt
python promo_backend/run_all.py
```

## Integración Android

La app debe leer `promotions.json` desde una URL pública del repositorio o desde una API propia.

URL pública actual:

```text
https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/promotions.json
```

Campos principales:

- `bank`
- `category`
- `merchant_name`
- `benefit_summary`
- `benefit_type`
- `percentages`
- `promotion_days`
- `day_text`
- `validity`
- `caps_and_minimums`
- `level_rules`
- `source_url`

Para uso personal, se puede consumir directamente el JSON publicado. Para comercializar, conviene poner una API intermedia con cache, autenticación y analítica.

La carpeta `android-integration/` contiene un kit de integración para la APK generada en AI Studio: DTOs, cliente remoto y guía de parche para reemplazar datos hardcodeados por cache local + JSON remoto.
