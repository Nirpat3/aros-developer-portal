package com.shreai.sdk.example

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class EventViewModel(application: Application) : AndroidViewModel(application) {
    private val sdk = ShreSDK("dev-tenant-001")

    private val _events = MutableStateFlow<List<EventRecord>>(emptyList())
    val events: StateFlow<List<EventRecord>> = _events

    private val _cartItems = MutableStateFlow<List<Product>>(emptyList())
    val cartItems: StateFlow<List<Product>> = _cartItems

    fun trackProductView(productId: String) {
        viewModelScope.launch {
            val event = mapOf(
                "eventId" to UUID.randomUUID().toString(),
                "eventName" to "product_view",
                "entityType" to "product",
                "entityId" to productId,
                "timestamp" to getCurrentTimestamp(),
            )

            sdk.sendEventsBatch(listOf(event),
                onSuccess = { response ->
                    addEventRecord("product_view", "sent")
                },
                onError = { error ->
                    addEventRecord("product_view", "error: ${error.message}")
                }
            )
        }
    }

    fun addToCart(product: Product) {
        viewModelScope.launch {
            _cartItems.value = _cartItems.value + product

            val event = mapOf(
                "eventId" to UUID.randomUUID().toString(),
                "eventName" to "cart_add",
                "entityType" to "product",
                "entityId" to product.id,
                "metadata" to mapOf(
                    "name" to product.name,
                    "price" to product.price,
                ),
                "timestamp" to getCurrentTimestamp(),
            )

            sdk.sendEventsBatch(listOf(event),
                onSuccess = { response ->
                    addEventRecord("cart_add", "sent")
                },
                onError = { error ->
                    addEventRecord("cart_add", "error: ${error.message}")
                }
            )
        }
    }

    fun checkout() {
        viewModelScope.launch {
            val items = _cartItems.value
            if (items.isEmpty()) return@launch

            val total = items.sumOf { it.price }
            val event = mapOf(
                "eventId" to UUID.randomUUID().toString(),
                "eventName" to "purchase",
                "entityType" to "order",
                "entityId" to UUID.randomUUID().toString(),
                "metadata" to mapOf(
                    "items" to items.size,
                    "total" to total,
                    "products" to items.map { it.id },
                ),
                "timestamp" to getCurrentTimestamp(),
            )

            sdk.sendEventsBatch(listOf(event),
                onSuccess = { response ->
                    addEventRecord("purchase", "sent")
                    _cartItems.value = emptyList()
                },
                onError = { error ->
                    addEventRecord("purchase", "error: ${error.message}")
                }
            )
        }
    }

    private fun addEventRecord(eventName: String, status: String) {
        val record = EventRecord(
            eventName = eventName,
            timestamp = getCurrentTimestamp(),
            status = status
        )
        _events.value = listOf(record) + _events.value
    }

    private fun getCurrentTimestamp(): String {
        val format = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
        return format.format(Date())
    }
}
