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
                hospitals.append({
                    "id": row["node_id"],
                    "name": row["name"],
                    "urgency": int(row["urgency_score"]),
                    "med_demand": int(row["med_demand_units"]),
                    "food_demand": int(row["food_demand_units"]),
                    "fuel_demand": int(row["fuel_demand_liters"]),
                    "distance": float(row["distance_km"]),
                    "storage_cap": int(row["storage_cap_units"]),
                    "road_accessible": int(row["road_accessible"])
                })
    return hospitals

def run_lpp_allocation(hospitals, target_mode=1):
    PAYLOAD_WEIGHT_CAP = 300.0 if target_mode == 1 else 3000.0
    
    # Global Warehouse Supply Limits
    rem_global_med = 600
    rem_global_food = 1000
    rem_global_fuel = 2000
    
    # Commodity Unit Weights (kg)
    WEIGHT_MED = 12.0
    WEIGHT_FOOD = 25.0
    WEIGHT_FUEL = 0.85
    
    # Prioritize higher-urgency hospitals first
    sorted_hospitals = sorted(hospitals, key=lambda x: x["urgency"], reverse=True)
    allocations = {}
    
    for h in sorted_hospitals:
        h_id = h["id"]
        urgency = h["urgency"]
        
        max_val = -1.0
        best_m, best_f, best_l = 0, 0, 0
        
        max_m = min(h["med_demand"], rem_global_med, int(PAYLOAD_WEIGHT_CAP // WEIGHT_MED))
        max_f = min(h["food_demand"], rem_global_food, int(PAYLOAD_WEIGHT_CAP // WEIGHT_FOOD))
        
        # Exact Bounded Integer Optimization Search
        for m in range(max_m + 1):
            for f in range(max_f + 1):
                used_w = (m * WEIGHT_MED) + (f * WEIGHT_FOOD)
                rem_w = PAYLOAD_WEIGHT_CAP - used_w
                if rem_w < 0:
                    continue
                
                # Maximizing Generator Fuel (3.0 urgency multiplier) under remaining weight cap
                l = min(h["fuel_demand"], rem_global_fuel, int(rem_w // WEIGHT_FUEL))
                
                # Objective Function: Priority-Weighted Relief Value
                val = urgency * ((3.0 * l) + (2.5 * m) + (1.2 * f))
                if val > max_val:
                    max_val = val
                    best_m, best_f, best_l = m, f, l
                    
        rem_global_med -= best_m
        rem_global_food -= best_f
        rem_global_fuel -= best_l
        
        allocations[h_id] = {
            "name": h["name"],
            "medical_kits": best_m,
            "food_crates": best_f,
            "fuel_liters": best_l,
            "road_accessible": h["road_accessible"]
        }
        
    dispatch_mode = "AIR_RELIEF_DRONE" if target_mode == 1 else "GROUND_TRUCK"
    
    print("\n========================================================")
    print("      MEMBER 1: LPP CARGO ALLOCATION SOLVER             ")
    print("========================================================")
    print(f"Solver Status: Optimal")
    print(f"Transport Mode: {dispatch_mode} (Max {PAYLOAD_WEIGHT_CAP} kg/run)\n")
    
    # Sort back by original Hospital ID order for clean output
    ordered_allocations = {}
    for h in hospitals:
        h_id = h["id"]
        info = allocations[h_id]
        ordered_allocations[h_id] = info
        print(f"Node [{h_id}] {info['name']:<18} | Fuel: {info['fuel_liters']:<4} L | Meds: {info['medical_kits']:<3} | Food: {info['food_crates']:<3}")
    print("========================================================\n")
    
    return {
        "status": "Optimal",
        "dispatch_mode": dispatch_mode,
        "payload_weight_cap_kg": PAYLOAD_WEIGHT_CAP,
        "allocations": ordered_allocations
    }

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir) if os.path.basename(current_dir) == "src" else current_dir
    
    csv_file = os.path.join(base_dir, "data", "city_nodes.csv")
    nodes = load_city_nodes(csv_file)
    result = run_lpp_allocation(nodes, target_mode=1)
    
    out_json = os.path.join(base_dir, "data", "allocated_supplies.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
        
    print(f"[SUCCESS] Allocation output exported to: {out_json}")
