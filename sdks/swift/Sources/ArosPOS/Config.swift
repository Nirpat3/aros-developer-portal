import Foundation

// MARK: - Supported POS Vendors

public enum POSVendor: String, Codable, Sendable, CaseIterable {
    case mobilepos
    case verifoneCommander = "verifone-commander"
    case verifoneRuby = "verifone-ruby"
    case ncrAloha = "ncr-aloha"
    case ncrCounterpoint = "ncr-counterpoint"
    case ncrVoyix = "ncr-voyix"
    case gilbarcoPassport = "gilbarco-passport"
    case gilbarcoFlexpay = "gilbarco-flexpay"
    case wayneFusion = "wayne-fusion"
    case oracleSimphony = "oracle-simphony"
    case clover
    case square
    case toast
    case lightspeed
    case shopifyPOS = "shopify-pos"
    case generic
}

// MARK: - SDK Configuration

public struct ArosPOSConfig: Sendable {

    /// Base URL of the Shre platform (e.g. "http://server:5497").
    public let endpoint: String

    /// Tenant identifier for multi-tenant isolation.
    public let tenantId: String

    /// POS vendor integration type.
    public let vendor: POSVendor

    /// Unique device identifier for this register / terminal.
    public let deviceId: String

    /// Maximum number of events buffered before an automatic flush.
    public var batchSize: Int

    /// Interval in seconds between automatic flush attempts.
    public var flushInterval: TimeInterval

    /// Maximum events retained in the offline queue.
    public var maxQueueSize: Int

    /// URLSession timeout for individual requests.
    public var requestTimeout: TimeInterval

    public init(
        endpoint: String,
        tenantId: String,
        vendor: POSVendor,
        deviceId: String,
        batchSize: Int = 25,
        flushInterval: TimeInterval = 5,
        maxQueueSize: Int = 10_000,
        requestTimeout: TimeInterval = 10
    ) {
        self.endpoint = endpoint.hasSuffix("/") ? String(endpoint.dropLast()) : endpoint
        self.tenantId = tenantId
        self.vendor = vendor
        self.deviceId = deviceId
        self.batchSize = batchSize
        self.flushInterval = flushInterval
        self.maxQueueSize = maxQueueSize
        self.requestTimeout = requestTimeout
    }
}
