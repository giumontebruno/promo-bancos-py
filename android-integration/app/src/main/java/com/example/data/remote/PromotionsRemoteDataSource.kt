package com.example.data.remote

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

class PromotionsRemoteDataSource(
    private val client: HttpClient = defaultClient()
) {
    suspend fun fetchPromotions(): List<PromotionDto> =
        client.get(PROMOTIONS_URL).body()

    suspend fun fetchManifest(): PromotionsManifestDto =
        client.get(MANIFEST_URL).body()

    companion object {
        const val PROMOTIONS_URL =
            "https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/promotions.json"
        const val MANIFEST_URL =
            "https://raw.githubusercontent.com/giumontebruno/promo-bancos-py/main/public/manifest.json"

        fun defaultClient(): HttpClient =
            HttpClient(OkHttp) {
                install(ContentNegotiation) {
                    json(
                        Json {
                            ignoreUnknownKeys = true
                            explicitNulls = false
                        }
                    )
                }
            }
    }
}
