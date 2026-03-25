package com.aros.pos

/**
 * Supported POS vendor identifiers.
 *
 * Use [PosVendor.CUSTOM] with a suffix for unlisted vendors (e.g. `"custom-acme"`).
 */
object PosVendor {
    const val MOBILE_POS = "mobilepos"
    const val VERIFONE_COMMANDER = "verifone-commander"
    const val VERIFONE_RUBY = "verifone-ruby"
    const val NCR_ALOHA = "ncr-aloha"
    const val NCR_COUNTERPOINT = "ncr-counterpoint"
    const val NCR_VOYIX = "ncr-voyix"
    const val GILBARCO_PASSPORT = "gilbarco-passport"
    const val GILBARCO_FLEXPAY = "gilbarco-flexpay"
    const val WAYNE_FUSION = "wayne-fusion"
    const val ORACLE_SIMPHONY = "oracle-simphony"
    const val CLOVER = "clover"
    const val SQUARE = "square"
    const val TOAST = "toast"
    const val LIGHTSPEED = "lightspeed"
    const val SHOPIFY_POS = "shopify-pos"
    const val GENERIC = "generic"

    /** Prefix for custom vendor identifiers. Use as `"custom-yourvendor"`. */
    const val CUSTOM = "custom-"

    private val KNOWN = setOf(
        MOBILE_POS, VERIFONE_COMMANDER, VERIFONE_RUBY,
        NCR_ALOHA, NCR_COUNTERPOINT, NCR_VOYIX,
        GILBARCO_PASSPORT, GILBARCO_FLEXPAY, WAYNE_FUSION,
        ORACLE_SIMPHONY, CLOVER, SQUARE, TOAST,
        LIGHTSPEED, SHOPIFY_POS, GENERIC
    )

    /** Returns `true` if [vendor] is a known vendor or matches the `custom-*` pattern. */
    fun isValid(vendor: String): Boolean =
        vendor in KNOWN || vendor.startsWith(CUSTOM)
}

/**
 * Configuration for [ArosPOS].
 *
 * @property endpoint   Base URL of the AROS API (e.g. `"http://server:5497"`).
 * @property tenantId   Tenant / store identifier.
 * @property vendor     POS vendor identifier (see [PosVendor]).
 * @property deviceId   Unique device or register identifier.
 * @property apiKey     Bearer token for API authentication.
 * @property timeoutMs  HTTP request timeout in milliseconds (default 10 000).
 * @property offlineQueue  When `true`, events are queued and flushed in batches while offline (default `true`).
 * @property maxQueueSize  Maximum number of events held in the offline queue (default 500).
 * @property flushIntervalMs  Interval between automatic queue flushes in milliseconds (default 5 000).
 */
data class ArosPOSConfig(
    val endpoint: String,
    val tenantId: String,
    val vendor: String,
    val deviceId: String,
    val apiKey: String = "",
    val timeoutMs: Int = 10_000,
    val offlineQueue: Boolean = true,
    val maxQueueSize: Int = 500,
    val flushIntervalMs: Long = 5_000L
) {
    init {
        require(endpoint.isNotBlank()) { "endpoint must not be blank" }
        require(tenantId.isNotBlank()) { "tenantId must not be blank" }
        require(PosVendor.isValid(vendor)) { "unknown vendor '$vendor' — use PosVendor constants or 'custom-*'" }
        require(deviceId.isNotBlank()) { "deviceId must not be blank" }
    }

    /** Endpoint with trailing slash stripped for consistent URL building. */
    internal val baseUrl: String get() = endpoint.trimEnd('/')
}
