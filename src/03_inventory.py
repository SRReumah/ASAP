import json
import math
import os
import sys

def run_inventory_control(json_file):
    if not os.path.exists(json_file):
        print(f"[ERROR] Required file '{json_file}' missing. Run Member 1 script first.")
        sys.exit(1)

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[ERROR] Corrupted JSON in '{json_file}'.")
        sys.exit(1)

    allocations = data.get("allocations", {})
    SETUP_COST_S = 150.00
    HOLDING_COST_FUEL_H = 1.50
    LEAD_TIME_DAYS = 3.0
    DAILY_STD_DEV = 12.0
    Z_FACTOR = 1.65

    print("\n========================================================")
    print("  MEMBER 3: HOSPITAL GENERATOR FUEL & INVENTORY ENGINE  ")
    print("========================================================")

    for h_id, h_info in allocations.items():
        name = h_info.get("name", h_id)
        fuel_liters = max(0, h_info.get("fuel_liters", 0))
        
        annual_fuel = max(fuel_liters * 12, 1)
        daily_fuel_burn = annual_fuel / 365.0
        
        # EOQ = sqrt((2 * D * S) / H)
        eoq_fuel = math.sqrt((2 * annual_fuel * SETUP_COST_S) / max(0.01, HOLDING_COST_FUEL_H))
        
        # Safety Stock = Z * sigma_d * sqrt(Lead_Time)
        safety_stock_fuel = Z_FACTOR * DAILY_STD_DEV * math.sqrt(LEAD_TIME_DAYS)
        
        # Reorder Point (ROP) = (Daily Burn * Lead Time) + Safety Stock
        rop_fuel = (daily_fuel_burn * LEAD_TIME_DAYS) + safety_stock_fuel

        print(f"Hospital Node [{h_id}]: {name}")
        print(f"  Generator Fuel Allocated: {fuel_liters} Liters")
        print(f"  Daily Fuel Burn Rate    : {daily_fuel_burn:.1f} Liters/day ({daily_fuel_burn/24.0:.1f} L/hr)")
        print(f"  EOQ (Optimal Fuel Batch): {math.ceil(eoq_fuel)} Liters")
        print(f"  Safety Stock Reserve    : {math.ceil(safety_stock_fuel)} Liters")
        print(f"  Reorder Threshold (ROP) : {math.ceil(rop_fuel)} Liters")
        print("-" * 56)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alloc_path = os.path.join(base_dir, "data", "allocated_supplies.json")
    run_inventory_control(alloc_path)