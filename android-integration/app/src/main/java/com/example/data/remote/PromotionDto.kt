package com.example.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PromotionDto(
    val id: String,
    val bank: String,
    val category: String,
    @SerialName("merchant_name") val merchantName: String,
    @SerialName("merchant_locations_or_group") val merchantLocationsOrGroup: String = "",
    @SerialName("benefit_summary") val benefitSummary: String = "",
    @SerialName("benefit_type") val benefitType: String = "",
    val percentages: List<String> = emptyList(),
    @SerialName("promotion_days") val promotionDays: List<String> = emptyList(),
    @SerialName("day_text") val dayText: String = "",
    val validity: String = "",
    @SerialName("caps_and_minimums") val capsAndMinimums: String = "",
    @SerialName("level_rules") val levelRules: String = "",
    @SerialName("source_url") val sourceUrl: String = "",
    @SerialName("raw_detail") val rawDetail: String = ""
)

@Serializable
data class PromotionsManifestDto(
    @SerialName("generated_at") val generatedAt: String,
    @SerialName("promotion_count") val promotionCount: Int,
    val banks: List<String> = emptyList(),
    val categories: List<String> = emptyList()
)
