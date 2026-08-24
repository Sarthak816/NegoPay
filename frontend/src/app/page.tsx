'use client';
import { useState, useRef } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [negotiationResult, setNegotiationResult] = useState<any>(null);
  const [negotiating, setNegotiating] = useState(false);
  const [budgetMessage, setBudgetMessage] = useState('');
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);
  
  const gridRef = useRef<HTMLDivElement>(null);

  const searchProducts = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/products/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_price: null, category: null })
      });
      const data = await res.json();
      setProducts(data.results || []);
      
      setTimeout(() => {
        gridRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
      
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handlePayment = () => {
    if (!negotiationResult?.purchase_result?.order_id) return;
    
    if (!(window as any).Razorpay) {
        alert("Razorpay SDK failed to load. Please check your connection or refresh the page.");
        return;
    }

    const options = {
        key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_TSiPLxrVngFkoT",
        amount: Math.round(negotiationResult.final_price * 100),
        currency: "INR",
        name: "NegoPay",
        description: "Agentic Commerce Purchase",
        order_id: negotiationResult.purchase_result.order_id,
        handler: function (response: any) {
            setPaymentStatus("PAID");
            alert(`Payment successful! Payment ID: ${response.razorpay_payment_id}`);
        },
        prefill: {
            name: "Test User",
            email: "test@example.com",
            contact: "9999999999"
        },
        theme: {
            color: "#2563eb"
        }
    };
    
    const rzp = new (window as any).Razorpay(options);
    rzp.on('payment.failed', function (response: any) {
        alert(`Payment failed: ${response.error.description}`);
    });
    rzp.open();
  };

  const startNegotiation = async () => {
    if (!selectedProduct) return;
    setNegotiating(true);
    setNegotiationResult(null);
    setPaymentStatus(null);
    try {
      const res = await fetch('http://localhost:8000/api/negotiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner_id: 'user_123',
          product_id: selectedProduct.id,
          initial_message: budgetMessage || `I want to buy ${selectedProduct.name}. Can you give me a good deal?`
        })
      });
      const data = await res.json();
      setNegotiationResult(data.result);
    } catch (e) {
      console.error(e);
    }
    setNegotiating(false);
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-blue-600">NegoPay</h1>
            <p className="text-gray-500 mt-1">Agent-to-Agent Commerce via Razorpay</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow-sm border text-sm">
            <span className="font-semibold">User:</span> user_123 <br/>
            <span className="font-semibold text-green-600">Mandate:</span> Active (Max ₹2000)
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex gap-2">
          <input 
            type="text"
            className="flex-1 p-3 border rounded-lg shadow-sm"
            placeholder="Search for products (e.g., earbuds, books)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchProducts()}
          />
          <button 
            onClick={searchProducts}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Main Content Area */}
        <div ref={gridRef} className="grid grid-cols-1 lg:grid-cols-3 gap-8 scroll-mt-8">
          
          {/* Products List */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold border-b pb-2">Marketplace</h2>
            {products.length === 0 && !loading && (
              <p className="text-gray-400">Search for products to see results...</p>
            )}
            {products.map((p: any) => (
              <div 
                key={p.id} 
                className={`p-4 rounded-xl border bg-white cursor-pointer transition ${selectedProduct?.id === p.id ? 'border-blue-500 ring-1 ring-blue-500 shadow-md' : 'hover:shadow-md'}`}
                onClick={() => { setSelectedProduct(p); setNegotiationResult(null); }}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-lg">{p.name}</h3>
                    <p className="text-sm text-gray-500">Merchant: {p.merchant_id} | Stock: {p.stock}</p>
                  </div>
                  <span className="text-lg font-bold text-green-600">₹{p.price}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Negotiation Panel */}
          <div className="bg-white border rounded-xl shadow-sm p-6 flex flex-col h-[600px]">
            <h2 className="text-xl font-semibold border-b pb-2 mb-4 shrink-0">Agent Negotiation</h2>
            
            {!selectedProduct ? (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                Select a product to start your AI buyer agent.
              </div>
            ) : (
              <div className="flex-1 flex flex-col min-h-0">
                {/* Product target info */}
                <div className="bg-blue-50 text-blue-800 p-3 rounded-lg text-sm mb-4 shrink-0">
                  <strong>Target:</strong> {selectedProduct.name} (List: ₹{selectedProduct.price})
                </div>

                {/* Chat Log */}
                <div className="flex-1 overflow-y-auto border rounded-lg bg-gray-50 p-4 space-y-4 mb-4">
                  {!negotiationResult && !negotiating && (
                    <p className="text-gray-400 text-center mt-10">Set your budget and click Negotiate. Your buyer agent will handle the rest.</p>
                  )}
                  {negotiating && (
                    <div className="animate-pulse flex items-center justify-center h-full text-blue-500 font-medium">
                      Agents are negotiating in the background...
                    </div>
                  )}
                  {negotiationResult?.transcript?.map((turn: any, i: number) => (
                    <div key={i} className={`flex flex-col ${turn.sender === 'BUYER' ? 'items-end' : 'items-start'}`}>
                      <span className="text-xs font-bold text-gray-500 mb-1">{turn.sender === 'BUYER' ? 'Your Buyer Agent' : 'Merchant Agent'}</span>
                      <div className={`max-w-[80%] p-3 rounded-2xl break-words whitespace-pre-wrap ${turn.sender === 'BUYER' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-gray-200 text-gray-800 rounded-tl-none'}`}>
                        {turn.action && <div className="text-xs font-bold opacity-70 mb-1">[{turn.action}] {turn.price ? `₹${turn.price}` : ''}</div>}
                        {turn.message}
                      </div>
                    </div>
                  ))}
                  
                  {/* Final Status */}
                  {negotiationResult && (
                    <div className={`mt-4 p-4 rounded-lg text-center font-bold border shrink-0 
                      ${negotiationResult.status === 'ACCEPTED' ? 'bg-green-100 text-green-800 border-green-300' : 
                        negotiationResult.status === 'REQUIRES_APPROVAL' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : 
                        'bg-red-100 text-red-800 border-red-300'}`}>
                      
                      {negotiationResult.status === 'REQUIRES_APPROVAL' 
                        ? `SYSTEM PENDING: Human approval required for ₹${negotiationResult.final_price}` 
                        : `RESULT: ${negotiationResult.status}`}

                      {negotiationResult.status === 'ACCEPTED' && negotiationResult.final_price && (
                        <div>Final Price: ₹{negotiationResult.final_price}</div>
                      )}
                      
                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status === 'success' && (
                        <div className="mt-2 text-sm bg-white/50 p-3 rounded text-left break-words">
                          <p><strong>Razorpay Order:</strong> {negotiationResult.purchase_result.order_id}</p>
                          <p><strong>Payment Status:</strong> {paymentStatus === 'PAID' ? '✅ PAID' : '⏳ PENDING CHECKOUT'}</p>
                          
                          {paymentStatus !== 'PAID' && (
                            <button 
                              onClick={handlePayment}
                              className="mt-3 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow-md transition"
                            >
                              Pay Now (₹{negotiationResult.final_price})
                            </button>
                          )}
                        </div>
                      )}

                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status !== 'success' && (
                        <div className="mt-2 text-sm bg-white/50 p-2 rounded text-left break-words text-red-700">
                          <p><strong>Blocked Reason:</strong> {negotiationResult.purchase_result.reason}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Control Panel */}
                <div className="flex gap-2 shrink-0 mt-auto w-full">
                  <input
                    type="text"
                    className="flex-1 min-w-0 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="E.g., I won't pay more than ₹1000..."
                    value={budgetMessage}
                    onChange={(e) => setBudgetMessage(e.target.value)}
                    disabled={negotiating}
                  />
                  <button
                    onClick={startNegotiation}
                    disabled={negotiating}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium whitespace-nowrap"
                  >
                    Deploy Agent
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Audit Trail / Mission Control */}
          <div className="bg-gray-900 border-gray-800 border rounded-xl shadow-sm p-6 flex flex-col h-[600px] font-mono text-green-400">
            <h2 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-4 text-white">Mission Control (Audit Log)</h2>
            <div className="flex-1 overflow-y-auto space-y-2 text-sm">
              {!negotiationResult && !negotiating && (
                <p className="text-gray-500">Waiting for agent deployment...</p>
              )}
              {negotiating && (
                <p className="animate-pulse text-blue-400">[SYSTEM] Agent negotiation protocol initiated...</p>
              )}
              {negotiationResult?.audit_trail?.map((log: any, i: number) => (
                <div key={i} className={`p-2 rounded border border-gray-800 ${log.type === 'FAILURE' ? 'bg-red-900/20 text-red-400' : log.type === 'SUCCESS' ? 'bg-green-900/20 text-green-400' : 'bg-gray-800/50'}`}>
                  <span className="opacity-50 text-xs mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {log.detail}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
