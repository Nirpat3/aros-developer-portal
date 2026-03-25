// swift-tools-version: 5.7

import PackageDescription

let package = Package(
    name: "ArosPOS",
    platforms: [
        .iOS(.v15),
        .macOS(.v12)
    ],
    products: [
        .library(name: "ArosPOS", targets: ["ArosPOS"])
    ],
    targets: [
        .target(
            name: "ArosPOS",
            path: "Sources/ArosPOS"
        )
    ]
)
