import csv
import json
import math
import os
import sys
import heapq
import urllib.request

# Staggered Elevation-Based Flood Thresholds for Realistic Rainfall Progression
NODE_FLOOD_THRESHOLDS = {
    "H1": 15.0,  # Low-lying river basin (Floods first at 15mm)
    "H2": 40.0,  # Mid-valley sector (Floods at 40mm)
    "H3": 65.0,  # Eastern drainage basin (Floods at 65mm)
    "H4": 85.0,  # Elevated southern ridge (Floods last at 85mm)
}


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates straight-line air flight distance (km) between two GPS points using the Haversine formula."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def check_live_flood_risk(lat, lon, cached_status, simulated_rain=None, node_id=None):
    """Evaluates road accessibility based on staggered elevation thresholds during simulation."""
    if simulated_rain is not None:
        total_rain = float(simulated_rain)
        threshold = NODE_FLOOD_THRESHOLDS.get(node_id, 15.0)

        if total_rain >= threshold:
            print(f"  [SIMULATOR] Rain ({total_rain} mm >= {threshold} mm threshold) at Node [{node_id}] -> ROAD FLOODED")
            return 0, False
        else:
            print(f"  [SIMULATOR] Clear Weather ({total_rain} mm < {threshold} mm threshold) at Node [{node_id}] -> ROAD OPEN")
            return 1, False

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,rain"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                current = data.get("current", {})
                precip = current.get("precipitation", 0.0)
                rain = current.get("rain", 0.0)
                total_rain = max(precip, rain)

                threshold = NODE_FLOOD_THRESHOLDS.get(node_id, 15.0)
                if total_rain >= threshold:
                    print(f"  [LIVE SENSOR] High Rain ({total_rain} mm) at Node [{node_id}] -> ROAD FLOODED")
                    return 0, True
                else:
                    print(f"  [LIVE SENSOR] Clear Weather ({total_rain} mm) at Node [{node_id}] -> ROAD OPEN")
                    return 1, True
    except Exception as e:
        print(f"  [OFFLINE CACHE] Internet down ({e}). Using Last Known State: {cached_status}")
        return cached_status, False

    return cached_status, False


def evaluate_route_telemetry(csv_path, flood_override_node=None, simulated_rain=None):
    if not os.path.exists(csv_path):
        print(f"[ERROR] Node dataset missing at: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    base_lat, base_lon = None, None
    for row in rows:
        if row["node_type"].strip().lower() == "warehouse":
            base_lat = float(row["latitude"])
            base_lon = float(row["longitude"])
            print(f"[MEMBER 2 DATA-LOADER] Warehouse Base GPS: ({base_lat}, {base_lon})")
            break

    if base_lat is None or base_lon is None:
        base_lat, base_lon = 27.7172, 85.3240

    hospitals = []
    blocked_nodes = set()
    cache_updated = False

    print("\n---------------- MEMBER 2: TELEMETRY & ROUTE EVALUATION ----------------")
    for row in rows:
        if row["node_type"].strip().lower() == "hospital":
            h_id = row["node_id"].strip()
            h_lat = float(row["latitude"])
            h_lon = float(row["longitude"])
            cached_road_status = int(row["road_accessible"])

            if flood_override_node and h_id.upper() == flood_override_node.upper():
                print(f"  [SIMULATOR] Localized Flood Injected at Node [{h_id}] ({row['name']}) -> ROAD BLOCKED")
                road_status = 0
                was_live = False
            else:
                road_status, was_live = check_live_flood_risk(
                    h_lat, h_lon, cached_road_status, simulated_rain, node_id=h_id
                )

            if road_status == 0:
                blocked_nodes.add(h_id)

            if was_live and road_status != cached_road_status:
                row["road_accessible"] = str(road_status)
                cache_updated = True

            calculated_dist = calculate_haversine_distance(
                base_lat, base_lon, h_lat, h_lon
            )

            hospitals.append(
                {
                    "id": h_id,
                    "name": row["name"],
                    "urgency": int(row["urgency_score"]),
                    "med_demand": int(row["med_demand_units"]),
                    "food_demand": int(row["food_demand_units"]),
                    "fuel_demand": int(row["fuel_demand_liters"]),
                    "distance": calculated_dist,
                    "storage_cap": int(row["storage_cap_units"]),
                    "road_accessible": road_status,
                }
            )
    print("------------------------------------------------------------------------\n")

    if cache_updated:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print("[MEMBER 2 CACHE] Persisted updated telemetry state to disk.")

    has_flooded_roads = len(blocked_nodes) > 0
    max_dist = max(n["distance"] for n in hospitals)

    if has_flooded_roads or max_dist > 20.0:
        target_mode = 1  # Air Relief Drone
        print(f"[MEMBER 2 AUTO-ROUTER] Obstacles/Floods ({len(blocked_nodes)} blocked) detected -> Selecting AIR DRONE Mode.")
    else:
        target_mode = 0  # Ground Truck
        print("[MEMBER 2 AUTO-ROUTER] All roads clear -> Selecting GROUND TRUCK Mode.")

    return hospitals, target_mode


if __name__ == "__main__":
    flood_node_flag = None
    sim_rain_flag = None

    if "--simulate-flood" in sys.argv:
        idx = sys.argv.index("--simulate-flood")
        if idx + 1 < len(sys.argv):
            flood_node_flag = sys.argv[idx + 1]

    if "--rain" in sys.argv:
        idx = sys.argv.index("--rain")
        if idx + 1 < len(sys.argv):
            sim_rain_flag = sys.argv[idx + 1]

    csv_file = os.path.join("data", "city_nodes.csv")
    nodes, selected_mode = evaluate_route_telemetry(csv_file, flood_override_node=flood_node_flag, simulated_rain=sim_rain_flag)

    mode_str = "AIR_RELIEF_DRONE" if selected_mode == 1 else "GROUND_TRUCK"
    print(f"\n[MEMBER 2 OUTPUT] Telemetry Evaluation Complete.")
    print(f"Target Transport Mode: {mode_str}")
    print(f"Evaluated Nodes      : {len(nodes)} Hospitals")
