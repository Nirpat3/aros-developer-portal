package com.shreai.sdk.example

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

class ShreSDK(
    private val tenantId: String,
    private val baseUrl: String = "https://apiauth.shre.ai"
) {
    private val client = OkHttpClient()

    fun sendEventsBatch(
        events: List<Map<String, Any>>,
        onSuccess: (Map<String, Any>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        try {
            val url = "$baseUrl/v1/events/batch"
            val headers = mapOf(
                "Content-Type" to "application/json",
                "x-shre-tenant" to tenantId,
                "x-shre-app" to "android",
            )

            val jsonArray = JSONArray()
            events.forEach { event ->
                val jsonObject = JSONObject(event)
                jsonArray.put(jsonObject)
            }

            val requestBody = JSONObject().apply {
                put("events", jsonArray)
            }.toString().toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .apply {
                    headers.forEach { (key, value) -> addHeader(key, value) }
                }
                .build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    throw IOException("HTTP ${response.code}: ${response.body?.string()}")
                }

                val responseBody = response.body?.string() ?: "{}"
                val result = JSONObject(responseBody).toMap()
                onSuccess(result)
            }
        } catch (e: Exception) {
            onError(e)
        }
    }

    private fun JSONObject.toMap(): Map<String, Any> {
        val map = mutableMapOf<String, Any>()
        val keys = this.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            map[key] = this.get(key)
        }
        return map
    }
}
