# Shre SDK Android/Kotlin Example

Working Android application with Jetpack Compose demonstrating Shre SDK integration for mobile event tracking.

## Features

- **Jetpack Compose UI**: Modern Material 3 design
- **Product Catalog**: Browse and track product views
- **Shopping Cart**: Add items and track checkout
- **Event Log**: Real-time display of all tracked events
- **Coroutines**: Async SDK operations
- **ViewModel**: Clean architecture with state management

## Running

### Prerequisites
- Android Studio 2023.2+
- Android SDK 24+ (target 34)
- Kotlin 1.9.22+

### Build & Run
```bash
cd aros-developer-portal/examples/android-example
./gradlew build
./gradlew installDebug emulatorDebug
# Or open in Android Studio and click Run
```

## App Structure

### Tabs
1. **Products** — Browse catalog, track views
2. **Cart** — View items, checkout
3. **Events** — Real-time event log

### Events Tracked
- `product_view` — When user views a product
- `cart_add` — When item added to cart
- `purchase` — When checkout completed

## Integration Points

### ViewModel with SDK
```kotlin
class EventViewModel(application: Application) : AndroidViewModel(application) {
    private val sdk = ShreSDK("dev-tenant-001")

    fun trackProductView(productId: String) {
        viewModelScope.launch {
            sdk.sendEventsBatch(listOf(event),
                onSuccess = { response -> /* handle success */ },
                onError = { error -> /* handle error */ }
            )
        }
    }
}
```

### Compose Integration
```kotlin
@Composable
fun ProductCard(product: Product, onAction: (Product, String) -> Unit) {
    Button(onClick = { onAction(product, "view") }) {
        Text("View")
    }
}
```

## Production Checklist

- [ ] Change tenant_id to your workspace ID
- [ ] Use HTTPS URLs for production
- [ ] Implement proper error handling
- [ ] Add database persistence for cart
- [ ] Set up analytics dashboard
- [ ] Configure Firebase Integration
- [ ] Deploy to Google Play Store
