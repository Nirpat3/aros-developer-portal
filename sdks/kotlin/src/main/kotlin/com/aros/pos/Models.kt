package com.aros.pos

import java.time.Instant

// ---------------------------------------------------------------------------
// Connexus event
// ---------------------------------------------------------------------------

/**
 * A single POS event destined for the Connexus ingest endpoint.
 */
data class ConnexusEvent(
    val vendor: String,
    val eventType: String,
    val data: Map<String, Any?>,
    val deviceId: String,
    val tenantId: String,
    val timestamp: String = Instant.now().toString()
)

// ---------------------------------------------------------------------------
// Convenience event data helpers
// ---------------------------------------------------------------------------

/** Data payload for an item-scanned event. */
data class ItemData(
    val barcode: String,
    val price: Double = 0.0,
    val quantity: Int = 1,
    val name: String = "",
    val metadata: Map<String, Any?> = emptyMap()
)

/** Data payload for a transaction-completed event. */
data class TransactionData(
    val transactionId: String,
    val total: Double = 0.0,
    val itemCount: Int = 0,
    val paymentMethod: String = "",
    val metadata: Map<String, Any?> = emptyMap()
)

/** Data payload for a fuel-dispensed event. */
data class FuelData(
    val pumpNumber: Int,
    val fuelGrade: String = "",
    val gallons: Double = 0.0,
    val total: Double = 0.0,
    val metadata: Map<String, Any?> = emptyMap()
)

// ---------------------------------------------------------------------------
// Intelligence response types
// ---------------------------------------------------------------------------

/** A single product recommendation. */
data class Recommendation(
    val itemId: String = "",
    val name: String = "",
    val confidence: Double = 0.0,
    val reason: String = "",
    val metadata: Map<String, Any?> = emptyMap()
)

/** Response from `POST /v1/pos/recommend`. */
data class RecommendationResponse(
    val recommendations: List<Recommendation> = emptyList(),
    val raw: Map<String, Any?> = emptyMap()
)

/** A single quick-order item. */
data class QuickOrderItem(
    val itemId: String = "",
    val name: String = "",
    val frequency: Int = 0,
    val lastPurchased: String = "",
    val metadata: Map<String, Any?> = emptyMap()
)

/** Response from `POST /v1/pos/quick-order`. */
data class QuickOrderResponse(
    val items: List<QuickOrderItem> = emptyList(),
    val raw: Map<String, Any?> = emptyMap()
)

/** A single cashier message. */
data class CashierMessage(
    val messageId: String = "",
    val content: String = "",
    val priority: String = "normal",
    val createdAt: String = "",
    val metadata: Map<String, Any?> = emptyMap()
)

/** Response from `GET /v1/pos/messages/{deviceId}`. */
data class MessagesResponse(
    val messages: List<CashierMessage> = emptyList(),
    val raw: Map<String, Any?> = emptyMap()
)

/** Response from `GET /v1/pos/analytics`. */
data class AnalyticsResponse(
    val data: Map<String, Any?> = emptyMap(),
    val raw: Map<String, Any?> = emptyMap()
)

/** Response from `POST /v1/pos/messages/{id}/ack`. */
data class AckResponse(
    val acknowledged: Boolean = false,
    val raw: Map<String, Any?> = emptyMap()
)

/** Response from `POST /v1/connexus/register`. */
data class RegisterResponse(
    val registered: Boolean = false,
    val raw: Map<String, Any?> = emptyMap()
)
