# Integración con la APK

## Enfoque recomendado

La APK no debería hacer scraping. Debe consumir una base ya procesada:

1. GitHub Actions actualiza `public/promotions.json`.
2. La app descarga ese JSON al abrir o al tocar "Actualizar".
3. Room guarda una copia local para uso offline.
4. La UI filtra por día, categoría, banco, comercio y favoritos.

## URL de datos

Cuando el repo esté en GitHub, la URL puede ser:

```text
https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/promotions.json
```

Más adelante se puede reemplazar por:

```text
https://api.tudominio.com/promotions
```

## Modelo Kotlin sugerido

```kotlin
data class PromotionDto(
    val id: String,
    val bank: String,
    val category: String,
    val merchant_name: String,
    val merchant_locations_or_group: String,
    val benefit_summary: String,
    val benefit_type: String,
    val percentages: List<String>,
    val promotion_days: List<String>,
    val day_text: String,
    val validity: String,
    val caps_and_minimums: String,
    val level_rules: String,
    val source_url: String
)
```

## Funciones de app

- Pantalla "Hoy": filtra `promotion_days` por el día actual.
- Categorías: agrupa por `category`.
- Bancos: filtra por `bank`.
- Favoritos: guarda `merchant_name`, `category` y/o `bank`.
- Notificaciones: cada mañana compara favoritos contra promociones del día.
- Nivel ueno: guardar nivel del usuario y mostrar reglas en `level_rules`.

## Próximo paso técnico

Reemplazar cualquier `CatalogData.kt` o datos hardcodeados por un repositorio remoto:

```text
Remote JSON -> Repository -> Room -> ViewModel -> Screens
```
