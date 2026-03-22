CITIES = {
    "bangalore": {
        "name":    "Bangalore",
        "emoji":   "🌆",
        "lat_min": 12.85,
        "lat_max": 13.05,
        "lon_min": 77.45,
        "lon_max": 77.75,
        "center":  [12.97, 77.59],
        "zoom":    12,
        "agents":  20,
        "orders":  100,
        "traffic_zones": [
            (25, 25, 15, "Koramangala Traffic Zone", 1.8),
            (75, 75, 10, "Whitefield Traffic Zone",  2.2),
            (50, 50, 20, "MG Road Traffic Zone",     1.5),
        ]
    },
    "delhi": {
        "name":    "Delhi",
        "emoji":   "🏛️",
        "lat_min": 28.50,
        "lat_max": 28.75,
        "lon_min": 76.95,
        "lon_max": 77.30,
        "center":  [28.61, 77.20],
        "zoom":    11,
        "agents":  25,
        "orders":  120,
        "traffic_zones": [
            (30, 70, 18, "Connaught Place Traffic Zone", 2.5),
            (70, 30, 12, "Noida Border Traffic Zone",    2.0),
            (50, 50, 22, "Ring Road Traffic Zone",       1.8),
        ]
    },
    "mumbai": {
        "name":    "Mumbai",
        "emoji":   "🌊",
        "lat_min": 18.90,
        "lat_max": 19.20,
        "lon_min": 72.78,
        "lon_max": 73.00,
        "center":  [19.07, 72.87],
        "zoom":    12,
        "agents":  30,
        "orders":  150,
        "traffic_zones": [
            (40, 60, 15, "Dharavi Traffic Zone",  2.8),
            (60, 40, 10, "BKC Traffic Zone",       2.0),
            (20, 80, 12, "Dadar Traffic Zone",     1.9),
            (80, 20,  8, "Andheri Traffic Zone",   2.2),
        ]
    }
}

current_city = {"key": "bangalore", "config": CITIES["bangalore"]}

def set_city(key: str) -> dict:
    if key not in CITIES:
        return {"error": f"Unknown city: {key}"}
    current_city["key"]    = key
    current_city["config"] = CITIES[key]
    return {"status": "ok", "city": CITIES[key]}

def get_city() -> dict:
    return {
        "current": current_city["key"],
        "config":  current_city["config"],
        "all":     CITIES
    }

def get_current_city() -> dict:
    return current_city["config"]