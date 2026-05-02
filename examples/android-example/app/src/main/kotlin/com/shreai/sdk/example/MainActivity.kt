package com.shreai.sdk.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            ShreSDKExample()
        }
    }
}

@Composable
fun ShreSDKExample(viewModel: EventViewModel = viewModel()) {
    var selectedTab by remember { mutableStateOf(0) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5))
    ) {
        // Header
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Shre SDK Android Example", fontSize = 24.sp)
                Text("Real-time event tracking with Jetpack Compose", fontSize = 14.sp, color = Color.Gray)
            }
        }

        // Tab buttons
        Row(modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp)
        ) {
            Button(
                onClick = { selectedTab = 0 },
                modifier = Modifier
                    .weight(1f)
                    .padding(4.dp)
            ) {
                Text("Products")
            }
            Button(
                onClick = { selectedTab = 1 },
                modifier = Modifier
                    .weight(1f)
                    .padding(4.dp)
            ) {
                Text("Cart")
            }
            Button(
                onClick = { selectedTab = 2 },
                modifier = Modifier
                    .weight(1f)
                    .padding(4.dp)
            ) {
                Text("Events")
            }
        }

        // Content
        when (selectedTab) {
            0 -> ProductsTab(viewModel)
            1 -> CartTab(viewModel)
            2 -> EventsTab(viewModel)
        }
    }
}

@Composable
fun ProductsTab(viewModel: EventViewModel) {
    val products = listOf(
        Product("1", "Laptop", 999.0, "electronics"),
        Product("2", "Mouse", 29.0, "electronics"),
        Product("3", "Keyboard", 79.0, "electronics"),
        Product("4", "Monitor", 299.0, "electronics"),
        Product("5", "Headphones", 149.0, "electronics"),
        Product("6", "USB Cable", 9.0, "accessories"),
    )

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(products) { product ->
            ProductCard(product) { p, action ->
                when (action) {
                    "view" -> viewModel.trackProductView(p.id)
                    "cart" -> viewModel.addToCart(p)
                }
            }
        }
    }
}

@Composable
fun ProductCard(product: Product, onAction: (Product, String) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(product.name, fontSize = 16.sp)
            Text("$${product.price}", fontSize = 14.sp, color = Color.Gray)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(onClick = { onAction(product, "view") }) {
                    Text("View")
                }
                Button(onClick = { onAction(product, "cart") }) {
                    Text("Add to Cart")
                }
            }
        }
    }
}

@Composable
fun CartTab(viewModel: EventViewModel) {
    val cartItems by viewModel.cartItems.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp)
    ) {
        if (cartItems.isEmpty()) {
            Text("Cart is empty", color = Color.Gray, modifier = Modifier.padding(16.dp))
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(cartItems) { item ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(item.name)
                            Text("$${item.price}")
                        }
                    }
                }
            }

            val total = cartItems.sumOf { it.price }
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("Total: $$${String.format("%.2f", total)}", fontSize = 18.sp)
                    Button(
                        onClick = { viewModel.checkout() },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp)
                    ) {
                        Text("Checkout (${cartItems.size} items)")
                    }
                }
            }
        }
    }
}

@Composable
fun EventsTab(viewModel: EventViewModel) {
    val events by viewModel.events.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        if (events.isEmpty()) {
            item {
                Text("No events yet", color = Color.Gray)
            }
        } else {
            items(events) { event ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    containerColor = Color(0xFFF9F9F9)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(event.eventName, fontSize = 14.sp)
                        Text(event.timestamp, fontSize = 12.sp, color = Color.Gray)
                        Text(event.status, fontSize = 12.sp, color = if (event.status == "sent") Color.Green else Color.Red)
                    }
                }
            }
        }
    }
}

data class Product(val id: String, val name: String, val price: Double, val category: String)
data class EventRecord(val eventName: String, val timestamp: String, val status: String)
