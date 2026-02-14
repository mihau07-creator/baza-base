const { useState, useEffect, useMemo } = React;

// Safe access to Recharts to prevent app crash if CDN fails
const RechartsObj = window.Recharts || null;
const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, ResponsiveContainer, Cell } = RechartsObj || {};

// Lucide Icons wrapper since CDN exposes them differently sometimes
// We will assume Lucide icons are safe to use as `lucide.createIcons()` or similar, 
// but for React components we might need to rely on standard SVGs if the wrapper isn't React-ready via simple CDN.
// Let's use simple SVG icons for reliability in this specific setup to avoid "module not found" or global scope issues.
const IconSearch = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>;
const IconFileText = () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>;
const IconReceipt = () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"></path><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"></path><path d="M12 17V7"></path></svg>;
const IconChevronDown = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>;
const IconChevronUp = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>;
const IconBarChart = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>;
const IconList = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>;

// --- Components ---

function FilterBar({ onFilterChange, sources, defaultRange = 'last30' }) {
    // Helper to get formatted date string YYYY-MM-DD
    const formatDate = (date) => date.toISOString().split('T')[0];

    // Helper to calculate ranges
    const getRange = (type) => {
        const end = new Date();
        const start = new Date();

        switch (type) {
            case 'today':
                break; // start is today
            case 'yesterday':
                start.setDate(start.getDate() - 1);
                end.setDate(end.getDate() - 1);
                break;
            case 'last7':
                start.setDate(start.getDate() - 7);
                break;
            case 'last14':
                start.setDate(start.getDate() - 14);
                break;
            case 'last28': // 4 weeks
                start.setDate(start.getDate() - 28);
                break;
            case 'last30':
                start.setDate(start.getDate() - 30);
                break;
            case 'thisMonth':
                start.setDate(1);
                break;
            case 'lastMonth':
                start.setMonth(start.getMonth() - 1);
                start.setDate(1);
                end.setDate(0); // Last day of previous month
                break;
            case 'thisQuarter':
                const quarter = Math.floor(start.getMonth() / 3);
                start.setMonth(quarter * 3);
                start.setDate(1);
                break;
            case 'lastQuarter':
                const prevQuarter = Math.floor(start.getMonth() / 3) - 1;
                if (prevQuarter < 0) {
                    start.setFullYear(start.getFullYear() - 1);
                    start.setMonth(9); // Oct
                } else {
                    start.setMonth(prevQuarter * 3);
                }
                start.setDate(1);
                // End of last quarter
                end.setTime(start.getTime()); // Copy start
                end.setMonth(end.getMonth() + 3);
                end.setDate(0);
                break;
            case 'thisYear':
                start.setMonth(0, 1);
                break;
            case 'lastYear':
                start.setFullYear(start.getFullYear() - 1);
                start.setMonth(0, 1);
                end.setFullYear(end.getFullYear() - 1);
                end.setMonth(11, 31);
                break;
            case 'allTime':
                return { from: '', to: '' };
            case 'custom':
                return null;
            default:
                start.setDate(start.getDate() - 30);
        }
        return { from: formatDate(start), to: formatDate(end) };
    };

    const [rangeType, setRangeType] = useState(defaultRange);
    const [filters, setFilters] = useState(() => {
        const range = getRange(defaultRange);
        return {
            dateFrom: range ? range.from : '',
            dateTo: range ? range.to : '',
            source: '',
            client: ''
        };
    });

    // Initialize parent with default filters on mount
    useEffect(() => {
        onFilterChange(filters);
    }, []);

    const handleRangeChange = (e) => {
        const type = e.target.value;
        setRangeType(type);
        const range = getRange(type);

        if (range) {
            const newFilters = { ...filters, dateFrom: range.from, dateTo: range.to };
            setFilters(newFilters);
            onFilterChange(newFilters);
        }
    };

    const handleChange = (key, value) => {
        const newFilters = { ...filters, [key]: value };
        // If user manually changes date, switch to 'custom'
        if (key === 'dateFrom' || key === 'dateTo') {
            setRangeType('custom');
        }
        setFilters(newFilters);
        onFilterChange(newFilters);
    };

    return (
        <div className="flex flex-wrap gap-4 items-center bg-gray-900/80 p-2 rounded-lg border border-gray-700 mb-4">
            <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">Zakres:</span>
                <select
                    className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                    value={rangeType}
                    onChange={handleRangeChange}
                >
                    <option value="today">Dzisiaj</option>
                    <option value="yesterday">Od wczoraj</option>
                    <option value="last7">Ostatnie 7 dni</option>
                    <option value="last14">Ostatnie 14 dni</option>
                    <option value="last28">Ostatnie 4 tygodnie (28 dni)</option>
                    <option value="last30">Ostatnie 30 dni</option>
                    <option value="thisMonth">Bieżący miesiąc</option>
                    <option value="lastMonth">Poprzedni miesiąc</option>
                    <option value="thisQuarter">Bieżący kwartał</option>
                    <option value="lastQuarter">Poprzedni kwartał</option>
                    <option value="thisYear">Bieżący rok</option>
                    <option value="lastYear">Poprzedni rok</option>
                    <option value="allTime">Od początku</option>
                    <option value="custom">Niestandardowy</option>
                </select>
            </div>

            <div className="h-6 w-px bg-gray-700 mx-2 hidden md:block"></div>

            <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">Data od:</span>
                <input
                    type="date"
                    className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                    value={filters.dateFrom}
                    onChange={e => handleChange('dateFrom', e.target.value)}
                />
            </div>
            <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">do:</span>
                <input
                    type="date"
                    className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                    value={filters.dateTo}
                    onChange={e => handleChange('dateTo', e.target.value)}
                />
            </div>

            <div className="h-6 w-px bg-gray-700 mx-2 hidden md:block"></div>

            <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">Firma/NIP:</span>
                <input
                    type="text"
                    placeholder="Wyszukaj..."
                    className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none w-32 md:w-40"
                    value={filters.client}
                    onChange={e => handleChange('client', e.target.value)}
                />
            </div>

            <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">Źródło:</span>
                <select
                    className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                    value={filters.source}
                    onChange={e => handleChange('source', e.target.value)}
                >
                    <option value="">Wszystkie</option>
                    {sources.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
            </div>

            <button
                onClick={() => {
                    handleRangeChange({ target: { value: 'last30' } }); // Reset to default
                    handleChange('client', '');
                    handleChange('source', '');
                }}
                className="text-xs text-red-400 hover:text-red-300 ml-auto px-2"
            >
                Resetuj
            </button>
        </div>
    );
}

function FileBadge({ type, orderId, exists, number }) {
    if (!exists) return <span className="text-gray-600 text-xs px-2 py-1 flex items-center gap-1 opacity-50 cursor-not-allowed"><span className="w-2 h-2 rounded-full bg-gray-600"></span>Brak</span>;

    const url = `/api/files/${orderId}/${type}`;
    const color = type === 'invoice' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30 hover:bg-blue-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30';
    const Icon = type === 'invoice' ? IconFileText : IconReceipt;
    const label = type === 'invoice' ? 'FV' : 'PAR';

    return (
        <a href={url} target="_blank" className={`flex items-center gap-2 px-2 py-1 rounded border transition-colors ${color} text-xs font-medium`}>
            <Icon />
            {label} {number || ''}
        </a>
    );
}

function OrderRow({ order }) {
    const [expanded, setExpanded] = useState(false);

    // Format date nicely
    const dateObj = new Date(order.date);
    const dateStr = dateObj.toLocaleDateString('pl-PL');
    const timeStr = dateObj.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });

    return (
        <>
            <tr className={`border-b border-gray-700/50 hover:bg-gray-800/50 transition-colors cursor-pointer text-sm ${expanded ? 'bg-blue-900/10' : ''}`} onClick={() => setExpanded(!expanded)}>
                <td className="p-3 font-mono text-blue-400 font-medium">
                    <div>{order.id}</div>
                    <div className="text-xs text-gray-500">{order.source}</div>
                </td>
                <td className="p-3 text-gray-300">
                    <div>{dateStr}</div>
                    <div className="text-xs text-gray-500">{timeStr}</div>
                </td>
                <td className="p-3">
                    <div className="font-semibold text-gray-200">{order.client_name}</div>
                    {(order.email || order.phone) && (
                        <div className="text-xs text-gray-400 mt-1">
                            {order.email && <div className="truncate max-w-[180px]" title={order.email}>{order.email}</div>}
                            {order.phone && <div>{order.phone.toString().replace('.0', '')}</div>}
                        </div>
                    )}
                </td>
                <td className="p-3 text-gray-300 text-xs">
                    {order.shipping_method ? (
                        <div>
                            <div className="font-medium text-gray-300">{order.shipping_method}</div>
                            <div className="text-gray-500">Koszt: {order.shipping_cost?.toFixed(2)}</div>
                        </div>
                    ) : <span className="text-gray-600">-</span>}
                </td>
                <td className="p-3 text-right font-medium text-emerald-400">
                    {order.total?.toFixed(2)} {order.currency}
                </td>
                <td className="p-3">
                    <div className="flex flex-col gap-1.5 items-start">
                        {order.invoice_path ?
                            <FileBadge type="invoice" orderId={order.id} exists={true} number={order.invoice_number} /> :
                            (order.invoice_number ? <span className="text-[10px] text-gray-500 border border-gray-700 px-1.5 py-0.5 rounded">FV (Brak)</span> : null)
                        }
                        {order.receipt_path ?
                            <FileBadge type="receipt" orderId={order.id} exists={true} number={order.receipt_number} /> :
                            (order.receipt_number ? <span className="text-[10px] text-gray-500 border border-gray-700 px-1.5 py-0.5 rounded">PAR (Brak)</span> : null)
                        }
                    </div>
                </td>
                <td className="p-3 text-gray-500 w-8">
                    {expanded ? <IconChevronUp className="w-4 h-4" /> : <IconChevronDown className="w-4 h-4" />}
                </td>
            </tr>
            {expanded && (
                <tr className="bg-gray-800/40 border-b border-gray-700/50">
                    <td colSpan="7" className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm animate-in fade-in duration-300">

                            {/* Column 1: Delivery & Payment */}
                            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 h-full">
                                <h4 className="text-blue-400 font-semibold mb-3 uppercase text-xs tracking-wider flex items-center gap-2">
                                    <IconReceipt /> Dostawa i Płatność
                                </h4>
                                <div className="space-y-2 text-gray-300">
                                    <div className="flex justify-between border-b border-gray-800 pb-1">
                                        <span className="text-gray-500">Metoda:</span>
                                        <span className="font-medium text-right">{order.shipping_method || '-'}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-gray-800 pb-1">
                                        <span className="text-gray-500">Koszt wysyłki:</span>
                                        <span>{order.shipping_cost?.toFixed(2)} {order.currency}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-gray-800 pb-1">
                                        <span className="text-gray-500">Razem do zapłaty:</span>
                                        <span className="text-emerald-400 font-bold">{order.total?.toFixed(2)} {order.currency}</span>
                                    </div>
                                    <div className="pt-2 text-xs text-gray-500">
                                        Źródło: {order.source}
                                    </div>
                                </div>
                            </div>

                            {/* Column 2: Client Data */}
                            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 h-full">
                                <h4 className="text-blue-400 font-semibold mb-3 uppercase text-xs tracking-wider flex items-center gap-2">
                                    <IconSearch /> Dane Klienta
                                </h4>
                                <div className="space-y-1 text-gray-300">
                                    <div className="font-medium text-white text-lg">{order.client_name}</div>
                                    {order.nip && <div className="text-emerald-400 font-mono text-xs bg-emerald-900/20 px-1 rounded w-max">NIP: {order.nip}</div>}
                                    <div className="pt-2 text-gray-400">{order.address}</div>
                                    <div className="pt-2 flex flex-col gap-1 text-xs">
                                        {order.email && <a href={`mailto:${order.email}`} className="text-blue-400 hover:underline truncate">{order.email}</a>}
                                        {order.phone && <a href={`tel:${order.phone}`} className="text-blue-400 hover:underline">{order.phone.toString().replace('.0', '')}</a>}
                                    </div>
                                </div>
                            </div>

                            {/* Column 3: Order Items */}
                            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 md:col-span-1 h-full">
                                <h4 className="text-blue-400 font-semibold mb-3 uppercase text-xs tracking-wider flex items-center gap-2">
                                    <IconList /> Pozycje Zamówienia
                                </h4>
                                {/* Scrollable list if too many items */}
                                <div className="max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                                    {/* We pass the pre-loaded items if they exist (api v2), if not fetch */}
                                    {order.items && order.items.length > 0 ? (
                                        <ul className="space-y-2">
                                            {order.items.map((item, idx) => (
                                                <li key={idx} className="flex justify-between items-start border-b border-gray-800 pb-2 last:border-0">
                                                    <div>
                                                        <div className="text-gray-200 text-sm">{item.name}</div>
                                                        <div className="text-xs text-gray-500 font-mono">{item.sku}</div>
                                                    </div>
                                                    <div className="text-right ml-3 whitespace-nowrap">
                                                        <div className="text-emerald-400 font-medium">{item.quantity} szt.</div>
                                                        <div className="text-xs text-gray-500">{item.price?.toFixed(2)}</div>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <OrderDetails orderId={order.id} />
                                    )}
                                </div>
                            </div>

                        </div>
                    </td>
                </tr>
            )}
        </>
    );
}

function OrderDetails({ orderId }) {
    const [items, setItems] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`/api/order/${orderId}`)
            .then(res => res.json())
            .then(data => {
                setItems(data.items || []);
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, [orderId]);

    if (loading) return <div className="text-gray-500">Ładowanie produktów...</div>;
    if (!items || items.length === 0) return <div className="text-gray-500">Brak produktów</div>;

    return (
        <ul className="space-y-2">
            {items.map((item, idx) => (
                <li key={idx} className="flex justify-between items-start border-l-2 border-gray-700 pl-3">
                    <span className="text-gray-200">{item.name}</span>
                    <span className="text-gray-400 whitespace-nowrap ml-4">
                        {item.quantity} x <span className="text-emerald-400">{item.price?.toFixed(2)}</span>
                    </span>
                </li>
            ))}
        </ul>
    );
}


function Dashboard() {
    const [searchTerm, setSearchTerm] = useState('');
    const [orders, setOrders] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(25);
    const [loading, setLoading] = useState(false);
    const [tab, setTab] = useState('list'); // 'list' or 'stats'
    const [sources, setSources] = useState([]);
    const [filters, setFilters] = useState({ dateFrom: '', dateTo: '', source: '', client: '' });

    // Fetch sources on load
    useEffect(() => {
        fetch('/api/sources').then(r => r.json()).then(setSources).catch(console.error);
    }, []);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchOrders();
        }, 500);
        return () => clearTimeout(timer);
    }, [searchTerm, page, limit, filters]);

    const fetchOrders = () => {
        setLoading(true);
        const params = new URLSearchParams({
            page,
            limit,
            q: searchTerm,
            date_from: filters.dateFrom,
            date_to: filters.dateTo,
            source: filters.source,
            client: filters.client
        });

        // Clean empty params
        for (const [key, value] of params.entries()) {
            if (!value || value === 'undefined') params.delete(key);
        }

        fetch(`/api/search?${params.toString()}`)
            .then(res => res.json())
            .then(data => {
                setOrders(data.data);
                setTotal(data.total);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    };

    return (
        <div className="max-w-7xl mx-auto p-6 h-screen flex flex-col">
            <header className="flex items-center gap-6 mb-8 bg-gray-900/40 p-4 rounded-2xl border border-gray-800/50 backdrop-blur-sm">
                {/* Logo with CSS trick: Invert content (black->white, white->black) then Screen blend (black becomes transparent) */}
                <div className="relative group">
                    <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <img
                        src="/logo.png"
                        alt="Logo"
                        className="h-16 w-auto relative z-10"
                        style={{ filter: 'invert(1)', mixBlendMode: 'screen' }}
                    />
                </div>

                <div className="flex-1">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        Archiwum Sprzedaży
                    </h1>
                    <p className="text-gray-500 mt-1 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        Lokalna baza zamówień
                    </p>
                </div>

                <div className="flex bg-gray-800 p-1 rounded-lg">
                    <button
                        onClick={() => setTab('list')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${tab === 'list' ? 'bg-gray-700 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                    >
                        <IconList /> Lista
                    </button>
                    <button
                        onClick={() => setTab('stats')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${tab === 'stats' ? 'bg-gray-700 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                    >
                        <IconBarChart /> Statystyki
                    </button>
                </div>
            </header>

            {tab === 'list' && (
                <div className="flex-1 flex flex-col min-h-0 bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden shadow-2xl backdrop-blur-sm">
                    {/* Toolbar */}
                    <div className="p-4 border-b border-gray-800 bg-gray-900/80">
                        <FilterBar sources={sources} onFilterChange={f => { setFilters(f); setPage(1); }} />

                        <div className="flex gap-4 items-center">
                            <div className="relative flex-1 max-w-md">
                                <input
                                    type="text"
                                    placeholder="Szukaj (Nazwisko, NIP, Email, Nr...)"
                                    className="w-full bg-gray-800 border border-gray-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder-gray-500"
                                    value={searchTerm}
                                    onChange={e => { setSearchTerm(e.target.value); setPage(1); }}
                                />
                                <div className="absolute left-3 top-3 text-gray-500">
                                    <IconSearch />
                                </div>
                            </div>
                            <div className="text-sm text-gray-500 ml-auto">
                                Znaleziono: <span className="text-white font-mono">{total}</span>
                            </div>
                        </div>
                    </div>

                    {/* Table Container */}
                    <div className="flex-1 overflow-auto">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-gray-800/80 sticky top-0 backdrop-blur-md z-10 text-xs uppercase tracking-wider text-gray-400 font-semibold">
                                <tr>
                                    <th className="p-3 w-32 border-b border-gray-700">Nr / Źródło</th>
                                    <th className="p-3 w-32 border-b border-gray-700">Data</th>
                                    <th className="p-3 border-b border-gray-700">Klient</th>
                                    <th className="p-3 w-40 border-b border-gray-700">Wysyłka</th>
                                    <th className="p-3 text-right w-28 border-b border-gray-700">Kwota</th>
                                    <th className="p-3 w-32 border-b border-gray-700 text-center">Dokumenty</th>
                                    <th className="p-3 w-8 border-b border-gray-700"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr>
                                        <td colSpan="6" className="p-12 text-center text-gray-500">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                            Szukam danych...
                                        </td>
                                    </tr>
                                ) : orders.map(order => (
                                    <OrderRow key={order.id} order={order} />
                                ))}
                                {!loading && orders.length === 0 && (
                                    <tr><td colSpan="6" className="p-12 text-center text-gray-500">Brak wyników</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="p-4 border-t border-gray-800 bg-gray-900/80 flex flex-wrap justify-between items-center gap-4">

                        {/* Rows per page */}
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                            <span>Wierszy na stronę:</span>
                            <select
                                value={limit}
                                onChange={e => { setLimit(Number(e.target.value)); setPage(1); }}
                                className="bg-gray-800 border border-gray-600 text-white rounded px-2 py-1 focus:ring-1 focus:ring-blue-500 outline-none"
                            >
                                {[25, 50, 100, 200].map(l => <option key={l} value={l}>{l}</option>)}
                            </select>
                        </div>

                        {/* Page Navigation */}
                        <div className="flex items-center gap-4">
                            <button
                                disabled={page <= 1}
                                onClick={() => setPage(p => p - 1)}
                                className="px-4 py-2 rounded bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                            >
                                Poprzednia
                            </button>

                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <span>Strona</span>
                                <input
                                    type="number"
                                    min="1"
                                    max={Math.ceil(total / limit)}
                                    value={page}
                                    onChange={e => {
                                        let val = parseInt(e.target.value);
                                        if (isNaN(val)) val = 1;
                                        if (val < 1) val = 1;
                                        const maxPages = Math.ceil(total / limit);
                                        if (val > maxPages) val = maxPages;
                                        setPage(val);
                                    }}
                                    className="w-16 bg-gray-800 border border-gray-600 text-white text-center rounded px-1 py-1 focus:ring-1 focus:ring-blue-500 outline-none"
                                />
                                <span>z <span className="text-white font-mono">{Math.ceil(total / limit)}</span></span>
                            </div>

                            <button
                                disabled={page >= Math.ceil(total / limit)}
                                onClick={() => setPage(p => p + 1)}
                                className="px-4 py-2 rounded bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                            >
                                Następna
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {tab === 'stats' && <StatsView sources={sources} />}
        </div>
    );
}

function StatsView({ sources }) {
    const [salesData, setSalesData] = useState([]);
    const [productData, setProductData] = useState([]);
    const [summary, setSummary] = useState(null);
    const [filters, setFilters] = useState({ dateFrom: '', dateTo: '', source: '', client: '' });
    const [sortBy, setSortBy] = useState('qty'); // 'qty' or 'value'

    useEffect(() => {
        const params = new URLSearchParams({
            date_from: filters.dateFrom,
            date_to: filters.dateTo,
            source: filters.source,
            client: filters.client
        });
        for (const [key, value] of params.entries()) if (!value) params.delete(key);

        // Sales
        fetch(`/api/stats/sales?${params.toString()}`)
            .then(res => res.json())
            .then(data => {
                setSalesData(data.map(d => ({
                    name: d.month,
                    Sprzedaż: d.total_sales,
                    Ilość: d.quantity
                })));
            });

        // Summary
        fetch(`/api/stats/summary?${params.toString()}`)
            .then(res => res.json())
            .then(data => setSummary(data));

        // Products
        params.append('sort_by', sortBy);
        fetch(`/api/stats/products?${params.toString()}`)
            .then(res => res.json())
            .then(data => setProductData(data));

    }, [filters, sortBy]);

    if (!RechartsObj) return null; // Error handled in parent or fallback

    return (
        <div className="flex-1 overflow-auto flex flex-col gap-6 animate-in fade-in duration-300">

            {/* Stats Toolbar */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
                    <IconBarChart /> Filtrowanie Statystyk
                </h3>
                <FilterBar sources={sources} onFilterChange={setFilters} />
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 shadow-xl backdrop-blur-sm flex flex-col items-center justify-center">
                        <span className="text-gray-400 text-sm uppercase tracking-wider font-semibold mb-2">Sprzedaż Produktów</span>
                        <span className="text-3xl font-bold text-emerald-400">{summary.revenue?.toFixed(2)} <span className="text-lg text-emerald-600">PLN</span></span>
                    </div>
                    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 shadow-xl backdrop-blur-sm flex flex-col items-center justify-center">
                        <span className="text-gray-400 text-sm uppercase tracking-wider font-semibold mb-2">Sprzedane Sztuki</span>
                        <span className="text-3xl font-bold text-blue-400">{summary.quantity} <span className="text-lg text-blue-600">szt.</span></span>
                    </div>
                    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 shadow-xl backdrop-blur-sm flex flex-col items-center justify-center">
                        <span className="text-gray-400 text-sm uppercase tracking-wider font-semibold mb-2">Koszty Wysyłki (GLS/Inne)</span>
                        <span className="text-3xl font-bold text-orange-400">{summary.shipping_cost?.toFixed(2)} <span className="text-lg text-orange-600">PLN</span></span>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sales Chart */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 shadow-xl backdrop-blur-sm lg:col-span-2">
                    <h3 className="text-lg font-semibold text-gray-200 mb-6">Sprzedaż w czasie (PLN)</h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RechartsObj.ComposedChart data={salesData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis yAxisId="left" stroke="#94a3b8" />
                                <YAxis yAxisId="right" orientation="right" stroke="#10b981" />
                                <Tooltip
                                    formatter={(value, name) => {
                                        if (name === 'Sprzedaż') return [`${value.toFixed(2)} PLN`, name];
                                        if (name === 'Ilość') return [`${value} szt.`, name];
                                        return [value, name];
                                    }}
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#e2e8f0' }}
                                    cursor={{ fill: '#334155', opacity: 0.4 }}
                                />
                                <Legend />
                                <Bar yAxisId="left" dataKey="Sprzedaż" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                <RechartsObj.Line yAxisId="right" type="monotone" dataKey="Ilość" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
                            </RechartsObj.ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Top Products */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 shadow-xl backdrop-blur-sm lg:col-span-2">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-200">Top 10 Produktów</h3>
                    <div className="flex bg-gray-800 rounded p-1">
                        <button
                            onClick={() => setSortBy('qty')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${sortBy === 'qty' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                        >
                            Wg Ilości
                        </button>
                        <button
                            onClick={() => setSortBy('value')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${sortBy === 'value' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                        >
                            Wg Wartości
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-800/50 text-xs uppercase text-gray-400">
                            <tr>
                                <th className="p-3 rounded-l-lg">Nazwa</th>
                                <th className="p-3 text-right">Ilość</th>
                                <th className="p-3 text-right rounded-r-lg">Przychód (est.)</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {productData.map((prod, idx) => (
                                <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                                    <td className="p-3 text-sm text-gray-300 font-medium">{prod.name}</td>
                                    <td className="p-3 text-right text-gray-400">{prod.quantity} szt.</td>
                                    <td className="p-3 text-right text-emerald-400 font-mono">{prod.revenue?.toFixed(2)} PLN</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Dashboard />);
