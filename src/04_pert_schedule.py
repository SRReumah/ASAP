import math

def run_pert_cpm():
    activities = {
        "A": {"name": "Fuel & Cargo Loading at Base", "preds": [], "a": 10, "m": 15, "b": 26},
        "B": {"name": "C Network Check & AES Encryption", "preds": [], "a": 1, "m": 2, "b": 3},
        "C": {"name": "Pre-Flight Wireless Handshake", "preds": ["B"], "a": 2, "m": 3, "b": 6},
        "D": {"name": "Air Drone Transit to Hospital", "preds": ["A", "C"], "a": 20, "m": 35, "b": 80},
        "E": {"name": "Winch Offloading at Hospital", "preds": ["D"], "a": 10, "m": 15, "b": 20},
        "F": {"name": "HMAC Verification & Fuel Ingest", "preds": ["E"], "a": 3, "m": 5, "b": 9}
    }

    # Step 1: Compute Expected Duration Te & Variance
    for k, v in activities.items():
        v["Te"] = (v["a"] + 4.0 * v["m"] + v["b"]) / 6.0
        v["Var"] = ((v["b"] - v["a"]) / 6.0) ** 2
        v["ES"] = v["EF"] = v["LS"] = v["LF"] = v["Slack"] = 0.0

    # Step 2: Forward Pass
    for k, v in activities.items():
        v["ES"] = 0.0 if not v["preds"] else max(activities[p]["EF"] for p in v["preds"] if p in activities)
        v["EF"] = v["ES"] + v["Te"]

    total_project_time = max(v["EF"] for v in activities.values())

    # Step 3: Backward Pass
    for k in reversed(list(activities.keys())):
        v = activities[k]
        actual_succs = [s_id for s_id, s_val in activities.items() if k in s_val["preds"]]
        v["LF"] = total_project_time if not actual_succs else min(activities[s]["LS"] for s in actual_succs)
        v["LS"] = v["LF"] - v["Te"]
        v["Slack"] = v["LS"] - v["ES"]

    crit_path = [k for k, v in activities.items() if abs(v["Slack"]) < 1e-5]

    print("\n========================================================")
    print("      MEMBER 4: PERT DISPATCH CRITICAL PATH SCHEDULER    ")
    print("========================================================")
    print(f"{'ID':<4} {'Activity Description':<32} {'Te (min)':<10} {'Slack':<6}")
    print("-" * 56)
    for k, v in activities.items():
        print(f"{k:<4} {v['name']:<32} {v['Te']:<10.2f} {v['Slack']:<6.1f}")
    print("-" * 56)
    print(f"Total Expected Flight Loop Time: {total_project_time:.2f} minutes")
    print(f"CRITICAL PATH SEQUENCE        : {' -> '.join(crit_path)}\n")

if __name__ == "__main__":
    run_pert_cpm()