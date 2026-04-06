import { useState, useEffect, useRef } from "react";
import axios from "axios";
import MapPanel from "./MapPanel";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import {
  Truck, Activity, Package, AlertTriangle,
  CheckCircle, Clock, Zap, Globe, Settings,
  TrendingUp, MessageSquare, Brain, RefreshCw,
  BarChart2, Search, FileText
} from "lucide-react";

const API = "http://127.0.0.1:8000";

// ── HELPERS ───────────────────────────────────────────────────────────

const get = async (url) => {
  try { return (await axios.get(`${API}${url}`)).data; }
  catch { return null; }
};

const post = async (url, data = {}) => {
  try { return (await axios.post(`${API}${url}`, data)).data; }
  catch { return null; }
};

// ── GLOBAL STYLES ─────────────────────────────────────────────────────

const globalStyles = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;500;700;900&display=swap');

  :root {
    --bg-void:       #020408;
    --bg-deep:       #060d14;
    --bg-panel:      #0a1520;
    --bg-panel-alt:  #0d1b26;
    --bg-hover:      #111f2e;
    --border-dim:    #162330;
    --border-glow:   #1e3a4f;
    --border-active: #0fa3b1;
    --accent-cyan:   #0fa3b1;
    --accent-cyan2:  #06d6e8;
    --accent-green:  #00ff88;
    --accent-amber:  #ffb703;
    --accent-red:    #ff3860;
    --accent-purple: #9b5de5;
    --text-primary:  #c8e6f0;
    --text-secondary:#6b96aa;
    --text-dim:      #3a6070;
    --text-mono:     #7ec8d4;
    --scanline: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.15) 2px,
      rgba(0,0,0,0.15) 4px
    );
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg-void);
    color: var(--text-primary);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Scrollbars */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg-deep); }
  ::-webkit-scrollbar-thumb { background: var(--accent-cyan); border-radius: 2px; }

  /* Scanline overlay on panels */
  .scanline::after {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--scanline);
    pointer-events: none;
    z-index: 1;
    opacity: 0.4;
    border-radius: inherit;
  }

  /* Corner bracket decoration */
  .bracket-corner {
    position: relative;
  }
  .bracket-corner::before,
  .bracket-corner::after {
    content: '';
    position: absolute;
    width: 10px;
    height: 10px;
    border-color: var(--accent-cyan);
    border-style: solid;
    opacity: 0.7;
  }
  .bracket-corner::before {
    top: 0; left: 0;
    border-width: 1px 0 0 1px;
  }
  .bracket-corner::after {
    bottom: 0; right: 0;
    border-width: 0 1px 1px 0;
  }

  /* Pulse animation */
  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 4px var(--accent-cyan), 0 0 8px rgba(15,163,177,0.3); }
    50%       { box-shadow: 0 0 8px var(--accent-cyan), 0 0 20px rgba(15,163,177,0.5); }
  }

  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
  @keyframes scandown {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100%); }
  }
  @keyframes data-flow {
    0%   { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
  }
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .live-pulse { animation: pulse-glow 2s ease-in-out infinite; }
  .blink      { animation: blink 1.4s step-end infinite; }

  @keyframes toast-in {
    from { opacity: 0; transform: translateX(40px) scale(0.95); }
    to   { opacity: 1; transform: translateX(0) scale(1); }
  }
  @keyframes toast-out {
    from { opacity: 1; transform: translateX(0) scale(1); }
    to   { opacity: 0; transform: translateX(40px) scale(0.95); }
  }
  .toast-enter { animation: toast-in 0.25s cubic-bezier(0.34,1.56,0.64,1) forwards; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { animation: spin 1s linear infinite; display: inline-block; }

  /* Grid lines background texture */
  .grid-bg {
    background-image:
      linear-gradient(rgba(15,163,177,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(15,163,177,0.04) 1px, transparent 1px);
    background-size: 32px 32px;
  }

  /* Number display font */
  .mono { font-family: 'Share Tech Mono', monospace; }
  .orbitron { font-family: 'Orbitron', monospace; }
  .rajdhani { font-family: 'Rajdhani', sans-serif; }
`;

// ── PANEL COMPONENT ───────────────────────────────────────────────────

const Panel = ({ children, className = "", title, titleIcon: TitleIcon, badge, noPad, style }) => (
  <div
    style={{
      background: 'var(--bg-panel)',
      border: '1px solid var(--border-glow)',
      borderRadius: 2,
      position: 'relative',
      overflow: 'hidden',
      animation: 'fadeInUp 0.3s ease',
      ...style,
    }}
    className={`bracket-corner ${className}`}
  >
    {/* Top accent bar */}
    <div style={{
      height: 2,
      background: 'linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-cyan2) 50%, transparent 100%)',
      position: 'absolute', top: 0, left: 0, right: 0,
    }} />

    {title && (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 14px 8px',
        borderBottom: '1px solid var(--border-dim)',
        background: 'rgba(15,163,177,0.04)',
      }}>
        {TitleIcon && <TitleIcon size={12} style={{ color: 'var(--accent-cyan)' }} />}
        <span style={{
          fontFamily: 'Rajdhani, sans-serif',
          fontSize: 11, fontWeight: 700, letterSpacing: '0.18em',
          color: 'var(--text-secondary)', textTransform: 'uppercase',
        }}>
          {title}
        </span>
        {badge && <span style={{ marginLeft: 'auto' }}>{badge}</span>}
      </div>
    )}

    <div style={noPad ? {} : { padding: '14px' }}>
      {children}
    </div>
  </div>
);

// ── METRIC CARD ───────────────────────────────────────────────────────

const MetricCard = ({ icon: Icon, label, value, sub, color = "cyan" }) => {
  const colorMap = {
    cyan:   { accent: 'var(--accent-cyan)',   bg: 'rgba(15,163,177,0.07)',  border: 'rgba(15,163,177,0.25)' },
    green:  { accent: 'var(--accent-green)',  bg: 'rgba(0,255,136,0.07)',   border: 'rgba(0,255,136,0.2)'   },
    amber:  { accent: 'var(--accent-amber)',  bg: 'rgba(255,183,3,0.07)',   border: 'rgba(255,183,3,0.2)'   },
    red:    { accent: 'var(--accent-red)',    bg: 'rgba(255,56,96,0.07)',   border: 'rgba(255,56,96,0.2)'   },
    purple: { accent: 'var(--accent-purple)', bg: 'rgba(155,93,229,0.07)',  border: 'rgba(155,93,229,0.2)'  },
  };
  const c = colorMap[color] || colorMap.cyan;

  return (
    <div style={{
      background: c.bg, border: `1px solid ${c.border}`,
      borderRadius: 2, padding: '14px 16px',
      position: 'relative', overflow: 'hidden',
    }} className="bracket-corner">
      {/* Top glow bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 1,
        background: c.accent, opacity: 0.7,
      }} />
      {/* Background cross-hair */}
      <div style={{
        position: 'absolute', top: 0, right: 0, bottom: 0, left: 0,
        backgroundImage: `radial-gradient(circle at 85% 15%, ${c.accent}15 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, position: 'relative' }}>
        <div style={{
          width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: `${c.accent}18`, border: `1px solid ${c.accent}50`, borderRadius: 2,
        }}>
          <Icon size={11} style={{ color: c.accent }} />
        </div>
        <span style={{
          fontSize: 9, fontWeight: 700, letterSpacing: '0.2em',
          color: 'var(--text-dim)', textTransform: 'uppercase', fontFamily: 'Rajdhani',
        }}>
          {label}
        </span>
      </div>

      <div style={{
        fontFamily: 'Orbitron, monospace', fontSize: 22, fontWeight: 700,
        color: c.accent, lineHeight: 1, marginBottom: 4, position: 'relative',
        textShadow: `0 0 12px ${c.accent}80`,
      }}>
        {value}
      </div>
      {sub && (
        <div style={{
          fontSize: 10, color: 'var(--text-dim)', fontFamily: 'Share Tech Mono',
          letterSpacing: '0.05em',
        }}>
          {sub}
        </div>
      )}
    </div>
  );
};

// ── STATUS BADGE ──────────────────────────────────────────────────────

const Badge = ({ text, color }) => {
  const colorMap = {
    green:  { bg: 'rgba(0,255,136,0.1)',   color: 'var(--accent-green)',  border: 'rgba(0,255,136,0.3)'   },
    red:    { bg: 'rgba(255,56,96,0.1)',   color: 'var(--accent-red)',    border: 'rgba(255,56,96,0.3)'   },
    amber:  { bg: 'rgba(255,183,3,0.1)',   color: 'var(--accent-amber)',  border: 'rgba(255,183,3,0.3)'   },
    blue:   { bg: 'rgba(15,163,177,0.1)',  color: 'var(--accent-cyan)',   border: 'rgba(15,163,177,0.3)'  },
    purple: { bg: 'rgba(155,93,229,0.1)',  color: 'var(--accent-purple)', border: 'rgba(155,93,229,0.3)'  },
  };
  const c = colorMap[color] || colorMap.blue;

  return (
    <span style={{
      fontSize: 9, padding: '2px 8px', borderRadius: 1,
      background: c.bg, color: c.color, border: `1px solid ${c.border}`,
      fontFamily: 'Share Tech Mono', letterSpacing: '0.1em',
      textTransform: 'uppercase', fontWeight: 600,
    }}>
      {text}
    </span>
  );
};

// ── BUTTON ────────────────────────────────────────────────────────────

const Btn = ({ onClick, children, variant = "default", disabled }) => {
  const variants = {
    default: {
      bg: 'transparent', border: 'var(--border-glow)', color: 'var(--text-secondary)',
      hover: 'var(--bg-hover)',
    },
    primary: {
      bg: 'rgba(15,163,177,0.15)', border: 'var(--accent-cyan)', color: 'var(--accent-cyan)',
    },
    success: {
      bg: 'rgba(0,255,136,0.1)', border: 'var(--accent-green)', color: 'var(--accent-green)',
    },
    danger: {
      bg: 'rgba(255,56,96,0.1)', border: 'var(--accent-red)', color: 'var(--accent-red)',
    },
  };
  const v = variants[variant] || variants.default;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '6px 14px',
        background: v.bg,
        border: `1px solid ${v.border}`,
        color: v.color,
        borderRadius: 2,
        fontSize: 11,
        fontFamily: 'Rajdhani, sans-serif',
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        transition: 'all 0.15s',
        outline: 'none',
      }}
    >
      {children}
    </button>
  );
};

// ── DIVIDER LINE ─────────────────────────────────────────────────────

const Divider = () => (
  <div style={{
    height: 1, background: 'var(--border-dim)', margin: '10px 0',
  }} />
);

// ── LOG ENTRY ─────────────────────────────────────────────────────────

const LogEntry = ({ log, i }) => {
  const isReassign = log.includes("REASSIGNED");
  const isBreach   = log.includes("SLA BREACH");
  const isDeliver  = log.includes("DELIVERED");
  const isInject   = log.includes("INJECTED");
  const isAgent    = log.includes("AGENT");

  const style = isReassign
    ? { bg: 'rgba(255,56,96,0.06)',   color: '#ff8fa3', border: 'rgba(255,56,96,0.2)',   prefix: '⚠', tag: 'REASSIGN' }
    : isBreach
    ? { bg: 'rgba(255,183,3,0.06)',   color: '#ffd166', border: 'rgba(255,183,3,0.2)',   prefix: '!', tag: 'SLA' }
    : isDeliver
    ? { bg: 'rgba(0,255,136,0.05)',   color: '#00e07a', border: 'rgba(0,255,136,0.15)',  prefix: '✓', tag: 'OK' }
    : isInject
    ? { bg: 'rgba(15,163,177,0.06)',  color: '#7ec8d4', border: 'rgba(15,163,177,0.2)', prefix: '→', tag: 'IN' }
    : isAgent
    ? { bg: 'rgba(155,93,229,0.06)', color: '#c4b5fd', border: 'rgba(155,93,229,0.2)',  prefix: '◈', tag: 'AI' }
    : { bg: 'rgba(10,21,32,0.8)',    color: 'var(--text-secondary)', border: 'var(--border-dim)', prefix: '·', tag: '--' };

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 8,
      padding: '5px 8px',
      background: style.bg, border: `1px solid ${style.border}`,
      borderRadius: 1, fontSize: 10, fontFamily: 'Share Tech Mono',
      color: style.color,
    }}>
      <span style={{ opacity: 0.6, minWidth: 16 }}>{style.tag}</span>
      <span style={{ flex: 1, wordBreak: 'break-all' }}>{log}</span>
    </div>
  );
};

// ── TOOLTIP STYLE ─────────────────────────────────────────────────────

const tooltipStyle = {
  contentStyle: {
    background: '#0a1520', border: '1px solid var(--border-glow)',
    borderRadius: 2, fontSize: 11, fontFamily: 'Share Tech Mono',
    color: 'var(--text-primary)',
  },
  labelStyle: { color: 'var(--accent-cyan)', fontFamily: 'Share Tech Mono' },
};

// ----- Report Panel ----------------------------------------------------
const ReportPanel = () => {
  const [reports,    setReports]    = useState(null);
  const [generating, setGenerating] = useState(false);
  const [selected,   setSelected]   = useState(0);

  const fetchReports = async () => {
    const r = await get("/api/reports");
    if (r) setReports(r);
  };

  useEffect(() => {
    fetchReports();
    const i = setInterval(fetchReports, 5000);
    return () => clearInterval(i);
  }, []);

  const generate = async () => {
    setGenerating(true);
    await post("/api/reports/generate");
    setTimeout(async () => {
      await fetchReports();
      setGenerating(false);
    }, 10000);
  };

  return (
    <div>
      <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:14 }}>
        <Btn onClick={generate} variant="primary" disabled={generating}>
          {generating ? "⟳ GENERATING..." : "📋 GENERATE REPORT"}
        </Btn>
        {reports?.last_generated && (
          <span style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)' }}>
            Last generated: {reports.last_generated}
          </span>
        )}
        <Badge text={`${reports?.total || 0} REPORTS`} color="blue" />
      </div>

      {reports?.reports?.length > 0 && (
        <div style={{ display:'grid', gridTemplateColumns:'200px 1fr', gap:12 }}>
          {/* Report list */}
          <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
            {reports.reports.map((r,i) => (
              <button key={r.id} onClick={() => setSelected(i)}
                style={{ padding:'8px 10px', cursor:'pointer', textAlign:'left', borderRadius:2, background:selected===i?'rgba(15,163,177,0.1)':'var(--bg-panel-alt)', border:`1px solid ${selected===i?'var(--accent-cyan)':'var(--border-dim)'}`, transition:'all 0.15s' }}>
                <div style={{ fontSize:10, fontFamily:'Orbitron', color:selected===i?'var(--accent-cyan)':'var(--text-secondary)', marginBottom:3 }}>
                  REPORT #{r.id}
                </div>
                <div style={{ fontSize:9, fontFamily:'Share Tech Mono', color:'var(--text-dim)' }}>
                  {r.city} · {r.scenario}
                </div>
                <div style={{ fontSize:9, fontFamily:'Share Tech Mono', color:'var(--text-dim)' }}>
                  {r.on_time}% on-time · T{r.tick}
                </div>
                {r.status === "fallback" && (
                  <Badge text="FALLBACK" color="amber" />
                )}
              </button>
            ))}
          </div>

          {/* Report content */}
          {reports.reports[selected] && (
            <div style={{ background:'var(--bg-panel-alt)', border:'1px solid var(--border-dim)', borderRadius:2, padding:14 }}>
              {/* Report header */}
              <div style={{ display:'flex', gap:10, marginBottom:12, flexWrap:'wrap' }}>
                {[
                  { label:'CITY',      val: reports.reports[selected].city },
                  { label:'SCENARIO',  val: reports.reports[selected].scenario },
                  { label:'ON-TIME',   val: `${reports.reports[selected].on_time}%` },
                  { label:'DELIVERED', val: reports.reports[selected].delivered },
                  { label:'TICK',      val: reports.reports[selected].tick },
                ].map(({ label, val }) => (
                  <div key={label} style={{ background:'var(--bg-panel)', border:'1px solid var(--border-dim)', borderRadius:2, padding:'5px 10px' }}>
                    <div style={{ fontSize:8, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.12em' }}>{label}</div>
                    <div style={{ fontSize:11, fontFamily:'Orbitron', color:'var(--accent-cyan)', marginTop:1 }}>{val}</div>
                  </div>
                ))}
              </div>
              {/* Report body */}
              <div style={{ fontSize:11, fontFamily:'Share Tech Mono', color:'var(--text-mono)', lineHeight:1.8, whiteSpace:'pre-wrap', letterSpacing:'0.03em', maxHeight:280, overflowY:'auto' }}>
                {reports.reports[selected].content}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── MAIN APP ──────────────────────────────────────────────────────────

export default function App() {
  const [metrics,   setMetrics]   = useState(null);
  const [agents,    setAgents]    = useState([]);
  const [logs,      setLogs]      = useState([]);
  const [history,   setHistory]   = useState([]);
  const [scenario,  setScenario]  = useState(null);
  const [city,      setCity]      = useState(null);
  const [rlData,    setRlData]    = useState(null);
  const [abData,    setAbData]    = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [agentAI,   setAgentAI]   = useState(null);
  const [nlQuery,   setNlQuery]   = useState("");
  const [nlAnswer,  setNlAnswer]  = useState("");
  const [nlLoading, setNlLoading] = useState(false);
  const [wsStatus,  setWsStatus]  = useState("connecting");
  const [tick,      setTick]      = useState(0);
  const [toast,     setToast]     = useState(null);
  const [loading,   setLoading]   = useState({});
  const [forecast,      setForecast]      = useState(null);
  const [tuning,        setTuning]        = useState(null);
  const [orders,        setOrders]        = useState([]);
  const [explain,       setExplain]       = useState(null);
  const [selectedOrder, setSelectedOrder] = useState("");
  const [speed,   setSpeed]   = useState(1.0);
  const [replay,  setReplay]  = useState(null);
  const wsRef = useRef(null);

  const notify = (msg, type = "success") => {
    setToast({ msg, type, id: Date.now() });
    setTimeout(() => setToast(null), 3500);
  };

  const setLoad = (key, val) => setLoading(prev => ({ ...prev, [key]: val }));

  // ── WEBSOCKET ───────────────────────────────────────────────────────

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws");
      wsRef.current = ws;
      ws.onopen    = () => setWsStatus("live");
      ws.onclose   = () => { setWsStatus("reconnecting"); setTimeout(connect, 3000); };
      ws.onerror   = () => ws.close();
      ws.onmessage = (e) => {
        const d = JSON.parse(e.data);
        if (d.type === "tick_update") {
          setMetrics(d.metrics);
          setAgents(d.agents);
          setLogs(d.logs);
          setTick(d.tick);
        }
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, []);

  // ── POLLING for non-WS data ─────────────────────────────────────────

  const refresh = async () => {
    const [
      sc, ct, hi, rl, ab, an, ag, fc, tu, or,
      sp, rp
    ] = await Promise.all([
      get("/api/scenario"), 
      get("/api/city"),
      get("/api/history"),  
      get("/api/rl/status"),
      get("/api/ab/results"),
      get("/api/anomalies"),
      get("/api/agent"),    
      get("/api/forecast"),
      get("/api/tuning"),   
      get("/api/orders"),
      get("/api/speed"),          
      get("/api/replay/sessions"),  
    ]);

    if (sc) setScenario(sc);
    if (ct) setCity(ct);
    if (hi) setHistory(hi.slice(-20));
    if (rl) setRlData(rl);
    if (ab) setAbData(ab);
    if (an) setAnomalies(an);
    if (ag) setAgentAI(ag);
    if (fc) setForecast(fc);
    if (tu) setTuning(tu);
    if (or) setOrders(or);
    if (sp) setSpeed(sp.speed);
    if (rp) setReplay(rp);
  };

  const fetchExplain = async (orderId) => {
    if (!orderId) return;
    const res = await get(`/api/explain/${orderId}`);
    if (res) setExplain(res);
  };

  const assignedOrders = orders.filter(o => o.status === "assigned");

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  // ── NL QUERY ────────────────────────────────────────────────────────

  const askQuery = async (q) => {
    const query = q || nlQuery;
    if (!query) return;
    setNlLoading(true);
    setNlAnswer("");
    const res = await post("/api/query", { query });
    setNlAnswer(res?.answer || "No answer received");
    setNlLoading(false);
  };

  // ── SCENARIO CHANGE ─────────────────────────────────────────────────

  const changeScenario = async (mode) => {
    await post(`/api/scenario/${mode}`);
    refresh();
  };

  const changeCity = async (key) => {
    await post(`/api/city/${key}`);
    refresh();
  };

  if (!metrics) return (
    <>
      <style>{globalStyles}</style>
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-void)',
      }} className="grid-bg">
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, margin: '0 auto 20px',
            border: '1px solid var(--accent-cyan)', borderRadius: 2,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(15,163,177,0.4)',
          }} className="live-pulse">
            <Truck size={28} style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <p style={{
            fontFamily: 'Share Tech Mono', fontSize: 12,
            color: 'var(--text-secondary)', letterSpacing: '0.2em',
          }}>
            INITIALIZING FLEET AI ENGINE<span className="blink">_</span>
          </p>
        </div>
      </div>
    </>
  );

  const scenarios = scenario?.all || {};
  const cities    = city?.all    || {};

  return (
    <>
      <style>{globalStyles}</style>
      <div style={{
        minHeight: '100vh', background: 'var(--bg-void)',
        padding: '16px 20px', maxWidth: 1600, margin: '0 auto',
      }} className="grid-bg">

        {/* ── TOAST NOTIFICATION ── */}
        {toast && (
          <div key={toast.id} className="toast-enter" style={{
            position: 'fixed', top: 20, right: 20, zIndex: 9999,
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 16px', borderRadius: 2, minWidth: 300, maxWidth: 440,
            fontFamily: 'Share Tech Mono', fontSize: 11, letterSpacing: '0.06em',
            boxShadow: '0 8px 32px rgba(0,0,0,0.7)',
            ...(toast.type === "success"
              ? { background: 'rgba(0,30,18,0.97)', border: '1px solid rgba(0,255,136,0.4)', color: '#00e07a' }
              : toast.type === "info"
              ? { background: 'rgba(4,18,30,0.97)', border: '1px solid rgba(15,163,177,0.4)', color: 'var(--accent-cyan)' }
              : { background: 'rgba(30,4,12,0.97)', border: '1px solid rgba(255,56,96,0.4)', color: '#ff8fa3' }
            ),
          }}>
            <span style={{ fontSize: 15 }}>
              {toast.type === "success" ? "✓" : toast.type === "info" ? "◈" : "⚠"}
            </span>
            <span style={{ flex: 1, lineHeight: 1.5 }}>{toast.msg}</span>
            <button onClick={() => setToast(null)} style={{
              background: 'none', border: 'none', color: 'inherit',
              cursor: 'pointer', fontSize: 12, opacity: 0.5, padding: '0 2px',
            }}>✕</button>
          </div>
        )}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 20, paddingBottom: 14,
          borderBottom: '1px solid var(--border-dim)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Logo block */}
            <div style={{
              width: 46, height: 46, background: 'rgba(15,163,177,0.1)',
              border: '1px solid var(--accent-cyan)', borderRadius: 2,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 16px rgba(15,163,177,0.25)',
            }}>
              <Truck size={22} style={{ color: 'var(--accent-cyan)' }} />
            </div>
            <div>
              <div style={{
                fontFamily: 'Orbitron, monospace', fontSize: 16, fontWeight: 700,
                color: 'var(--text-primary)', letterSpacing: '0.08em',
                textShadow: '0 0 20px rgba(15,163,177,0.4)',
              }}>
                FLEET AI ENGINE
              </div>
              <div style={{
                fontFamily: 'Share Tech Mono', fontSize: 10,
                color: 'var(--text-dim)', letterSpacing: '0.15em', marginTop: 2,
              }}>
                v4.0 · AUTONOMOUS DISPATCH · {city?.config?.name?.toUpperCase() || "BANGALORE"}
              </div>
            </div>

            {/* Separator */}
            <div style={{ width: 1, height: 32, background: 'var(--border-glow)', margin: '0 4px' }} />

            {/* System markers */}
            {[
              { label: 'WS', ok: wsStatus === "live" },
              { label: 'RL', ok: !!rlData },
              { label: 'AI', ok: !!agentAI },
            ].map(({ label, ok }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 5,
                fontSize: 9, fontFamily: 'Share Tech Mono', letterSpacing: '0.12em',
                color: ok ? 'var(--accent-green)' : 'var(--accent-red)',
              }}>
                <div style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: ok ? 'var(--accent-green)' : 'var(--accent-red)',
                  boxShadow: ok ? '0 0 6px var(--accent-green)' : '0 0 6px var(--accent-red)',
                }} />
                {label}
              </div>
            ))}
          </div>

          {/* Right header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              fontFamily: 'Share Tech Mono', fontSize: 10,
              color: 'var(--text-dim)', letterSpacing: '0.1em',
            }}>
              {scenario?.config?.name?.toUpperCase() || "NORMAL"} MODE
            </div>
            <div style={{
              fontFamily: 'Orbitron', fontSize: 11, fontWeight: 700,
              color: 'var(--accent-cyan)', letterSpacing: '0.15em',
              padding: '4px 12px',
              border: '1px solid var(--accent-cyan)',
              borderRadius: 2,
              background: 'rgba(15,163,177,0.08)',
              textShadow: '0 0 8px var(--accent-cyan)',
            }}>
              TICK <span style={{ color: '#fff' }}>{String(tick).padStart(4, '0')}</span>
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '5px 12px', borderRadius: 2,
              border: `1px solid ${wsStatus === "live" ? 'rgba(0,255,136,0.3)' : 'rgba(255,183,3,0.3)'}`,
              background: wsStatus === "live" ? 'rgba(0,255,136,0.06)' : 'rgba(255,183,3,0.06)',
              fontFamily: 'Share Tech Mono', fontSize: 10, letterSpacing: '0.12em',
              color: wsStatus === "live" ? 'var(--accent-green)' : 'var(--accent-amber)',
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: wsStatus === "live" ? 'var(--accent-green)' : 'var(--accent-amber)',
                animation: wsStatus === "live" ? 'blink 1s ease infinite' : 'none',
              }} />
              {wsStatus === "live" ? "STREAM LIVE" : "RECONNECTING"}
            </div>
          </div>
        </div>

        {/* ── CITY + SCENARIO CONTROLS ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <Panel title="City Node" titleIcon={Globe}>
            <div style={{ display: 'flex', gap: 8 }}>
              {["bangalore", "delhi", "mumbai"].map(key => (
                <button key={key}
                  onClick={() => changeCity(key)}
                  style={{
                    flex: 1, padding: '7px 0', cursor: 'pointer',
                    background: city?.current === key ? 'rgba(15,163,177,0.15)' : 'transparent',
                    border: `1px solid ${city?.current === key ? 'var(--accent-cyan)' : 'var(--border-glow)'}`,
                    borderRadius: 2, fontSize: 11, fontFamily: 'Rajdhani', fontWeight: 700,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                    color: city?.current === key ? 'var(--accent-cyan)' : 'var(--text-dim)',
                    transition: 'all 0.15s',
                    boxShadow: city?.current === key ? '0 0 12px rgba(15,163,177,0.2)' : 'none',
                  }}>
                  {cities[key]?.emoji} {cities[key]?.name || key}
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Scenario Mode" titleIcon={Settings}>
            <div style={{ display: 'flex', gap: 8 }}>
              {["normal", "rush_hour", "low_demand", "chaos"].map(key => (
                <button key={key}
                  onClick={() => changeScenario(key)}
                  style={{
                    flex: 1, padding: '7px 0', cursor: 'pointer',
                    background: scenario?.current === key ? 'rgba(155,93,229,0.15)' : 'transparent',
                    border: `1px solid ${scenario?.current === key ? 'var(--accent-purple)' : 'var(--border-glow)'}`,
                    borderRadius: 2, fontSize: 11, fontFamily: 'Rajdhani', fontWeight: 700,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                    color: scenario?.current === key ? 'var(--accent-purple)' : 'var(--text-dim)',
                    transition: 'all 0.15s',
                    boxShadow: scenario?.current === key ? '0 0 12px rgba(155,93,229,0.2)' : 'none',
                  }}>
                  {scenarios[key]?.emoji} {scenarios[key]?.name || key}
                </button>
              ))}
            </div>
          </Panel>
        </div>

        {/* ── KEY METRICS ── */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10, marginBottom: 16,
        }}>
          <MetricCard icon={Package}       label="Total Orders"  value={metrics.total_orders}                  color="cyan"   />
          <MetricCard icon={CheckCircle}   label="Delivered"     value={metrics.total_delivered}               color="green"  />
          <MetricCard icon={AlertTriangle} label="Reassignments" value={metrics.total_reassigned}              color="amber"  />
          <MetricCard icon={Activity}      label="On-Time Rate"  value={`${metrics.on_time_rate}%`}            color="green"  />
          <MetricCard icon={TrendingUp}    label="Dist Saved"    value={`${metrics.dist_saved_pct}%`}          color="purple" />
          <MetricCard icon={Zap}           label="Cost Saved"    value={`₹${metrics.cost_saved_inr?.toLocaleString()}`} color="amber" />
        </div>

        {/* ── CHARTS ROW ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <Panel title="On-Time Rate · Trend" titleIcon={Activity}>
            <ResponsiveContainer width="100%" height={170}>
              <LineChart data={history}>
                <XAxis
                  dataKey="tick"
                  tick={{ fontSize: 9, fill: '#3a6070', fontFamily: 'Share Tech Mono' }}
                  axisLine={{ stroke: 'var(--border-dim)' }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 105]}
                  tick={{ fontSize: 9, fill: '#3a6070', fontFamily: 'Share Tech Mono' }}
                  axisLine={{ stroke: 'var(--border-dim)' }}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} />
                <Line
                  type="monotone" dataKey="on_time_rate" stroke="var(--accent-green)"
                  strokeWidth={1.5} dot={false} name="On-Time %"
                  style={{ filter: 'drop-shadow(0 0 4px var(--accent-green))' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Panel>

          <Panel title="Order Queue · State" titleIcon={Package}>
            <ResponsiveContainer width="100%" height={170}>
              <BarChart data={[{
                name: "Orders",
                Pending:   metrics.pending,
                Assigned:  metrics.assigned,
                Delivered: metrics.total_delivered,
                Failed:    metrics.failed
              }]}>
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 9, fill: '#3a6070', fontFamily: 'Share Tech Mono' }}
                  axisLine={{ stroke: 'var(--border-dim)' }} tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 9, fill: '#3a6070', fontFamily: 'Share Tech Mono' }}
                  axisLine={{ stroke: 'var(--border-dim)' }} tickLine={false}
                />
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 9, fontFamily: 'Share Tech Mono', color: 'var(--text-dim)' }} />
                <Bar dataKey="Pending"   fill="#3a6070" radius={[2,2,0,0]} />
                <Bar dataKey="Assigned"  fill="var(--accent-cyan)" radius={[2,2,0,0]} />
                <Bar dataKey="Delivered" fill="var(--accent-green)" radius={[2,2,0,0]} />
                <Bar dataKey="Failed"    fill="var(--accent-red)" radius={[2,2,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Panel>
        </div>

        {/* ── LIVE MAP ── */}
        <div style={{ marginBottom: 16 }}>
          <MapPanel currentCity={city?.current || "bangalore"} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          {/* Agents */}
          <Panel title="Agent Matrix" titleIcon={Truck}>
            <div style={{ maxHeight: 256, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
              {agents.map(a => (
                <div key={a.agent_id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px',
                  background: 'var(--bg-panel-alt)', border: '1px solid var(--border-dim)',
                  borderRadius: 2,
                  borderLeft: `2px solid ${a.status === "busy" ? 'var(--accent-amber)' : 'var(--accent-green)'}`,
                }}>
                  {/* ID block */}
                  <div style={{
                    width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: a.status === "busy" ? 'rgba(255,183,3,0.1)' : 'rgba(0,255,136,0.1)',
                    border: `1px solid ${a.status === "busy" ? 'rgba(255,183,3,0.3)' : 'rgba(0,255,136,0.3)'}`,
                    borderRadius: 1,
                    fontFamily: 'Orbitron', fontSize: 10, fontWeight: 700,
                    color: a.status === "busy" ? 'var(--accent-amber)' : 'var(--accent-green)',
                  }}>
                    {a.agent_id}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <span style={{
                        fontSize: 11, fontWeight: 700, fontFamily: 'Rajdhani', color: 'var(--text-primary)',
                        letterSpacing: '0.08em',
                      }}>
                        AGENT_{String(a.agent_id).padStart(2,'0')}
                      </span>
                      <Badge text={a.status} color={a.status === "busy" ? "amber" : "green"} />
                    </div>
                    {/* Load bar */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        flex: 1, height: 3, background: 'var(--bg-deep)',
                        borderRadius: 1, overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${a.load_pct}%`,
                          background: a.load_pct >= 100
                            ? 'var(--accent-red)'
                            : a.load_pct > 60
                            ? 'var(--accent-amber)'
                            : 'var(--accent-green)',
                          borderRadius: 1,
                          boxShadow: `0 0 6px ${a.load_pct >= 100 ? 'var(--accent-red)' : a.load_pct > 60 ? 'var(--accent-amber)' : 'var(--accent-green)'}`,
                          transition: 'width 0.4s ease',
                        }} />
                      </div>
                      <span style={{
                        fontSize: 9, fontFamily: 'Share Tech Mono',
                        color: 'var(--text-dim)', minWidth: 28, textAlign: 'right',
                      }}>
                        {a.load_pct}%
                      </span>
                    </div>
                  </div>

                  <div style={{
                    fontSize: 9, fontFamily: 'Share Tech Mono',
                    color: 'var(--text-dim)', textAlign: 'right',
                  }}>
                    {a.current_orders.length}/{a.capacity}<br />
                    <span style={{ color: 'var(--text-dim)', fontSize: 8 }}>LOAD</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* Live Decision Log */}
          <Panel title="Decision Log · Live" titleIcon={Activity}
            badge={<span style={{
              fontSize: 9, fontFamily: 'Share Tech Mono', color: 'var(--accent-cyan)',
              letterSpacing: '0.1em',
            }} className="blink">● STREAMING</span>}
          >
            <div style={{
              maxHeight: 256, overflowY: 'auto',
              display: 'flex', flexDirection: 'column', gap: 4,
            }}>
              {logs.length === 0 && (
                <div style={{
                  fontSize: 10, fontFamily: 'Share Tech Mono',
                  color: 'var(--text-dim)', padding: 8,
                }}>
                  AWAITING EVENTS<span className="blink">_</span>
                </div>
              )}
              {logs.map((log, i) => <LogEntry key={i} log={log} i={i} />)}
            </div>
          </Panel>
        </div>

        {/* ── ANOMALIES ── */}
        {anomalies && anomalies.total > 0 && (
          <Panel
            title="Anomaly Detection System"
            titleIcon={AlertTriangle}
            badge={
              <div style={{ display: 'flex', gap: 6 }}>
                <Badge text={`${anomalies.critical_count} CRIT`} color="red" />
                <Badge text={`${anomalies.warning_count} WARN`} color="amber" />
              </div>
            }
            style={{ marginBottom: 16 }}
          >
            <div style={{
              display: 'flex', flexDirection: 'column', gap: 4,
              maxHeight: 128, overflowY: 'auto',
            }}>
              {anomalies.recent?.slice(-5).reverse().map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                  padding: '5px 10px', borderRadius: 1,
                  background: a.severity === "critical" ? 'rgba(255,56,96,0.06)' : 'rgba(255,183,3,0.06)',
                  border: `1px solid ${a.severity === "critical" ? 'rgba(255,56,96,0.2)' : 'rgba(255,183,3,0.2)'}`,
                  fontSize: 10, fontFamily: 'Share Tech Mono',
                  color: a.severity === "critical" ? '#ff8fa3' : '#ffd166',
                }}>
                  <span style={{ opacity: 0.5, minWidth: 50 }}>[{a.time}]</span>
                  <span style={{ opacity: 0.5, minWidth: 48 }}>T:{a.tick}</span>
                  <span>{a.message}</span>
                </div>
              ))}
            </div>
          </Panel>
        )}

        {/* ── AI AGENT + NL QUERY ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          {/* Autonomous AI Agent */}
          <Panel title="Autonomous AI Agent" titleIcon={Brain}
            badge={agentAI && (
              <Badge
                text={agentAI.status}
                color={agentAI.status === "complete" ? "green" : agentAI.status === "running" ? "amber" : "blue"}
              />
            )}
          >
            {agentAI && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                  {[
                    { val: agentAI.total_obs, label: 'OBSERVATIONS' },
                    { val: agentAI.total_actions, label: 'ACTIONS' },
                  ].map(({ val, label }) => (
                    <div key={label} style={{
                      background: 'var(--bg-panel-alt)', border: '1px solid var(--border-dim)',
                      borderRadius: 2, padding: '10px', textAlign: 'center',
                    }}>
                      <div style={{
                        fontFamily: 'Orbitron', fontSize: 20, fontWeight: 700,
                        color: 'var(--accent-cyan)',
                        textShadow: '0 0 10px rgba(15,163,177,0.5)',
                      }}>
                        {val}
                      </div>
                      <div style={{
                        fontSize: 8, fontFamily: 'Share Tech Mono',
                        color: 'var(--text-dim)', letterSpacing: '0.15em', marginTop: 3,
                      }}>
                        {label}
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{
                  maxHeight: 120, overflowY: 'auto',
                  display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12,
                }}>
                  {agentAI.observations?.map((obs, i) => (
                    <div key={i} style={{
                      fontSize: 9, fontFamily: 'Share Tech Mono', padding: '4px 8px',
                      borderRadius: 1, lineHeight: 1.6,
                      background: obs.severity === "critical"
                        ? 'rgba(255,56,96,0.06)' : obs.severity === "warning"
                        ? 'rgba(255,183,3,0.06)' : 'rgba(0,255,136,0.05)',
                      color: obs.severity === "critical"
                        ? '#ff8fa3' : obs.severity === "warning"
                        ? '#ffd166' : '#00cc6a',
                      border: '1px solid transparent',
                    }}>
                      ◈ [{obs.time}] {obs.text?.slice(0, 120)}...
                    </div>
                  ))}
                </div>

                <Btn onClick={async () => {
                  setLoad("agent", true);
                  notify("Agent cycle initiated — scanning fleet state...", "info");
                  await post("/api/agent/run");
                  await refresh();
                  setLoad("agent", false);
                  notify("Agent cycle complete — observations updated.", "success");
                }} variant="primary" disabled={loading.agent}>
                  {loading.agent ? "⟳ RUNNING..." : "⬡ RUN AGENT CYCLE"}
                </Btn>
              </>
            )}
          </Panel>

          {/* NL Query */}
          <Panel title="Natural Language Interface" titleIcon={MessageSquare}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
              {["Which agent has highest load?", "System status?", "How many SLA breaches?", "Change scenario?"].map(q => (
                <button key={q} onClick={() => askQuery(q)}
                  style={{
                    padding: '4px 10px', cursor: 'pointer',
                    background: 'var(--bg-panel-alt)', border: '1px solid var(--border-glow)',
                    borderRadius: 2, fontSize: 9, fontFamily: 'Share Tech Mono',
                    color: 'var(--text-secondary)', letterSpacing: '0.06em',
                    transition: 'all 0.15s',
                  }}>
                  {q}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <input
                type="text"
                value={nlQuery}
                onChange={e => setNlQuery(e.target.value)}
                onKeyDown={e => e.key === "Enter" && askQuery()}
                placeholder="INPUT QUERY_"
                style={{
                  flex: 1,
                  background: 'var(--bg-deep)', border: '1px solid var(--border-glow)',
                  color: 'var(--text-primary)', borderRadius: 2,
                  padding: '8px 12px', fontSize: 11,
                  fontFamily: 'Share Tech Mono', letterSpacing: '0.06em',
                  outline: 'none',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--accent-cyan)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-glow)'}
              />
              <Btn onClick={() => askQuery()} variant="primary" disabled={nlLoading}>
                {nlLoading ? "···" : "EXEC"}
              </Btn>
            </div>

            {nlAnswer && (
              <div style={{
                background: 'rgba(15,163,177,0.06)', border: '1px solid rgba(15,163,177,0.2)',
                borderRadius: 2, padding: '10px 12px',
                fontSize: 11, fontFamily: 'Share Tech Mono', color: 'var(--text-mono)',
                lineHeight: 1.7, letterSpacing: '0.04em',
              }}>
                <span style={{ color: 'var(--accent-cyan)', marginRight: 8 }}>▶</span>
                {nlAnswer}
              </div>
            )}
          </Panel>
        </div>

        {/* ── RL + A/B ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {/* RL Agent */}
          <Panel title="RL Dispatch Agent" titleIcon={Zap}
            badge={rlData && <Badge text={rlData.status} color={rlData.status === "trained" ? "green" : "amber"} />}
          >
            {rlData && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 12 }}>
                {[
                  { val: rlData.states_explored, label: 'STATES' },
                  { val: rlData.episodes, label: 'EPISODES' },
                  { val: rlData.avg_reward_100, label: 'AVG REWARD' },
                ].map(({ val, label }) => (
                  <div key={label} style={{
                    background: 'var(--bg-panel-alt)', border: '1px solid var(--border-dim)',
                    borderRadius: 2, padding: '8px', textAlign: 'center',
                  }}>
                    <div style={{
                      fontFamily: 'Orbitron', fontSize: 16, fontWeight: 700,
                      color: 'var(--accent-amber)',
                      textShadow: '0 0 8px rgba(255,183,3,0.4)',
                    }}>
                      {val}
                    </div>
                    <div style={{
                      fontSize: 8, fontFamily: 'Share Tech Mono',
                      color: 'var(--text-dim)', letterSpacing: '0.12em', marginTop: 3,
                    }}>
                      {label}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <Btn onClick={async () => {
                setLoad("rl_train", true);
                notify("RL training started — 50 episodes running...", "info");
                await post("/api/rl/train?episodes=50");
                await refresh();
                setLoad("rl_train", false);
                notify("RL training complete! Model updated.", "success");
              }} disabled={loading.rl_train}>
                {loading.rl_train
                  ? <span>⟳ <span className="spin" style={{ display: 'inline-block' }}>◌</span> TRAINING...</span>
                  : "▶ TRAIN 50 EPS"}
              </Btn>
              <Btn onClick={async () => {
                setLoad("rl_deploy", true);
                notify("Deploying RL agent to dispatch queue...", "info");
                const res = await post("/api/rl/assign");
                setLoad("rl_deploy", false);
                if (res) notify(`RL assigned ${res.assigned ?? '?'} orders, skipped ${res.skipped ?? '?'}`, "success");
                else notify("RL deploy failed — check backend", "error");
                await refresh();
              }} variant="success" disabled={loading.rl_deploy}>
                {loading.rl_deploy
                  ? <span>⟳ ASSIGNING...</span>
                  : "⚡ DEPLOY RL"}
              </Btn>
            </div>
          </Panel>

          {/* A/B Testing */}
          <Panel title="A/B Test · Greedy vs RL" titleIcon={RefreshCw}>
            {abData?.results?.winner && (
              <div style={{
                padding: '8px 12px', marginBottom: 12, borderRadius: 2,
                background: abData.results.winner === "RL Agent"
                  ? 'rgba(155,93,229,0.08)' : 'rgba(15,163,177,0.08)',
                border: `1px solid ${abData.results.winner === "RL Agent"
                  ? 'rgba(155,93,229,0.3)' : 'rgba(15,163,177,0.3)'}`,
                fontFamily: 'Orbitron', fontSize: 11, fontWeight: 700,
                color: abData.results.winner === "RL Agent" ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                letterSpacing: '0.1em',
              }}>
                ◆ WINNER: {abData.results.winner.toUpperCase()}
              </div>
            )}
            {abData?.results?.greedy && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                <div style={{
                  background: 'rgba(15,163,177,0.06)', border: '1px solid rgba(15,163,177,0.2)',
                  borderRadius: 2, padding: 10,
                }}>
                  <div style={{
                    fontSize: 9, fontFamily: 'Share Tech Mono', letterSpacing: '0.12em',
                    color: 'var(--accent-cyan)', marginBottom: 6,
                  }}>
                    ◈ GREEDY
                  </div>
                  <div style={{ fontSize: 14, fontFamily: 'Orbitron', color: '#fff', marginBottom: 2 }}>
                    {abData.results.greedy.avg_on_time}%
                  </div>
                  <div style={{ fontSize: 9, fontFamily: 'Share Tech Mono', color: 'var(--text-dim)' }}>
                    {abData.results.greedy.avg_distance}u avg dist
                  </div>
                </div>
                <div style={{
                  background: 'rgba(155,93,229,0.06)', border: '1px solid rgba(155,93,229,0.2)',
                  borderRadius: 2, padding: 10,
                }}>
                  <div style={{
                    fontSize: 9, fontFamily: 'Share Tech Mono', letterSpacing: '0.12em',
                    color: 'var(--accent-purple)', marginBottom: 6,
                  }}>
                    ◈ RL AGENT
                  </div>
                  <div style={{ fontSize: 14, fontFamily: 'Orbitron', color: '#fff', marginBottom: 2 }}>
                    {abData.results.rl.avg_on_time}%
                  </div>
                  <div style={{ fontSize: 9, fontFamily: 'Share Tech Mono', color: 'var(--text-dim)' }}>
                    {abData.results.rl.avg_distance}u avg dist
                  </div>
                </div>
              </div>
            )}
            <Btn onClick={async () => {
              setLoad("ab", true);
              notify("A/B test started — Greedy vs RL running 20 ticks each...", "info");
              await post("/api/ab/run?ticks=20");
              setTimeout(async () => {
                await refresh();
                setLoad("ab", false);
                notify("A/B test complete — results updated!", "success");
              }, 35000);
            }} variant="primary" disabled={loading.ab}>
              {loading.ab ? "⟳ RUNNING TEST..." : "⚔ EXECUTE A/B TEST"}
            </Btn>
          </Panel>
        </div>
        
        {/* ── DEMAND FORECAST ── */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16 }}>
          <Panel title="Demand Forecast" titleIcon={BarChart2}>
            {forecast && forecast.history?.length > 1 ? (
              <>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8, marginBottom:10 }}>
                  {[
                    { val: forecast.prediction, label:'NEXT TICK' },
                    { val: forecast.avg_demand, label:'AVG DEMAND' },
                    { val: forecast.trend?.toUpperCase(), label:'TREND' },
                  ].map(({ val, label }) => (
                    <div key={label} style={{ background:'var(--bg-panel-alt)', border:'1px solid var(--border-dim)', borderRadius:2, padding:'8px', textAlign:'center' }}>
                      <div style={{ fontFamily:'Orbitron', fontSize:14, fontWeight:700, color:'var(--accent-purple)', textShadow:'0 0 8px rgba(155,93,229,0.4)' }}>{val}</div>
                      <div style={{ fontSize:8, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.12em', marginTop:3 }}>{label}</div>
                    </div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={110}>
                  <LineChart data={forecast.history.map((v,i) => ({ tick:i, demand:v }))}>
                    <XAxis dataKey="tick" tick={{ fontSize:8, fill:'#3a6070', fontFamily:'Share Tech Mono' }} axisLine={{ stroke:'var(--border-dim)' }} tickLine={false} />
                    <YAxis tick={{ fontSize:8, fill:'#3a6070', fontFamily:'Share Tech Mono' }} axisLine={{ stroke:'var(--border-dim)' }} tickLine={false} />
                    <Tooltip {...tooltipStyle} />
                    <Line type="monotone" dataKey="demand" stroke="var(--accent-purple)" strokeWidth={1.5} dot={false} name="Demand" />
                  </LineChart>
                </ResponsiveContainer>
              </>
            ) : (
              <div style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)', padding:8 }}>COLLECTING DATA<span className="blink">_</span></div>
            )}
          </Panel>

          {/* ── WEIGHT TUNER ── */}
          <Panel title="Weight Auto-Tuner · Results" titleIcon={Settings}>
            <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:12 }}>
              <Btn onClick={async () => {
                notify("Weight tuning started — testing 10 combinations...","info");
                await post("/api/tuning/start");
                await refresh();
              }} variant="primary">▶ START TUNING</Btn>
              {tuning && <Badge text={tuning.status} color={tuning.status==="complete"?"green":tuning.status==="running"?"amber":"blue"} />}
              {tuning?.best && <span style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--accent-green)' }}>Best: {tuning.best.score} score</span>}
            </div>
            {tuning?.results?.length > 0 && (
              <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
                <div style={{ display:'grid', gridTemplateColumns:'40px 60px 70px 70px 70px 60px 60px 60px', gap:6, padding:'4px 8px', fontSize:8, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.1em' }}>
                  <span>RANK</span><span>SCORE</span><span>ON-TIME</span><span>DIST</span><span>PROX</span><span>CAP</span><span>URG</span><span>DEAD</span>
                </div>
                {tuning.results.slice(0,5).map((r,i) => (
                  <div key={i} style={{ display:'grid', gridTemplateColumns:'40px 60px 70px 70px 70px 60px 60px 60px', gap:6, padding:'6px 8px', borderRadius:2, background:i===0?'rgba(0,255,136,0.05)':'var(--bg-panel-alt)', border:`1px solid ${i===0?'rgba(0,255,136,0.2)':'var(--border-dim)'}`, fontSize:10, fontFamily:'Share Tech Mono' }}>
                    <span style={{ color:i===0?'var(--accent-green)':'var(--text-dim)' }}>#{i+1}</span>
                    <span style={{ color:'var(--accent-amber)' }}>{r.score}</span>
                    <span style={{ color:'var(--accent-green)' }}>{r.on_time_rate}%</span>
                    <span style={{ color:'var(--text-secondary)' }}>{r.avg_distance}u</span>
                    <span style={{ color:'var(--accent-cyan)' }}>{r.weights.W_PROXIMITY}</span>
                    <span style={{ color:'var(--text-secondary)' }}>{r.weights.W_CAPACITY}</span>
                    <span style={{ color:'var(--text-secondary)' }}>{r.weights.W_URGENCY}</span>
                    <span style={{ color:'var(--text-secondary)' }}>{r.weights.W_DEADLINE}</span>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>

        {/* ── DECISION EXPLAINABILITY ── */}
        <Panel title="Decision Explainability" titleIcon={Search} style={{ marginBottom:16 }}>
          <div style={{ display:'flex', gap:10, marginBottom:12, alignItems:'center' }}>
            <select
              value={selectedOrder}
              onChange={e => { setSelectedOrder(e.target.value); fetchExplain(e.target.value); }}
              style={{ flex:1, background:'var(--bg-deep)', border:'1px solid var(--border-glow)', color:'var(--text-primary)', borderRadius:2, padding:'7px 10px', fontSize:11, fontFamily:'Share Tech Mono', outline:'none', cursor:'pointer' }}
            >
              <option value="">SELECT ORDER TO EXPLAIN_</option>
              {assignedOrders.slice(0,20).map(o => (
                <option key={o.order_id} value={o.order_id}>
                  Order {o.order_id} | P{o.priority} | Deadline {o.deadline}s
                </option>
              ))}
            </select>
          </div>
          {explain && explain.candidates && (
            <>
              <div style={{ display:'flex', gap:10, marginBottom:10, flexWrap:'wrap' }}>
                {[
                  { label:'ORDER',    val:`#${explain.order_id}` },
                  { label:'PRIORITY', val:`P${explain.priority}` },
                  { label:'DEADLINE', val:`${explain.deadline}s` },
                  { label:'ASSIGNED', val:`AGENT ${explain.assigned_agent}` },
                ].map(({ label, val }) => (
                  <div key={label} style={{ background:'var(--bg-panel-alt)', border:'1px solid var(--border-dim)', borderRadius:2, padding:'6px 12px' }}>
                    <div style={{ fontSize:8, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.12em' }}>{label}</div>
                    <div style={{ fontSize:12, fontFamily:'Orbitron', color:'var(--accent-cyan)', marginTop:2 }}>{val}</div>
                  </div>
                ))}
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
                {explain.candidates.map((c,i) => (
                  <div key={i} style={{ display:'grid', gridTemplateColumns:'60px 80px 80px 80px 80px 1fr 80px', gap:8, alignItems:'center', padding:'7px 10px', borderRadius:2, background:c.is_assigned?'rgba(0,255,136,0.06)':'var(--bg-panel-alt)', border:`1px solid ${c.is_assigned?'rgba(0,255,136,0.3)':c.eligible?'var(--border-dim)':'rgba(255,56,96,0.2)'}`, fontSize:10, fontFamily:'Share Tech Mono' }}>
                    <span style={{ color:'var(--accent-cyan)' }}>A{c.agent_id}</span>
                    <span style={{ color:'var(--text-secondary)' }}>{c.score.toFixed(4)}</span>
                    <span style={{ color:'var(--text-dim)' }}>{c.distance}u</span>
                    <span style={{ color:'var(--text-dim)' }}>{c.est_time}s ETA</span>
                    <span style={{ color:'var(--text-dim)' }}>{c.delay}x delay</span>
                    <span style={{ color:c.eligible?'var(--accent-green)':'var(--accent-red)', fontSize:9 }}>
                      {c.eligible ? '✓ ELIGIBLE' : `✗ ${c.reason}`}
                    </span>
                    <span style={{ color:c.is_assigned?'var(--accent-green)':'transparent', fontWeight:700 }}>
                      {c.is_assigned ? '⭐ CHOSEN' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </Panel>
        {/* ── INCIDENT REPORTS ── */}
        <Panel title="LLM Incident Report Generator" titleIcon={FileText} style={{ marginBottom:16 }}>
          <ReportPanel />
        </Panel>

        {/* ── SIMULATION CONTROLS ── */}
        <Panel title="Simulation Controls · Reset & Replay" titleIcon={RefreshCw} style={{ marginBottom:16 }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>

            {/* Reset + Speed */}
            <div>
              <div style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.15em', marginBottom:10 }}>SIMULATION CONTROL</div>
              <div style={{ display:'flex', gap:8, marginBottom:14 }}>
                <Btn onClick={async () => {
                  if (!window.confirm("Reset simulation? All progress will be lost.")) return;
                  await post("/api/reset");
                  notify("Simulation reset — fresh start!", "success");
                  await refresh();
                }} variant="danger">
                  ⟳ RESET SIM
                </Btn>
              </div>

              <div style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.15em', marginBottom:8 }}>SIMULATION SPEED</div>
              <div style={{ display:'flex', gap:6 }}>
                {[0.5, 1.0, 2.0, 5.0].map(s => (
                  <button key={s}
                    onClick={async () => {
                      await post(`/api/speed/${s}`);
                      setSpeed(s);
                      notify(`Speed set to ${s}x`, "info");
                    }}
                    style={{
                      flex:1, padding:'7px 0', cursor:'pointer',
                      background: speed===s ? 'rgba(255,183,3,0.15)' : 'transparent',
                      border: `1px solid ${speed===s ? 'var(--accent-amber)' : 'var(--border-glow)'}`,
                      borderRadius:2, fontSize:11, fontFamily:'Orbitron', fontWeight:700,
                      color: speed===s ? 'var(--accent-amber)' : 'var(--text-dim)',
                      transition:'all 0.15s',
                    }}>
                    {s}x
                  </button>
                ))}
              </div>
              <div style={{ fontSize:9, fontFamily:'Share Tech Mono', color:'var(--text-dim)', marginTop:6 }}>
                Current: <span style={{ color:'var(--accent-amber)' }}>{speed}x</span> · Tick interval: <span style={{ color:'var(--accent-cyan)' }}>{(3/speed).toFixed(1)}s</span>
              </div>
            </div>

            {/* Replay viewer */}
            <div>
              <div style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)', letterSpacing:'0.15em', marginBottom:10 }}>
                SESSION REPLAY · {replay?.total_ticks || 0} TICKS LOGGED
              </div>
              {replay && replay.total_ticks > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={120}>
                    <LineChart data={replay.sessions.slice(-50)}>
                      <XAxis dataKey="tick" tick={{ fontSize:8, fill:'#3a6070', fontFamily:'Share Tech Mono' }} axisLine={{ stroke:'var(--border-dim)' }} tickLine={false} />
                      <YAxis domain={[0,105]} tick={{ fontSize:8, fill:'#3a6070', fontFamily:'Share Tech Mono' }} axisLine={{ stroke:'var(--border-dim)' }} tickLine={false} />
                      <Tooltip {...tooltipStyle} />
                      <Line type="monotone" dataKey="on_time_rate" stroke="var(--accent-green)" strokeWidth={1.5} dot={false} name="On-Time %" />
                      <Line type="monotone" dataKey="agents_busy" stroke="var(--accent-amber)" strokeWidth={1} dot={false} name="Agents Busy" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div style={{ fontSize:9, fontFamily:'Share Tech Mono', color:'var(--text-dim)', marginTop:6 }}>
                    Ticks <span style={{ color:'var(--accent-cyan)' }}>{replay.tick_range?.min}</span> → <span style={{ color:'var(--accent-cyan)' }}>{replay.tick_range?.max}</span> · Stored in SQLite
                  </div>
                </>
              ) : (
                <div style={{ fontSize:10, fontFamily:'Share Tech Mono', color:'var(--text-dim)', padding:8 }}>
                  NO SESSION DATA<span className="blink">_</span>
                </div>
              )}
            </div>
          </div>
        </Panel>
        {/* ── FOOTER ── */}
        <div style={{
          borderTop: '1px solid var(--border-dim)', paddingTop: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{
            fontFamily: 'Share Tech Mono', fontSize: 9,
            color: 'var(--text-dim)', letterSpacing: '0.15em',
          }}>
            FLEET-AI ENGINE v4.0 · WS:SQLITE:RL:GEMINI
          </span>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            {[
              { label: 'TICK', val: String(tick).padStart(4,'0') },
              { label: 'NODE', val: city?.config?.name?.toUpperCase() || 'BANGALORE' },
              { label: 'MODE', val: scenario?.config?.name?.toUpperCase() || 'NORMAL' },
            ].map(({ label, val }) => (
              <span key={label} style={{
                fontSize: 9, fontFamily: 'Share Tech Mono', letterSpacing: '0.12em',
                color: 'var(--text-dim)',
              }}>
                {label}: <span style={{ color: 'var(--accent-cyan)' }}>{val}</span>
              </span>
            ))}
          </div>
        </div>

      </div>
    </>
  );
}