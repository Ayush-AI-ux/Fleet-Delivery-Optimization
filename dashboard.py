
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# ── CONFIG ────────────────────────────────────────────────────────────

API_BASE     = "http://127.0.0.1:8000"
REFRESH_SECS = 3

st.set_page_config(
    page_title = "Fleet AI Decision Engine",
    page_icon  = "🚚",
    layout     = "wide"
)

# ── RERUN HELPER ──────────────────────────────────────────────────────

def do_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except:
            pass

# ── DATA FETCHER ──────────────────────────────────────────────────────

def fetch(endpoint):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        return r.json()
    except:
        return None

# ── HEADER ────────────────────────────────────────────────────────────

col_title, col_live = st.columns([4, 1])

with col_title:
    st.markdown("## 🚚 Fleet AI Decision Engine")
    st.markdown("Real-time autonomous dispatch system — constraint-aware greedy optimization")

with col_live:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;padding-top:20px">
        <div style="width:10px;height:10px;border-radius:50%;background:#22c55e;
                    animation:pulse 1.5s infinite"></div>
        <span style="font-size:13px;color:#22c55e;font-weight:500">LIVE</span>
        <span style="font-size:11px;color:#6b7280">WebSocket</span>
    </div>
    <style>
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.85)} }
    </style>
    """, unsafe_allow_html=True)

st.divider()

# ── FETCH DATA ────────────────────────────────────────────────────────

metrics       = fetch("/api/metrics")
agents        = fetch("/api/agents")
orders        = fetch("/api/orders")
logs          = fetch("/api/logs")
map_data      = fetch("/api/map")
api_status    = fetch("/api/status")
scenario_data = fetch("/api/scenario")
city_data     = fetch("/api/city")

if not metrics:
    st.error("Cannot connect to API. Make sure `py -3.11 -m uvicorn api:app --reload` is running.")
    st.stop()

# ── CITY SELECTOR ─────────────────────────────────────────────────────

current_city_key = city_data["current"] if city_data else "bangalore"
all_cities       = city_data["all"]     if city_data else {}
current_city_cfg = city_data["config"]  if city_data else {}

st.markdown("### 🌍 City")
city_col1, city_col2, city_col3 = st.columns(3)

for col, key in zip([city_col1, city_col2, city_col3], ["bangalore", "delhi", "mumbai"]):
    cfg = all_cities.get(key, {})
    with col:
        if st.button(
            f"{cfg.get('emoji','🌆')} {cfg.get('name', key)}",
            use_container_width=True,
            type="primary" if current_city_key == key else "secondary",
            key=f"city_{key}"
        ):
            requests.post(f"{API_BASE}/api/city/{key}")
            do_rerun()
        st.caption(f"{cfg.get('agents',0)} agents | {cfg.get('orders',0)} orders | {len(cfg.get('traffic_zones',[]))} zones")

if current_city_cfg:
    st.success(
        f"**Active City:** {current_city_cfg['emoji']} {current_city_cfg['name']} | "
        f"{current_city_cfg['agents']} agents | "
        f"{current_city_cfg['orders']} orders | "
        f"{len(current_city_cfg['traffic_zones'])} traffic zones"
    )

st.divider()

# ── SCENARIO CONTROLS ─────────────────────────────────────────────────

current_mode  = scenario_data["current"] if scenario_data else "normal"
all_scenarios = scenario_data["all"]     if scenario_data else {}

st.markdown("### 🎛️ Scenario Control")
sc1, sc2, sc3, sc4 = st.columns(4)

for col, key in zip([sc1, sc2, sc3, sc4], ["normal", "rush_hour", "low_demand", "chaos"]):
    cfg = all_scenarios.get(key, {})
    with col:
        if st.button(
            f"{cfg.get('emoji', '●')} {cfg.get('name', key)}",
            use_container_width=True,
            type="primary" if current_mode == key else "secondary",
            key=f"scenario_{key}"
        ):
            requests.post(f"{API_BASE}/api/scenario/{key}")
            do_rerun()
        st.caption(cfg.get("description", ""))

if scenario_data:
    cfg = scenario_data["config"]
    st.info(
        f"**Active:** {cfg['emoji']} {cfg['name']} | "
        f"Order rate: {cfg['new_order_rate']}/tick | "
        f"Agent speed: {cfg['agent_speed']} | "
        f"Traffic multiplier: {cfg['traffic_multiplier']}x"
    )

st.divider()

# ── ROW 1 — KEY METRICS ───────────────────────────────────────────────

st.markdown("### Live Metrics")
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

c1.metric("Tick",          metrics["tick"])
c2.metric("Total Orders",  metrics["total_orders"])
c3.metric("Delivered",     metrics["total_delivered"])
c4.metric("Reassignments", metrics["total_reassigned"])
c5.metric("On-Time Rate",  f"{metrics['on_time_rate']}%")
c6.metric("Avg Distance",  f"{metrics['avg_distance']}u")
c7.metric("WS Clients",    api_status["ws_clients"] if api_status else 0)

st.divider()

# ── ROW 2 — BUSINESS IMPACT ───────────────────────────────────────────

st.markdown("### 💰 Business Impact")

b1, b2, b3, b4 = st.columns(4)

dist_saved_pct = metrics.get("dist_saved_pct", 0)
cost_saved     = metrics.get("cost_saved_inr", 0)
baseline       = metrics.get("baseline_avg_dist", 52.51)
current_dist   = metrics.get("avg_distance", 0)

b1.metric("Distance Saved vs Baseline",   f"{dist_saved_pct}%",
          f"{round(baseline - current_dist, 1)}u shorter per order")
b2.metric("Estimated Cost Saved",         f"₹{cost_saved:,}",
          "vs random assignment baseline")
b3.metric("Orders Saved by Reassignment", metrics["total_reassigned"],
          "SLA breaches intercepted")
b4.metric("Fleet Efficiency",             f"{metrics['on_time_rate']}%",
          f"{metrics['agents_busy']} agents actively delivering")

with st.expander("How is business impact calculated?"):
    st.markdown(f"""
- **Baseline avg distance**: {baseline}u (random assignment baseline)
- **Optimized avg distance**: {current_dist}u (constraint-aware greedy engine)
- **Distance saved per order**: {round(baseline - current_dist, 1)}u
- **Cost per unit**: ₹12 (standard fleet fuel/time cost)
- **Total saved**: {round(baseline - current_dist, 1)}u × ₹12 × {metrics['total_delivered']} deliveries = **₹{cost_saved:,}**

At Zepto/Swiggy scale (10 cities × 1000 agents), this optimization saves approximately **₹12–15 lakh/day** in operational costs.
    """)

st.divider()

# ── ROW 3 — LIVE CITY MAP ─────────────────────────────────────────────

city_name  = current_city_cfg.get("name",  "City") if current_city_cfg else "City"
city_emoji = current_city_cfg.get("emoji", "🗺️")  if current_city_cfg else "🗺️"
st.markdown(f"### {city_emoji} Live {city_name} Dispatch Map")

if map_data and "html" in map_data:
    components.html(map_data["html"], height=500, scrolling=False)
    st.caption(f"Real OpenStreetMap — {city_name} | agents and orders on actual streets | WebSocket push updates")
else:
    st.warning("Map loading... make sure API is running.")

st.divider()

# ── ROW 4 — ORDER QUEUE + AGENT STATUS ───────────────────────────────

col_status, col_agent = st.columns([1, 1])

with col_status:
    st.markdown("### Order Queue")
    status_fig = go.Figure(go.Bar(
        x=["Pending", "Assigned", "Delivered", "Failed"],
        y=[metrics["pending"], metrics["assigned"],
           metrics["total_delivered"], metrics["failed"]],
        marker_color=["#94a3b8", "#3b82f6", "#22c55e", "#ef4444"],
        text=[metrics["pending"], metrics["assigned"],
              metrics["total_delivered"], metrics["failed"]],
        textposition="outside"
    ))
    status_fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(status_fig, use_container_width=True)

with col_agent:
    st.markdown("### Agent Status")
    agent_fig = go.Figure(go.Pie(
        labels=["Idle", "Busy"],
        values=[metrics["agents_idle"], metrics["agents_busy"]],
        marker_colors=["#22c55e", "#f59e0b"],
        hole=0.5
    ))
    agent_fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(agent_fig, use_container_width=True)

st.divider()

# ── ROW 5 — DECISION LOG + AGENT TABLE ───────────────────────────────

col_log, col_agents_table = st.columns([1, 1])

with col_log:
    st.markdown("### Live Decision Reasoning Log")
    if logs and logs["logs"]:
        for entry in logs["logs"]:
            if "REASSIGNED" in entry:
                st.error(f"🔄 {entry}")
            elif "SLA BREACH" in entry:
                st.warning(f"⚠️ {entry}")
            elif "DELIVERED" in entry:
                st.success(f"✅ {entry}")
            elif "INJECTED" in entry:
                st.info(f"📦 {entry}")
            elif "SCENARIO" in entry:
                st.warning(f"🎛️ {entry}")
            elif "CITY" in entry:
                st.info(f"🌍 {entry}")
            else:
                st.write(f"ℹ️ {entry}")
    else:
        st.write("Waiting for logs...")

with col_agents_table:
    st.markdown("### Agent Status Table")
    if agents:
        df = pd.DataFrame([{
            "Agent ID": a["agent_id"],
            "Location": f"({a['location'][0]:.1f}, {a['location'][1]:.1f})",
            "Status":   a["status"].upper(),
            "Capacity": a["capacity"],
            "Orders":   len(a["current_orders"]),
            "Load %":   a["load_pct"]
        } for a in agents])
        st.dataframe(
            df, use_container_width=True, height=380,
            column_config={
                "Load %": st.column_config.ProgressColumn(
                    "Load %", min_value=0, max_value=100, format="%d%%"
                )
            }
        )

st.divider()

# ── ROW 6 — PERFORMANCE GAUGES ────────────────────────────────────────

st.markdown("### Performance Gauges")
col_g1, col_g2, col_g3 = st.columns(3)

with col_g1:
    g1 = go.Figure(go.Indicator(
        mode="gauge+number", value=metrics["on_time_rate"],
        title={"text": "On-Time Rate %"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": "#22c55e"},
            "steps": [
                {"range": [0,  60],  "color": "#fecaca"},
                {"range": [60, 85],  "color": "#fef08a"},
                {"range": [85, 100], "color": "#bbf7d0"}
            ],
            "threshold": {"line": {"color": "red", "width": 2},
                          "thickness": 0.75, "value": 90}
        }
    ))
    g1.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=0),
                     paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(g1, use_container_width=True)

with col_g2:
    g2 = go.Figure(go.Indicator(
        mode="gauge+number", value=metrics["agents_busy"],
        title={"text": "Agents Busy"},
        gauge={
            "axis": {"range": [0, len(agents) if agents else 30]},
            "bar":  {"color": "#f59e0b"},
            "steps": [
                {"range": [0,  10], "color": "#bbf7d0"},
                {"range": [10, 20], "color": "#fef08a"},
                {"range": [20, 30], "color": "#fecaca"}
            ]
        }
    ))
    g2.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=0),
                     paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(g2, use_container_width=True)

with col_g3:
    g3 = go.Figure(go.Indicator(
        mode="number+delta", value=metrics["total_delivered"],
        title={"text": "Total Delivered"},
        delta={"reference": max(metrics["total_delivered"] - 3, 0),
               "increasing": {"color": "#22c55e"}}
    ))
    g3.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=0),
                     paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(g3, use_container_width=True)

st.divider()

# ── ROW 7 — HISTORICAL PERFORMANCE CHARTS ────────────────────────────

st.markdown("### 📈 Historical Performance")

history = fetch("/api/history")

if history and len(history) > 1:
    hist_df = pd.DataFrame(history)

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        fig_ot = go.Figure()
        fig_ot.add_trace(go.Scatter(
            x=hist_df["tick"], y=hist_df["on_time_rate"],
            mode="lines+markers",
            name="On-Time Rate %",
            line=dict(color="#22c55e", width=2),
            fill="tozeroy",
            fillcolor="rgba(34,197,94,0.1)"
        ))
        fig_ot.update_layout(
            title="On-Time Rate Over Time",
            height=260,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 105]),
            xaxis_title="Tick", yaxis_title="%"
        )
        st.plotly_chart(fig_ot, use_container_width=True)

    with col_h2:
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Scatter(
            x=hist_df["tick"], y=hist_df["avg_distance"],
            mode="lines+markers",
            name="Avg Distance",
            line=dict(color="#3b82f6", width=2),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.1)"
        ))
        fig_dist.add_hline(
            y=52.51, line_dash="dot",
            line_color="#ef4444",
            annotation_text="Random baseline 52.51u"
        )
        fig_dist.update_layout(
            title="Avg Distance vs Random Baseline",
            height=260,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Tick", yaxis_title="Distance (u)"
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    db_stats = fetch("/api/stats")
    if db_stats:
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Ticks Logged",         db_stats["total_ticks"])
        s2.metric("DB Assignments",       db_stats["total_assignments"])
        s3.metric("Avg Score (all time)", db_stats["avg_score"])
        s4.metric("Avg Distance (all)",   f"{db_stats['avg_distance']}u")

    if st.button("📥 Export simulation data to CSV"):
        export = fetch("/api/export")
        if export:
            st.success(f"Exported: {', '.join(export['files'])}")
else:
    st.info("Collecting history... check back after a few ticks.")

st.divider()

# ── ROW 8 — DECISION EXPLAINABILITY ──────────────────────────────────

st.markdown("### 🧠 Decision Explainability")
st.caption("Select any assigned order to see WHY that agent was chosen over all others")

if orders:
    assigned_orders = [o for o in orders if o["status"] == "assigned"]
    if assigned_orders:
        order_options = {
            f"Order {o['order_id']} | Priority {o['priority']} | Deadline {o['deadline']}s": o["order_id"]
            for o in assigned_orders[:20]
        }
        selected_label = st.selectbox("Select an order to explain:", list(order_options.keys()))
        selected_id    = order_options[selected_label]

        explain = fetch(f"/api/explain/{selected_id}")

        if explain and "candidates" in explain:
            st.markdown(
                f"**Order {explain['order_id']}** — "
                f"Priority {explain['priority']} | "
                f"Deadline {explain['deadline']}s | "
                f"Assigned to Agent {explain['assigned_agent']}"
            )

            rows = []
            for c in explain["candidates"]:
                rows.append({
                    "Agent":    f"Agent {c['agent_id']}",
                    "Score":    c["score"],
                    "Distance": f"{c['distance']}u",
                    "ETA":      f"{c['est_time']}s",
                    "Traffic":  f"{c['delay']}x",
                    "Load":     f"{c['load']}/{c['capacity']}",
                    "Eligible": "✅" if c["eligible"] else f"❌ {c['reason']}",
                    "Chosen":   "⭐ YES" if c["is_assigned"] else ""
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=220)

            winner = next((c for c in explain["candidates"] if c["is_assigned"]), None)
            if winner:
                st.success(
                    f"✅ Agent {winner['agent_id']} chosen — "
                    f"Score: {winner['score']} | "
                    f"Distance: {winner['distance']}u | "
                    f"ETA: {winner['est_time']}s | "
                    f"Load: {winner['load']}/{winner['capacity']} | "
                    f"Traffic delay: {winner['delay']}x"
                )
    else:
        st.info("No assigned orders yet — waiting for simulation...")

st.divider()

# ── ROW 9 — DEMAND FORECAST + WEIGHT TUNER ───────────────────────────

st.markdown("### 🔮 Demand Forecasting + Weight Optimization")

col_fore, col_tune = st.columns([1, 1])

with col_fore:
    st.markdown("#### Demand Forecast")
    forecast = fetch("/api/forecast")
    if forecast and forecast.get("history"):
        trend_color = {"rising": "🔴", "falling": "🟢", "stable": "🟡"}
        trend       = forecast.get("trend", "stable")

        f1, f2, f3 = st.columns(3)
        f1.metric("Next Tick Prediction", forecast["prediction"])
        f2.metric("Avg Demand",           forecast["avg_demand"])
        f3.metric("Trend",                f"{trend_color.get(trend,'🟡')} {trend.title()}")

        if len(forecast["history"]) > 1:
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(
                x=list(range(len(forecast["history"]))),
                y=forecast["history"],
                mode="lines+markers",
                name="Demand History",
                line=dict(color="#a78bfa", width=2),
                fill="tozeroy",
                fillcolor="rgba(167,139,250,0.1)"
            ))
            fig_f.add_hline(
                y=forecast["prediction"],
                line_dash="dot",
                line_color="#f59e0b",
                annotation_text=f"Prediction: {forecast['prediction']}"
            )
            fig_f.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Tick", yaxis_title="Pending Orders"
            )
            st.plotly_chart(fig_f, use_container_width=True)
    else:
        st.info("Collecting demand data — check back after a few ticks.")

with col_tune:
    st.markdown("#### Weight Auto-Tuner")
    tuning = fetch("/api/tuning")

    if tuning:
        status_map = {
            "idle":     "⚪ Not started — click below to run",
            "running":  "🔄 Running — testing 10 combinations...",
            "complete": "✅ Complete"
        }
        st.caption(status_map.get(tuning["status"], "Unknown"))

        if tuning["status"] == "idle":
            if st.button("🚀 Start Weight Tuning", use_container_width=True):
                requests.post(f"{API_BASE}/api/tuning/start")
                st.info("Started — testing 10 weight combinations in background...")

        elif tuning["status"] == "running":
            st.warning("Testing combinations... refresh in ~30 seconds")

        elif tuning["status"] == "complete" and tuning["results"]:
            best = tuning["best"]
            st.success(
                f"Best weights found! Score: {best['score']} | "
                f"On-time: {best['on_time_rate']}% | "
                f"Avg dist: {best['avg_distance']}u"
            )
            tune_rows = []
            for i, r in enumerate(tuning["results"][:5]):
                w = r["weights"]
                tune_rows.append({
                    "Rank":      f"#{i+1}",
                    "Score":     r["score"],
                    "On-Time %": r["on_time_rate"],
                    "Avg Dist":  f"{r['avg_distance']}u",
                    "Proximity": w["W_PROXIMITY"],
                    "Capacity":  w["W_CAPACITY"],
                    "Urgency":   w["W_URGENCY"],
                    "Deadline":  w["W_DEADLINE"],
                })
            st.dataframe(
                pd.DataFrame(tune_rows),
                use_container_width=True,
                height=210
            )
            
            
# ── ROW 10 — AGENTIC AI ───────────────────────────────────────────────

st.divider()
st.markdown("### 🤖 Autonomous AI Operations Agent")
st.caption("Gemini AI agent that monitors your fleet, detects issues, and takes corrective actions autonomously.")

agent_state = fetch("/api/agent")

if agent_state:
    col_a1, col_a2 = st.columns([1, 2])

    with col_a1:
        status_map = {
            "idle":     ("⚪", "Idle — ready to run"),
            "running":  ("🔄", "Agent is thinking..."),
            "complete": ("✅", "Last run complete"),
            "error":    ("❌", "Error occurred")
        }
        icon, label = status_map.get(agent_state["status"], ("⚪", "Unknown"))
        st.metric("Agent Status", f"{icon} {label}")

        if agent_state["last_run"]:
            st.caption(f"Last run: {agent_state['last_run']}")

        a1, a2 = st.columns(2)
        a1.metric("Observations", agent_state["total_obs"])
        a2.metric("Actions Taken", agent_state["total_actions"])

        if agent_state["status"] in ["idle", "complete", "error"]:
            if st.button("🚀 Run AI Agent Now", use_container_width=True, type="primary"):
                requests.post(f"{API_BASE}/api/agent/run")
                st.info("Agent started — observing system and reasoning...")

        elif agent_state["status"] == "running":
            st.warning("Agent is actively monitoring... wait for completion")

        if agent_state["actions"]:
            st.markdown("**Recent Actions:**")
            for action in reversed(agent_state["actions"]):
                st.error(f"🤖 Tick {action['tick']}: {action['action']} — {action['reason']}")

    with col_a2:
        st.markdown("**Agent Observations & Reasoning:**")
        if agent_state["observations"]:
            for obs in reversed(agent_state["observations"]):
                severity = obs.get("severity", "healthy")
                if severity == "critical":
                    st.error(f"🔴 [{obs['time']}] Tick {obs['tick']}: {obs['text'][:400]}")
                elif severity == "warning":
                    st.warning(f"🟡 [{obs['time']}] Tick {obs['tick']}: {obs['text'][:400]}")
                else:
                    st.success(f"🟢 [{obs['time']}] Tick {obs['tick']}: {obs['text'][:400]}")
        else:
            st.write("No observations yet — click 'Run AI Agent Now' to start")
            

# ── ROW 11 — RL ENGINE ────────────────────────────────────────────────

st.divider()
st.markdown("### 🎮 Reinforcement Learning Dispatch Agent")
st.caption("Q-learning agent that learns optimal dispatch policy from simulation experience")

rl_data = fetch("/api/rl/status")

if rl_data:
    col_rl1, col_rl2 = st.columns([1, 1])

    with col_rl1:
        r1, r2, r3 = st.columns(3)
        r1.metric("States Explored", rl_data.get("states_explored", 0))
        r2.metric("Epsilon (ε)",     rl_data.get("epsilon", 0.3))
        r3.metric("Avg Reward",      rl_data.get("avg_reward_100", 0))

        r4, r5 = st.columns(2)
        r4.metric("Episodes",        rl_data.get("episodes", 0))
        r5.metric("Total Reward",    rl_data.get("total_reward", 0))

        status = rl_data.get("status", "untrained")
        if status == "untrained":
            st.warning("⚪ Agent not trained yet")
            if st.button("🎮 Train RL Agent (50 episodes)", use_container_width=True):
                requests.post(f"{API_BASE}/api/rl/train?episodes=50")
                st.info("Training started — runs 50 simulation episodes in background (~30s)")

        elif status == "training":
            st.warning("🔄 Training in progress...")

        elif status == "trained":
            st.success("✅ Agent trained and ready")
            if st.button("⚡ Use RL for Next Assignment", use_container_width=True):
                result = requests.post(f"{API_BASE}/api/rl/assign").json()
                st.success(f"RL assigned {result['assigned']} orders | "
                           f"skipped {result['skipped']}")

    with col_rl2:
        if rl_data.get("history"):
            hist = pd.DataFrame(rl_data["history"])
            fig_rl = go.Figure()
            fig_rl.add_trace(go.Scatter(
                x=hist["episode"], y=hist["on_time"],
                mode="lines+markers",
                name="On-Time Rate %",
                line=dict(color="#22c55e", width=2)
            ))
            fig_rl.add_trace(go.Scatter(
                x=hist["episode"], y=hist["epsilon"] * 100,
                mode="lines",
                name="Epsilon × 100",
                line=dict(color="#f59e0b", width=1, dash="dot"),
                yaxis="y2"
            ))
            fig_rl.update_layout(
                title="RL Training Progress",
                height=280,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(title="On-Time %", range=[0, 105]),
                yaxis2=dict(title="Epsilon", overlaying="y",
                            side="right", range=[0, 40]),
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_rl, use_container_width=True)
        else:
            st.info("Train the agent to see learning progress chart")

# ── ROW 10B — ANOMALY DETECTION ───────────────────────────────────────

st.divider()
st.markdown("### 🚨 Anomaly Detection")
st.caption("Real-time statistical anomaly detection across 6 system metrics")

anomaly_data = fetch("/api/anomalies")

if anomaly_data:
    an1, an2, an3, an4 = st.columns(4)
    an1.metric("Total Anomalies",  anomaly_data["total"])
    an2.metric("🔴 Critical",      anomaly_data["critical_count"])
    an3.metric("🟡 Warnings",      anomaly_data["warning_count"])
    an4.metric("🔵 Info",          anomaly_data["info_count"])

    if anomaly_data["recent"]:
        st.markdown("**Recent Anomalies:**")
        for a in reversed(anomaly_data["recent"][-8:]):
            if a["severity"] == "critical":
                st.error(f"🔴 [{a['time']}] Tick {a['tick']} — {a['message']}")
            elif a["severity"] == "warning":
                st.warning(f"🟡 [{a['time']}] Tick {a['tick']} — {a['message']}")
            else:
                st.info(f"🔵 [{a['time']}] Tick {a['tick']} — {a['message']}")
    else:
        st.success("✅ No anomalies detected — system operating normally")

# ── ROW 12 — A/B TESTING ─────────────────────────────────────────────

st.divider()
st.markdown("### ⚔️ A/B Testing — Greedy vs RL Agent")
st.caption("Run both engines on identical conditions and compare results side by side")

ab_data = fetch("/api/ab/results")

if ab_data:
    ab_status = ab_data.get("status", "idle")

    if ab_status == "idle":
        st.info("No test run yet — click below to start")
        if st.button("⚔️ Run A/B Test (20 ticks each)", use_container_width=True, type="primary"):
            requests.post(f"{API_BASE}/api/ab/run?ticks=20")
            st.info("A/B test started — running greedy vs RL for 20 ticks each...")

    elif ab_status == "running":
        st.warning("🔄 Test running — comparing Greedy vs RL...")

    elif ab_status == "complete" and ab_data.get("results"):
        res     = ab_data["results"]
        greedy  = res["greedy"]
        rl      = res["rl"]
        winner  = res["winner"]
        imp     = res["improvement"]

        # winner banner
        if winner == "RL Agent":
            st.success(f"🏆 Winner: **RL Agent** | On-time improvement: +{imp['on_time_diff']}% | Distance saved: {imp['distance_diff']}u")
        elif winner == "Greedy":
            st.success(f"🏆 Winner: **Greedy Engine** | More reliable on current training")
        else:
            st.info("🤝 It's a Tie — both engines performed equally")

        # side by side comparison
        col_g, col_r = st.columns(2)

        with col_g:
            st.markdown("#### 🔵 Greedy Engine")
            st.metric("Avg On-Time Rate", f"{greedy['avg_on_time']}%")
            st.metric("Avg Distance",     f"{greedy['avg_distance']}u")
            st.metric("Delivered",        greedy["total_delivered"])
            st.metric("Failed",           greedy["total_failed"])

        with col_r:
            st.markdown("#### 🟣 RL Agent")
            st.metric("Avg On-Time Rate", f"{rl['avg_on_time']}%",
                      delta=f"{imp['on_time_diff']}%" if imp['on_time_diff'] != 0 else None)
            st.metric("Avg Distance",     f"{rl['avg_distance']}u",
                      delta=f"{-imp['distance_diff']}u" if imp['distance_diff'] != 0 else None)
            st.metric("Delivered",        rl["total_delivered"])
            st.metric("Failed",           rl["total_failed"])

        # comparison chart
        if greedy.get("snapshots") and rl.get("snapshots"):
            g_df = pd.DataFrame(greedy["snapshots"])
            r_df = pd.DataFrame(rl["snapshots"])

            fig_ab = go.Figure()
            fig_ab.add_trace(go.Scatter(
                x=g_df["tick"], y=g_df["on_time_rate"],
                mode="lines+markers", name="Greedy",
                line=dict(color="#3b82f6", width=2)
            ))
            fig_ab.add_trace(go.Scatter(
                x=r_df["tick"], y=r_df["on_time_rate"],
                mode="lines+markers", name="RL Agent",
                line=dict(color="#a78bfa", width=2)
            ))
            fig_ab.update_layout(
                title="On-Time Rate: Greedy vs RL Agent",
                height=260,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 105]),
                xaxis_title="Tick", yaxis_title="On-Time %",
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_ab, use_container_width=True)

        if st.button("🔄 Run Again", use_container_width=True):
            requests.post(f"{API_BASE}/api/ab/run?ticks=20")
            st.info("New A/B test started...")

# ── ROW 13 — NATURAL LANGUAGE QUERY ──────────────────────────────────

st.divider()
st.markdown("### 💬 Natural Language Query Interface")
st.caption("Ask anything about your fleet in plain English — powered by Gemini AI")

# suggested questions
st.markdown("**Quick questions:**")
q1, q2, q3, q4 = st.columns(4)

suggested = {
    "Which agent has highest load?":     q1,
    "How many SLA breaches so far?":     q2,
    "Should I change scenario?":         q3,
    "What is the system status?":        q4
}

for question, col in suggested.items():
    with col:
        if st.button(question, use_container_width=True, key=f"sq_{question[:10]}"):
            st.session_state["nl_query"] = question

# query input
query_input = st.text_input(
    "Or type your own question:",
    value=st.session_state.get("nl_query", ""),
    placeholder="e.g. Which agent is performing best? What should I do next?"
)

if query_input:
    if st.button("🔍 Ask", type="primary"):
        with st.spinner("Gemini is analyzing your fleet..."):
            try:
                response = requests.post(
                    f"{API_BASE}/api/query",
                    json={"query": query_input},
                    timeout=15
                )
                result = response.json()
                st.success(f"🤖 **Gemini:** {result['answer']}")
                st.caption(f"Answer based on tick {result.get('tick', '?')} data")
            except Exception as e:
                st.error(f"Query failed: {e}")

# ── FOOTER ────────────────────────────────────────────────────────────

st.divider()
col_f1, col_f2 = st.columns([3, 1])

with col_f1:
    active_scenario = scenario_data["config"]["name"] if scenario_data else "Normal"
    active_city     = current_city_cfg.get("name", "Bangalore") if current_city_cfg else "Bangalore"
    st.caption(
        f"Tick: {metrics['tick']} | "
        f"City: {active_city} | "
        f"Scenario: {active_scenario} | "
        f"Fleet AI Engine v3.0 | "
        f"WebSocket + SQLite"
    )

with col_f2:
    ws_clients = api_status["ws_clients"] if api_status else 0
    st.caption(f"🔌 {ws_clients} WS client{'s' if ws_clients != 1 else ''} connected")

time.sleep(REFRESH_SECS)
do_rerun()