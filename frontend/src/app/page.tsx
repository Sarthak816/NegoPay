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
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/mandate/user_123`)
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
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/mandate/user_123`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_per_transaction: mandate.max_per_transaction,
          max_daily_spend: mandate.max_daily_spend,
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/products/search`, {
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

  // Agentic Auto-Pay Trigger (Hybrid Approach)
  useEffect(() => {
    if (negotiationResult?.purchase_result?.status === 'success' && paymentStatus !== 'PAID') {
      // Small delay for dramatic effect before AI automatically steals the screen
      const timer = setTimeout(() => {
        handlePayment();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [negotiationResult?.purchase_result?.status]);

  const startNegotiation = async () => {
    if (!selectedProduct) return;
    setNegotiating(true);
    setNegotiationResult({
      status: 'NEGOTIATING',
      transcript: [],
      audit_trail: []
    });
    setPaymentStatus(null);
    
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/negotiate';
    const ws = new WebSocket(wsUrl);
    
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
    <main className="min-h-screen bg-zinc-50 text-zinc-900 pb-12 font-sans selection:bg-zinc-200 antialiased">
      {/* Impeccable Header */}
      <header className="sticky top-0 z-40 bg-white/70 backdrop-blur-xl border-b border-zinc-200/50 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="NegoPay Logo" className="w-8 h-8 object-contain invert drop-shadow-sm" />
          <div>
            <h1 className="text-2xl italic font-bold tracking-tight text-zinc-900 leading-none">NegoPay</h1>
            <p className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase mt-0.5">Agentic Commerce Gateway</p>
          </div>
        </div>
        
        <div className="relative">
          {/* Mandate Settings Toggle */}
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 shadow-sm text-zinc-700 text-sm font-semibold px-4 py-2 rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-zinc-900/10"
          >
            ⚙️ Mandate Limits
          </button>

          {/* Mandate Settings Panel Popup */}
          {showSettings && (
            <div className="absolute right-0 top-full mt-3 w-[380px] bg-white/95 backdrop-blur-2xl border border-zinc-200/60 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] p-6 text-zinc-900 z-50 transform transition-all">
              <div className="flex justify-between items-center mb-1">
                <h2 className="text-lg font-bold tracking-tight">Human Control Mandate</h2>
                <button onClick={() => setShowSettings(false)} className="text-zinc-400 hover:text-zinc-900 transition-colors focus:outline-none">✖</button>
              </div>
              <p className="text-xs text-zinc-500 mb-6 leading-relaxed">Define the financial boundaries for your AI Buyer Agent. The agent cannot bypass these rules.</p>
              
              {mandate ? (
                <div className="space-y-6">
                  {[
                    { label: 'Max Budget per Transaction', key: 'max_per_transaction' },
                    { label: 'Max Daily Spend', key: 'max_daily_spend' },
                    { label: 'Auto-Approve Limit', key: 'require_approval_above' }
                  ].map((field) => (
                    <div key={field.key}>
                      <label className="block font-semibold text-xs text-zinc-700 mb-2 uppercase tracking-wide">{field.label} (₹)</label>
                      <input 
                        type="range" 
                        min="100" max="100000" step="500"
                        value={mandate[field.key]}
                        onChange={(e) => setMandate({...mandate, [field.key]: parseFloat(e.target.value)})}
                        className="w-full h-1.5 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-zinc-900"
                      />
                      <div className="text-right font-mono font-medium mt-1.5 text-sm text-zinc-900">₹{mandate[field.key].toLocaleString()}</div>
                    </div>
                  ))}
                  
                  <button 
                    onClick={saveMandate}
                    className="w-full bg-zinc-900 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-black transition-colors shadow-sm active:scale-[0.98]"
                  >
                    Save Limits
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-zinc-500">
                   <span className="w-4 h-4 border-2 border-zinc-300 border-t-zinc-900 rounded-full animate-spin"></span> Loading limits...
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Search */}
        <div className="flex gap-3">
          <input 
            type="text" 
            className="flex-1 p-3.5 bg-white border border-zinc-200/80 rounded-2xl shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all"
            placeholder="Search for laptops, microphones, headphones..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchProducts()}
          />
          <button 
            onClick={searchProducts}
            disabled={loading}
            className="bg-zinc-900 text-white px-8 py-3.5 rounded-2xl font-semibold text-sm hover:bg-black disabled:opacity-50 transition-all shadow-sm active:scale-[0.98]"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* 3-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" ref={gridRef}>
          
          {/* Marketplace */}
          <div className="bg-white border border-zinc-200/60 rounded-2xl shadow-sm p-6 flex flex-col h-[calc(100vh-220px)] min-h-[500px]">
            <h2 className="text-lg font-bold tracking-tight text-zinc-900 border-b border-zinc-100 pb-3 mb-4">Marketplace</h2>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
              {products.map((p: any) => (
                <div 
                  key={p.id} 
                  onClick={() => setSelectedProduct(p)}
                  className={`p-4 border rounded-2xl cursor-pointer transition-all duration-200 ${selectedProduct?.id === p.id ? 'border-zinc-900 bg-zinc-50/50 shadow-sm' : 'border-zinc-200/60 hover:border-zinc-300 hover:bg-zinc-50/30'}`}
                >
                  <div className="font-semibold text-zinc-900 text-sm leading-snug mb-1">{p.name}</div>
                  <div className="text-xs text-zinc-500 font-medium mb-3">Merchant: {p.merchant_id} <span className="opacity-50">|</span> Stock: {p.stock}</div>
                  <div className="font-bold text-zinc-900 font-mono">₹{p.price.toLocaleString()}</div>
                </div>
              ))}
              {products.length === 0 && !loading && (
                <p className="text-zinc-400 text-sm text-center mt-10">No products found. Search to begin.</p>
              )}
            </div>
          </div>
          
          {/* Negotiation / Chat */}
          <div className="bg-white border border-zinc-200/60 rounded-2xl shadow-sm p-6 flex flex-col h-[calc(100vh-220px)] min-h-[500px]">
            <h2 className="text-lg font-bold tracking-tight text-zinc-900 border-b border-zinc-100 pb-3 mb-4">Agent Negotiation</h2>
            
            {!selectedProduct ? (
              <div className="flex-1 flex items-center justify-center text-zinc-400 text-sm">
                Select a product to start negotiating
              </div>
            ) : (
              <div className="flex-1 flex flex-col min-h-0">
                <div className="bg-zinc-50 border border-zinc-200/50 p-3 rounded-xl mb-4 text-xs shrink-0 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-zinc-900">Target:</span> {selectedProduct.name}
                  </div>
                  <div className="text-zinc-500 font-mono font-medium bg-white px-2 py-1 rounded border border-zinc-200">List: ₹{selectedProduct.price}</div>
                </div>
                
                <div className="flex-1 overflow-y-auto space-y-5 mb-4 pr-2 scrollbar-thin">
                  {negotiationResult?.transcript?.map((turn: any, i: number) => (
                    <div key={i} className={`flex flex-col ${turn.sender === 'BUYER' ? 'items-end' : 'items-start'}`}>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1 px-1">
                        {turn.sender === 'BUYER' ? 'Your Buyer Agent' : 'Merchant Agent'}
                      </span>
                      <div className={`max-w-[85%] p-4 text-sm leading-relaxed ${turn.sender === 'BUYER' ? 'bg-zinc-900 text-white rounded-2xl rounded-tr-sm shadow-sm' : 'bg-zinc-100/80 text-zinc-900 rounded-2xl rounded-tl-sm border border-zinc-200/50'}`}>
                        {turn.action && <div className="text-[10px] font-bold opacity-60 mb-2 tracking-wide uppercase">[{turn.action}] {turn.price ? `₹${turn.price}` : ''}</div>}
                        {turn.message}
                      </div>
                    </div>
                  ))}

                  {/* Agent Processing Indicator */}
                  {negotiating && (
                    <div className={`flex flex-col ${(!negotiationResult?.transcript?.length || negotiationResult.transcript[negotiationResult.transcript.length - 1].sender === 'SELLER') ? 'items-end' : 'items-start'} mt-4`}>
                      {(!negotiationResult?.transcript?.length || negotiationResult.transcript[negotiationResult.transcript.length - 1].sender === 'SELLER') ? (
                        <div className="bg-zinc-100 border border-zinc-200/50 text-zinc-600 px-4 py-2.5 rounded-2xl rounded-tr-sm text-xs font-mono flex items-center gap-2 shadow-sm">
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"></span>
                          [ BUYER_AGENT: COMPUTING BID ]
                        </div>
                      ) : (
                        <div className="bg-white border border-zinc-200/50 text-zinc-600 px-4 py-2.5 rounded-2xl rounded-tl-sm text-xs font-mono flex items-center gap-2 shadow-sm">
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse"></span>
                          [ SELLER_AGENT: ANALYZING GUARDS ]
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Final Status */}
                  {negotiationResult && negotiationResult.status !== 'NEGOTIATING' && (
                    <div className={`mt-6 p-5 rounded-2xl text-center border shrink-0 
                      ${negotiationResult.status === 'ACCEPTED' ? 'bg-[#f0fdf4] text-[#166534] border-[#bbf7d0]' : 
                        negotiationResult.status === 'REQUIRES_APPROVAL' ? 'bg-[#fefce8] text-[#854d0e] border-[#fef08a]' : 
                        'bg-[#fef2f2] text-[#991b1b] border-[#fecaca]'}`}>
                      
                      <div className="font-bold tracking-tight text-sm uppercase">
                        {negotiationResult.status === 'REQUIRES_APPROVAL' 
                          ? `SYSTEM PENDING: Approval required for ₹${negotiationResult.final_price}` 
                          : `RESULT: ${negotiationResult.status}`}
                      </div>

                      {negotiationResult.status === 'ACCEPTED' && negotiationResult.final_price && (
                        <div className="mt-1 font-mono text-lg font-bold">Final Price: ₹{negotiationResult.final_price}</div>
                      )}
                      
                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status === 'success' && (
                        <div className="mt-4 text-sm bg-white/60 p-4 rounded-xl text-left border border-black/5">
                          <p className="text-[#166534] font-bold mb-1 flex items-center gap-2"><span className="text-lg">✓</span> Mandate Approved (Auto-Checkout)</p>
                          <div className="mt-3 space-y-1">
                            <p className="text-xs"><strong>Order ID:</strong> <span className="font-mono bg-white px-1.5 py-0.5 rounded border border-zinc-100">{negotiationResult.purchase_result.order_id}</span></p>
                            <p className="text-xs"><strong>Payment:</strong> {paymentStatus === 'PAID' ? '✅ PAID' : '⏳ PENDING'}</p>
                          </div>
                          
                          {paymentStatus !== 'PAID' && (
                            <p className="mt-3 text-xs opacity-70 animate-pulse font-medium">Launching Razorpay Checkout...</p>
                          )}
                        </div>
                      )}

                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status === 'requires_approval' && (
                        <div className="mt-4 text-sm bg-white/60 p-4 rounded-xl text-left border border-black/5 text-[#854d0e]">
                          <p className="font-bold mb-2 flex items-center gap-2"><span className="text-lg">⚠️</span> Human Approval Required</p>
                          <p className="text-xs leading-relaxed">{negotiationResult.purchase_result.reason}</p>
                          
                          {paymentStatus !== 'PAID' && (
                            <button 
                              onClick={handlePayment}
                              className="mt-4 w-full py-2.5 bg-black text-white rounded-xl text-sm font-semibold hover:bg-zinc-800 transition-all shadow-sm active:scale-[0.98]"
                            >
                              Approve & Pay (₹{negotiationResult.final_price})
                            </button>
                          )}
                          {paymentStatus === 'PAID' && <p className="mt-3 text-[#166534] font-bold">✅ PAYMENT SUCCESSFUL</p>}
                        </div>
                      )}

                      {negotiationResult.purchase_result && negotiationResult.purchase_result.status === 'failed' && (
                        <div className="mt-3 text-sm bg-white/60 p-3 rounded-xl text-left border border-black/5 text-[#991b1b]">
                          <p className="text-xs"><strong>Blocked Reason:</strong> {negotiationResult.purchase_result.reason}</p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div ref={chatEndRef} />
                </div>

                {/* Control Panel */}
                <div className="flex gap-2 shrink-0 mt-auto w-full pt-4 border-t border-zinc-100">
                  <input
                    type="text"
                    className="flex-1 min-w-0 p-3.5 bg-zinc-50 border border-zinc-200/80 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all"
                    placeholder="E.g., I won't pay more than ₹1000..."
                    value={budgetMessage}
                    onChange={(e) => setBudgetMessage(e.target.value)}
                    disabled={negotiating}
                    onKeyDown={(e) => e.key === 'Enter' && startNegotiation()}
                  />
                  <button
                    onClick={startNegotiation}
                    disabled={negotiating}
                    className="px-6 py-3.5 bg-zinc-900 text-white rounded-xl text-sm font-semibold hover:bg-black disabled:opacity-50 transition-all shadow-sm active:scale-[0.98] whitespace-nowrap"
                  >
                    Deploy Agent
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Audit Trail / Mission Control */}
          <div className="bg-[#0a0a0a] border border-[#222] rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 flex flex-col h-[calc(100vh-220px)] min-h-[500px]">
            <h2 className="text-xs font-bold tracking-widest text-zinc-100 uppercase border-b border-[#333] pb-3 mb-4 flex justify-between items-center">
              Mission Control Log
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            </h2>
            <div className="flex-1 overflow-y-auto space-y-0 text-[11px] font-mono pr-2 scrollbar-thin scrollbar-thumb-[#333]">
              {!negotiationResult && !negotiating && (
                <p className="text-zinc-600 italic py-2">Awaiting agent deployment sequence...</p>
              )}
              {negotiating && (!negotiationResult?.audit_trail || negotiationResult.audit_trail.length === 0) && (
                <p className="text-zinc-400 animate-pulse py-2">[SYSTEM] Initializing agent negotiation protocol...</p>
              )}
              {negotiationResult?.audit_trail?.map((log: any, i: number) => (
                <div key={i} className={`py-2 border-b border-white/5 ${log.type === 'FAILURE' ? 'text-red-400' : log.type === 'SUCCESS' ? 'text-[#4ade80]' : 'text-zinc-400'}`}>
                  <span className="opacity-40 mr-2">[{log.timestamp || new Date().toLocaleTimeString()}]</span>
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
