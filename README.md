# 🚚 Fleet AI Decision Engine

Real-time autonomous dispatch system for dynamic fleet resource allocation — built with constraint-aware optimization, reinforcement learning, and Gemini-powered agentic AI.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Live-success)

🔴 **Live API:** [fleet-delivery-optimization-production.up.railway.app](https://fleet-delivery-optimization-production.up.railway.app)

📖 **API Docs:** [fleet-delivery-optimization-production.up.railway.app/docs](https://fleet-delivery-optimization-production.up.railway.app/docs)

---

## 📌 What Problem Does This Solve?

Every delivery platform — Swiggy, Zepto, Porter — has a core problem: **which delivery agent picks up which order?** Do it wrong and agents waste fuel, orders arrive late, and customers complain.

This system is the AI brain that makes those decisions automatically, every 3 seconds, across 3 Indian cities. It considers distance, traffic, agent capacity, and order deadlines — and if an agent is going to miss a delivery, the system detects that **9 seconds in advance** and reassigns automatically.

---

## 🎯 Results

| Metric | Optimized Engine | Random Baseline | Improvement |
|---|---|---|---|
| Avg Distance | 25.9u | 52.5u | 50.6% shorter routes |
| On-Time Rate | 98% | 67% | +31% improvement |
| SLA Breaches | Pre-emptively prevented | Reactive only | Proactive AI |
| Cities Supported | 3 simultaneous | — | Bangalore, Delhi, Mumbai |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│         WebSocket + REST API + Leaflet Map                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ WebSocket / REST
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                            │
│              41 REST Endpoints + WebSocket                   │
├─────────────┬───────────┬──────────────┬────────────────────┤
│  Simulation │    RL     │   Gemini AI  │   Multi-Fleet       │
│    Engine   │   Agent   │    Agent     │   Manager           │
├─────────────┴───────────┴──────────────┴────────────────────┤
│                    SQLite Database                            │
│         Tick snapshots · Assignments · Events                 │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🤖 AI & Optimization
- **Constraint-Aware Greedy Engine** — scores agents using weighted formula: proximity (50%), capacity (20%), urgency (20%), deadline (10%)
- **Q-Learning RL Agent** — trained over 3,750+ episodes, 143 states explored, epsilon-greedy policy with decay
- **Predictive SLA Detection** — 3-tick lookahead detects breaches 9 seconds before they happen and pre-emptively reassigns
- **Demand Forecasting** — weighted moving average predicts order volume per tick with trend detection
- **Weight Auto-Tuner** — grid search across 10 scoring weight combinations to find optimal hyperparameters
- **Anomaly Detection** — Z-score based detection across 6 system metrics with critical/warning/info severity

### 🌍 Multi-City & Scenarios
- **3 Cities** — Bangalore (20 agents), Delhi (25 agents), Mumbai (30 agents) with real traffic zones
- **4 Scenarios** — Normal, Rush Hour (8 orders/tick), Low Demand, Chaos Mode (12 orders/tick)
- **Multi-Fleet** — run all 3 cities simultaneously in isolated threads with live leaderboard

### 🤖 Agentic AI
- **Gemini AI Operations Agent** — monitors 7 system metrics, reasons autonomously, switches scenarios without human input
- **Natural Language Query** — ask plain English questions about your fleet, Gemini answers using live API data
- **LLM Incident Reports** — auto-generates 200-word professional operations reports after each session
- **A/B Testing Framework** — runs greedy vs RL on identical conditions, compares results side by side

### ⚡ Real-Time Architecture
- **WebSocket Push** — simulation broadcasts live tick data to all connected clients instantly
- **SQLite Persistence** — every assignment, delivery, breach logged for historical analysis and replay
- **Speed Control** — run simulation at 0.5x, 1x, 2x, or 5x speed
- **Reset & Replay** — full simulation reset and session replay from SQLite history

### 🎨 React Frontend
- **Cyberpunk dark theme** — Orbitron + Share Tech Mono fonts, bracket corner decorations
- **60fps Route Animation** — agents smoothly interpolate positions using requestAnimationFrame + lerp
- **Trail Effect** — each agent leaves a fading dashed trail showing recent path
- **Live Leaflet Map** — real OpenStreetMap with CartoDB dark tiles, route lines color-coded by priority
- **Decision Explainability** — select any order to see exactly why that agent was chosen over all others

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, WebSockets, SQLite |
| AI/ML | Q-Learning, Gemini 2.5 Flash, NumPy |
| Frontend | React, Tailwind CSS, Recharts, Leaflet |
| Maps | Folium, react-leaflet, OpenStreetMap |
| Deployment | Docker, Railway (API), Vercel (Frontend) |

---

## 📁 Project Structure

```
fleet-ai-engine/
├── api.py              # FastAPI backend — 41 endpoints + WebSocket
├── simulation.py       # Agent + Order data structures
├── engine.py            # Constraint-aware greedy assignment
├── realtime.py          # 3-second simulation loop
├── rl_engine.py          # Q-learning RL dispatch agent
├── agent.py             # Gemini autonomous AI agent
├── anomaly.py           # Statistical anomaly detection
├── predictor.py          # Predictive SLA breach detection
├── forecaster.py         # Demand forecasting
├── optimizer.py          # Weight grid search tuner
├── ab_testing.py         # Greedy vs RL A/B framework
├── multi_fleet.py         # Simultaneous multi-city simulation
├── incident_report.py     # LLM report generator
├── scenario.py           # Scenario configurations
├── cities.py             # City configurations
├── database.py            # SQLite logging
├── map_view.py            # Folium map builder
├── Dockerfile             # Docker configuration
├── requirements.txt        # Python dependencies
└── frontend/              # React application
    ├── src/
    │   ├── App.js         # Main dashboard
    │   └── MapPanel.jsx    # Animated Leaflet map
    └── package.json
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone the repo
```bash
git clone https://github.com/Ayush-AI-ux/Fleet-Delivery-Optimization.git
cd Fleet-Delivery-Optimization
```

### 2. Set up environment
```bash
# Create .env file
echo "GEMINI_API_KEY=your-key-here" > .env
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend
```bash
uvicorn api:app --reload
# API running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 5. Run the frontend
```bash
cd frontend
npm install
npm start
# Dashboard at http://localhost:3000
```

### 6. Or use Docker
```bash
docker build -t fleet-ai .
docker run -p 8000:8000 --env-file .env fleet-ai
```

---

## 🔌 API Endpoints

The API has 41 REST endpoints + 1 WebSocket. Key ones:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/metrics` | Live system metrics |
| GET | `/api/agents` | All agent states |
| GET | `/api/orders` | All order states |
| POST | `/api/scenario/{mode}` | Change scenario |
| POST | `/api/city/{city}` | Switch city |
| GET | `/api/rl/status` | RL agent stats |
| POST | `/api/rl/train` | Train RL agent |
| GET | `/api/anomalies` | Anomaly detection data |
| GET | `/api/predictions` | Predictive SLA data |
| POST | `/api/query` | Natural language query |
| GET | `/api/fleet/status` | Multi-fleet status |
| POST | `/api/reset` | Reset simulation |
| WS | `/ws` | Real-time tick push |

Full documentation: [fleet-delivery-optimization-production.up.railway.app/docs](https://fleet-delivery-optimization-production.up.railway.app/docs)

---

## 🧠 How the AI Works

### Assignment Algorithm
```
Score = 0.5 × proximity + 0.2 × capacity + 0.2 × urgency + 0.1 × deadline
```
Hard constraints checked first — if agent can't reach before deadline, eliminated.

### Q-Learning RL Agent
```
State  = (distance_bucket, capacity_bucket, priority, deadline_bucket)
Action = assign (1) or skip (0)
Reward = +10 on-time delivery, -8 SLA breach, -2×priority for skipping
Update = Q(s,a) += α × (r + γ × max Q(s',a') - Q(s,a))
```

### Predictive SLA Detection
```
risk_score = current_ETA / deadline
if risk_score > 0.75 → pre-emptive reassignment 3 ticks early
```

---

## 📊 Business Impact

At Zepto/Swiggy scale (10 cities × 1000 agents):
- 50% shorter routes = 50% less fuel per delivery
- ₹12-15 lakh/day estimated operational savings
- Proactive AI prevents SLA breaches before they happen

---

## 👨‍💻 Author

**Ayush Mittal**
B.Tech CS, GLA University Mathura (2026-27)
GitHub: [@Ayush-AI-ux](https://github.com/Ayush-AI-ux)

---

## 📄 License

MIT License — free to use and modify.
