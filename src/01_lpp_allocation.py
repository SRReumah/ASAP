import importlib.util
import json
import os
import sys
import pulp
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatus

# Dynamic import for Member 2 module
spec = importlib.util.spec_from_file_location("m2_route_risk", os.path.join("src", "02_route_risk.py"))
m2_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m2_module)
evaluate_route_telemetry = m2_module.evaluate_route_telemetry


def run_lpp_allocation(hospitals, target_mode=0):
    SUPPLY_MED = 600
    SUPPLY_FOOD = 1000
    SUPPLY_FUEL = 2000

    WEIGHT_MED = 12.0   # kg/kit
    WEIGHT_FOOD = 25.0  # kg/crate
    WEIGHT_FUEL = 0.85  # kg/liter

    prob = LpProblem("Disaster_Relief_Allocation", LpMaximize)

    med_vars = {
        h["id"]: LpVariable(f"Med_{h['id']}", lowBound=0, cat="Integer")
        for h in hospitals
    }
    food_vars = {
        h["id"]: LpVariable(f"Food_{h['id']}", lowBound=0, cat="Integer")
        for h in hospitals
    }
    fuel_vars = {
        h["id"]: LpVariable(f"Fuel_{h['id']}", lowBound=0, cat="Integer")
        for h in hospitals
    }

    prob += (
        lpSum(
            [
                (fuel_vars[h["id"]] * h["urgency"] * 3.0)
                + (med_vars[h["id"]] * h["urgency"] * 2.5)
                + (food_vars[h["id"]] * h["urgency"] * 1.2)
                for h in hospitals
            ]
        ),
        "Maximize_Priority_Value",
    )

    prob += (
        lpSum([med_vars[h["id"]] for h in hospitals]) <= SUPPLY_MED,
        "Supply_Limit_Med",
    )
    prob += (
        lpSum([food_vars[h["id"]] for h in hospitals]) <= SUPPLY_FOOD,
        "Supply_Limit_Food",
    )
    prob += (
        lpSum([fuel_vars[h["id"]] for h in hospitals]) <= SUPPLY_FUEL,
        "Supply_Limit_Fuel",
    )

    for h in hospitals:
        prob += med_vars[h["id"]] <= h["med_demand"], f"Max_Med_{h['id']}"
        prob += food_vars[h["id"]] <= h["food_demand"], f"Max_Food_{h['id']}"
        prob += fuel_vars[h["id"]] <= h["fuel_demand"], f"Max_Fuel_{h['id']}"
        
        # Node-Specific Dynamic Payload Cap:
        # Flooded/Blocked roads are restricted to Air Drone Payload (300kg).
        # Open roads receive Ground Truck Payload (3000kg).
        node_cap = 300.0 if h["road_accessible"] == 0 else 3000.0

        prob += (
            (med_vars[h["id"]] * WEIGHT_MED)
            + (food_vars[h["id"]] * WEIGHT_FOOD)
            + (fuel_vars[h["id"]] * WEIGHT_FUEL)
        ) <= node_cap, f"Weight_Cap_{h['id']}"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    status_str = LpStatus[prob.status]

    output = {
        "status": status_str,
        "dispatch_mode": (
            "AIR_RELIEF_DRONE" if target_mode == 1 else "GROUND_TRUCK"
        ),
        "payload_weight_cap_kg": 300.0 if target_mode == 1 else 3000.0,
        "allocations": {},
    }

    for h in hospitals:
        m_val = int(med_vars[h["id"]].varValue or 0)
        f_val = int(food_vars[h["id"]].varValue or 0)
        l_val = int(fuel_vars[h["id"]].varValue or 0)

        total_kg = (m_val * WEIGHT_MED) + (f_val * WEIGHT_FOOD) + (l_val * WEIGHT_FUEL)

        output["allocations"][h["id"]] = {
            "name": h["name"],
            "medical_kits": m_val,
            "food_crates": f_val,
            "fuel_liters": l_val,
            "delivered_weight_kg": round(total_kg, 1),
            "road_accessible": h["road_accessible"],
            "distance_km": h["distance"],
        }

    return output


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
    nodes, auto_mode = evaluate_route_telemetry(csv_file, flood_override_node=flood_node_flag, simulated_rain=sim_rain_flag)
    result = run_lpp_allocation(nodes, target_mode=auto_mode)

    out_json = os.path.join("data", "allocated_supplies.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(f"[SUCCESS] Allocation output exported to: {out_json}")
