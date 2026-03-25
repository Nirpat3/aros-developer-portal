package com.aros.pos

import kotlinx.coroutines.*
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.atomic.AtomicBoolean

/**
 * AROS POS SDK — Kotlin / Android.
 *
 * Pure Kotlin with no external dependencies beyond `kotlinx-coroutines` and
 * `java.net.HttpURLConnection`. Compatible with Android API 24+ and JVM servers.
 *
 * Usage:
 * ```kotlin
 * val pos = ArosPOS(ArosPOSConfig(
 *     endpoint = "http://server:5497",
 *     tenantId = "store-42",
 *     vendor = PosVendor.VERIFONE_COMMANDER,
 *     deviceId = "REG-001"
 * ))
 *
 * // fire-and-forget
 * pos.itemScanned(ItemData(barcode = "012345", price = 9.99))
 *
 * // suspend (returns result)
 * val recs = pos.getRecommendations("item-123")
 *
 * // clean shutdown
 * pos.close()
 * ```
 */
class ArosPOS(private val config: ArosPOSConfig) {

    private val queue = ConcurrentLinkedQueue<ConnexusEvent>()
    private val running = AtomicBoolean(false)
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var flushJob: Job? = null

    init {
        if (config.offlineQueue) startFlushLoop()
    }

    // -----------------------------------------------------------------------
    // Lifecycle
    // -----------------------------------------------------------------------

    /**
     * Flush the remaining queue and cancel background jobs.
     * Safe to call multiple times.
     */
    fun close() {
        if (!running.compareAndSet(true, false) && flushJob == null) return
        running.set(false)
        runBlocking { flushQueue() }
        scope.cancel()
    }

    // -----------------------------------------------------------------------
    // Device registration
    // -----------------------------------------------------------------------

    /** Register this device with the Connexus platform. */
    suspend fun register(capabilities: Map<String, Any?> = emptyMap()): RegisterResponse {
        val body = buildJsonObject {
            put("vendor", config.vendor)
            put("deviceId", config.deviceId)
            put("tenantId", config.tenantId)
            put("capabilities", capabilities)
        }
        val raw = post("/v1/connexus/register", body)
        return RegisterResponse(
            registered = raw["registered"] as? Boolean ?: (raw["status"] == "ok"),
            raw = raw
        )
    }

    // -----------------------------------------------------------------------
    // Fire-and-forget event methods
    // -----------------------------------------------------------------------

    /** Record an item-scanned event. Queued and flushed automatically. */
    fun itemScanned(item: ItemData) {
        enqueue("item_scanned", buildMap {
            put("barcode", item.barcode)
            put("price", item.price)
            put("quantity", item.quantity)
            if (item.name.isNotEmpty()) put("name", item.name)
            putAll(item.metadata)
        })
    }

    /** Record a transaction-completed event. */
    fun transactionCompleted(tx: TransactionData) {
        enqueue("transaction_completed", buildMap {
            put("transactionId", tx.transactionId)
            put("total", tx.total)
            put("itemCount", tx.itemCount)
            if (tx.paymentMethod.isNotEmpty()) put("paymentMethod", tx.paymentMethod)
            putAll(tx.metadata)
        })
    }

    /** Record a fuel-dispensed event. */
    fun fuelDispensed(fuel: FuelData) {
        enqueue("fuel_dispensed", buildMap {
            put("pumpNumber", fuel.pumpNumber)
            if (fuel.fuelGrade.isNotEmpty()) put("fuelGrade", fuel.fuelGrade)
            put("gallons", fuel.gallons)
            put("total", fuel.total)
            putAll(fuel.metadata)
        })
    }

    /** Record a custom event with an arbitrary data payload. */
    fun trackEvent(eventType: String, data: Map<String, Any?> = emptyMap()) {
        enqueue(eventType, data)
    }

    // -----------------------------------------------------------------------
    // Suspend intelligence methods
    // -----------------------------------------------------------------------

    /** Get product recommendations for the given [itemId]. */
    suspend fun getRecommendations(
        itemId: String,
        limit: Int = 5
    ): RecommendationResponse {
        val body = buildJsonObject {
            put("itemId", itemId)
            put("tenantId", config.tenantId)
            put("deviceId", config.deviceId)
            put("limit", limit)
        }
        val raw = post("/v1/pos/recommend", body)
        val recs = (raw["recommendations"] as? List<*>)?.mapNotNull { entry ->
            val m = entry as? Map<*, *> ?: return@mapNotNull null
            Recommendation(
                itemId = m["itemId"]?.toString().orEmpty(),
                name = m["name"]?.toString().orEmpty(),
                confidence = (m["confidence"] as? Number)?.toDouble() ?: 0.0,
                reason = m["reason"]?.toString().orEmpty(),
                metadata = m.filterKeys { it != "itemId" && it != "name" && it != "confidence" && it != "reason" }
                    .map { (k, v) -> k.toString() to v }
                    .toMap()
            )
        } ?: emptyList()
        return RecommendationResponse(recommendations = recs, raw = raw)
    }

    /** Get quick-order items for the current device. */
    suspend fun getQuickOrder(customerId: String = ""): QuickOrderResponse {
        val body = buildJsonObject {
            put("tenantId", config.tenantId)
            put("deviceId", config.deviceId)
            if (customerId.isNotEmpty()) put("customerId", customerId)
        }
        val raw = post("/v1/pos/quick-order", body)
        val items = (raw["items"] as? List<*>)?.mapNotNull { entry ->
            val m = entry as? Map<*, *> ?: return@mapNotNull null
            QuickOrderItem(
                itemId = m["itemId"]?.toString().orEmpty(),
                name = m["name"]?.toString().orEmpty(),
                frequency = (m["frequency"] as? Number)?.toInt() ?: 0,
                lastPurchased = m["lastPurchased"]?.toString().orEmpty(),
                metadata = m.filterKeys { it !in setOf("itemId", "name", "frequency", "lastPurchased") }
                    .map { (k, v) -> k.toString() to v }
                    .toMap()
            )
        } ?: emptyList()
        return QuickOrderResponse(items = items, raw = raw)
    }

    /** Fetch pending messages for this device. */
    suspend fun getMessages(): MessagesResponse {
        val raw = get("/v1/pos/messages/${config.deviceId}?tenantId=${enc(config.tenantId)}")
        val msgs = (raw["messages"] as? List<*>)?.mapNotNull { entry ->
            val m = entry as? Map<*, *> ?: return@mapNotNull null
            CashierMessage(
                messageId = m["messageId"]?.toString().orEmpty(),
                content = m["content"]?.toString().orEmpty(),
                priority = m["priority"]?.toString() ?: "normal",
                createdAt = m["createdAt"]?.toString().orEmpty(),
                metadata = m.filterKeys { it !in setOf("messageId", "content", "priority", "createdAt") }
                    .map { (k, v) -> k.toString() to v }
                    .toMap()
            )
        } ?: emptyList()
        return MessagesResponse(messages = msgs, raw = raw)
    }

    /** Acknowledge a message by its [messageId]. */
    suspend fun acknowledgeMessage(messageId: String): AckResponse {
        val raw = post("/v1/pos/messages/$messageId/ack", buildJsonObject {
            put("deviceId", config.deviceId)
            put("tenantId", config.tenantId)
        })
        return AckResponse(
            acknowledged = raw["acknowledged"] as? Boolean ?: (raw["status"] == "ok"),
            raw = raw
        )
    }

    /** Fetch real-time analytics for the tenant. */
    suspend fun getAnalytics(minutes: Int = 60): AnalyticsResponse {
        val raw = get("/v1/pos/analytics?tenantId=${enc(config.tenantId)}&minutes=$minutes")
        return AnalyticsResponse(data = raw, raw = raw)
    }

    // -----------------------------------------------------------------------
    // Direct ingest (bypass queue)
    // -----------------------------------------------------------------------

    /** Send a single event immediately, bypassing the offline queue. */
    suspend fun ingest(event: ConnexusEvent): Map<String, Any?> =
        post("/v1/connexus/ingest", eventToMap(event))

    /** Send a batch of events immediately with the learn endpoint. */
    suspend fun ingestLearn(events: List<ConnexusEvent>): Map<String, Any?> =
        post("/v1/connexus/ingest/learn", buildJsonObject {
            put("events", events.map { eventToMap(it) })
        })

    // -----------------------------------------------------------------------
    // Queue internals
    // -----------------------------------------------------------------------

    private fun enqueue(eventType: String, data: Map<String, Any?>) {
        val event = ConnexusEvent(
            vendor = config.vendor,
            eventType = eventType,
            data = data,
            deviceId = config.deviceId,
            tenantId = config.tenantId,
            timestamp = Instant.now().toString()
        )
        if (!config.offlineQueue) {
            scope.launch { runCatching { ingest(event) } }
            return
        }
        if (queue.size >= config.maxQueueSize) {
            queue.poll() // drop oldest
        }
        queue.add(event)
    }

    private fun startFlushLoop() {
        running.set(true)
        flushJob = scope.launch {
            while (running.get() && isActive) {
                delay(config.flushIntervalMs)
                flushQueue()
            }
        }
    }

    private suspend fun flushQueue() {
        if (queue.isEmpty()) return
        val batch = mutableListOf<ConnexusEvent>()
        while (batch.size < config.maxQueueSize) {
            val event = queue.poll() ?: break
            batch.add(event)
        }
        if (batch.isEmpty()) return
        try {
            ingestLearn(batch)
        } catch (_: Exception) {
            // Re-queue on failure (up to max size)
            for (event in batch) {
                if (queue.size >= config.maxQueueSize) break
                queue.add(event)
            }
        }
    }

    // -----------------------------------------------------------------------
    // HTTP transport (java.net only)
    // -----------------------------------------------------------------------

    private suspend fun post(path: String, body: Map<String, Any?>): Map<String, Any?> =
        withContext(Dispatchers.IO) { http("POST", path, body) }

    private suspend fun get(path: String): Map<String, Any?> =
        withContext(Dispatchers.IO) { http("GET", path, null) }

    private fun http(method: String, path: String, body: Map<String, Any?>?): Map<String, Any?> {
        val url = URL("${config.baseUrl}$path")
        val conn = url.openConnection() as HttpURLConnection
        try {
            conn.requestMethod = method
            conn.connectTimeout = config.timeoutMs
            conn.readTimeout = config.timeoutMs
            conn.setRequestProperty("Content-Type", "application/json")
            conn.setRequestProperty("Accept", "application/json")
            if (config.apiKey.isNotEmpty()) {
                conn.setRequestProperty("Authorization", "Bearer ${config.apiKey}")
            }

            if (body != null) {
                conn.doOutput = true
                OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { writer ->
                    writer.write(toJson(body))
                }
            }

            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: "{}"
            val parsed = parseJson(text)

            if (code !in 200..299) {
                throw ArosPOSException("HTTP $code on $method $path", code, parsed)
            }
            return parsed
        } finally {
            conn.disconnect()
        }
    }

    // -----------------------------------------------------------------------
    // Minimal JSON serializer / parser (no external deps)
    // -----------------------------------------------------------------------

    private fun toJson(value: Any?): String = when (value) {
        null -> "null"
        is String -> "\"${escapeJson(value)}\""
        is Number -> value.toString()
        is Boolean -> value.toString()
        is Map<*, *> -> value.entries.joinToString(",", "{", "}") { (k, v) ->
            "\"${escapeJson(k.toString())}\":${toJson(v)}"
        }
        is List<*> -> value.joinToString(",", "[", "]") { toJson(it) }
        else -> "\"${escapeJson(value.toString())}\""
    }

    private fun escapeJson(s: String): String = s
        .replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")

    @Suppress("UNCHECKED_CAST")
    private fun parseJson(text: String): Map<String, Any?> {
        // Minimal recursive-descent JSON parser — handles objects, arrays,
        // strings, numbers, booleans, and null. Sufficient for API responses.
        val t = text.trim()
        if (t.isEmpty() || t == "null") return emptyMap()
        return JsonParser(t).parseObject()
    }

    private fun eventToMap(e: ConnexusEvent): Map<String, Any?> = buildMap {
        put("vendor", e.vendor)
        put("eventType", e.eventType)
        put("data", e.data)
        put("deviceId", e.deviceId)
        put("tenantId", e.tenantId)
        put("timestamp", e.timestamp)
    }

    private fun enc(s: String): String = java.net.URLEncoder.encode(s, "UTF-8")

    // -----------------------------------------------------------------------
    // Builder helper
    // -----------------------------------------------------------------------

    private inline fun buildJsonObject(block: MutableMap<String, Any?>.() -> Unit): Map<String, Any?> =
        mutableMapOf<String, Any?>().apply(block)
}

// ---------------------------------------------------------------------------
// Minimal JSON parser (no external dependencies)
// ---------------------------------------------------------------------------

internal class JsonParser(private val src: String) {
    private var pos = 0

    fun parseObject(): Map<String, Any?> {
        skipWhitespace()
        if (pos >= src.length || src[pos] != '{') return emptyMap()
        pos++ // skip '{'
        val map = mutableMapOf<String, Any?>()
        skipWhitespace()
        if (pos < src.length && src[pos] == '}') { pos++; return map }
        while (pos < src.length) {
            skipWhitespace()
            val key = parseString()
            skipWhitespace()
            expect(':')
            skipWhitespace()
            val value = parseValue()
            map[key] = value
            skipWhitespace()
            if (pos < src.length && src[pos] == ',') { pos++; continue }
            break
        }
        skipWhitespace()
        if (pos < src.length && src[pos] == '}') pos++
        return map
    }

    private fun parseArray(): List<Any?> {
        pos++ // skip '['
        val list = mutableListOf<Any?>()
        skipWhitespace()
        if (pos < src.length && src[pos] == ']') { pos++; return list }
        while (pos < src.length) {
            skipWhitespace()
            list.add(parseValue())
            skipWhitespace()
            if (pos < src.length && src[pos] == ',') { pos++; continue }
            break
        }
        skipWhitespace()
        if (pos < src.length && src[pos] == ']') pos++
        return list
    }

    private fun parseValue(): Any? {
        skipWhitespace()
        if (pos >= src.length) return null
        return when (src[pos]) {
            '"' -> parseString()
            '{' -> parseObject()
            '[' -> parseArray()
            't', 'f' -> parseBoolean()
            'n' -> parseNull()
            else -> parseNumber()
        }
    }

    private fun parseString(): String {
        expect('"')
        val sb = StringBuilder()
        while (pos < src.length) {
            val c = src[pos++]
            if (c == '"') return sb.toString()
            if (c == '\\' && pos < src.length) {
                when (val esc = src[pos++]) {
                    '"' -> sb.append('"')
                    '\\' -> sb.append('\\')
                    '/' -> sb.append('/')
                    'n' -> sb.append('\n')
                    'r' -> sb.append('\r')
                    't' -> sb.append('\t')
                    'u' -> {
                        if (pos + 4 <= src.length) {
                            val hex = src.substring(pos, pos + 4)
                            sb.append(hex.toInt(16).toChar())
                            pos += 4
                        }
                    }
                    else -> { sb.append('\\'); sb.append(esc) }
                }
            } else {
                sb.append(c)
            }
        }
        return sb.toString()
    }

    private fun parseNumber(): Number {
        val start = pos
        if (pos < src.length && src[pos] == '-') pos++
        while (pos < src.length && src[pos].isDigit()) pos++
        var isDouble = false
        if (pos < src.length && src[pos] == '.') {
            isDouble = true
            pos++
            while (pos < src.length && src[pos].isDigit()) pos++
        }
        if (pos < src.length && (src[pos] == 'e' || src[pos] == 'E')) {
            isDouble = true
            pos++
            if (pos < src.length && (src[pos] == '+' || src[pos] == '-')) pos++
            while (pos < src.length && src[pos].isDigit()) pos++
        }
        val s = src.substring(start, pos)
        return if (isDouble) s.toDouble() else s.toLong()
    }

    private fun parseBoolean(): Boolean {
        return if (src.startsWith("true", pos)) { pos += 4; true }
        else { pos += 5; false }
    }

    private fun parseNull(): Any? { pos += 4; return null }

    private fun skipWhitespace() {
        while (pos < src.length && src[pos].isWhitespace()) pos++
    }

    private fun expect(c: Char) {
        if (pos < src.length && src[pos] == c) pos++
    }
}

// ---------------------------------------------------------------------------
// Exception
// ---------------------------------------------------------------------------

/**
 * Thrown when an API request fails with a non-2xx status code.
 */
class ArosPOSException(
    message: String,
    val statusCode: Int,
    val body: Map<String, Any?> = emptyMap()
) : RuntimeException(message)
