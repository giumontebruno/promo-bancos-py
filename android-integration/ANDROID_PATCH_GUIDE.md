# Android Integration Patch

Use this patch in the AI Studio Android project to replace hardcoded sample data with the live promotions database.

## Data URLs

```text
https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/promotions.json
https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/manifest.json
```

## Gradle dependencies

Add Ktor and Kotlin serialization if they are not already present:

```kotlin
implementation("io.ktor:ktor-client-core:2.3.12")
implementation("io.ktor:ktor-client-okhttp:2.3.12")
implementation("io.ktor:ktor-client-content-negotiation:2.3.12")
implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.12")
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
```

Add the serialization plugin if needed:

```kotlin
id("org.jetbrains.kotlin.plugin.serialization") version "<kotlin-version>"
```

## Files to add

Copy:

- `app/src/main/java/com/example/data/remote/PromotionDto.kt`
- `app/src/main/java/com/example/data/remote/PromotionsRemoteDataSource.kt`

## Repository change

In `BenefitsRepository`, add a remote data source and a sync function:

```kotlin
private val remote = PromotionsRemoteDataSource()

suspend fun syncRemotePromotions(): Result<Int> = runCatching {
    val promotions = remote.fetchPromotions()
    // Map PromotionDto -> local PromotionEntity.
    // Upsert into Room in a transaction.
    // Return number of promotions saved.
    promotions.size
}
```

Then make all screens read from Room instead of `CatalogData`.

## Required UI behavior

- On app start: load cached Room data immediately, then refresh in the background.
- Refresh button: call `syncRemotePromotions()`.
- Search: match `bank`, `category`, `merchantName`, `benefitSummary`, `capsAndMinimums`, `levelRules`.
- Today screen: filter by `promotionDays`.
- ueno details: always show `levelRules` and `capsAndMinimums`.

## Room storage suggestion

Store list fields as semicolon-separated strings unless the project already has converters:

```kotlin
percentages = dto.percentages.joinToString("; ")
promotionDays = dto.promotionDays.joinToString("; ")
```

