export default function ShoppingCart({ items, onCheckout }) {
  const total = items.reduce((sum, item) => sum + item.price, 0)

  return (
    <div className="card">
      <h2>Shopping Cart</h2>
      {items.length === 0 ? (
        <p style={{color: '#999'}}>Cart is empty</p>
      ) : (
        <>
          <div style={{marginBottom: '10px'}}>
            {items.map((item, idx) => (
              <div key={idx} style={{display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #eee'}}>
                <span>{item.name}</span>
                <span>${item.price.toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div style={{fontSize: '18px', fontWeight: 'bold', marginBottom: '10px'}}>
            Total: ${total.toFixed(2)}
          </div>
          <button onClick={onCheckout} style={{width: '100%', padding: '12px', fontSize: '14px'}}>
            Checkout ({items.length} items)
          </button>
        </>
      )}
    </div>
  )
}
