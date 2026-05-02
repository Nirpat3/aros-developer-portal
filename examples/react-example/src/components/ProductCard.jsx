export default function ProductCard({ product, onView, onAddToCart }) {
  return (
    <div className="product">
      <h4>{product.name}</h4>
      <p style={{color: '#666', margin: '5px 0'}}>
        ${product.price.toFixed(2)}
      </p>
      <button onClick={() => onView(product)} style={{fontSize: '12px'}}>
        View
      </button>
      <button onClick={() => onAddToCart(product)} style={{fontSize: '12px'}}>
        Add to Cart
      </button>
    </div>
  )
}
