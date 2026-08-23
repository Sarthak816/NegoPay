'use client';
import { useState } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [negotiationResult, setNegotiationResult] = useState<any>(null);
  const [negotiating, setNegotiating] = useState(false);
  const [budgetMessage, setBudgetMessage] = useState('');

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
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const startNegotiation = async () => {
    if (!selectedProduct) return;
    setNegotiating(true);
    setNegotiationResult(null);
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
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
            <h2 className="text-xl font-semibold border-b pb-2 mb-4">Agent Negotiation</h2>
            
            {!selectedProduct ? (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                Select a product to start your AI buyer agent.
              </div>
            ) : (
              <div className="flex flex-col h-full">
                {/* Product target info */}
                <div className="bg-blue-50 text-blue-800 p-3 rounded-lg text-sm mb-4">
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
                      <div className={`max-w-[80%] p-3 rounded-2xl ${turn.sender === 'BUYER' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-gray-200 text-gray-800 rounded-tl-none'}`}>
                        {turn.action && <div className="text-xs font-bold opacity-70 mb-1">[{turn.action}] {turn.price ? `₹${turn.price}` : ''}</div>}
                        {turn.message}
                      </div>
                    </div>
                  ))}
                  
                  {/* Final Status */}
                  {negotiationResult && (
                    <div className={`mt-4 p-4 rounded-lg text-center font-bold border ${negotiationResult.status === 'ACCEPTED' ? 'bg-green-100 text-green-800 border-green-300' : 'bg-red-100 text-red-800 border-red-300'}`}>
                      RESULT: {negotiationResult.status}
                      {negotiationResult.final_price && <div>Final Price: ₹{negotiationResult.final_price}</div>}
                      {negotiationResult.purchase_result && (
                        <div className="mt-2 text-sm bg-white/50 p-2 rounded text-left">
                          <p><strong>Razorpay Order:</strong> {negotiationResult.purchase_result.order_id}</p>
                          <p><strong>Payment Status:</strong> {negotiationResult.purchase_result.status}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Control Panel */}
                <div className="flex gap-2 mt-auto">
                  <input
                    type="text"
                    className="flex-1 p-2 border rounded-lg text-sm"
                    placeholder="E.g., I won't pay more than ₹1000..."
                    value={budgetMessage}
                    onChange={(e) => setBudgetMessage(e.target.value)}
                    disabled={negotiating}
                  />
                  <button
                    onClick={startNegotiation}
                    disabled={negotiating}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
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
