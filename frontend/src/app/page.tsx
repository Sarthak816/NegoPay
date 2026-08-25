'use client';
import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [negotiationResult, setNegotiationResult] = useState<any>(null);
  const [negotiating, setNegotiating] = useState(false);
  const [budgetMessage, setBudgetMessage] = useState('');
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);
  
  const [mandate, setMandate] = useState<any>(null);
  const [showSettings, setShowSettings] = useState(false);
  
  const gridRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const auditEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/mandate/user_123')
      .then(res => res.json())
      .then(data => setMandate(data))
      .catch(err => console.error("Failed to load mandate", err));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [negotiationResult?.transcript, negotiating]);

  useEffect(() => {
    auditEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [negotiationResult?.audit_trail, negotiating]);

  const saveMandate = async () => {
    try {
      await fetch('http://localhost:8000/api/mandate/user_123', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_per_transaction: mandate.max_per_transaction,
          require_approval_above: mandate.require_approval_above
        })
      });
      alert('Mandate Updated Successfully!');
      setShowSettings(false);
    } catch (e) {
      console.error(e);
      alert('Failed to update mandate');
    }
  };

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
    setNegotiationResult({
      status: 'NEGOTIATING',
      transcript: [],
      audit_trail: []
    });
    setPaymentStatus(null);
    
    const ws = new WebSocket('ws://localhost:8000/ws/negotiate');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        owner_id: 'user_123',
        product_id: selectedProduct.id,
        initial_message: budgetMessage || `I want to buy ${selectedProduct.name}. Can you give me a good deal?`
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        setNegotiationResult((prev: any) => {
          const next = { ...prev };
          if (!next.audit_trail) next.audit_trail = [];
          if (!next.transcript) next.transcript = [];
          
          if (data.type === 'audit') {
            next.audit_trail = [...next.audit_trail, data.log];
          } else if (data.type === 'chat') {
            next.transcript = [...next.transcript, data.turn];
          } else if (data.type === 'status') {
            next.status = data.status;
            next.final_price = data.final_price;
            next.purchase_result = data.purchase_result;
          }
          return next;
        });
      } catch (e) {
        console.error("Error parsing WS message", e);
      }
    };
    
    ws.onclose = () => {
      setNegotiating(false);
    };
    
    ws.onerror = (e) => {
      console.error('WebSocket Error:', e);
      setNegotiating(false);
    };
  };

  return (
    <main className="min-h-screen bg-[#F4F6F8] text-[#1D2329] pb-12 font-sans">
      {/* Header */}
      <header className="bg-[#02042B] text-white p-4 shadow-md sticky top-0 z-10 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            NegoPay
            <span className="text-xs bg-[#3366FF] px-2 py-0.5 rounded-full font-medium">TEST</span>
          </h1>
          <p className="text-sm opacity-80 font-medium mt-0.5">Agentic Commerce Gateway (Powered by Razorpay AI)</p>
        </div>
        
        {/* Mandate Settings Toggle */}
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition"
        >
          ⚙️ Mandate Settings
        </button>
      </header>

      {/* Mandate Settings Panel */}
      {showSettings && (
        <div className="bg-white border-b shadow-sm p-6 mb-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-xl font-bold mb-4">Human Control Mandate</h2>
            <p className="text-sm text-gray-500 mb-6">Define the financial boundaries for your AI Buyer Agent. The agent cannot bypass these rules.</p>
            
            {mandate ? (
              <div className="space-y-6">
                <div>
                  <label className="block font-bold mb-2">Max Budget per Transaction (₹)</label>
                  <input 
                    type="range" 
                    min="100" max="10000" step="100"
                    value={mandate.max_per_transaction}
                    onChange={(e) => setMandate({...mandate, max_per_transaction: parseFloat(e.target.value)})}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#3366FF]"
                  />
                  <div className="text-right font-mono font-bold mt-1 text-[#3366FF]">₹{mandate.max_per_transaction}</div>
                </div>
                
                <div>
                  <label className="block font-bold mb-2">Auto-Approve Limit (₹)</label>
                  <input 
                    type="range" 
                    min="100" max="10000" step="100"
                    value={mandate.require_approval_above}
                    onChange={(e) => setMandate({...mandate, require_approval_above: parseFloat(e.target.value)})}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#3366FF]"
                  />
                  <div className="text-right font-mono font-bold mt-1 text-[#3366FF]">₹{mandate.require_approval_above}</div>
                </div>
                
                <button 
                  onClick={saveMandate}
                  className="bg-[#02042B] text-white px-6 py-2 rounded-lg font-bold hover:bg-[#13192F] transition"
                >
                  Save Mandate
                </button>
              </div>
            ) : (
              <p>Loading mandate...</p>
            )}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto p-4 mt-6 space-y-6">
        
        {/* Search */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex gap-4">
          <input 
            type="text" 
            placeholder="Search products to buy (e.g., 'earbuds')..." 
            className="flex-1 p-3 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-[#3366FF] transition"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchProducts()}
          />
          <button 
            onClick={searchProducts}
            disabled={loading}
            className="bg-[#3366FF] hover:bg-[#2b52cc] text-white px-8 py-3 rounded-lg font-bold transition disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Main Content Area */}
        <div ref={gridRef} className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[600px]">
          {/* Marketplace Column */}
          <div className="bg-white border-gray-200 border rounded-xl shadow-sm p-6 flex flex-col h-[600px]">
            <h2 className="text-xl font-bold border-b border-gray-100 pb-2 mb-4">Marketplace</h2>
            <div className="flex-1 overflow-y-auto space-y-3">
              {products.length === 0 && !loading && (
                <p className="text-gray-500 text-sm">Search to see available products.</p>
              )}
              {products.map((p: any) => (
                <div 
                  key={p.id} 
                  className={`p-4 rounded-xl border bg-white cursor-pointer transition ${selectedProduct?.id === p.id ? 'border-[#3366FF] ring-1 ring-[#3366FF] shadow-md' : 'hover:shadow-md'}`}
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
          </div>

          {/* Negotiation Column */}
          <div className="bg-white border-gray-200 border rounded-xl shadow-sm p-6 flex flex-col h-[600px]">
            <h2 className="text-xl font-bold border-b border-gray-100 pb-2 mb-4">Agent Negotiation</h2>
            
            {!selectedProduct ? (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                Select a product to start your AI buyer agent.
              </div>
            ) : (
              <div className="flex-1 flex flex-col min-h-0">
                {/* Product target info */}
                <div className="bg-[#f0f4ff] border border-[#d6e4ff] text-[#02042B] p-3 rounded-lg text-sm mb-4 shrink-0">
                  <strong>Target:</strong> {selectedProduct.name} (List: ₹{selectedProduct.price})
                </div>

                {/* Chat Log */}
                <div className="flex-1 overflow-y-auto border rounded-lg bg-gray-50 p-4 space-y-4 mb-4">
                  {!negotiationResult && !negotiating && (
                    <p className="text-gray-400 text-center mt-10">Set your budget and click Negotiate. Your buyer agent will handle the rest.</p>
                  )}
                  
                  {negotiationResult?.transcript?.map((turn: any, i: number) => (
                    <div key={i} className={`flex flex-col ${turn.sender === 'BUYER' ? 'items-end' : 'items-start'}`}>
                      <span className="text-xs font-bold text-gray-500 mb-1">{turn.sender === 'BUYER' ? 'Your Buyer Agent' : 'Merchant Agent'}</span>
                      <div className={`max-w-[80%] p-3 rounded-2xl break-words whitespace-pre-wrap ${turn.sender === 'BUYER' ? 'bg-[#3366FF] text-white rounded-tr-none shadow-sm' : 'bg-white border border-gray-200 text-[#1D2329] rounded-tl-none shadow-sm'}`}>
                        {turn.action && <div className="text-xs font-bold opacity-70 mb-1">[{turn.action}] {turn.price ? `₹${turn.price}` : ''}</div>}
                        {turn.message}
                      </div>
                    </div>
                  ))}

                  {/* Agent Processing Indicator */}
                  {negotiating && (
                    <div className={`flex flex-col ${(!negotiationResult?.transcript?.length || negotiationResult.transcript[negotiationResult.transcript.length - 1].sender === 'SELLER') ? 'items-end' : 'items-start'} mt-4`}>
                      {(!negotiationResult?.transcript?.length || negotiationResult.transcript[negotiationResult.transcript.length - 1].sender === 'SELLER') ? (
                        <div className="bg-[#f0f4ff] border border-[#d6e4ff] text-[#3366FF] px-4 py-2 rounded-lg text-xs font-mono animate-pulse flex items-center gap-2 shadow-sm">
                          <span className="w-2 h-2 rounded-full bg-[#3366FF] animate-ping"></span>
                          [ BUYER_AGENT: COMPUTING OPTIMAL BID... ]
                        </div>
                      ) : (
                        <div className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-xs font-mono animate-pulse flex items-center gap-2 shadow-sm">
                          <span className="w-2 h-2 rounded-full bg-gray-500 animate-ping"></span>
                          [ SELLER_AGENT: ANALYZING MARGIN GUARDS... ]
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Final Status */}
                  {negotiationResult && negotiationResult.status !== 'NEGOTIATING' && (
                    <div className={`mt-4 p-4 rounded-lg text-center font-bold border shrink-0 
                      ${negotiationResult.status === 'ACCEPTED' ? 'bg-[#E6F4EA] text-[#137333] border-[#ceead6]' : 
                        negotiationResult.status === 'REQUIRES_APPROVAL' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : 
                        'bg-red-100 text-red-800 border-red-300'}`}>
                      
                      {negotiationResult.status === 'REQUIRES_APPROVAL' 
                        ? `SYSTEM PENDING: Human approval required for ₹${negotiationResult.final_price}` 
                        : `RESULT: ${negotiationResult.status}`}

                      {negotiationResult.status === 'ACCEPTED' && negotiationResult.final_price && (
                        <div>Final Price: ₹{negotiationResult.final_price}</div>
                      )}
                      
                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status === 'success' && (
                        <div className="mt-2 text-sm bg-white/80 p-3 rounded text-left break-words">
                          <p><strong>Razorpay Order:</strong> {negotiationResult.purchase_result.order_id}</p>
                          <p><strong>Payment Status:</strong> {paymentStatus === 'PAID' ? '✅ PAID' : '⏳ PENDING CHECKOUT'}</p>
                          
                          {paymentStatus !== 'PAID' && (
                            <button 
                              onClick={handlePayment}
                              className="mt-3 w-full py-2 bg-[#02042B] text-white rounded-lg hover:bg-[#13192F] font-bold shadow-md transition"
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
                  
                  {/* Invisible element to scroll to */}
                  <div ref={chatEndRef} />
                </div>

                {/* Control Panel */}
                <div className="flex gap-2 shrink-0 mt-auto w-full">
                  <input
                    type="text"
                    className="flex-1 min-w-0 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#3366FF]"
                    placeholder="E.g., I won't pay more than ₹1000..."
                    value={budgetMessage}
                    onChange={(e) => setBudgetMessage(e.target.value)}
                    disabled={negotiating}
                  />
                  <button
                    onClick={startNegotiation}
                    disabled={negotiating}
                    className="px-4 py-2 bg-[#3366FF] text-white rounded-lg hover:bg-[#2b52cc] disabled:opacity-50 font-medium whitespace-nowrap"
                  >
                    Deploy Agent
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Audit Trail / Mission Control */}
          <div className="bg-[#02042B] border-[#13192F] border rounded-xl shadow-sm p-6 flex flex-col h-[600px] font-mono text-[#A0AEC0]">
            <h2 className="text-xl font-semibold border-b border-[#13192F] pb-2 mb-4 text-white">Mission Control (Audit Log)</h2>
            <div className="flex-1 overflow-y-auto space-y-2 text-sm">
              {!negotiationResult && !negotiating && (
                <p className="text-[#A0AEC0]/70">Waiting for agent deployment...</p>
              )}
              {negotiating && (!negotiationResult?.audit_trail || negotiationResult.audit_trail.length === 0) && (
                <p className="animate-pulse text-[#3366FF]">[SYSTEM] Agent negotiation protocol initiated...</p>
              )}
              {negotiationResult?.audit_trail?.map((log: any, i: number) => (
                <div key={i} className={`p-2 rounded border border-[#13192F] ${log.type === 'FAILURE' ? 'bg-red-900/20 text-red-400' : log.type === 'SUCCESS' ? 'bg-[#E6F4EA]/10 text-[#2db555]' : 'bg-[#13192F]/50 text-white'}`}>
                  <span className="opacity-50 text-xs mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {log.detail}
                </div>
              ))}
              <div ref={auditEndRef} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
