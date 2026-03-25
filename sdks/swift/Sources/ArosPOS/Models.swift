import Foundation

// MARK: - Events

public struct ConnexusEvent: Codable, Sendable {
    public let vendor: String
    public let eventType: String
    public let data: [String: AnyCodable]
    public let deviceId: String
    public let tenantId: String
    public let timestamp: String

    public init(
        vendor: String,
        eventType: String,
        data: [String: AnyCodable],
        deviceId: String,
        tenantId: String,
        timestamp: Date = Date()
    ) {
        self.vendor = vendor
        self.eventType = eventType
        self.data = data
        self.deviceId = deviceId
        self.tenantId = tenantId
        self.timestamp = ISO8601DateFormatter().string(from: timestamp)
    }

    enum CodingKeys: String, CodingKey {
        case vendor, eventType, data, deviceId, tenantId, timestamp
    }
}

// MARK: - Item Data (convenience for item-scanned events)

public struct ItemData: Sendable {
    public let barcode: String
    public let price: Double
    public let quantity: Int
    public let description: String?

    public init(barcode: String, price: Double, quantity: Int = 1, description: String? = nil) {
        self.barcode = barcode
        self.price = price
        self.quantity = quantity
        self.description = description
    }

    var asDictionary: [String: AnyCodable] {
        var dict: [String: AnyCodable] = [
            "barcode": AnyCodable(barcode),
            "price": AnyCodable(price),
            "quantity": AnyCodable(quantity)
        ]
        if let description { dict["description"] = AnyCodable(description) }
        return dict
    }
}

// MARK: - Device Registration

public struct DeviceRegistration: Codable, Sendable {
    public let deviceId: String
    public let tenantId: String
    public let vendor: String
    public let metadata: [String: AnyCodable]?

    public init(deviceId: String, tenantId: String, vendor: String, metadata: [String: AnyCodable]? = nil) {
        self.deviceId = deviceId
        self.tenantId = tenantId
        self.vendor = vendor
        self.metadata = metadata
    }
}

public struct DeviceRegistrationResponse: Codable, Sendable {
    public let ok: Bool
    public let deviceId: String?
    public let message: String?
}

// MARK: - Recommendations

public struct RecommendationRequest: Codable, Sendable {
    public let itemId: String
    public let tenantId: String
    public let limit: Int
}

public struct Recommendation: Codable, Sendable {
    public let itemId: String
    public let name: String?
    public let score: Double?
    public let reason: String?
}

public struct RecommendationResponse: Codable, Sendable {
    public let ok: Bool
    public let recommendations: [Recommendation]?
    public let message: String?
}

// MARK: - Quick Order

public struct QuickOrderRequest: Codable, Sendable {
    public let customerId: String
    public let tenantId: String
    public let limit: Int
}

public struct QuickOrderItem: Codable, Sendable {
    public let itemId: String
    public let name: String?
    public let frequency: Int?
    public let lastOrdered: String?
}

public struct QuickOrderResponse: Codable, Sendable {
    public let ok: Bool
    public let items: [QuickOrderItem]?
    public let message: String?
}

// MARK: - Messages

public struct DeviceMessage: Codable, Sendable {
    public let id: String
    public let type: String?
    public let title: String?
    public let body: String?
    public let priority: String?
    public let createdAt: String?
}

public struct MessagesResponse: Codable, Sendable {
    public let ok: Bool
    public let messages: [DeviceMessage]?
}

public struct AckResponse: Codable, Sendable {
    public let ok: Bool
}

// MARK: - Analytics

public struct AnalyticsResponse: Codable, Sendable {
    public let ok: Bool
    public let data: [String: AnyCodable]?
    public let message: String?
}

// MARK: - Basket Learning

public struct BasketLearnRequest: Codable, Sendable {
    public let tenantId: String
    public let deviceId: String
    public let items: [[String: AnyCodable]]
    public let transactionId: String?
}

// MARK: - Type-erased Codable wrapper

/// A type-erased `Codable` + `Sendable` value for heterogeneous dictionaries.
public struct AnyCodable: Codable, Sendable {
    public let value: Any & Sendable

    public init(_ value: Any & Sendable) {
        self.value = value
    }

    // MARK: Decodable

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            value = NSNull()
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map(\.value)
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues(\.value)
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported type")
        }
    }

    // MARK: Encodable

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case is NSNull:
            try container.encodeNil()
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0 as! any Sendable) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0 as! any Sendable) })
        default:
            try container.encode(String(describing: value))
        }
    }
}
