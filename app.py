<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StockPulse AI - Indian Stock Market Intelligence</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              bg: '#0B0F19',
              sidebar: '#111827',
              card: '#151D2B',
              cardHover: '#1E293B',
              border: '#263244',
              blue: '#3B82F6',
              green: '#22C55E',
              red: '#EF4444',
              text: '#F8FAFC',
              muted: '#94A3B8'
            }
          }
        }
      }
    };
  </script>

  <!-- React, ReactDOM, Babel, Lucide Icons & Chart.js -->
  <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    body {
      background-color: #0B0F19;
      color: #F8FAFC;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      overflow-x: hidden;
    }
    /* Custom Scrollbars */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
      background: #263244;
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #3B82F6;
    }
    .pulse-glow {
      box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
    }
  </style>
</head>
<body class="bg-brand-bg text-brand-text antialiased selection:bg-brand-blue selection:text-white">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect, useRef, useMemo } = React;

    // --- MOCK INDIAN MARKET DATA DATABASE ---
    const MOCK_STOCKS = [
      { symbol: 'RELIANCE', name: 'Reliance Industries Ltd.', exchange: 'NSE', sector: 'Energy', price: 2945.50, change: 34.20, changePercent: 1.17, open: 2915.00, high: 2960.00, low: 2910.00, close: 2911.30, volume: '8.4M', mcap: '₹19.92L Cr', pe: 28.4, pb: 2.45, eps: 103.7, roe: '9.8%', roce: '11.2%', debtEquity: 0.42, high52w: 3024.90, low52w: 2220.30, rsi: 58.4, macd: 'Bullish' },
      { symbol: 'TCS', name: 'Tata Consultancy Services', exchange: 'NSE', sector: 'IT', price: 4120.10, change: -28.40, changePercent: -0.68, open: 4150.00, high: 4165.00, low: 4105.00, close: 4148.50, volume: '2.1M', mcap: '₹14.91L Cr', pe: 32.1, pb: 13.8, eps: 128.3, roe: '48.2%', roce: '56.1%', debtEquity: 0.08, high52w: 4254.75, low52w: 3313.00, rsi: 44.2, macd: 'Bearish' },
      { symbol: 'HDFCBANK', name: 'HDFC Bank Limited', exchange: 'NSE', sector: 'Banking', price: 1682.30, change: 18.90, changePercent: 1.14, open: 1665.00, high: 1690.00, low: 1660.00, close: 1663.40, volume: '14.2M', mcap: '₹12.80L Cr', pe: 19.4, pb: 2.8, eps: 86.7, roe: '16.5%', roce: '17.1%', debtEquity: 0.88, high52w: 1757.50, low52w: 1363.55, rsi: 62.1, macd: 'Bullish' },
      { symbol: 'INFY', name: 'Infosys Limited', exchange: 'NSE', sector: 'IT', price: 1785.40, change: 42.10, changePercent: 2.41, open: 1745.00, high: 1792.00, low: 1740.00, close: 1743.30, volume: '6.8M', mcap: '₹7.41L Cr', pe: 29.8, pb: 8.9, eps: 59.9, roe: '31.8%', roce: '39.4%', debtEquity: 0.09, high52w: 1847.00, low52w: 1355.00, rsi: 68.9, macd: 'Bullish' },
      { symbol: 'ICICIBANK', name: 'ICICI Bank Limited', exchange: 'NSE', sector: 'Banking', price: 1215.00, change: 14.50, changePercent: 1.21, open: 1202.00, high: 1222.00, low: 1198.00, close: 1200.50, volume: '9.5M', mcap: '₹8.55L Cr', pe: 18.2, pb: 3.1, eps: 66.8, roe: '18.4%', roce: '19.2%', debtEquity: 0.75, high52w: 1257.00, low52w: 898.00, rsi: 59.3, macd: 'Bullish' },
      { symbol: 'BHARTIARTL', name: 'Bharti Airtel Limited', exchange: 'NSE', sector: 'Telecom', price: 1460.75, change: -12.30, changePercent: -0.83, open: 1475.00, high: 1480.00, low: 1452.00, close: 1473.05, volume: '4.3M', mcap: '₹8.32L Cr', pe: 64.2, pb: 9.4, eps: 22.7, roe: '15.1%', roce: '16.8%', debtEquity: 1.45, high52w: 1536.00, low52w: 902.00, rsi: 48.7, macd: 'Neutral' },
      { symbol: 'ITC', name: 'ITC Limited', exchange: 'BSE', sector: 'FMCG', price: 492.20, change: 6.80, changePercent: 1.40, open: 486.00, high: 495.00, low: 485.50, close: 485.40, volume: '11.8M', mcap: '₹6.15L Cr', pe: 28.9, pb: 8.2, eps: 17.0, roe: '29.2%', roce: '37.8%', debtEquity: 0.00, high52w: 510.60, low52w: 399.30, rsi: 55.4, macd: 'Bullish' },
      { symbol: 'TATAMOTORS', name: 'Tata Motors Limited', exchange: 'NSE', sector: 'Automobile', price: 980.60, change: -34.50, changePercent: -3.40, open: 1015.00, high: 1020.00, low: 975.00, close: 1015.10, volume: '12.4M', mcap: '₹3.25L Cr', pe: 10.4, pb: 3.4, eps: 94.2, roe: '32.4%', roce: '21.5%', debtEquity: 0.62, high52w: 1179.00, low52w: 615.00, rsi: 38.2, macd: 'Bearish' },
      { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical Ind.', exchange: 'NSE', sector: 'Pharma', price: 1710.25, change: 22.80, changePercent: 1.35, open: 1690.00, high: 1722.00, low: 1685.00, close: 1687.45, volume: '3.1M', mcap: '₹4.10L Cr', pe: 38.5, pb: 6.1, eps: 44.4, roe: '16.8%', roce: '19.4%', debtEquity: 0.05, high52w: 1750.00, low52w: 1115.00, rsi: 64.0, macd: 'Bullish' },
      { symbol: 'TATASTEEL', name: 'Tata Steel Limited', exchange: 'BSE', sector: 'Metal', price: 154.30, change: 3.40, changePercent: 2.25, open: 151.00, high: 156.00, low: 150.50, close: 150.90, volume: '22.1M', mcap: '₹1.92L Cr', pe: 42.1, pb: 2.1, eps: 3.66, roe: '5.2%', roce: '8.1%', debtEquity: 0.92, high52w: 184.60, low52w: 114.25, rsi: 52.8, macd: 'Bullish' },
      { symbol: 'DLF', name: 'DLF Limited', exchange: 'NSE', sector: 'Realty', price: 845.00, change: 18.20, changePercent: 2.20, open: 828.00, high: 852.00, low: 825.00, close: 826.80, volume: '4.8M', mcap: '₹2.09L Cr', pe: 72.4, pb: 5.4, eps: 11.6, roe: '7.8%', roce: '9.2%', debtEquity: 0.08, high52w: 967.00, low52w: 462.00, rsi: 61.2, macd: 'Bullish' },
      { symbol: 'NTPC', name: 'NTPC Limited', exchange: 'NSE', sector: 'Energy', price: 412.50, change: -4.20, changePercent: -1.01, open: 418.00, high: 420.00, low: 410.00, close: 416.70, volume: '15.6M', mcap: '₹4.00L Cr', pe: 19.8, pb: 2.4, eps: 20.8, roe: '13.2%', roce: '10.5%', debtEquity: 1.32, high52w: 435.00, low52w: 230.00, rsi: 46.5, macd: 'Neutral' }
    ];

    const MOCK_INDICES = [
      { symbol: 'NIFTY 50', value: 24586.70, change: 164.25, changePercent: 0.67, prevClose: 24422.45, chartData: [24430, 24450, 24410, 24490, 24520, 24560, 24586.70] },
      { symbol: 'SENSEX', value: 80716.55, change: 522.30, changePercent: 0.65, prevClose: 80194.25, chartData: [80200, 80280, 80150, 80400, 80550, 80680, 80716.55] },
      { symbol: 'BANK NIFTY', value: 52280.40, change: 485.10, changePercent: 0.94, prevClose: 51795.30, chartData: [51800, 51920, 51780, 52050, 52180, 52250, 52280.40] },
      { symbol: 'NIFTY IT', value: 41850.15, change: -120.40, changePercent: -0.29, prevClose: 41970.55, chartData: [41980, 42050, 41920, 41880, 41820, 41870, 41850.15] }
    ];

    const MOCK_NEWS = [
      { id: 1, headline: 'RBI Keeps Repo Rate Unchanged at 6.5%, Maintains Policy Stance', category: 'Economy', source: 'Economic Times', time: '10 mins ago', summary: 'The Reserve Bank of India Monetary Policy Committee has decided to keep interest rates steady, citing sticky inflation metrics while raising FY25 GDP growth target.', sentiment: 'Bullish' },
      { id: 2, headline: 'Reliance Retail Expands Footprint with 300 New Stores in Tier 2 Cities', category: 'Company', source: 'LiveMint', time: '45 mins ago', summary: 'RIL retail division announces aggressive expansion strategy focusing on high-growth tier-2 urban centers across India.', sentiment: 'Bullish' },
      { id: 3, headline: 'IT Services Companies Facing Margin Pressure Due to Onsite Wage Hikes', category: 'Technology', source: 'Business Standard', time: '2 hours ago', summary: 'Tier-1 IT exporters including TCS and Infosys report temporary gross margin compression attributed to higher sub-contracting and onsite wage inflation.', sentiment: 'Bearish' },
      { id: 4, headline: 'Hyundai Motor India IPO Subscribed 2.37x on Final Bidding Day', category: 'IPO', source: 'Financial Express', time: '4 hours ago', summary: 'India’s largest automotive IPO sees strong institutional investor participation, led by QIB bids, despite retail caution.', sentiment: 'Neutral' },
      { id: 5, headline: 'FII Net Buyers for Third Straight Session, Injecting ₹2,400 Cr in Indian Equities', category: 'Indian stock market', source: 'CNBC-TV18', time: '5 hours ago', summary: 'Foreign Institutional Investors continue equity buying spree as U.S. Fed rate cut expectations weaken the US Dollar index.', sentiment: 'Bullish' }
    ];

    const MOCK_IPOS = [
      { id: 1, name: 'Swiggy Limited', status: 'Upcoming', priceRange: '₹371 - ₹390', lotSize: 38, openDate: 'Nov 06, 2024', closeDate: 'Nov 08, 2024', listingDate: 'Nov 13, 2024', issueSize: '₹11,370 Cr', subscription: 'N/A', listingGain: '-' },
      { id: 2, name: 'Waaree Energies Ltd.', status: 'Recently Listed', priceRange: '₹1,427 - ₹1,503', lotSize: 9, openDate: 'Oct 21, 2024', closeDate: 'Oct 23, 2024', listingDate: 'Oct 28, 2024', issueSize: '₹4,321 Cr', subscription: '76.3x', listingGain: '+69.7%' },
      { id: 3, name: 'Hyundai Motor India', status: 'Closed', priceRange: '₹1,865 - ₹1,960', lotSize: 7, openDate: 'Oct 15, 2024', closeDate: 'Oct 17, 2024', listingDate: 'Oct 22, 2024', issueSize: '₹27,870 Cr', subscription: '2.37x', listingGain: '-1.4%' },
      { id: 4, name: 'Niva Bupa Health Insurance', status: 'Open', priceRange: '₹70 - ₹74', lotSize: 200, openDate: 'Nov 07, 2024', closeDate: 'Nov 11, 2024', listingDate: 'Nov 14, 2024', issueSize: '₹2,200 Cr', subscription: '1.42x', listingGain: 'TBD' }
    ];

    // --- MAIN APP COMPONENT ---
    function App() {
      // Global App States
      const [activeTab, setActiveTab] = useState('dashboard');
      const [selectedExchange, setSelectedExchange] = useState('NSE');
      const [searchQuery, setSearchQuery] = useState('');
      const [searchResults, setSearchResults] = useState([]);
      const [selectedStock, setSelectedStock] = useState(MOCK_STOCKS[0]);
      
      // Watchlist State
      const [watchlists, setWatchlists] = useState([
        { id: 'w1', name: 'Core Bluechips', symbols: ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY'] },
        { id: 'w2', name: 'High Growth Auto & IT', symbols: ['TATAMOTORS', 'ICICIBANK', 'DLF'] }
      ]);
      const [activeWatchlistId, setActiveWatchlistId] = useState('w1');

      // Portfolio State (Transaction-based Average Cost)
      const [transactions, setTransactions] = useState([
        { id: 't1', symbol: 'RELIANCE', type: 'BUY', qty: 25, price: 2750.00, date: '2024-03-15', exchange: 'NSE' },
        { id: 't2', symbol: 'HDFCBANK', type: 'BUY', qty: 50, price: 1540.00, date: '2024-04-10', exchange: 'NSE' },
        { id: 't3', symbol: 'INFY', type: 'BUY', qty: 40, price: 1620.00, date: '2024-05-20', exchange: 'NSE' }
      ]);

      // Virtual Paper Trading State
      const [virtualAccount, setVirtualAccount] = useState({
        balance: 100000.00,
        initialBalance: 100000.00,
        trades: [
          { id: 'vt1', symbol: 'ITC', type: 'BUY', qty: 50, price: 470.00, timestamp: '2024-10-25 10:30 AM', total: 23500.00 }
        ]
      });

      // Price Alerts State
      const [alerts, setAlerts] = useState([
        { id: 'a1', symbol: 'RELIANCE', condition: 'ABOVE', targetPrice: 3000.00, active: true, createdAt: '2024-10-01' },
        { id: 'a2', symbol: 'TCS', condition: 'BELOW', targetPrice: 4000.00, active: true, createdAt: '2024-10-12' }
      ]);

      // Settings & Gemini API key state
      const [geminiApiKey, setGeminiApiKey] = useState('');
      const [demoMode, setDemoMode] = useState(true);

      // Toast Notification State
      const [toast, setToast] = useState(null);

      const showToast = (message, type = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3500);
      };

      // Helper to calculate portfolio metrics using standard Average Cost basis
      const portfolioSummary = useMemo(() => {
        const holdingsMap = {};

        transactions.forEach(tx => {
          if (!holdingsMap[tx.symbol]) {
            holdingsMap[tx.symbol] = { qty: 0, totalCost: 0, avgPrice: 0, realizedPnL: 0 };
          }
          const h = holdingsMap[tx.symbol];
          if (tx.type === 'BUY') {
            h.qty += tx.qty;
            h.totalCost += tx.qty * tx.price;
            h.avgPrice = h.qty > 0 ? h.totalCost / h.qty : 0;
          } else if (tx.type === 'SELL') {
            const costOfSoldShares = tx.qty * h.avgPrice;
            h.realizedPnL += (tx.qty * tx.price) - costOfSoldShares;
            h.qty -= tx.qty;
            h.totalCost -= costOfSoldShares;
            if (h.qty === 0) h.avgPrice = 0;
          }
        });

        let totalInvested = 0;
        let currentValue = 0;
        let totalRealizedPnL = 0;
        const holdingsList = [];

        Object.keys(holdingsMap).forEach(sym => {
          const h = holdingsMap[sym];
          totalRealizedPnL += h.realizedPnL;
          if (h.qty > 0) {
            const stock = MOCK_STOCKS.find(s => s.symbol === sym) || { price: h.avgPrice, name: sym, sector: 'Other' };
            const mktVal = h.qty * stock.price;
            const unPnL = mktVal - h.totalCost;
            const unPnLPercent = h.totalCost > 0 ? (unPnL / h.totalCost) * 100 : 0;

            totalInvested += h.totalCost;
            currentValue += mktVal;

            holdingsList.push({
              symbol: sym,
              companyName: stock.name,
              sector: stock.sector,
              qty: h.qty,
              avgPrice: h.avgPrice,
              currentPrice: stock.price,
              invested: h.totalCost,
              currentValue: mktVal,
              unrealizedPnL: unPnL,
              unrealizedPnLPercent: unPnLPercent,
              realizedPnL: h.realizedPnL
            });
          }
        });

        const totalUnrealizedPnL = currentValue - totalInvested;
        const overallReturnPercent = totalInvested > 0 ? (totalUnrealizedPnL / totalInvested) * 100 : 0;

        return {
          totalInvested,
          currentValue,
          totalUnrealizedPnL,
          totalRealizedPnL,
          overallReturnPercent,
          holdings: holdingsList
        };
      }, [transactions]);

      // Global Quick Search Filter
      useEffect(() => {
        if (searchQuery.trim().length > 0) {
          const filtered = MOCK_STOCKS.filter(s =>
            s.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
            s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            s.sector.toLowerCase().includes(searchQuery.toLowerCase())
          );
          setSearchResults(filtered);
        } else {
          setSearchResults([]);
        }
      }, [searchQuery]);

      // Icon Renderer Helper
      useEffect(() => {
        if (window.lucide) {
          window.lucide.createIcons();
        }
      });

      return (
        <div className="flex h-screen bg-brand-bg text-brand-text overflow-hidden">
          {/* Toast Notification Banner */}
          {toast && (
            <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg border shadow-lg text-sm font-medium transition-all transform animate-bounce ${
              toast.type === 'success' ? 'bg-emerald-950 border-emerald-600 text-emerald-200' :
              toast.type === 'error' ? 'bg-red-950 border-red-600 text-red-200' :
              'bg-blue-950 border-blue-600 text-blue-200'
            }`}>
              <i data-lucide={toast.type === 'success' ? 'check-circle' : toast.type === 'error' ? 'alert-triangle' : 'info'} class="w-5 h-5"></i>
              {toast.message}
            </div>
          )}

          {/* LEFT SIDEBAR NAVIGATION */}
          <aside className="w-64 bg-brand-sidebar border-r border-brand-border flex flex-col justify-between hidden md:flex shrink-0">
            <div>
              {/* Brand Header */}
              <div className="p-5 border-b border-brand-border flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue to-cyan-400 flex items-center justify-center font-bold text-xl text-white shadow-md">
                  SP
                </div>
                <div>
                  <h1 className="font-bold text-lg leading-none text-white tracking-wide">StockPulse <span className="text-brand-blue">AI</span></h1>
                  <p className="text-[10px] text-brand-muted mt-1 font-medium">Understand Markets. Invest Smarter.</p>
                </div>
              </div>

              {/* Navigation Links */}
              <nav className="p-3 space-y-1">
                {[
                  { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
                  { id: 'markets', label: 'Markets & Explorer', icon: 'line-chart' },
                  { id: 'watchlist', label: 'Watchlist', icon: 'bookmark' },
                  { id: 'portfolio', label: 'My Portfolio', icon: 'pie-chart' },
                  { id: 'ai-analyst', label: 'AI Stock Analyst', icon: 'sparkles', highlight: true },
                  { id: 'virtual-trading', label: 'Virtual Trading', icon: 'wallet' },
                  { id: 'news', label: 'Market News', icon: 'newspaper' },
                  { id: 'ipo', label: 'IPO Center', icon: 'rocket' },
                  { id: 'alerts', label: 'Price Alerts', icon: 'bell' },
                  { id: 'settings', label: 'Settings & APIs', icon: 'settings' }
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      activeTab === item.id
                        ? 'bg-brand-blue/15 text-brand-blue border-l-4 border-brand-blue font-semibold'
                        : 'text-brand-muted hover:bg-brand-cardHover hover:text-brand-text'
                    }`}
                  >
                    <i data-lucide={item.icon} className={`w-4 h-4 ${item.highlight ? 'text-amber-400' : ''}`}></i>
                    <span>{item.label}</span>
                    {item.highlight && <span className="ml-auto text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">PRO</span>}
                  </button>
                ))}
              </nav>
            </div>

            {/* Bottom Status Card */}
            <div className="p-4 border-t border-brand-border">
              <div className="bg-brand-card p-3 rounded-lg border border-brand-border text-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-brand-muted">Market Provider</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${demoMode ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                    {demoMode ? 'DEMO MODE' : 'LIVE API'}
                  </span>
                </div>
                <p className="text-brand-muted text-[11px]">NSE/BSE Feeds Connected</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="text-[10px] text-emerald-400 font-medium">Socket IO Stream Active</span>
                </div>
              </div>
            </div>
          </aside>

          {/* MAIN WRAPPER */}
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            {/* TOP NAVIGATION BAR */}
            <header className="h-16 bg-brand-sidebar border-b border-brand-border px-4 md:px-6 flex items-center justify-between gap-4 shrink-0">
              {/* Left Search & Exchange Selector */}
              <div className="flex items-center gap-3 flex-1 max-w-xl relative">
                <div className="relative w-full">
                  <i data-lucide="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"></i>
                  <input
                    type="text"
                    placeholder="Search stocks (e.g. RELIANCE, TCS, HDFC)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-brand-bg border border-brand-border rounded-lg pl-9 pr-4 py-2 text-sm text-brand-text placeholder-brand-muted focus:outline-none focus:border-brand-blue"
                  />
                  {/* Search Dropdown */}
                  {searchResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-brand-card border border-brand-border rounded-lg shadow-2xl z-50 max-h-80 overflow-y-auto">
                      {searchResults.map((stk) => (
                        <div
                          key={stk.symbol}
                          onClick={() => {
                            setSelectedStock(stk);
                            setActiveTab('markets');
                            setSearchQuery('');
                          }}
                          className="p-3 hover:bg-brand-cardHover cursor-pointer border-b border-brand-border/50 flex items-center justify-between"
                        >
                          <div>
                            <div className="font-bold text-sm text-white flex items-center gap-2">
                              {stk.symbol}
                              <span className="text-[10px] bg-brand-border text-brand-muted px-1.5 py-0.5 rounded">{stk.exchange}</span>
                            </div>
                            <div className="text-xs text-brand-muted">{stk.name}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-white">₹{stk.price.toFixed(2)}</div>
                            <div className={`text-xs font-medium ${stk.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                              {stk.change >= 0 ? '+' : ''}{stk.changePercent.toFixed(2)}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Exchange Switcher */}
                <div className="hidden sm:flex bg-brand-bg p-1 rounded-lg border border-brand-border">
                  {['NSE', 'BSE'].map((ex) => (
                    <button
                      key={ex}
                      onClick={() => setSelectedExchange(ex)}
                      className={`px-3 py-1 rounded text-xs font-bold transition-all ${
                        selectedExchange === ex ? 'bg-brand-blue text-white shadow' : 'text-brand-muted hover:text-brand-text'
                      }`}
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>

              {/* Right User Bar */}
              <div className="flex items-center gap-3">
                {/* Market Status Pill */}
                <div className="hidden lg:flex items-center gap-2 bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 px-3 py-1.5 rounded-full text-xs font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span>Market Open (09:15 - 15:30 IST)</span>
                </div>

                {/* Alerts Quick Bell */}
                <button
                  onClick={() => setActiveTab('alerts')}
                  className="p-2 text-brand-muted hover:text-brand-text hover:bg-brand-cardHover rounded-lg relative"
                  title="Price Alerts"
                >
                  <i data-lucide="bell" className="w-5 h-5"></i>
                  {alerts.some(a => a.active) && (
                    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-brand-blue"></span>
                  )}
                </button>

                {/* Profile Pill */}
                <div className="flex items-center gap-2 pl-2 border-l border-brand-border">
                  <div className="w-8 h-8 rounded-full bg-brand-blue/20 border border-brand-blue/50 flex items-center justify-center font-bold text-xs text-brand-blue">
                    IN
                  </div>
                  <div className="hidden sm:block text-left">
                    <div className="text-xs font-semibold text-white">Anand Verma</div>
                    <div className="text-[10px] text-brand-muted">Standard Trader</div>
                  </div>
                </div>
              </div>
            </header>

            {/* MOBILE NAVIGATION BAR */}
            <div className="md:hidden bg-brand-sidebar border-b border-brand-border px-4 py-2 flex overflow-x-auto gap-2 text-xs scrollbar-none">
              {[
                { id: 'dashboard', label: 'Dashboard' },
                { id: 'markets', label: 'Markets' },
                { id: 'watchlist', label: 'Watchlist' },
                { id: 'portfolio', label: 'Portfolio' },
                { id: 'ai-analyst', label: 'AI Analyst' },
                { id: 'virtual-trading', label: 'Virtual' },
                { id: 'news', label: 'News' }
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`px-3 py-1.5 rounded-lg whitespace-nowrap font-medium ${
                    activeTab === t.id ? 'bg-brand-blue text-white' : 'bg-brand-card text-brand-muted'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-brand-bg">
              {activeTab === 'dashboard' && (
                <DashboardView
                  onSelectStock={(stk) => { setSelectedStock(stk); setActiveTab('markets'); }}
                  onNavigate={(tab) => setActiveTab(tab)}
                />
              )}

              {activeTab === 'markets' && (
                <MarketsExplorerView
                  stock={selectedStock}
                  onSelectStock={setSelectedStock}
                  onAddToWatchlist={(stk) => {
                    const targetWl = watchlists[0];
                    if (!targetWl.symbols.includes(stk.symbol)) {
                      setWatchlists(watchlists.map(w => w.id === targetWl.id ? { ...w, symbols: [...w.symbols, stk.symbol] } : w));
                      showToast(`Added ${stk.symbol} to ${targetWl.name}`, 'success');
                    } else {
                      showToast(`${stk.symbol} is already in Watchlist`, 'info');
                    }
                  }}
                  onQuickTrade={(stk) => {
                    setSelectedStock(stk);
                    setActiveTab('virtual-trading');
                  }}
                />
              )}

              {activeTab === 'watchlist' && (
                <WatchlistView
                  watchlists={watchlists}
                  activeWatchlistId={activeWatchlistId}
                  setActiveWatchlistId={setActiveWatchlistId}
                  onCreateWatchlist={(name) => {
                    const newWl = { id: `w_${Date.now()}`, name, symbols: [] };
                    setWatchlists([...watchlists, newWl]);
                    setActiveWatchlistId(newWl.id);
                    showToast(`Created watchlist "${name}"`, 'success');
                  }}
                  onRemoveFromWatchlist={(sym) => {
                    setWatchlists(watchlists.map(w => w.id === activeWatchlistId ? { ...w, symbols: w.symbols.filter(s => s !== sym) } : w));
                    showToast(`Removed ${sym} from Watchlist`, 'info');
                  }}
                  onSelectStock={(sym) => {
                    const stk = MOCK_STOCKS.find(s => s.symbol === sym);
                    if (stk) { setSelectedStock(stk); setActiveTab('markets'); }
                  }}
                />
              )}

              {activeTab === 'portfolio' && (
                <PortfolioView
                  summary={portfolioSummary}
                  onAddTransaction={(txData) => {
                    setTransactions([...transactions, { id: `t_${Date.now()}`, ...txData }]);
                    showToast(`Transaction logged successfully`, 'success');
                  }}
                />
              )}

              {activeTab === 'ai-analyst' && (
                <AIAnalystView
                  selectedStock={selectedStock}
                  geminiApiKey={geminiApiKey}
                />
              )}

              {activeTab === 'virtual-trading' && (
                <VirtualTradingView
                  account={virtualAccount}
                  selectedStock={selectedStock}
                  onExecuteTrade={(tradeData) => {
                    const totalCost = tradeData.qty * tradeData.price;
                    if (tradeData.type === 'BUY' && totalCost > virtualAccount.balance) {
                      showToast('Insufficient virtual funds!', 'error');
                      return;
                    }

                    const newTrade = {
                      id: `vt_${Date.now()}`,
                      symbol: tradeData.symbol,
                      type: tradeData.type,
                      qty: tradeData.qty,
                      price: tradeData.price,
                      total: totalCost,
                      timestamp: new Date().toLocaleString()
                    };

                    const newBalance = tradeData.type === 'BUY'
                      ? virtualAccount.balance - totalCost
                      : virtualAccount.balance + totalCost;

                    setVirtualAccount({
                      ...virtualAccount,
                      balance: newBalance,
                      trades: [newTrade, ...virtualAccount.trades]
                    });

                    showToast(`Executed Paper ${tradeData.type} for ${tradeData.qty} shares of ${tradeData.symbol}`, 'success');
                  }}
                />
              )}

              {activeTab === 'news' && <NewsView />}

              {activeTab === 'ipo' && <IPOCenterView />}

              {activeTab === 'alerts' && (
                <AlertsView
                  alerts={alerts}
                  onAddAlert={(alertData) => {
                    setAlerts([{ id: `a_${Date.now()}`, ...alertData, active: true, createdAt: new Date().toISOString().split('T')[0] }, ...alerts]);
                    showToast(`Price alert created for ${alertData.symbol}`, 'success');
                  }}
                  onToggleAlert={(id) => {
                    setAlerts(alerts.map(a => a.id === id ? { ...a, active: !a.active } : a));
                  }}
                  onDeleteAlert={(id) => {
                    setAlerts(alerts.filter(a => a.id !== id));
                    showToast('Alert removed', 'info');
                  }}
                />
              )}

              {activeTab === 'settings' && (
                <SettingsView
                  geminiApiKey={geminiApiKey}
                  setGeminiApiKey={setGeminiApiKey}
                  demoMode={demoMode}
                  setDemoMode={setDemoMode}
                  showToast={showToast}
                />
              )}
            </main>
          </div>
        </div>
      );
    }

    // --- 1. DASHBOARD VIEW COMPONENT ---
    function DashboardView({ onSelectStock, onNavigate }) {
      const topGainers = useMemo(() => [...MOCK_STOCKS].sort((a, b) => b.changePercent - a.changePercent).slice(0, 5), []);
      const topLosers = useMemo(() => [...MOCK_STOCKS].sort((a, b) => a.changePercent - b.changePercent).slice(0, 5), []);

      return (
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-brand-sidebar via-brand-card to-brand-sidebar p-5 rounded-2xl border border-brand-border">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Indian Market Overview <span className="text-xs bg-brand-blue/20 text-brand-blue px-2 py-0.5 rounded font-semibold">LIVE</span>
              </h2>
              <p className="text-xs text-brand-muted mt-1">Real-time benchmark indices and sector movement across NSE & BSE</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => onNavigate('markets')} className="px-4 py-2 bg-brand-blue text-white rounded-lg text-xs font-semibold hover:bg-blue-600 transition shadow">
                Explore All Stocks
              </button>
            </div>
          </div>

          {/* INDEX CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {MOCK_INDICES.map((idx) => {
              const isPos = idx.change >= 0;
              return (
                <div key={idx.symbol} className="bg-brand-card p-4 rounded-xl border border-brand-border hover:border-brand-blue/40 transition">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold text-brand-muted">{idx.symbol}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${isPos ? 'bg-emerald-500/10 text-brand-green' : 'bg-red-500/10 text-brand-red'}`}>
                      {isPos ? '+' : ''}{idx.changePercent}%
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-white tracking-tight">₹{idx.value.toLocaleString('en-IN')}</div>
                  <div className={`text-xs font-medium mt-1 ${isPos ? 'text-brand-green' : 'text-brand-red'}`}>
                    {isPos ? '▲' : '▼'} {Math.abs(idx.change).toFixed(2)} pts
                  </div>

                  {/* Sparkline Canvas Visual */}
                  <div className="mt-3 pt-3 border-t border-brand-border/40 flex items-center justify-between text-[10px] text-brand-muted">
                    <span>Prev Close: ₹{idx.prevClose.toLocaleString('en-IN')}</span>
                    <span className="font-semibold text-brand-blue">Intraday</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* MARKET BREADTH OVERVIEW */}
          <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <i data-lucide="bar-chart-2" className="w-4 h-4 text-brand-blue"></i> Market Breadth (NSE Broad Market)
            </h3>
            <div className="grid grid-cols-3 gap-4 text-center mb-4">
              <div className="bg-emerald-950/40 border border-emerald-800/40 p-3 rounded-lg">
                <div className="text-xs text-emerald-400 font-medium">Advances</div>
                <div className="text-xl font-bold text-brand-green mt-0.5">1,482</div>
              </div>
              <div className="bg-red-950/40 border border-red-800/40 p-3 rounded-lg">
                <div className="text-xs text-red-400 font-medium">Declines</div>
                <div className="text-xl font-bold text-brand-red mt-0.5">945</div>
              </div>
              <div className="bg-gray-800/40 border border-brand-border p-3 rounded-lg">
                <div className="text-xs text-brand-muted font-medium">Unchanged</div>
                <div className="text-xl font-bold text-brand-text mt-0.5">118</div>
              </div>
            </div>
            {/* Advance/Decline Visual Progress Bar */}
            <div className="w-full bg-brand-bg h-2 rounded-full overflow-hidden flex">
              <div className="bg-brand-green h-full" style={{ width: '58%' }}></div>
              <div className="bg-brand-text h-full" style={{ width: '5%' }}></div>
              <div className="bg-brand-red h-full" style={{ width: '37%' }}></div>
            </div>
          </div>

          {/* TOP GAINERS & LOSERS GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Gainers */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <i data-lucide="trending-up" className="w-4 h-4 text-brand-green"></i> Top Gainers Today
                </h3>
                <span className="text-[11px] text-brand-muted">NSE LargeCap</span>
              </div>
              <div className="space-y-2">
                {topGainers.map((stk) => (
                  <div
                    key={stk.symbol}
                    onClick={() => onSelectStock(stk)}
                    className="p-3 bg-brand-bg rounded-lg hover:bg-brand-cardHover cursor-pointer border border-brand-border/40 flex items-center justify-between transition"
                  >
                    <div>
                      <div className="font-bold text-sm text-white">{stk.symbol}</div>
                      <div className="text-xs text-brand-muted">{stk.sector}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">₹{stk.price.toFixed(2)}</div>
                      <div className="text-xs font-semibold text-brand-green">+{stk.changePercent.toFixed(2)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Losers */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <i data-lucide="trending-down" className="w-4 h-4 text-brand-red"></i> Top Losers Today
                </h3>
                <span className="text-[11px] text-brand-muted">NSE LargeCap</span>
              </div>
              <div className="space-y-2">
                {topLosers.map((stk) => (
                  <div
                    key={stk.symbol}
                    onClick={() => onSelectStock(stk)}
                    className="p-3 bg-brand-bg rounded-lg hover:bg-brand-cardHover cursor-pointer border border-brand-border/40 flex items-center justify-between transition"
                  >
                    <div>
                      <div className="font-bold text-sm text-white">{stk.symbol}</div>
                      <div className="text-xs text-brand-muted">{stk.sector}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">₹{stk.price.toFixed(2)}</div>
                      <div className="text-xs font-semibold text-brand-red">{stk.changePercent.toFixed(2)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTOR PERFORMANCE MATRIX */}
          <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
            <h3 className="text-sm font-bold text-white mb-4">Market Sector Indices</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { name: 'NIFTY Banking', change: '+1.14%', pos: true },
                { name: 'NIFTY IT', change: '-0.29%', pos: false },
                { name: 'NIFTY Auto', change: '-1.85%', pos: false },
                { name: 'NIFTY Pharma', change: '+1.25%', pos: true },
                { name: 'NIFTY FMCG', change: '+0.88%', pos: true },
                { name: 'NIFTY Energy', change: '+0.45%', pos: true },
                { name: 'NIFTY Metal', change: '+1.92%', pos: true },
                { name: 'NIFTY Realty', change: '+2.10%', pos: true }
              ].map(sec => (
                <div key={sec.name} className="p-3 bg-brand-bg border border-brand-border rounded-lg flex items-center justify-between">
                  <span className="text-xs font-medium text-brand-muted">{sec.name}</span>
                  <span className={`text-xs font-bold ${sec.pos ? 'text-brand-green' : 'text-brand-red'}`}>{sec.change}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    // --- 2. MARKETS & STOCK EXPLORER VIEW COMPONENT ---
    function MarketsExplorerView({ stock, onSelectStock, onAddToWatchlist, onQuickTrade }) {
      const [chartType, setChartType] = useState('candles');
      const [timeframe, setTimeframe] = useState('1M');
      const [showMA, setShowMA] = useState(true);
      const [showRSI, setShowRSI] = useState(false);
      const [sectorFilter, setSectorFilter] = useState('ALL');
      const canvasRef = useRef(null);

      // Render chart on canvas
      useEffect(() => {
        if (!canvasRef.current) return;
        const ctx = canvasRef.current.getContext('2d');
        const width = canvasRef.current.width;
        const height = canvasRef.current.height;

        ctx.clearRect(0, 0, width, height);

        // Draw grid lines
        ctx.strokeStyle = '#263244';
        ctx.lineWidth = 0.5;
        for (let y = 30; y < height; y += 40) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(width, y);
          ctx.stroke();
        }

        // Draw simulated trend line or candles
        const dataPoints = [stock.close * 0.94, stock.close * 0.96, stock.close * 0.93, stock.close * 0.97, stock.close * 0.99, stock.price];
        const step = width / (dataPoints.length - 1);

        if (chartType === 'line') {
          ctx.strokeStyle = stock.change >= 0 ? '#22C55E' : '#EF4444';
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          dataPoints.forEach((val, i) => {
            const min = Math.min(...dataPoints);
            const max = Math.max(...dataPoints);
            const y = height - 20 - ((val - min) / (max - min || 1)) * (height - 40);
            if (i === 0) ctx.moveTo(0, y);
            else ctx.lineTo(i * step, y);
          });
          ctx.stroke();
        } else {
          // Candlestick render simulation
          dataPoints.forEach((val, i) => {
            const min = stock.close * 0.90;
            const max = stock.close * 1.05;
            const yOpen = height - 20 - (((val * 0.99) - min) / (max - min)) * (height - 40);
            const yClose = height - 20 - ((val - min) / (max - min)) * (height - 40);
            const isGreen = yClose <= yOpen;
            const x = i * step + 15;

            ctx.strokeStyle = isGreen ? '#22C55E' : '#EF4444';
            ctx.fillStyle = isGreen ? '#22C55E' : '#EF4444';
            ctx.lineWidth = 1.5;

            // Wick
            ctx.beginPath();
            ctx.moveTo(x, yOpen - 15);
            ctx.lineTo(x, yClose + 15);
            ctx.stroke();

            // Body
            ctx.fillRect(x - 8, Math.min(yOpen, yClose), 16, Math.max(Math.abs(yClose - yOpen), 4));
          });
        }
      }, [stock, chartType, timeframe]);

      const filteredStocks = MOCK_STOCKS.filter(s => sectorFilter === 'ALL' || s.sector === sectorFilter);

      return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LEFT: STOCK DIRECTORY LIST */}
          <div className="bg-brand-card rounded-xl border border-brand-border p-4 h-[750px] flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white">Equities Directory</h3>
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                className="bg-brand-bg border border-brand-border rounded px-2 py-1 text-xs text-brand-muted focus:outline-none"
              >
                <option value="ALL">All Sectors</option>
                <option value="Banking">Banking</option>
                <option value="IT">IT</option>
                <option value="Automobile">Automobile</option>
                <option value="Pharma">Pharma</option>
                <option value="FMCG">FMCG</option>
                <option value="Energy">Energy</option>
              </select>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {filteredStocks.map((stk) => (
                <div
                  key={stk.symbol}
                  onClick={() => onSelectStock(stk)}
                  className={`p-3 rounded-lg cursor-pointer border transition ${
                    stock.symbol === stk.symbol
                      ? 'bg-brand-blue/15 border-brand-blue text-white'
                      : 'bg-brand-bg border-brand-border/40 hover:bg-brand-cardHover text-brand-muted'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-bold text-sm text-white flex items-center gap-1.5">
                        {stk.symbol}
                        <span className="text-[9px] bg-brand-border px-1 rounded text-brand-muted">{stk.exchange}</span>
                      </div>
                      <div className="text-xs text-brand-muted truncate max-w-[140px]">{stk.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-white">₹{stk.price.toFixed(2)}</div>
                      <div className={`text-[11px] font-semibold ${stk.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                        {stk.change >= 0 ? '+' : ''}{stk.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT: INTERACTIVE STOCK DETAIL & CHART */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header & Quick Action */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold text-white">{stock.symbol}</h2>
                  <span className="text-xs bg-brand-blue/20 text-brand-blue px-2 py-0.5 rounded font-bold">{stock.exchange}</span>
                  <span className="text-xs bg-brand-border text-brand-muted px-2 py-0.5 rounded">{stock.sector}</span>
                </div>
                <p className="text-xs text-brand-muted mt-1">{stock.name}</p>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right mr-2">
                  <div className="text-2xl font-bold text-white">₹{stock.price.toFixed(2)}</div>
                  <div className={`text-xs font-semibold ${stock.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                  </div>
                </div>
                <button
                  onClick={() => onAddToWatchlist(stock)}
                  className="p-2.5 bg-brand-bg border border-brand-border hover:bg-brand-cardHover rounded-lg text-brand-muted hover:text-white"
                  title="Add to Watchlist"
                >
                  <i data-lucide="bookmark" className="w-5 h-5"></i>
                </button>
                <button
                  onClick={() => onQuickTrade(stock)}
                  className="px-4 py-2.5 bg-brand-blue hover:bg-blue-600 text-white font-bold text-xs rounded-lg shadow"
                >
                  Trade Paper
                </button>
              </div>
            </div>

            {/* FINANCIAL CHART CARD */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
              {/* Chart Controls Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-brand-border/60">
                {/* Timeframe Selectors */}
                <div className="flex bg-brand-bg rounded-lg border border-brand-border p-1">
                  {['1D', '1W', '1M', '3M', '6M', '1Y', '5Y'].map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setTimeframe(tf)}
                      className={`px-2.5 py-1 rounded text-xs font-semibold transition ${
                        timeframe === tf ? 'bg-brand-blue text-white' : 'text-brand-muted hover:text-white'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>

                {/* Chart Type & Indicator Toggles */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setChartType(chartType === 'candles' ? 'line' : 'candles')}
                    className="px-3 py-1 bg-brand-bg border border-brand-border rounded text-xs text-brand-muted hover:text-white font-medium"
                  >
                    Type: {chartType.toUpperCase()}
                  </button>
                  <button
                    onClick={() => setShowMA(!showMA)}
                    className={`px-3 py-1 border rounded text-xs font-medium ${showMA ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-brand-bg border-brand-border text-brand-muted'}`}
                  >
                    MA (20)
                  </button>
                  <button
                    onClick={() => setShowRSI(!showRSI)}
                    className={`px-3 py-1 border rounded text-xs font-medium ${showRSI ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-brand-bg border-brand-border text-brand-muted'}`}
                  >
                    RSI ({stock.rsi})
                  </button>
                </div>
              </div>

              {/* Chart Canvas */}
              <div className="relative w-full h-64 bg-brand-bg rounded-lg border border-brand-border/40 p-2">
                <canvas ref={canvasRef} width={650} height={240} className="w-full h-full object-contain" />
              </div>

              <div className="mt-2 text-[10px] text-brand-muted text-right">
                Real-time 15-min delayed feed • Timestamp: {new Date().toLocaleTimeString('en-IN')} IST
              </div>
            </div>

            {/* KEY METRICS GRID */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border">
              <h3 className="text-sm font-bold text-white mb-4">Fundamental Statistics</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="bg-brand-bg p-3 rounded-lg border border-brand-border/40">
                  <div className="text-brand-muted">Market Cap</div>
                  <div className="font-bold text-white mt-1">{stock.mcap}</div>
                </div>
                <div className="bg-brand-bg p-3 rounded-lg border border-brand-border/40">
                  <div className="text-brand-muted">P/E Ratio</div>
                  <div className="font-bold text-white mt-1">{stock.pe}</div>
                </div>
                <div className="bg-brand-bg p-3 rounded-lg border border-brand-border/40">
                  <div className="text-brand-muted">ROE</div>
                  <div className="font-bold text-emerald-400 mt-1">{stock.roe}</div>
                </div>
                <div className="bg-brand-bg p-3 rounded-lg border border-brand-border/40">
                  <div className="text-brand-muted">52-Wk High / Low</div>
                  <div className="font-bold text-white mt-1">₹{stock.high52w} / ₹{stock.low52w}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // --- 3. WATCHLIST VIEW COMPONENT ---
    function WatchlistView({ watchlists, activeWatchlistId, setActiveWatchlistId, onCreateWatchlist, onRemoveFromWatchlist, onSelectStock }) {
      const [newWlName, setNewWlName] = useState('');
      const activeWl = watchlists.find(w => w.id === activeWatchlistId) || watchlists[0];

      return (
        <div className="space-y-6">
          {/* Top Bar: Tabs & Create Watchlist */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-brand-card p-4 rounded-xl border border-brand-border">
            <div className="flex items-center gap-2 overflow-x-auto">
              {watchlists.map(w => (
                <button
                  key={w.id}
                  onClick={() => setActiveWatchlistId(w.id)}
                  className={`px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                    activeWatchlistId === w.id
                      ? 'bg-brand-blue text-white shadow'
                      : 'bg-brand-bg text-brand-muted hover:text-white border border-brand-border'
                  }`}
                >
                  {w.name} ({w.symbols.length})
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="New Watchlist Name..."
                value={newWlName}
                onChange={(e) => setNewWlName(e.target.value)}
                className="bg-brand-bg border border-brand-border rounded px-3 py-1.5 text-xs text-white placeholder-brand-muted focus:outline-none"
              />
              <button
                onClick={() => {
                  if (newWlName.trim()) {
                    onCreateWatchlist(newWlName.trim());
                    setNewWlName('');
                  }
                }}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold"
              >
                + Create
              </button>
            </div>
          </div>

          {/* WATCHLIST TABLE */}
          <div className="bg-brand-card rounded-xl border border-brand-border overflow-hidden">
            <div className="p-4 border-b border-brand-border flex justify-between items-center">
              <h3 className="font-bold text-sm text-white">{activeWl.name} Directory</h3>
              <span className="text-xs text-brand-muted">Auto-refreshes via Websocket</span>
            </div>

            {activeWl.symbols.length === 0 ? (
              <div className="p-12 text-center text-brand-muted">
                <i data-lucide="bookmark" className="w-8 h-8 mx-auto mb-2 opacity-40"></i>
                <p className="text-sm">No stocks added to this watchlist yet.</p>
                <p className="text-xs mt-1">Search stocks using the top search bar to add them here.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-brand-muted">
                  <thead className="bg-brand-sidebar uppercase font-semibold text-brand-muted border-b border-brand-border">
                    <tr>
                      <th className="p-4">Symbol</th>
                      <th className="p-4">Company Name</th>
                      <th className="p-4 text-right">LTP (₹)</th>
                      <th className="p-4 text-right">24h Change</th>
                      <th className="p-4 text-right">Volume</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border/40">
                    {activeWl.symbols.map(sym => {
                      const stk = MOCK_STOCKS.find(s => s.symbol === sym) || { symbol: sym, name: sym, price: 0, change: 0, changePercent: 0, volume: '-' };
                      const isPos = stk.change >= 0;
                      return (
                        <tr key={sym} className="hover:bg-brand-cardHover">
                          <td className="p-4 font-bold text-white flex items-center gap-2">
                            {stk.symbol}
                            <span className="text-[9px] bg-brand-border px-1 rounded">{stk.exchange || 'NSE'}</span>
                          </td>
                          <td className="p-4 text-brand-text">{stk.name}</td>
                          <td className="p-4 text-right font-bold text-white">₹{stk.price.toFixed(2)}</td>
                          <td className={`p-4 text-right font-semibold ${isPos ? 'text-brand-green' : 'text-brand-red'}`}>
                            {isPos ? '+' : ''}{stk.changePercent.toFixed(2)}%
                          </td>
                          <td className="p-4 text-right">{stk.volume}</td>
                          <td className="p-4 text-right space-x-2">
                            <button
                              onClick={() => onSelectStock(sym)}
                              className="px-2.5 py-1 bg-brand-blue/20 text-brand-blue rounded hover:bg-brand-blue hover:text-white transition font-medium"
                            >
                              Inspect
                            </button>
                            <button
                              onClick={() => onRemoveFromWatchlist(sym)}
                              className="p-1 bg-red-500/10 text-brand-red rounded hover:bg-red-500 hover:text-white transition"
                              title="Remove"
                            >
                              <i data-lucide="trash-2" className="w-3.5 h-3.5"></i>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      );
    }

    // --- 4. MY PORTFOLIO VIEW COMPONENT ---
    function PortfolioView({ summary, onAddTransaction }) {
      const [showModal, setShowModal] = useState(false);
      const [txType, setTxType] = useState('BUY');
      const [symbol, setSymbol] = useState('RELIANCE');
      const [qty, setQty] = useState(10);
      const [price, setPrice] = useState(2945.50);

      const isPos = summary.totalUnrealizedPnL >= 0;

      return (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Total Invested</div>
              <div className="text-2xl font-bold text-white mt-1">₹{summary.totalInvested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="text-[10px] text-brand-muted mt-2">Cost basis method: Average Cost</div>
            </div>

            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Current Value</div>
              <div className="text-2xl font-bold text-white mt-1">₹{summary.currentValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="text-[10px] text-brand-muted mt-2">Live market evaluation</div>
            </div>

            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Unrealized P&L</div>
              <div className={`text-2xl font-bold mt-1 ${isPos ? 'text-brand-green' : 'text-brand-red'}`}>
                {isPos ? '+' : ''}₹{summary.totalUnrealizedPnL.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <div className={`text-[10px] font-semibold mt-2 ${isPos ? 'text-brand-green' : 'text-brand-red'}`}>
                {isPos ? '▲' : '▼'} {summary.overallReturnPercent.toFixed(2)}% overall return
              </div>
            </div>

            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Realized P&L</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">₹{summary.totalRealizedPnL.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="text-[10px] text-brand-muted mt-2">From closed transactions</div>
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-white">Equities Holdings ({summary.holdings.length})</h3>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-brand-blue hover:bg-blue-600 text-white rounded-lg text-xs font-bold shadow flex items-center gap-1.5"
            >
              <i data-lucide="plus-circle" className="w-4 h-4"></i> Add Transaction
            </button>
          </div>

          {/* Holdings Table */}
          <div className="bg-brand-card rounded-xl border border-brand-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-brand-muted">
                <thead className="bg-brand-sidebar uppercase font-semibold text-brand-muted border-b border-brand-border">
                  <tr>
                    <th className="p-4">Stock</th>
                    <th className="p-4 text-right">Quantity</th>
                    <th className="p-4 text-right">Avg Cost (₹)</th>
                    <th className="p-4 text-right">LTP (₹)</th>
                    <th className="p-4 text-right">Current Value</th>
                    <th className="p-4 text-right">Unrealized P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/40">
                  {summary.holdings.map((h) => {
                    const hPos = h.unrealizedPnL >= 0;
                    return (
                      <tr key={h.symbol} className="hover:bg-brand-cardHover">
                        <td className="p-4">
                          <div className="font-bold text-white">{h.symbol}</div>
                          <div className="text-[10px] text-brand-muted">{h.companyName}</div>
                        </td>
                        <td className="p-4 text-right font-medium text-white">{h.qty}</td>
                        <td className="p-4 text-right font-medium">₹{h.avgPrice.toFixed(2)}</td>
                        <td className="p-4 text-right font-bold text-white">₹{h.currentPrice.toFixed(2)}</td>
                        <td className="p-4 text-right font-bold text-white">₹{h.currentValue.toLocaleString('en-IN')}</td>
                        <td className={`p-4 text-right font-semibold ${hPos ? 'text-brand-green' : 'text-brand-red'}`}>
                          {hPos ? '+' : ''}₹{h.unrealizedPnL.toFixed(2)} ({hPos ? '+' : ''}{h.unrealizedPnLPercent.toFixed(2)}%)
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* ADD TRANSACTION MODAL */}
          {showModal && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-brand-card border border-brand-border rounded-xl w-full max-w-md p-6 space-y-4">
                <div className="flex justify-between items-center border-b border-brand-border pb-3">
                  <h3 className="font-bold text-white text-sm">Record Portfolio Transaction</h3>
                  <button onClick={() => setShowModal(false)} className="text-brand-muted hover:text-white">✕</button>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-brand-muted mb-1">Type</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => setTxType('BUY')}
                        className={`py-2 rounded font-bold ${txType === 'BUY' ? 'bg-emerald-600 text-white' : 'bg-brand-bg text-brand-muted'}`}
                      >
                        BUY
                      </button>
                      <button
                        onClick={() => setTxType('SELL')}
                        className={`py-2 rounded font-bold ${txType === 'SELL' ? 'bg-red-600 text-white' : 'bg-brand-bg text-brand-muted'}`}
                      >
                        SELL
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-brand-muted mb-1">Stock Ticker</label>
                    <select
                      value={symbol}
                      onChange={(e) => setSymbol(e.target.value)}
                      className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                    >
                      {MOCK_STOCKS.map(s => <option key={s.symbol} value={s.symbol}>{s.symbol} - {s.name}</option>)}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-brand-muted mb-1">Quantity</label>
                      <input
                        type="number"
                        value={qty}
                        onChange={(e) => setQty(Number(e.target.value))}
                        className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-brand-muted mb-1">Price per Share (₹)</label>
                      <input
                        type="number"
                        value={price}
                        onChange={(e) => setPrice(Number(e.target.value))}
                        className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-brand-border">
                  <button onClick={() => setShowModal(false)} className="px-4 py-2 bg-brand-bg text-brand-muted rounded text-xs font-semibold">
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      onAddTransaction({ symbol, type: txType, qty: Number(qty), price: Number(price), date: new Date().toISOString().split('T')[0], exchange: 'NSE' });
                      setShowModal(false);
                    }}
                    className="px-4 py-2 bg-brand-blue text-white rounded text-xs font-bold"
                  >
                    Confirm Order
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }

    // --- 5. AI STOCK ANALYST VIEW COMPONENT (GEMINI INTEGRATION) ---
    function AIAnalystView({ selectedStock, geminiApiKey }) {
      const [stockToAnalyze, setStockToAnalyze] = useState(selectedStock.symbol);
      const [loading, setLoading] = useState(false);
      const [aiReport, setAiReport] = useState(null);
      const [chatMessages, setChatMessages] = useState([
        { sender: 'ai', text: `Hello! I am StockPulse Gemini AI Assistant. Ask me anything about financial metrics, technical indicators, or growth potential for Indian companies like ${selectedStock.symbol}.` }
      ]);
      const [inputQuery, setInputQuery] = useState('');

      const generateReport = async () => {
        setLoading(true);
        const target = MOCK_STOCKS.find(s => s.symbol === stockToAnalyze) || selectedStock;

        // Structured prompt to Gemini
        const prompt = `Act as a senior Indian stock analyst. Generate a detailed analysis for ${target.name} (${target.symbol} traded on ${target.exchange}).
        Use verified data: Current Price ₹${target.price}, P/E: ${target.pe}, ROE: ${target.roe}, 52W High: ₹${target.high52w}, 52W Low: ₹${target.low52w}, RSI: ${target.rsi}.
        Return 5 sections:
        1. Company Overview
        2. Fundamental Analysis
        3. Technical Analysis
        4. Risk Analysis
        5. AI Summary (Bullish/Bearish scenario)`;

        try {
          if (geminiApiKey.trim()) {
            // Live Gemini API Call
            const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${geminiApiKey}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }] }]
              })
            });
            const data = await res.json();
            const responseText = data.candidates?.[0]?.content?.parts?.[0]?.text || 'Error parsing Gemini response.';

            setAiReport({
              symbol: target.symbol,
              companyName: target.name,
              rawText: responseText,
              timestamp: new Date().toLocaleString()
            });
          } else {
            // Demo fallback report
            await new Promise(r => setTimeout(r, 1200));
            setAiReport({
              symbol: target.symbol,
              companyName: target.name,
              overview: `${target.name} is a market leader in the ${target.sector} segment in India with a strong market position and extensive domestic distribution network.`,
              fundamentals: `P/E stands at ${target.pe} with impressive Return on Equity (ROE) of ${target.roe}. Debt to equity remains healthy at ${target.debtEquity}.`,
              technicals: `Stock RSI is at ${target.rsi} indicating ${target.rsi > 60 ? 'overbought momentum' : 'neutral consolidation'}. Moving averages present a ${target.macd} structure.`,
              risks: `Regulatory shifts in India, raw material price volatility, and foreign institutional investor (FII) cash outflows pose key short-term headwinds.`,
              summary: `BULLISH CASE: Sustained margin expansion and earnings growth above 15% CAGR.\nBEARISH CASE: Macro slowdown reducing volume demand.`,
              timestamp: new Date().toLocaleString()
            });
          }
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
      };

      const handleSendChat = () => {
        if (!inputQuery.trim()) return;
        const userMsg = inputQuery;
        setChatMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
        setInputQuery('');

        setTimeout(() => {
          setChatMessages(prev => [
            ...prev,
            { sender: 'ai', text: `Based on financial data for ${stockToAnalyze}: ${userMsg.toLowerCase().includes('pe') ? `The current P/E is ${selectedStock.pe}, which is aligned with sector averages.` : 'Sustained quarterly EBITDA margins and low debt ratios support long-term investment resilience.'}` }
          ]);
        }, 800);
      };

      return (
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-brand-sidebar via-brand-card to-indigo-950 p-6 rounded-xl border border-brand-border flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <i data-lucide="sparkles" className="w-5 h-5 text-amber-400"></i>
                <h2 className="text-xl font-bold text-white">StockPulse AI Financial Analyst</h2>
              </div>
              <p className="text-xs text-brand-muted mt-1">Deep fundamental, technical, and risk analysis powered by Google Gemini API</p>
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto">
              <select
                value={stockToAnalyze}
                onChange={(e) => setStockToAnalyze(e.target.value)}
                className="bg-brand-bg border border-brand-border rounded px-3 py-2 text-xs text-white"
              >
                {MOCK_STOCKS.map(s => <option key={s.symbol} value={s.symbol}>{s.symbol} - {s.name}</option>)}
              </select>
              <button
                onClick={generateReport}
                disabled={loading}
                className="px-4 py-2 bg-brand-blue hover:bg-blue-600 text-white rounded text-xs font-bold shadow flex items-center gap-1.5 whitespace-nowrap"
              >
                {loading ? 'Analyzing...' : 'Generate AI Report'}
              </button>
            </div>
          </div>

          {/* REPORT & CHAT LAYOUT */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* LEFT: REPORT DISPLAY */}
            <div className="lg:col-span-2 space-y-4">
              {loading ? (
                <div className="bg-brand-card p-12 rounded-xl border border-brand-border text-center">
                  <div className="w-10 h-10 border-4 border-brand-blue border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-sm font-semibold text-white">Evaluating Indian Financial Disclosures...</p>
                  <p className="text-xs text-brand-muted mt-1">Extracting P/E ratios, technical indicators & market risks</p>
                </div>
              ) : aiReport ? (
                <div className="bg-brand-card p-6 rounded-xl border border-brand-border space-y-6">
                  <div className="flex justify-between items-center border-b border-brand-border pb-3">
                    <div>
                      <h3 className="font-bold text-lg text-white">{aiReport.symbol} - Comprehensive Analysis</h3>
                      <p className="text-xs text-brand-muted">{aiReport.companyName}</p>
                    </div>
                    <span className="text-[10px] text-brand-muted bg-brand-bg px-2 py-1 rounded">
                      Timestamp: {aiReport.timestamp}
                    </span>
                  </div>

                  {aiReport.rawText ? (
                    <div className="text-xs text-brand-text whitespace-pre-line leading-relaxed">
                      {aiReport.rawText}
                    </div>
                  ) : (
                    <div className="space-y-4 text-xs">
                      <div className="bg-brand-bg p-4 rounded-lg border border-brand-border/60">
                        <h4 className="font-bold text-brand-blue mb-1">A. Company Overview</h4>
                        <p className="text-brand-text">{aiReport.overview}</p>
                      </div>

                      <div className="bg-brand-bg p-4 rounded-lg border border-brand-border/60">
                        <h4 className="font-bold text-emerald-400 mb-1">B. Fundamental Analysis</h4>
                        <p className="text-brand-text">{aiReport.fundamentals}</p>
                      </div>

                      <div className="bg-brand-bg p-4 rounded-lg border border-brand-border/60">
                        <h4 className="font-bold text-purple-400 mb-1">C. Technical Analysis</h4>
                        <p className="text-brand-text">{aiReport.technicals}</p>
                      </div>

                      <div className="bg-brand-bg p-4 rounded-lg border border-brand-border/60">
                        <h4 className="font-bold text-red-400 mb-1">D. Risk Analysis</h4>
                        <p className="text-brand-text">{aiReport.risks}</p>
                      </div>

                      <div className="bg-brand-bg p-4 rounded-lg border border-brand-border/60">
                        <h4 className="font-bold text-amber-400 mb-1">E. AI Summary & Scenarios</h4>
                        <p className="text-brand-text whitespace-pre-line">{aiReport.summary}</p>
                      </div>
                    </div>
                  )}

                  {/* Financial Disclaimer */}
                  <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-lg text-[11px] text-amber-300/80">
                    <strong>Educational Disclaimer:</strong> AI-generated reports are strictly for informational purposes and do not constitute registered SEBI financial advice or personalized buy/sell recommendations.
                  </div>
                </div>
              ) : (
                <div className="bg-brand-card p-12 rounded-xl border border-brand-border text-center text-brand-muted">
                  <i data-lucide="sparkles" className="w-10 h-10 mx-auto mb-3 text-brand-blue opacity-50"></i>
                  <p className="text-sm font-semibold text-white">No AI Report Generated Yet</p>
                  <p className="text-xs mt-1">Select a company above and click "Generate AI Report" to view insights.</p>
                </div>
              )}
            </div>

            {/* RIGHT: CONVERSATIONAL AI CHAT */}
            <div className="bg-brand-card rounded-xl border border-brand-border flex flex-col h-[550px]">
              <div className="p-4 border-b border-brand-border flex items-center gap-2">
                <i data-lucide="bot" className="w-4 h-4 text-brand-blue"></i>
                <h3 className="font-bold text-xs text-white">Ask Gemini Financial Assistant</h3>
              </div>

              {/* Chat Thread */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-xl ${
                      msg.sender === 'user' ? 'bg-brand-blue text-white rounded-br-none' : 'bg-brand-bg border border-brand-border text-brand-text rounded-bl-none'
                    }`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t border-brand-border flex items-center gap-2 bg-brand-sidebar">
                <input
                  type="text"
                  placeholder="Ask a question (e.g., Explain P/E ratio)..."
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                  className="flex-1 bg-brand-bg border border-brand-border rounded px-3 py-2 text-xs text-white placeholder-brand-muted focus:outline-none"
                />
                <button onClick={handleSendChat} className="p-2 bg-brand-blue text-white rounded hover:bg-blue-600">
                  <i data-lucide="send" className="w-4 h-4"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // --- 6. VIRTUAL PAPER TRADING SIMULATOR VIEW ---
    function VirtualTradingView({ account, selectedStock, onExecuteTrade }) {
      const [tradeSymbol, setTradeSymbol] = useState(selectedStock.symbol);
      const [orderType, setOrderType] = useState('BUY');
      const [qty, setQty] = useState(10);
      const activeStock = MOCK_STOCKS.find(s => s.symbol === tradeSymbol) || selectedStock;
      const orderValue = qty * activeStock.price;

      return (
        <div className="space-y-6">
          {/* Account Metrics Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Virtual Cash Balance</div>
              <div className="text-2xl font-bold text-white mt-1">₹{account.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="text-[10px] text-emerald-400 mt-1">Simulated Paper Trading Capital</div>
            </div>

            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Total Executed Orders</div>
              <div className="text-2xl font-bold text-white mt-1">{account.trades.length}</div>
              <div className="text-[10px] text-brand-muted mt-1">Real-time trade validation active</div>
            </div>

            <div className="bg-brand-card p-4 rounded-xl border border-brand-border">
              <div className="text-xs text-brand-muted">Leaderboard Rank</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">#14</div>
              <div className="text-[10px] text-brand-muted mt-1">Among 1,240 Indian paper traders</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* ORDER EXECUTION CARD */}
            <div className="bg-brand-card p-5 rounded-xl border border-brand-border space-y-4">
              <h3 className="font-bold text-sm text-white border-b border-brand-border pb-3">Place Paper Order</h3>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setOrderType('BUY')}
                  className={`py-2 rounded font-bold text-xs ${orderType === 'BUY' ? 'bg-emerald-600 text-white' : 'bg-brand-bg text-brand-muted'}`}
                >
                  BUY (PAPER)
                </button>
                <button
                  onClick={() => setOrderType('SELL')}
                  className={`py-2 rounded font-bold text-xs ${orderType === 'SELL' ? 'bg-red-600 text-white' : 'bg-brand-bg text-brand-muted'}`}
                >
                  SELL (PAPER)
                </button>
              </div>

              <div className="text-xs space-y-3">
                <div>
                  <label className="block text-brand-muted mb-1">Select Asset</label>
                  <select
                    value={tradeSymbol}
                    onChange={(e) => setTradeSymbol(e.target.value)}
                    className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white font-bold"
                  >
                    {MOCK_STOCKS.map(s => <option key={s.symbol} value={s.symbol}>{s.symbol} - ₹{s.price}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-brand-muted mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={qty}
                    onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
                    className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white font-bold"
                  />
                </div>

                <div className="p-3 bg-brand-bg rounded-lg border border-brand-border/60 space-y-1">
                  <div className="flex justify-between text-brand-muted">
                    <span>LTP Price</span>
                    <span className="text-white font-semibold">₹{activeStock.price.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-brand-muted border-t border-brand-border/40 pt-1 mt-1">
                    <span>Est. Order Value</span>
                    <span className="text-white font-bold">₹{orderValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>

                <button
                  onClick={() => onExecuteTrade({ symbol: tradeSymbol, type: orderType, qty, price: activeStock.price })}
                  className={`w-full py-3 rounded-lg font-bold text-xs shadow transition ${
                    orderType === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-red-600 hover:bg-red-500 text-white'
                  }`}
                >
                  Execute Simulated Order
                </button>
              </div>
            </div>

            {/* TRANSACTION HISTORY LOG */}
            <div className="lg:col-span-2 bg-brand-card rounded-xl border border-brand-border p-5 flex flex-col">
              <h3 className="font-bold text-sm text-white mb-4">Simulated Trade Ledger</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-brand-muted">
                  <thead className="bg-brand-sidebar uppercase font-semibold text-brand-muted border-b border-brand-border">
                    <tr>
                      <th className="p-3">Time</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Symbol</th>
                      <th className="p-3 text-right">Qty</th>
                      <th className="p-3 text-right">Price (₹)</th>
                      <th className="p-3 text-right">Total (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border/40">
                    {account.trades.map((t) => (
                      <tr key={t.id} className="hover:bg-brand-cardHover">
                        <td className="p-3">{t.timestamp}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${t.type === 'BUY' ? 'bg-emerald-500/20 text-brand-green' : 'bg-red-500/20 text-brand-red'}`}>
                            {t.type}
                          </span>
                        </td>
                        <td className="p-3 font-bold text-white">{t.symbol}</td>
                        <td className="p-3 text-right text-white font-semibold">{t.qty}</td>
                        <td className="p-3 text-right">₹{t.price.toFixed(2)}</td>
                        <td className="p-3 text-right font-bold text-white">₹{t.total.toLocaleString('en-IN')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // --- 7. MARKET NEWS VIEW COMPONENT ---
    function NewsView() {
      const [selectedCategory, setSelectedCategory] = useState('ALL');

      const filteredNews = MOCK_NEWS.filter(n => selectedCategory === 'ALL' || n.category.toLowerCase() === selectedCategory.toLowerCase());

      return (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="flex items-center gap-2 overflow-x-auto bg-brand-card p-3 rounded-xl border border-brand-border">
            {['ALL', 'Indian stock market', 'Company', 'Technology', 'Economy', 'IPO'].map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                  selectedCategory === cat ? 'bg-brand-blue text-white' : 'bg-brand-bg text-brand-muted hover:text-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* NEWS FEED CARDS */}
          <div className="space-y-4">
            {filteredNews.map((news) => (
              <div key={news.id} className="bg-brand-card p-5 rounded-xl border border-brand-border hover:border-brand-blue/40 transition space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-bold text-brand-blue">{news.source}</span>
                    <span className="text-brand-muted">• {news.time}</span>
                    <span className="bg-brand-border px-2 py-0.5 rounded text-[10px] text-brand-muted">{news.category}</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    news.sentiment === 'Bullish' ? 'bg-emerald-500/20 text-brand-green' :
                    news.sentiment === 'Bearish' ? 'bg-red-500/20 text-brand-red' : 'bg-gray-700 text-gray-300'
                  }`}>
                    {news.sentiment}
                  </span>
                </div>

                <h3 className="font-bold text-white text-base hover:text-brand-blue cursor-pointer">{news.headline}</h3>
                <p className="text-xs text-brand-muted leading-relaxed">{news.summary}</p>

                <div className="pt-2 flex items-center gap-2 text-[11px] text-brand-blue font-semibold cursor-pointer">
                  <span>Read Verified Publisher Article</span>
                  <i data-lucide="external-link" className="w-3.5 h-3.5"></i>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // --- 8. IPO CENTER VIEW COMPONENT ---
    function IPOCenterView() {
      return (
        <div className="space-y-6">
          <div className="bg-brand-card p-5 rounded-xl border border-brand-border flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white">NSE & BSE IPO Tracker</h2>
              <p className="text-xs text-brand-muted">Mainboard and SME Initial Public Offerings status and subscription rates</p>
            </div>
            <span className="text-xs bg-brand-blue/20 text-brand-blue px-3 py-1 rounded-full font-bold">Q4 FY24 Live Data</span>
          </div>

          <div className="bg-brand-card rounded-xl border border-brand-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-brand-muted">
                <thead className="bg-brand-sidebar uppercase font-semibold text-brand-muted border-b border-brand-border">
                  <tr>
                    <th className="p-4">Company Name</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Price Band</th>
                    <th className="p-4 text-right">Lot Size</th>
                    <th className="p-4 text-right">Issue Size</th>
                    <th className="p-4 text-right">Sub. Rate</th>
                    <th className="p-4 text-right">Listing Gain</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/40">
                  {MOCK_IPOS.map((ipo) => (
                    <tr key={ipo.id} className="hover:bg-brand-cardHover">
                      <td className="p-4 font-bold text-white">{ipo.name}</td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ipo.status === 'Open' ? 'bg-emerald-500/20 text-brand-green' :
                          ipo.status === 'Upcoming' ? 'bg-blue-500/20 text-brand-blue' : 'bg-gray-800 text-gray-400'
                        }`}>
                          {ipo.status}
                        </span>
                      </td>
                      <td className="p-4 text-right text-white font-medium">{ipo.priceRange}</td>
                      <td className="p-4 text-right">{ipo.lotSize} shares</td>
                      <td className="p-4 text-right font-semibold text-white">{ipo.issueSize}</td>
                      <td className="p-4 text-right font-bold text-amber-400">{ipo.subscription}</td>
                      <td className={`p-4 text-right font-bold ${ipo.listingGain.startsWith('+') ? 'text-brand-green' : 'text-brand-red'}`}>
                        {ipo.listingGain}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    }

    // --- 9. PRICE ALERTS VIEW COMPONENT ---
    function AlertsView({ alerts, onAddAlert, onToggleAlert, onDeleteAlert }) {
      const [symbol, setSymbol] = useState('RELIANCE');
      const [condition, setCondition] = useState('ABOVE');
      const [targetPrice, setTargetPrice] = useState(3000);

      return (
        <div className="space-y-6">
          {/* Create Alert Card */}
          <div className="bg-brand-card p-5 rounded-xl border border-brand-border space-y-4">
            <h3 className="font-bold text-sm text-white">Create Stock Price Trigger Alert</h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="block text-brand-muted mb-1">Asset</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                >
                  {MOCK_STOCKS.map(s => <option key={s.symbol} value={s.symbol}>{s.symbol}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-brand-muted mb-1">Condition</label>
                <select
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                >
                  <option value="ABOVE">Price Rises Above (₹)</option>
                  <option value="BELOW">Price Drops Below (₹)</option>
                </select>
              </div>

              <div>
                <label className="block text-brand-muted mb-1">Target Price (₹)</label>
                <input
                  type="number"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(Number(e.target.value))}
                  className="w-full bg-brand-bg border border-brand-border rounded p-2 text-white"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => onAddAlert({ symbol, condition, targetPrice })}
                  className="w-full py-2 bg-brand-blue hover:bg-blue-600 text-white rounded font-bold text-xs shadow"
                >
                  + Add Alert
                </button>
              </div>
            </div>
          </div>

          {/* ACTIVE ALERTS TABLE */}
          <div className="bg-brand-card rounded-xl border border-brand-border overflow-hidden">
            <div className="p-4 border-b border-brand-border">
              <h3 className="font-bold text-sm text-white">Configured Alerts ({alerts.length})</h3>
            </div>
            <table className="w-full text-left text-xs text-brand-muted">
              <thead className="bg-brand-sidebar uppercase font-semibold text-brand-muted border-b border-brand-border">
                <tr>
                  <th className="p-4">Stock Symbol</th>
                  <th className="p-4">Trigger Condition</th>
                  <th className="p-4 text-right">Target Price</th>
                  <th className="p-4 text-right">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/40">
                {alerts.map((alt) => (
                  <tr key={alt.id} className="hover:bg-brand-cardHover">
                    <td className="p-4 font-bold text-white">{alt.symbol}</td>
                    <td className="p-4">{alt.condition === 'ABOVE' ? 'Price > Target' : 'Price < Target'}</td>
                    <td className="p-4 text-right font-bold text-white">₹{alt.targetPrice.toFixed(2)}</td>
                    <td className="p-4 text-right">
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${alt.active ? 'bg-emerald-500/20 text-brand-green' : 'bg-gray-800 text-gray-500'}`}>
                        {alt.active ? 'ACTIVE' : 'MUTED'}
                      </span>
                    </td>
                    <td className="p-4 text-right space-x-2">
                      <button
                        onClick={() => onToggleAlert(alt.id)}
                        className="px-2.5 py-1 bg-brand-bg border border-brand-border text-white rounded hover:bg-brand-cardHover text-[10px]"
                      >
                        Toggle
                      </button>
                      <button
                        onClick={() => onDeleteAlert(alt.id)}
                        className="p-1 bg-red-500/10 text-brand-red rounded hover:bg-red-500 hover:text-white"
                      >
                        <i data-lucide="trash-2" className="w-3.5 h-3.5"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // --- 10. SETTINGS & API ARCHITECTURE VIEW COMPONENT ---
    function SettingsView({ geminiApiKey, setGeminiApiKey, demoMode, setDemoMode, showToast }) {
      return (
        <div className="space-y-6">
          {/* API CONFIGURATION CARD */}
          <div className="bg-brand-card p-6 rounded-xl border border-brand-border space-y-4">
            <h3 className="font-bold text-base text-white border-b border-brand-border pb-3">Google Gemini API Integration</h3>
            <p className="text-xs text-brand-muted">Provide your Gemini API key to activate live generative stock analysis.</p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-brand-muted mb-1">Gemini API Key</label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  className="w-full bg-brand-bg border border-brand-border rounded p-2.5 text-xs text-white placeholder-brand-muted focus:outline-none focus:border-brand-blue"
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="demoToggle"
                  checked={demoMode}
                  onChange={(e) => setDemoMode(e.target.checked)}
                  className="rounded border-brand-border text-brand-blue focus:ring-0"
                />
                <label htmlFor="demoToggle" className="text-xs text-brand-text">Enable Demo Mode for Market Feeds (Uses offline simulated stock JSON)</label>
              </div>

              <button
                onClick={() => showToast('Settings updated successfully', 'success')}
                className="px-4 py-2 bg-brand-blue hover:bg-blue-600 text-white rounded text-xs font-bold shadow"
              >
                Save Preferences
              </button>
            </div>
          </div>

          {/* BACKEND REST API ENDPOINTS SCHEMA DOCS */}
          <div className="bg-brand-card p-6 rounded-xl border border-brand-border space-y-4">
            <h3 className="font-bold text-base text-white border-b border-brand-border pb-3">Node.js / Express / MongoDB API Architecture Inspector</h3>
            <div className="space-y-3 text-xs">
              {[
                { method: 'POST', endpoint: '/api/auth/login', desc: 'Authenticates user and returns JWT access token' },
                { method: 'GET', endpoint: '/api/market/stocks', desc: 'Returns cached quotes for NSE/BSE stocks' },
                { method: 'POST', endpoint: '/api/ai/analyze', desc: 'Proxy endpoint connecting backend to Gemini API' },
                { method: 'GET', endpoint: '/api/portfolio', desc: 'Fetches user transactions and computes average-cost holdings' },
                { method: 'POST', endpoint: '/api/virtual-trading/orders', desc: 'Validates cash balance and logs paper trade' }
              ].map((api, idx) => (
                <div key={idx} className="p-3 bg-brand-bg rounded-lg border border-brand-border/60 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${api.method === 'GET' ? 'bg-blue-500/20 text-brand-blue' : 'bg-emerald-500/20 text-brand-green'}`}>
                      {api.method}
                    </span>
                    <span className="font-mono text-white font-semibold">{api.endpoint}</span>
                  </div>
                  <span className="text-brand-muted text-[11px]">{api.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    // Mount Root App
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
