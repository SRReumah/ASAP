# Project ASAP: Emergency Air-Relief Command Center

> **An Integrated Operations Research (OR) and Cybersecurity Pipeline for Automated Disaster Relief & Drone Logistics**

---

## What is Project ASAP?

Imagine a severe flood hits a major city. Roads are underwater, power lines are knocked out, and communication infrastructure is damaged. Inside a local hospital, the emergency generator is running out of diesel fuel to power life-support machines and ICUs. Ambulances and supply trucks cannot navigate the flooded roads.

**Project ASAP** acts as an automated emergency response brain. It connects a hospital’s wireless distress signal directly to an emergency drone command center through a 4-step chain reaction:

1. **Scout & Protect (Member 2 - C Engine):** Checks if roads are flooded. If roads are blocked, it reroutes transport to **Air-Relief Drones**, finds the shortest $12\text{ km}$ flight path, and encrypts the telemetry signals with AES-256 encryption so cyber-attackers cannot hijack the drone mid-air.
2. **Optimal Packing (Member 1 - Python LPP):** Calculates the exact mix of Generator Fuel, Medical Kits, and Food Crates to pack without exceeding the drone’s strict $300\text{ kg}$ weight limit.
3. **Inventory Alarm (Member 3 - Python Inventory):** Monitors the hospital’s fuel burn rate and automatically triggers a reorder alert when fuel drops below $65\text{ Liters}$ ($35\text{ Liters}$ safety buffer).
4. **Flight Dispatcher (Member 4 - Python PERT/CPM):** Calculates the bottleneck tasks and determines that the total round-trip flight loop will take exactly **$76.33\text{ minutes}$**.

All of this happens live through an interactive **Command Center Dashboard** (`index.html`) driven by a real-time **Python API Server** (`server.py`).

---

## System Architecture & Individual Member Breakdown

The project is structured into **four independent backend engines** (written in C and Python) that execute sequentially when a distress signal is received, generating physical data artifacts on disk.

              ┌──────────────────────────────────────────┐
              │   Hospital Distress Signal Broadcast     │
              └────────────────────┬─────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Member 2: C Network Flow & Security Engine (c_core/net_crypto_core.c)    │
│    • Dijkstra Shortest Path (12 km) | Mode Switching (Air vs Ground)        │
│    • AES-256 Payload Encryption & HMAC-SHA256 Digital Signature Tag         │
│    └─► Generates: data/telemetry_packet.bin (109-byte binary struct)        │
└──────────────────────────────────────────┬──────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Member 1: Linear Programming Cargo Solver (src/01_lpp_allocation.py)     │
│    • Integer Linear Programming (ILP) Priority Value Maximization           │
│    • 300 kg Air Payload Constraint vs Multi-Commodity Demands               │
│    └─► Generates: data/allocated_supplies.json                              │
└──────────────────────────────────────────┬──────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Member 3: Inventory & Safety Stock Control (src/03_inventory.py)          │
│    • Economic Order Quantity (EOQ) & Daily Fuel Burn Calculations           │
│    • Safety Stock Reserve (35L) & Reorder Point Threshold (65L)             │
└──────────────────────────────────────────┬──────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. Member 4: PERT/CPM Flight Loop Scheduler (src/04_pert_schedule.py)       │
│    • Probabilistic Task Variance & Expected Durations (Te)                  │
│    • Forward/Backward Pass Slack Time Analysis                              │
│    • Critical Path Bottleneck Sequence: A ➔ D ➔ E ➔ F (76.33 minutes)       │
└─────────────────────────────────────────────────────────────────────────────┘


---

## Mathematical Formulations by Module

### Member 1: Integer Linear Programming (Cargo Allocation)
* **Objective Function:** Maximize Priority-Weighted Relief Utility ($Z$)
  $$\max Z = \sum_{h \in H} U_h \cdot \left( 3.0 \cdot x_{h}^{\text{fuel}} + 2.5 \cdot x_{h}^{\text{med}} + 1.2 \cdot x_{h}^{\text{food}} \right)$$
* **Subject to Payload Weight Cap ($300\text{ kg}$):**
  $$12.0 \cdot x_{h}^{\text{med}} + 25.0 \cdot x_{h}^{\text{food}} + 0.85 \cdot x_{h}^{\text{fuel}} \le 300.0\text{ kg}$$

### Member 2: Network Routing & Cryptography (C Language)
* **Dijkstra Shortest Path:** Relaxation condition $d(v) > d(u) + w(u,v)$ across adjacency matrices.
* **Security Protocol:** $109\text{-byte}$ memory packed struct containing AES-256-CBC encrypted payload and HMAC-SHA256 integrity tag (`data/telemetry_packet.bin`).

### Member 3: Inventory Control & Fuel Safety Stock
* **Economic Order Quantity ($\text{EOQ}$):** $\text{EOQ} = \sqrt{\frac{2 \cdot D \cdot S}{H}}$
* **Safety Stock ($\text{SS}$):** $\text{SS} = Z \cdot \sigma_d \cdot \sqrt{L} = 1.65 \cdot 12.0 \cdot \sqrt{3.0} \approx 35\text{ Liters}$
* **Reorder Point ($\text{ROP}$):** $\text{ROP} = (\text{Daily Burn} \cdot L) + \text{SS} = 65\text{ Liters}$

### Member 4: PERT/CPM Project Scheduling
* **Expected Activity Time ($T_e$):** $T_e = \frac{a + 4m + b}{6}$
* **Activity Variance ($\sigma^2$):** $\sigma^2 = \left(\frac{b - a}{6}\right)^2$
* **Slack Time:** $\text{Slack} = \text{LS} - \text{ES}$. Critical Path identified where $\text{Slack} = 0$.

---

## Repository Directory Structure

ASAP/
├── c_core/
│   ├── net_crypto_core.c       # Member 2: C Routing & AES/HMAC Security Engine
│   └── net_crypto_core.exe     # Compiled C Binary Executable
├── data/
│   ├── city_nodes.csv          # Shared Hospital & Base Node Dataset
│   ├── allocated_supplies.json # Output generated by Member 1 (LPP Solver)
│   └── telemetry_packet.bin    # Output generated by Member 2 (109-byte Binary Struct)
├── src/
│   ├── 01_lpp_allocation.py    # Member 1: Python LPP Cargo Allocation Engine
│   ├── 03_inventory.py         # Member 3: Python Hospital Inventory Engine
│   └── 04_pert_schedule.py     # Member 4: Python PERT Critical Path Scheduler
├── index.html                  # Full-Stack Command Center Web Dashboard
├── server.py                   # Master Full-Stack Python HTTP & API Server
└── README.md                   # System Documentation


---

## 🚀 How to Run the Project

### Prerequisites
* Python 3.8 or higher installed.
* GCC Compiler installed (for compiling C core, optional if pre-compiled executable exists).

### Step 1: Launch the Integrated Full-Stack Application
In your terminal, navigate to the `ASAP` root directory and run:

```powershell
python server.py
```
This starts the master Python API server at http://localhost:8000 and automatically opens the Command Center in your default browser.

Step 2: Live Demo Simulation
In the top-right view selector of the dashboard, switch to Phone: Hospital Unit.

Click BROADCAST EMERGENCY DISTRESS SIGNAL.

Watch the view automatically switch to Laptop: Command Center.

In your terminal, observe server.py physically executing net_crypto_core.exe, 01_lpp_allocation.py, 03_inventory.py, and 04_pert_schedule.py live. The dashboard will populate with real computed data from disk artifacts.

Step 3: Run Standalone Backend Scripts (For Individual Code Review)
Each backend module can also be executed independently in the terminal:

PowerShell
# 1. Test Member 2 C Security Engine
.\c_core\net_crypto_core.exe 1 0

# 2. Test Member 1 LPP Cargo Solver
python src/01_lpp_allocation.py

# 3. Test Member 3 Inventory Engine
python src/03_inventory.py

# 4. Test Member 4 PERT Scheduler
python src/04_pert_schedule.py
