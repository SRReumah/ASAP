import http.server
import socketserver
import json
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

class ASAPApiHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/dispatch':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
            data = json.loads(body) if body else {}

            target_hospital = str(data.get('target_hospital', '1'))
            road_status = str(data.get('road_status', '0')) # 0 = Flooded (Air Mode), 1 = Open (Ground)

            print("\n" + "="*60)
            print(" 🚨 REAL-TIME PIPELINE EXECUTION TRIGGERED VIA API")
            print("="*60)

            # -------------------------------------------------------------
            # STEP 1: Execute Member 2 (C Network & Crypto Engine)
            # -------------------------------------------------------------
            c_exe = BASE_DIR / "c_core" / ("net_crypto_core.exe" if os.name == 'nt' else "net_crypto_core")
            if not c_exe.exists():
                c_exe = BASE_DIR / ("net_crypto_core.exe" if os.name == 'nt' else "net_crypto_core")

            if c_exe.exists():
                print(f"[M2 ENGINE] Executing C binary: {c_exe} {target_hospital} {road_status}")
                res2 = subprocess.run([str(c_exe), target_hospital, road_status], capture_output=True, text=True)
                print(res2.stdout)
            else:
                print("[WARNING] C executable missing! Run 'gcc c_core/net_crypto_core.c -o c_core/net_crypto_core.exe' first.")

            # -------------------------------------------------------------
            # STEP 2: Execute Member 1 (PuLP LPP Allocation)
            # -------------------------------------------------------------
            lpp_script = BASE_DIR / "src" / "01_lpp_allocation.py"
            print(f"[M1 ENGINE] Executing PuLP Solver: {lpp_script}")
            res1 = subprocess.run([sys.executable, str(lpp_script)], capture_output=True, text=True)
            print(res1.stdout)

            # -------------------------------------------------------------
            # STEP 3: Execute Member 3 (Inventory & ROP Engine)
            # -------------------------------------------------------------
            inv_script = BASE_DIR / "src" / "03_inventory.py"
            print(f"[M3 ENGINE] Executing Inventory Engine: {inv_script}")
            res3 = subprocess.run([sys.executable, str(inv_script)], capture_output=True, text=True)
            print(res3.stdout)

            # -------------------------------------------------------------
            # STEP 4: Execute Member 4 (PERT Critical Path Scheduler)
            # -------------------------------------------------------------
            pert_script = BASE_DIR / "src" / "04_pert_schedule.py"
            print(f"[M4 ENGINE] Executing PERT Scheduler: {pert_script}")
            res4 = subprocess.run([sys.executable, str(pert_script)], capture_output=True, text=True)
            print(res4.stdout)

            # -------------------------------------------------------------
            # READ REAL OUTPUT ARTIFACTS GENERATED ON DISK
            # -------------------------------------------------------------
            alloc_json_path = BASE_DIR / "data" / "allocated_supplies.json"
            real_allocations = {}
            dispatch_mode = "AIR_RELIEF_DRONE" if road_status == "0" else "GROUND_TRUCK"
            
            if alloc_json_path.exists():
                with open(alloc_json_path, "r", encoding="utf-8") as f:
                    alloc_data = json.load(f)
                    real_allocations = alloc_data.get("allocations", {})
                    dispatch_mode = alloc_data.get("dispatch_mode", dispatch_mode)

            # Read C telemetry binary frame size
            telemetry_path = BASE_DIR / "data" / "telemetry_packet.bin"
            packet_size = telemetry_path.stat().st_size if telemetry_path.exists() else 0

            # Construct response payload with real computed data
            response_payload = {
                "status": "SUCCESS",
                "dispatch_mode": dispatch_mode,
                "telemetry_packet_bytes": packet_size,
                "allocations": real_allocations,
                "target_hospital_id": f"H{target_hospital}"
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        # Allow terminal output for API execution logs
        if "/api/dispatch" not in args[0]:
            pass

print("\n" + "=" * 65)
print("  ⚡ PROJECT ASAP: REAL-TIME FULL-STACK COMMAND CENTER")
print("=" * 65)
print(f" Server running at: http://localhost:{PORT}")
print(" Real-time API Endpoint active at: http://localhost:8000/api/dispatch")
print(" Press Ctrl+C to stop.\n")

webbrowser.open(f"http://localhost:{PORT}/index.html")

try:
    with socketserver.TCPServer(("", PORT), ASAPApiHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n[INFO] Server stopped.")
    sys.exit(0)