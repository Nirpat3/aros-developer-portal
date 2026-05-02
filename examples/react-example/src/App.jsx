import { useState, useEffect, useRef } from 'react'
import { ShreSDK } from '../lib/ShreSDK'
import ProductCard from './components/ProductCard'
import ShoppingCart from './components/ShoppingCart'
import EventLog from './components/EventLog'

export default function App() {
  const [events, setEvents] = useState([])
  const [cart, setCart] = useState([])
  const [status, setStatus] = useState('Initializing...')
  const sdkRef = useRef(null)

  // Product catalog
  const products = [
    { id: '1', name: 'Laptop', price: 999, category: 'electronics' },
    { id: '2', name: 'Mouse', price: 29, category: 'electronics' },
    { id: '3', name: 'Keyboard', price: 79, category: 'electronics' },
    { id: '4', name: 'Monitor', price: 299, category: 'electronics' },
    { id: '5', name: 'Headphones', price: 149, category: 'electronics' },
    { id: '6', name: 'USB Cable', price: 9, category: 'accessories' },
  ]

  // Initialize SDK
  useEffect(() => {
    const initSDK = async () => {
      try {
        const sdk = new ShreSDK('dev-tenant-001')
        sdkRef.current = sdk

        // Send initial pageview event
        await trackEvent({
          eventId: crypto.randomUUID(),
          eventName: 'pageview',
          entityType: 'page',
          entityId: 'product_catalog',
          timestamp: new Date().toISOString(),
        })

        setStatus('SDK initialized — Ready to track events')
      } catch (error) {
        setStatus(`Init error: ${error.message}`)
      }
    }

    initSDK()
  }, [])

  const trackEvent = async (event) => {
    if (!sdkRef.current) return

    try {
      const response = await sdkRef.current.sendEventsBatch([event])
      setEvents(prev => [{...event, status: 'sent'}, ...prev])
      return response
    } catch (error) {
      setEvents(prev => [{...event, status: `error: ${error.message}`}, ...prev])
      throw error
    }
  }

  const handleProductView = async (product) => {
    await trackEvent({
      eventId: crypto.randomUUID(),
      eventName: 'product_view',
      entityType: 'product',
      entityId: product.id,
      metadata: { name: product.name, price: product.price },
      timestamp: new Date().toISOString(),
    })
  }

  const handleAddToCart = async (product) => {
    setCart(prev => [...prev, product])
    await trackEvent({
      eventId: crypto.randomUUID(),
      eventName: 'cart_add',
      entityType: 'product',
      entityId: product.id,
      metadata: { name: product.name, price: product.price, cartSize: cart.length + 1 },
      timestamp: new Date().toISOString(),
    })
  }

  const handleCheckout = async () => {
    if (cart.length === 0) return

    const total = cart.reduce((sum, p) => sum + p.price, 0)
    await trackEvent({
      eventId: crypto.randomUUID(),
      eventName: 'purchase',
      entityType: 'order',
      entityId: `order-${Date.now()}`,
      metadata: {
        items: cart.length,
        total,
        products: cart.map(p => p.id),
      },
      timestamp: new Date().toISOString(),
    })
    setCart([])
  }

  return (
    <div>
      <div className="header">
        <h1>Shre SDK React Example</h1>
        <p>Real-time event tracking demo with product catalog</p>
        <p style={{color: '#666', fontSize: '14px'}}>Status: {status}</p>
      </div>

      <div className="grid">
        <div>
          <div className="card">
            <h2>Product Catalog</h2>
            <div className="product-grid">
              {products.map(product => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onView={handleProductView}
                  onAddToCart={handleAddToCart}
                />
              ))}
            </div>
          </div>
        </div>

        <div>
          <ShoppingCart
            items={cart}
            onCheckout={handleCheckout}
          />
        </div>
      </div>

      <div className="card" style={{marginTop: '20px'}}>
        <h2>Event Log</h2>
        <EventLog events={events} />
      </div>
    </div>
  )
}
