import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline,
         Popup, Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import axios from "axios";

const API = "http://127.0.0.1:8000";

const CITY_CENTERS = {
  bangalore: { center: [12.97, 77.59], zoom: 12 },
  delhi:     { center: [28.61, 77.20], zoom: 11 },
  mumbai:    { center: [19.07, 72.87], zoom: 12 }
};

const PRIORITY_COLORS = { 1: "#94a3b8", 2: "#3b82f6", 3: "#ef4444" };

function MapUpdater({ center, zoom }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom); }, [center, zoom]);
  return null;
}

export default function MapPanel({ currentCity = "bangalore" }) {
  const [routes,  setRoutes]  = useState([]);
  const [agents,  setAgents]  = useState([]);
  const [orders,  setOrders]  = useState([]);
  const [mapData, setMapData] = useState(null);

  const cityConfig = CITY_CENTERS[currentCity] || CITY_CENTERS.bangalore;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [r, m] = await Promise.all([
          axios.get(`${API}/api/routes`),
          axios.get(`${API}/api/map`)
        ]);
        setRoutes(r.data);
        setMapData(m.data);
      } catch(e) {}
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <div className="p-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">
          🗺️ Live Route Animation Map
        </h3>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-red-400 inline-block"></span> High Priority
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-400 inline-block"></span> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-slate-400 inline-block"></span> Low
          </span>
        </div>
      </div>

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

        {/* ── route lines ── */}
        {routes.map(r => (
          <Polyline
            key={`route-${r.agent_id}`}
            positions={[
              [r.agent_lat, r.agent_lon],
              [r.order_lat, r.order_lon]
            ]}
            color={PRIORITY_COLORS[r.priority] || "#3b82f6"}
            weight={2}
            opacity={0.8}
            dashArray="6 10"
          />
        ))}

        {/* ── agents ── */}
        {routes.map(r => (
          <CircleMarker
            key={`agent-${r.agent_id}`}
            center={[r.agent_lat, r.agent_lon]}
            radius={10}
            fillColor={r.status === "busy" ? "#f59e0b" : "#22c55e"}
            color="white"
            weight={2}
            fillOpacity={0.9}
          >
            <Tooltip permanent direction="top" offset={[0, -10]}>
              <span style={{ fontSize: "10px", fontWeight: "bold" }}>
                A{r.agent_id}
              </span>
            </Tooltip>
            <Popup>
              <div style={{ fontFamily: "sans-serif", fontSize: "12px" }}>
                <b>Agent {r.agent_id}</b><br/>
                Status: {r.status}<br/>
                Load: {r.load_pct}%<br/>
                → Order {r.order_id} (P{r.priority})
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* ── order destinations ── */}
        {routes.map(r => (
          <CircleMarker
            key={`order-${r.order_id}`}
            center={[r.order_lat, r.order_lon]}
            radius={6}
            fillColor={PRIORITY_COLORS[r.priority]}
            color="white"
            weight={1.5}
            fillOpacity={0.8}
          >
            <Tooltip>
              <span style={{ fontSize: "10px" }}>
                Order {r.order_id} · P{r.priority}
              </span>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="p-2 border-t border-slate-700 text-xs text-slate-500 text-center">
        {routes.length} active routes · Updates every 3s · Dark map = CartoDB
      </div>
    </div>
  );
}