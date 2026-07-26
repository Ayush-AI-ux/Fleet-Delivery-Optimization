import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline,
         Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import axios from "axios";

const API = "https://fleet-delivery-optimization-production.up.railway.app";

const CITY_CENTERS = {
  bangalore: { center: [12.97, 77.59], zoom: 12 },
  delhi:     { center: [28.61, 77.20], zoom: 11 },
  mumbai:    { center: [19.07, 72.87], zoom: 12 }
};

const PRIORITY_COLORS = {
  1: "#94a3b8",
  2: "#3b82f6",
  3: "#ef4444"
};

const AGENT_COLORS = {
  idle:   "#22c55e",
  busy:   "#f59e0b",
  breach: "#ef4444"
};

// ── MAP VIEW UPDATER ──────────────────────────────────────────────────

function MapUpdater({ center, zoom }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom); }, [center, zoom]);
  return null;
}

// ── LERP HELPER ───────────────────────────────────────────────────────

function lerp(a, b, t) {
  return a + (b - a) * t;
}

// ── MAIN MAP PANEL ────────────────────────────────────────────────────

export default function MapPanel({ currentCity = "bangalore" }) {
  const [routes,       setRoutes]       = useState([]);
  const [anomalies,    setAnomalies]    = useState(null);

  // animated positions — interpolated between ticks
  const agentPositions = useRef({});   // { agent_id: { lat, lon } }
  const agentTargets   = useRef({});   // { agent_id: { lat, lon } }
  const agentTrails    = useRef({});   // { agent_id: [[lat,lon], ...] }
  const agentBreaching = useRef({});   // { agent_id: bool }
  const animFrame      = useRef(null);
  const lastTick       = useRef(0);
  const startTime      = useRef(null);

  const [animatedAgents, setAnimatedAgents] = useState([]);
  const TICK_DURATION = 3000; // ms — matches backend TICK_INTERVAL

  const cityConfig = CITY_CENTERS[currentCity] || CITY_CENTERS.bangalore;

  // ── FETCH ROUTES ───────────────────────────────────────────────────

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [r, a] = await Promise.all([
          axios.get(`${API}/api/routes`),
          axios.get(`${API}/api/anomalies`)
        ]);

        const newRoutes = r.data;
        setRoutes(newRoutes);
        setAnomalies(a.data);

        // update targets for animation
        newRoutes.forEach(agent => {
          const id = agent.agent_id;
          const newPos = { lat: agent.agent_lat, lon: agent.agent_lon };

          if (!agentPositions.current[id]) {
            // first time — set position directly
            agentPositions.current[id] = { ...newPos };
          }

          // update target
          agentTargets.current[id] = { ...newPos };

          // init trail
          if (!agentTrails.current[id]) {
            agentTrails.current[id] = [];
          }
        });

        // reset animation start time on new tick
        startTime.current = performance.now();

      } catch (e) {}
    };

    fetchData();
    const interval = setInterval(fetchData, TICK_DURATION);
    return () => clearInterval(interval);
  }, []);

  // ── ANIMATION LOOP ─────────────────────────────────────────────────

  useEffect(() => {
    const animate = (now) => {
      if (!startTime.current) startTime.current = now;

      const elapsed = now - startTime.current;
      const t = Math.min(elapsed / TICK_DURATION, 1); // 0 → 1 over tick duration

      // smooth easing
      const eased = t < 0.5
        ? 2 * t * t
        : -1 + (4 - 2 * t) * t;

      const updated = [];

      Object.keys(agentTargets.current).forEach(id => {
        const target = agentTargets.current[id];
        const current = agentPositions.current[id] || target;

        // interpolate position
        const newLat = lerp(current.lat, target.lat, eased);
        const newLon = lerp(current.lon, target.lon, eased);

        agentPositions.current[id] = { lat: newLat, lon: newLon };

        // update trail every ~500ms
        const trail = agentTrails.current[id] || [];
        if (trail.length === 0 || elapsed % 500 < 16) {
          const newTrail = [...trail, [newLat, newLon]].slice(-8); // keep last 8 points
          agentTrails.current[id] = newTrail;
        }

        // find route data for this agent
        const routeData = routes.find(r => r.agent_id === parseInt(id));

        updated.push({
          agent_id:  parseInt(id),
          lat:       newLat,
          lon:       newLon,
          trail:     agentTrails.current[id] || [],
          status:    routeData?.status || "idle",
          load_pct:  routeData?.load_pct || 0,
          order_id:  routeData?.order_id,
          order_lat: routeData?.order_lat,
          order_lon: routeData?.order_lon,
          priority:  routeData?.priority || 1,
          is_breaching: agentBreaching.current[id] || false,
        });
      });

      setAnimatedAgents(updated);
      animFrame.current = requestAnimationFrame(animate);
    };

    animFrame.current = requestAnimationFrame(animate);
    return () => {
      if (animFrame.current) cancelAnimationFrame(animFrame.current);
    };
  }, [routes]);

  // ── DETECT BREACHING AGENTS from anomalies ─────────────────────────

  useEffect(() => {
    if (!anomalies?.recent) return;
    anomalies.recent.forEach(a => {
      if (a.type === "breach_spike" || a.severity === "critical") {
        // mark all busy agents as potentially breaching for visual
      }
    });
  }, [anomalies]);

  // ── RENDER ─────────────────────────────────────────────────────────

  return (
    <div style={{
      background: "var(--bg-panel)",
      border: "1px solid var(--border-glow)",
      borderRadius: 2,
      overflow: "hidden",
      position: "relative",
    }}>
      {/* Header */}
      <div style={{
        padding: "10px 14px",
        borderBottom: "1px solid var(--border-dim)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "rgba(15,163,177,0.04)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.18em",
            color: "var(--text-secondary)", textTransform: "uppercase",
            fontFamily: "Rajdhani, sans-serif",
          }}>
            Live Route Animation Map
          </span>
          <span style={{
            fontSize: 9, fontFamily: "Share Tech Mono",
            color: "var(--accent-green)", letterSpacing: "0.1em",
          }}>
            ● SMOOTH INTERPOLATION
          </span>
        </div>

        {/* Legend */}
        <div style={{ display: "flex", gap: 12, fontSize: 9, fontFamily: "Share Tech Mono", color: "var(--text-dim)" }}>
          {[
            { color: "#ef4444", label: "P3 route" },
            { color: "#3b82f6", label: "P2 route" },
            { color: "#94a3b8", label: "P1 route" },
            { color: "#f59e0b", label: "Agent busy" },
            { color: "#22c55e", label: "Agent idle" },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 10, height: 3, background: color, borderRadius: 1 }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={cityConfig.center}
        zoom={cityConfig.zoom}
        style={{ height: "480px", width: "100%" }}
        zoomControl={true}
      >
        <MapUpdater center={cityConfig.center} zoom={cityConfig.zoom} />

        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com">CARTO</a>'
        />

        {/* ── ROUTE LINES ── */}
        {animatedAgents.map(a => a.order_lat && (
          <Polyline
            key={`route-${a.agent_id}`}
            positions={[[a.lat, a.lon], [a.order_lat, a.order_lon]]}
            color={PRIORITY_COLORS[a.priority] || "#3b82f6"}
            weight={2}
            opacity={0.7}
            dashArray="6 10"
          />
        ))}

        {/* ── AGENT TRAILS ── */}
        {animatedAgents.map(a => a.trail.length > 1 && (
          <Polyline
            key={`trail-${a.agent_id}`}
            positions={a.trail}
            color={a.status === "busy" ? "#f59e0b" : "#22c55e"}
            weight={1.5}
            opacity={0.35}
            dashArray="2 4"
          />
        ))}

        {/* ── ORDER DESTINATIONS ── */}
        {animatedAgents.map(a => a.order_lat && (
          <CircleMarker
            key={`order-${a.order_id}`}
            center={[a.order_lat, a.order_lon]}
            radius={5}
            fillColor={PRIORITY_COLORS[a.priority]}
            color="white"
            weight={1.5}
            fillOpacity={0.85}
          >
            <Tooltip>
              <span style={{ fontSize: 11 }}>
                Order {a.order_id} · P{a.priority}
              </span>
            </Tooltip>
          </CircleMarker>
        ))}

        {/* ── ANIMATED AGENTS ── */}
        {animatedAgents.map(a => (
          <CircleMarker
            key={`agent-${a.agent_id}`}
            center={[a.lat, a.lon]}
            radius={a.status === "busy" ? 10 : 7}
            fillColor={
              a.is_breaching
                ? "#ef4444"
                : AGENT_COLORS[a.status] || "#22c55e"
            }
            color="white"
            weight={2}
            fillOpacity={0.92}
          >
            <Tooltip permanent direction="top" offset={[0, -12]}>
              <span style={{
                fontSize: 10, fontWeight: "bold",
                color: a.status === "busy" ? "#f59e0b" : "#22c55e"
              }}>
                A{a.agent_id}
              </span>
            </Tooltip>
            <Tooltip direction="right" offset={[10, 0]}>
              <div style={{ fontSize: 11, fontFamily: "sans-serif" }}>
                <b>Agent {a.agent_id}</b><br/>
                Status: {a.status}<br/>
                Load: {a.load_pct}%<br/>
                {a.order_id ? `→ Order ${a.order_id} (P${a.priority})` : "No order"}
              </div>
            </Tooltip>
          </CircleMarker>
        ))}

      </MapContainer>

      {/* Footer stats */}
      <div style={{
        padding: "8px 14px",
        borderTop: "1px solid var(--border-dim)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 9, fontFamily: "Share Tech Mono", color: "var(--text-dim)",
      }}>
        <span>
          {animatedAgents.filter(a => a.status === "busy").length} agents moving ·{" "}
          {animatedAgents.filter(a => a.order_lat).length} active routes ·{" "}
          smooth interpolation @ 60fps
        </span>
        <span>CartoDB Dark · OpenStreetMap</span>
      </div>
    </div>
  );
}