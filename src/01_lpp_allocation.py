import csv
import json
import os
import sys

def load_city_nodes(csv_path):
    if not os.path.exists(csv_path):
        print(f"[ERROR] Node dataset missing at: {csv_path}")
        sys.exit(1)
        
    hospitals = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("node_type") == "Hospital":
                try:
                    dist_val = float(row.get("distance_km", row.get("distance", 10.0)))
                except (ValueError, TypeError):
                    dist_val = 10.0
                    
                hospitals.append({
                    "id": row.get("node_id", "H1"),
                    "name": row.get("name", "Unknown Hospital"),
                    "urgency": int(row.get("urgency_score", 5)),
                    "med_demand": int(row.get("med_demand_units", 10)),
                    "food_demand": int(row.get("food_demand_units", 5)),
                    "fuel_demand": int(row.get("fuel_demand_liters", 200)),
                    "distance": dist_val,
                    "distance_km": dist_val,
                    "storage_cap": int(row.get("storage_cap_units", 500)),
                    "road_accessible": int(row.get("road_accessible", 1)),
                    "flood_threshold_m": float(row.get("flood_threshold_m", 1.5))
                })
    return hospitals

def run_lpp_allocation(hospitals, target_mode=1, scenario="balanced"):
    PAYLOAD_WEIGHT_CAP = 300.0 if target_mode == 1 else 3000.0
    
    rem_global_med = 600
    rem_global_food = 1000
    rem_global_fuel = 2000
    
    WEIGHT_MED = 12.0
    WEIGHT_FOOD = 25.0
    WEIGHT_FUEL = 0.85
    
    fuel_mult = 5.0 if scenario == "power" else (1.0 if scenario == "medical" else 3.0)
    med_mult = 1.0 if scenario == "power" else (5.0 if scenario == "medical" else 2.5)
    food_mult = 1.0 if scenario == "power" else (1.0 if scenario == "medical" else 1.2)

    sorted_hospitals = sorted(hospitals, key=lambda x: x.get("urgency", 5), reverse=True)
    allocations = {}
    
    for h in sorted_hospitals:
        h_id = h.get("id", "H1")
        urgency = h.get("urgency", 5)
        
        med_demand = h.get("med_demand", 10)
        food_demand = h.get("food_demand", 5)
        fuel_demand = h.get("fuel_demand", 200)
        
        max_val = -1.0
        best_m, best_f, best_l = 0, 0, 0
        
        max_m = min(med_demand, rem_global_med, int(PAYLOAD_WEIGHT_CAP // WEIGHT_MED))
        max_f = min(food_demand, rem_global_food, int(PAYLOAD_WEIGHT_CAP // WEIGHT_FOOD))
        
        for m in range(max_m + 1):
            for f in range(max_f + 1):
                used_w = (m * WEIGHT_MED) + (f * WEIGHT_FOOD)
                rem_w = PAYLOAD_WEIGHT_CAP - used_w
                if rem_w < 0:
                    continue
                
                l = min(fuel_demand, rem_global_fuel, int(rem_w // WEIGHT_FUEL))
                val = urgency * ((fuel_mult * l) + (med_mult * m) + (food_mult * f))
                if val > max_val:
                    max_val = val
                    best_m, best_f, best_l = m, f, l
                    
        rem_global_med -= best_m
        rem_global_food -= best_f
        rem_global_fuel -= best_l
        
        delivered_w = round((best_m * WEIGHT_MED) + (best_f * WEIGHT_FOOD) + (best_l * WEIGHT_FUEL), 2)
        dist_val = h.get("distance_km", h.get("distance", 10.0))
        
        # Populate ALL keys defensively so app.py NEVER encounters a KeyError
        allocations[h_id] = {
            "id": h_id,
            "name": h.get("name", "Hospital"),
            "urgency": urgency,
            "medical_kits": best_m,
            "food_crates": best_f,
            "fuel_liters": best_l,
            "delivered_weight_kg": delivered_w,
            "distance_km": dist_val,
            "distance": dist_val,
            "road_accessible": h.get("road_accessible", 1),
            "flood_threshold_m": h.get("flood_threshold_m", 1.5),
            "storage_cap": h.get("storage_cap", 500)
        }
        
    dispatch_mode = "AIR_RELIEF_DRONE" if target_mode == 1 else "GROUND_TRUCK"
    
    ordered_allocations = {}
    for h in hospitals:
        h_id = h.get("id", "H1")
        if h_id in allocations:
            ordered_allocations[h_id] = allocations[h_id]
        else:
            ordered_allocations[h_id] = {
                "id": h_id,
                "name": h.get("name", "Hospital"),
                "urgency": 5,
                "medical_kits": 0,
                "food_crates": 0,
                "fuel_liters": 0,
                "delivered_weight_kg": 0.0,
                "distance_km": 10.0,
                "distance": 10.0,
                "road_accessible": 1,
                "flood_threshold_m": 1.5,
                "storage_cap": 500
            }

    output = {
        "status": "Optimal",
        "scenario": scenario,
        "dispatch_mode": dispatch_mode,
        "payload_weight_cap_kg": PAYLOAD_WEIGHT_CAP,
        "allocations": ordered_allocations
    }
    
    return output

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir) if os.path.basename(current_dir) == "src" else current_dir
    
    scenario_arg = sys.argv[1] if len(sys.argv) > 1 else "balanced"
    
    csv_file = os.path.join(base_dir, "data", "city_nodes.csv")
    nodes = load_city_nodes(csv_file)
    result = run_lpp_allocation(nodes, target_mode=1, scenario=scenario_arg)
    
    out_json = os.path.join(base_dir, "data", "allocated_supplies.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
        
    print(f"[SUCCESS] Allocation output exported to: {out_json}")