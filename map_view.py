
# import folium
# from simulation import SimulationState
# from engine import assign_orders

# # ── COLOR MAPS ────────────────────────────────────────────────────────

# ORDER_COLORS = {
#     "pending":   "gray",
#     "assigned":  "blue",
#     "delivered": "green",
#     "failed":    "red"
# }

# AGENT_COLORS = {
#     "idle": "darkgreen",
#     "busy": "orange"
# }

# PRIORITY_ICONS = {
#     1: "arrow-down",
#     2: "minus",
#     3: "arrow-up"
# }

# # ── COORDINATE CONVERTER ──────────────────────────────────────────────

# def grid_to_latlon(x, y):
#     from cities import get_current_city
#     city = get_current_city()
#     lat  = city["lat_min"] + (y / 100) * (city["lat_max"] - city["lat_min"])
#     lon  = city["lon_min"] + (x / 100) * (city["lon_max"] - city["lon_min"])
#     return round(lat, 6), round(lon, 6)

# # ── MAP BUILDER ───────────────────────────────────────────────────────

# def build_map(sim, metrics=None):
#     from cities import get_current_city
#     city = get_current_city()

#     m = folium.Map(
#         location=city["center"],
#         zoom_start=city["zoom"],
#         tiles="CartoDB dark_matter"
#     )

#     # ── traffic zones ──
#     for zx, zy, radius, name, multiplier in city["traffic_zones"]:
#         lat, lon = grid_to_latlon(zx, zy)
#         radius_m = radius * 300

#         folium.Circle(
#             location=[lat, lon],
#             radius=radius_m,
#             color="red",
#             fill=True,
#             fill_color="red",
#             fill_opacity=0.08,
#             dash_array="5 5",
#             tooltip=f"⚠️ {name} | Delay: {multiplier}x"
#         ).add_to(m)

#         folium.Marker(
#             location=[lat, lon],
#             icon=folium.DivIcon(html=f"""
#                 <div style="
#                     background: rgba(220,38,38,0.85);
#                     color: white;
#                     font-size: 10px;
#                     font-weight: 600;
#                     padding: 3px 7px;
#                     border-radius: 4px;
#                     white-space: nowrap;
#                     border: 1px solid rgba(255,255,255,0.3)
#                 ">{name}</div>
#             """)
#         ).add_to(m)

#     # ── orders ──
#     for order in sim.orders:
#         lat, lon  = grid_to_latlon(*order.location)
#         color     = ORDER_COLORS.get(order.status, "gray")
#         icon_name = PRIORITY_ICONS.get(order.priority, "minus")

#         popup_html = f"""
#         <div style="font-family:sans-serif;min-width:180px">
#             <b style="font-size:13px">Order #{order.order_id}</b><br>
#             <hr style="margin:4px 0">
#             <table style="font-size:12px;width:100%">
#                 <tr><td>Status</td><td><b>{order.status.upper()}</b></td></tr>
#                 <tr><td>Priority</td><td>{'⬆️ HIGH' if order.priority==3 else '➡️ MED' if order.priority==2 else '⬇️ LOW'}</td></tr>
#                 <tr><td>Deadline</td><td>{round(order.deadline,1)}s</td></tr>
#                 <tr><td>Agent</td><td>{f'Agent {order.assigned_agent}' if order.assigned_agent is not None else 'Unassigned'}</td></tr>
#                 <tr><td>Location</td><td>{lat}, {lon}</td></tr>
#             </table>
#         </div>
#         """

#         folium.Marker(
#             location=[lat, lon],
#             popup=folium.Popup(popup_html, max_width=220),
#             tooltip=f"Order {order.order_id} | {order.status} | P{order.priority}",
#             icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
#         ).add_to(m)

#     # ── agents ──
#     for agent in sim.agents:
#         lat, lon = grid_to_latlon(*agent.location)
#         load_pct = round(len(agent.current_orders) / agent.capacity * 100)

#         popup_html = f"""
#         <div style="font-family:sans-serif;min-width:180px">
#             <b style="font-size:13px">🚚 Agent #{agent.agent_id}</b><br>
#             <hr style="margin:4px 0">
#             <table style="font-size:12px;width:100%">
#                 <tr><td>Status</td><td><b>{agent.status.upper()}</b></td></tr>
#                 <tr><td>Capacity</td><td>{len(agent.current_orders)}/{agent.capacity}</td></tr>
#                 <tr><td>Load</td><td>{load_pct}%</td></tr>
#                 <tr><td>Orders</td><td>{agent.current_orders}</td></tr>
#                 <tr><td>Location</td><td>{lat}, {lon}</td></tr>
#             </table>
#             <div style="background:#e5e7eb;border-radius:4px;height:6px;margin-top:6px">
#                 <div style="background:{'#ef4444' if load_pct==100 else '#f59e0b' if load_pct>60 else '#22c55e'};
#                             width:{load_pct}%;height:6px;border-radius:4px"></div>
#             </div>
#         </div>
#         """

#         folium.Marker(
#             location=[lat, lon],
#             popup=folium.Popup(popup_html, max_width=220),
#             tooltip=f"Agent {agent.agent_id} | {agent.status} | {len(agent.current_orders)}/{agent.capacity}",
#             icon=folium.DivIcon(html=f"""
#                 <div style="
#                     background: {'#f59e0b' if agent.status=='busy' else '#22c55e'};
#                     color: white;
#                     font-size: 11px;
#                     font-weight: 700;
#                     width: 28px;
#                     height: 28px;
#                     border-radius: 50%;
#                     display: flex;
#                     align-items: center;
#                     justify-content: center;
#                     border: 2px solid white;
#                     box-shadow: 0 2px 4px rgba(0,0,0,0.4)
#                 ">A{agent.agent_id}</div>
#             """)
#         ).add_to(m)
        
    
#     # ── city label ──
#     folium.Marker(
#         location=city["center"],
#         icon=folium.DivIcon(html=f"""
#             <div style="
#                 background: rgba(15,23,42,0.85);
#                 color: white;
#                 font-size: 13px;
#                 font-weight: 700;
#                 padding: 5px 12px;
#                 border-radius: 6px;
#                 border: 1px solid rgba(255,255,255,0.2);
#                 white-space: nowrap;
#             ">{city['emoji']} {city['name']} Fleet</div>
#         """)
#     ).add_to(m)

#     # ── legend ──
#     legend_html = f"""
#     <div style="
#         position: fixed;
#         bottom: 30px; left: 30px;
#         background: rgba(15,23,42,0.92);
#         color: white;
#         padding: 12px 16px;
#         border-radius: 8px;
#         font-family: sans-serif;
#         font-size: 12px;
#         border: 1px solid rgba(255,255,255,0.15);
#         z-index: 9999;
#         min-width: 180px;
#     ">
#         <b style="font-size:13px">{city['emoji']} {city['name']} Fleet Map</b>
#         <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
#         <div>🟢 Agent (idle)</div>
#         <div>🟠 Agent (busy)</div>
#         <div style="margin-top:6px">
#             <span style="color:#94a3b8">●</span> Order (pending)<br>
#             <span style="color:#3b82f6">●</span> Order (assigned)<br>
#             <span style="color:#22c55e">●</span> Order (delivered)<br>
#             <span style="color:#ef4444">●</span> Order (failed)
#         </div>
#         <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
#         <div style="color:#fca5a5">🔴 Traffic delay zone</div>
#         <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
#         <div style="color:#94a3b8;font-size:11px">
#             {len(sim.agents)} agents | {len(sim.orders)} orders
#         </div>
#     </div>
#     """
#     m.get_root().html.add_child(folium.Element(legend_html))

#     return m

# # ── GENERATE + SAVE ───────────────────────────────────────────────────

# if __name__ == "__main__":
#     sim = SimulationState()
#     assign_orders(sim, verbose=False)

#     m = build_map(sim)
#     m.save("map_output.html")

#     from cities import get_current_city
#     city = get_current_city()
#     print(f"\n Map saved → map_output.html")
#     print(f" City: {city['emoji']} {city['name']}")
#     print(f" Agents plotted  : {len(sim.agents)}")
#     print(f" Orders plotted  : {len(sim.orders)}")
#     print(f" Assigned orders : {len([o for o in sim.orders if o.status == 'assigned'])}")


import folium
from simulation import SimulationState
from engine import assign_orders

# ── COLOR MAPS ────────────────────────────────────────────────────────

ORDER_COLORS = {
    "pending":   "gray",
    "assigned":  "blue",
    "delivered": "green",
    "failed":    "red"
}

AGENT_COLORS = {
    "idle": "darkgreen",
    "busy": "orange"
}

PRIORITY_ICONS = {
    1: "arrow-down",
    2: "minus",
    3: "arrow-up"
}

ROUTE_COLORS = {
    1: "#94a3b8",   # low priority — gray
    2: "#3b82f6",   # medium priority — blue
    3: "#ef4444"    # high priority — red
}

# ── COORDINATE CONVERTER ──────────────────────────────────────────────

def grid_to_latlon(x, y):
    from cities import get_current_city
    city = get_current_city()
    lat  = city["lat_min"] + (y / 100) * (city["lat_max"] - city["lat_min"])
    lon  = city["lon_min"] + (x / 100) * (city["lon_max"] - city["lon_min"])
    return round(lat, 6), round(lon, 6)

# ── MAP BUILDER ───────────────────────────────────────────────────────

def build_map(sim, metrics=None):
    from cities import get_current_city
    city = get_current_city()

    m = folium.Map(
        location=city["center"],
        zoom_start=city["zoom"],
        tiles="CartoDB dark_matter"
    )

    # ── traffic zones ──
    for zx, zy, radius, name, multiplier in city["traffic_zones"]:
        lat, lon = grid_to_latlon(zx, zy)
        radius_m = radius * 300

        folium.Circle(
            location=[lat, lon],
            radius=radius_m,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.08,
            dash_array="5 5",
            tooltip=f"⚠️ {name} | Delay: {multiplier}x"
        ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=f"""
                <div style="
                    background: rgba(220,38,38,0.85);
                    color: white;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 3px 7px;
                    border-radius: 4px;
                    white-space: nowrap;
                    border: 1px solid rgba(255,255,255,0.3)
                ">{name}</div>
            """)
        ).add_to(m)

    # ── route lines — agent to assigned order ──
    for agent in sim.agents:
        if not agent.current_orders:
            continue
        target_order = sim.get_order_by_id(agent.current_orders[0])
        if not target_order:
            continue

        agent_lat, agent_lon = grid_to_latlon(*agent.location)
        order_lat, order_lon = grid_to_latlon(*target_order.location)

        color = ROUTE_COLORS.get(target_order.priority, "#3b82f6")

        # dashed route line
        folium.PolyLine(
            locations=[[agent_lat, agent_lon], [order_lat, order_lon]],
            color=color,
            weight=2,
            opacity=0.7,
            dash_array="5 8",
            tooltip=f"Agent {agent.agent_id} → Order {target_order.order_id} (P{target_order.priority})"
        ).add_to(m)

        # priority label at midpoint
        mid_lat = (agent_lat + order_lat) / 2
        mid_lon = (agent_lon + order_lon) / 2
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(html=f"""
                <div style="
                    background: {color};
                    color: white;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 1px 5px;
                    border-radius: 3px;
                    white-space: nowrap;
                    opacity: 0.9;
                ">→ P{target_order.priority}</div>
            """)
        ).add_to(m)

    # ── orders ──
    for order in sim.orders:
        lat, lon  = grid_to_latlon(*order.location)
        color     = ORDER_COLORS.get(order.status, "gray")
        icon_name = PRIORITY_ICONS.get(order.priority, "minus")

        popup_html = f"""
        <div style="font-family:sans-serif;min-width:180px">
            <b style="font-size:13px">Order #{order.order_id}</b><br>
            <hr style="margin:4px 0">
            <table style="font-size:12px;width:100%">
                <tr><td>Status</td><td><b>{order.status.upper()}</b></td></tr>
                <tr><td>Priority</td><td>{'⬆️ HIGH' if order.priority==3 else '➡️ MED' if order.priority==2 else '⬇️ LOW'}</td></tr>
                <tr><td>Deadline</td><td>{round(order.deadline,1)}s</td></tr>
                <tr><td>Agent</td><td>{f'Agent {order.assigned_agent}' if order.assigned_agent is not None else 'Unassigned'}</td></tr>
                <tr><td>Location</td><td>{lat}, {lon}</td></tr>
            </table>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"Order {order.order_id} | {order.status} | P{order.priority}",
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
        ).add_to(m)

    # ── agents ──
    for agent in sim.agents:
        lat, lon = grid_to_latlon(*agent.location)
        load_pct = round(len(agent.current_orders) / agent.capacity * 100)

        # pulse animation for busy agents
        pulse_style = ""
        if agent.status == "busy":
            pulse_style = "animation: agentPulse 1.5s infinite;"

        popup_html = f"""
        <div style="font-family:sans-serif;min-width:180px">
            <b style="font-size:13px">🚚 Agent #{agent.agent_id}</b><br>
            <hr style="margin:4px 0">
            <table style="font-size:12px;width:100%">
                <tr><td>Status</td><td><b>{agent.status.upper()}</b></td></tr>
                <tr><td>Capacity</td><td>{len(agent.current_orders)}/{agent.capacity}</td></tr>
                <tr><td>Load</td><td>{load_pct}%</td></tr>
                <tr><td>Orders</td><td>{agent.current_orders}</td></tr>
                <tr><td>Location</td><td>{lat}, {lon}</td></tr>
            </table>
            <div style="background:#e5e7eb;border-radius:4px;height:6px;margin-top:6px">
                <div style="background:{'#ef4444' if load_pct==100 else '#f59e0b' if load_pct>60 else '#22c55e'};
                            width:{load_pct}%;height:6px;border-radius:4px"></div>
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"Agent {agent.agent_id} | {agent.status} | {len(agent.current_orders)}/{agent.capacity}",
            icon=folium.DivIcon(html=f"""
                <style>
                @keyframes agentPulse {{
                    0%,100% {{ transform: scale(1); opacity: 1; }}
                    50% {{ transform: scale(1.2); opacity: 0.8; }}
                }}
                </style>
                <div style="
                    background: {'#f59e0b' if agent.status=='busy' else '#22c55e'};
                    color: white;
                    font-size: 11px;
                    font-weight: 700;
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.4);
                    {pulse_style}
                ">A{agent.agent_id}</div>
            """)
        ).add_to(m)

    # ── city label ──
    folium.Marker(
        location=city["center"],
        icon=folium.DivIcon(html=f"""
            <div style="
                background: rgba(15,23,42,0.85);
                color: white;
                font-size: 13px;
                font-weight: 700;
                padding: 5px 12px;
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.2);
                white-space: nowrap;
            ">{city['emoji']} {city['name']} Fleet</div>
        """)
    ).add_to(m)

    # ── legend ──
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px; left: 30px;
        background: rgba(15,23,42,0.92);
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: sans-serif;
        font-size: 12px;
        border: 1px solid rgba(255,255,255,0.15);
        z-index: 9999;
        min-width: 200px;
    ">
        <b style="font-size:13px">{city['emoji']} {city['name']} Fleet Map</b>
        <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
        <div>🟢 Agent (idle)</div>
        <div>🟠 Agent (busy — pulsing)</div>
        <div style="margin-top:6px">
            <span style="color:#94a3b8">●</span> Order (pending)<br>
            <span style="color:#3b82f6">●</span> Order (assigned)<br>
            <span style="color:#22c55e">●</span> Order (delivered)<br>
            <span style="color:#ef4444">●</span> Order (failed)
        </div>
        <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
        <div style="color:#fca5a5">🔴 Traffic delay zone</div>
        <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
        <div style="color:#94a3b8">-- P1 route (low)</div>
        <div style="color:#3b82f6">-- P2 route (medium)</div>
        <div style="color:#ef4444">-- P3 route (high)</div>
        <hr style="border-color:rgba(255,255,255,0.2);margin:6px 0">
        <div style="color:#94a3b8;font-size:11px">
            {len(sim.agents)} agents | {len(sim.orders)} orders
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

# ── GENERATE + SAVE ───────────────────────────────────────────────────

if __name__ == "__main__":
    sim = SimulationState()
    assign_orders(sim, verbose=False)

    m = build_map(sim)
    m.save("map_output.html")

    from cities import get_current_city
    city = get_current_city()
    print(f"\n Map saved → map_output.html")
    print(f" City: {city['emoji']} {city['name']}")
    print(f" Agents plotted  : {len(sim.agents)}")
    print(f" Orders plotted  : {len(sim.orders)}")
    print(f" Assigned orders : {len([o for o in sim.orders if o.status == 'assigned'])}")
    print(f" Active routes   : {len([a for a in sim.agents if a.current_orders])}")