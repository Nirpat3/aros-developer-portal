import Foundation

// MARK: - SDK Errors

public enum ArosPOSError: Error, Sendable {
    case invalidURL(String)
    case httpError(statusCode: Int, body: String?)
    case decodingFailed(Error)
    case notRegistered
}

// MARK: - Main SDK

/// Thread-safe AROS POS SDK backed by a Swift actor.
public final class ArosPOS: @unchecked Sendable {

    public let config: ArosPOSConfig

    private let engine: SDKEngine

    public init(config: ArosPOSConfig) {
        self.config = config
        self.engine = SDKEngine(config: config)
    }

    // MARK: - Device Registration

    /// Register this device with the Shre platform.
    @discardableResult
    public func registerDevice(metadata: [String: AnyCodable]? = nil) async throws -> DeviceRegistrationResponse {
        try await engine.registerDevice(metadata: metadata)
    }

    // MARK: - Fire-and-Forget Events

    /// Enqueue a raw ConnexusEvent. Flushed automatically on batch/timer.
    public func track(_ event: ConnexusEvent) {
        Task { await engine.enqueue(event) }
    }

    /// Convenience: item scanned event.
    public func itemScanned(_ item: ItemData) {
        let event = ConnexusEvent(
            vendor: config.vendor.rawValue,
            eventType: "item_scanned",
            data: item.asDictionary,
            deviceId: config.deviceId,
            tenantId: config.tenantId
        )
        track(event)
    }

    /// Convenience: transaction completed event.
    public func transactionCompleted(transactionId: String, total: Double, itemCount: Int) {
        let event = ConnexusEvent(
            vendor: config.vendor.rawValue,
            eventType: "transaction_completed",
            data: [
                "transactionId": AnyCodable(transactionId),
                "total": AnyCodable(total),
                "itemCount": AnyCodable(itemCount)
            ],
            deviceId: config.deviceId,
            tenantId: config.tenantId
        )
        track(event)
    }

    /// Convenience: custom event.
    public func trackEvent(_ eventType: String, data: [String: AnyCodable] = [:]) {
        let event = ConnexusEvent(
            vendor: config.vendor.rawValue,
            eventType: eventType,
            data: data,
            deviceId: config.deviceId,
            tenantId: config.tenantId
        )
        track(event)
    }

    // MARK: - Basket Learning

    /// Teach the platform about a completed basket for recommendation training.
    public func learnBasket(items: [[String: AnyCodable]], transactionId: String? = nil) async throws {
        try await engine.learnBasket(items: items, transactionId: transactionId)
    }

    // MARK: - Intelligence (async/await)

    /// Fetch item recommendations based on a scanned or selected item.
    public func getRecommendations(itemId: String, limit: Int = 5) async throws -> [Recommendation] {
        try await engine.getRecommendations(itemId: itemId, limit: limit)
    }

    /// Fetch a customer's frequently ordered items for quick reorder.
    public func getQuickOrder(customerId: String, limit: Int = 10) async throws -> [QuickOrderItem] {
        try await engine.getQuickOrder(customerId: customerId, limit: limit)
    }

    /// Fetch pending messages for this device.
    public func getMessages() async throws -> [DeviceMessage] {
        try await engine.getMessages()
    }

    /// Acknowledge a message so it is not delivered again.
    public func acknowledgeMessage(id: String) async throws {
        try await engine.acknowledgeMessage(id: id)
    }

    /// Fetch real-time analytics for the tenant.
    public func getAnalytics(minutes: Int = 60) async throws -> AnalyticsResponse {
        try await engine.getAnalytics(minutes: minutes)
    }

    // MARK: - Queue Management

    /// Force-flush the event queue immediately.
    public func flush() async {
        await engine.flush()
    }

    /// Number of events currently queued.
    public var pendingEventCount: Int {
        get async { await engine.pendingCount }
    }
}

// MARK: - Actor Engine (thread-safe internals)

actor SDKEngine {

    private let config: ArosPOSConfig
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    private var queue: [ConnexusEvent] = []
    private var flushTimer: Timer?

    init(config: ArosPOSConfig) {
        self.config = config

        let sessionConfig = URLSessionConfiguration.default
        sessionConfig.timeoutIntervalForRequest = config.requestTimeout
        self.session = URLSession(configuration: sessionConfig)

        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase

        Task { await startFlushTimer() }
    }

    // MARK: Queue

    var pendingCount: Int { queue.count }

    func enqueue(_ event: ConnexusEvent) {
        if queue.count >= config.maxQueueSize {
            queue.removeFirst(config.batchSize)
        }
        queue.append(event)
        if queue.count >= config.batchSize {
            Task { await flush() }
        }
    }

    func flush() async {
        guard !queue.isEmpty else { return }
        let batch = Array(queue.prefix(config.batchSize))
        do {
            try await postJSON(path: "/v1/connexus/ingest", body: ["events": batch])
            queue.removeFirst(min(batch.count, queue.count))
        } catch {
            // Events stay in queue for retry on next flush cycle.
        }
    }

    // MARK: Timer

    private func startFlushTimer() {
        let interval = config.flushInterval
        Task.detached { [weak self] in
            while true {
                try? await Task.sleep(nanoseconds: UInt64(interval * 1_000_000_000))
                await self?.flush()
            }
        }
    }

    // MARK: Device Registration

    func registerDevice(metadata: [String: AnyCodable]?) async throws -> DeviceRegistrationResponse {
        let body = DeviceRegistration(
            deviceId: config.deviceId,
            tenantId: config.tenantId,
            vendor: config.vendor.rawValue,
            metadata: metadata
        )
        let data = try await postJSON(path: "/v1/connexus/register", body: body)
        return try decoder.decode(DeviceRegistrationResponse.self, from: data)
    }

    // MARK: Basket Learning

    func learnBasket(items: [[String: AnyCodable]], transactionId: String?) async throws {
        let body = BasketLearnRequest(
            tenantId: config.tenantId,
            deviceId: config.deviceId,
            items: items,
            transactionId: transactionId
        )
        try await postJSON(path: "/v1/connexus/ingest/learn", body: body)
    }

    // MARK: Intelligence

    func getRecommendations(itemId: String, limit: Int) async throws -> [Recommendation] {
        let body = RecommendationRequest(itemId: itemId, tenantId: config.tenantId, limit: limit)
        let data = try await postJSON(path: "/v1/pos/recommend", body: body)
        let response = try decoder.decode(RecommendationResponse.self, from: data)
        return response.recommendations ?? []
    }

    func getQuickOrder(customerId: String, limit: Int) async throws -> [QuickOrderItem] {
        let body = QuickOrderRequest(customerId: customerId, tenantId: config.tenantId, limit: limit)
        let data = try await postJSON(path: "/v1/pos/quick-order", body: body)
        let response = try decoder.decode(QuickOrderResponse.self, from: data)
        return response.items ?? []
    }

    func getMessages() async throws -> [DeviceMessage] {
        let data = try await getJSON(
            path: "/v1/pos/messages/\(config.deviceId)",
            query: [("tenantId", config.tenantId)]
        )
        let response = try decoder.decode(MessagesResponse.self, from: data)
        return response.messages ?? []
    }

    func acknowledgeMessage(id: String) async throws {
        try await postJSON(path: "/v1/pos/messages/\(id)/ack", body: EmptyBody())
    }

    func getAnalytics(minutes: Int) async throws -> AnalyticsResponse {
        let data = try await getJSON(
            path: "/v1/pos/analytics",
            query: [("tenantId", config.tenantId), ("minutes", String(minutes))]
        )
        return try decoder.decode(AnalyticsResponse.self, from: data)
    }

    // MARK: - HTTP Helpers

    @discardableResult
    private func postJSON<T: Encodable>(path: String, body: T) async throws -> Data {
        guard let url = URL(string: config.endpoint + path) else {
            throw ArosPOSError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)
        return data
    }

    private func getJSON(path: String, query: [(String, String)] = []) async throws -> Data {
        var components = URLComponents(string: config.endpoint + path)
        if !query.isEmpty {
            components?.queryItems = query.map { URLQueryItem(name: $0.0, value: $0.1) }
        }
        guard let url = components?.url else {
            throw ArosPOSError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)
        return data
    }

    private func validateResponse(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200...299).contains(http.statusCode) else {
            throw ArosPOSError.httpError(
                statusCode: http.statusCode,
                body: String(data: data, encoding: .utf8)
            )
        }
    }
}

// MARK: - Internal Helpers

private struct EmptyBody: Encodable {}
