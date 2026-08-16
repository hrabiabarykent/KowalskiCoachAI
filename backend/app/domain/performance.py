from typing import Dict, Any
from app.domain.metrics import mps_to_pace

EVENT_TYPES = {
    "Bike": ["Road Race", "Gran Fondo", "Time Trial", "Gravel", "Zwift Race"],
    "Run": ["5k", "10k", "Half Marathon", "Marathon", "Ultra"],
    "Swim": ["1500m", "3.8km", "5km"],
    "Triathlon": ["Sprint", "Olympic", "70.3", "140.6", "Duathlon"]
}

def extract_zones(athlete_data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n--- [DEBUG] START: extract_zones ---")
    settings = athlete_data.get("sportSettings", [])
    zones_summary = {"bike_power": [], "bike_hr": [], "run_pace": [], "run_hr": [], "swim_pace": []}

    for sport in settings:
        s_types = sport.get("types", [])
        threshold = sport.get("threshold", 0)
        lthr = sport.get("lthr", 0)

        if "Ride" in s_types:
            pz = sport.get("power_zones", [])
            if pz and threshold > 0:
                prev = 0
                for i, val in enumerate(pz):
                    upper = int((val / 100) * threshold) if val < 500 else int(val)
                    zones_summary["bike_power"].append(f"Z{i+1} {prev}-{upper}W")
                    prev = upper + 1
            hz = sport.get("hr_zones", [])
            if hz:
                prev = 0
                for i, val in enumerate(hz):
                    zones_summary["bike_hr"].append(f"Z{i+1} {prev}-{int(val)}bpm")
                    prev = int(val) + 1

        if "Run" in s_types:
            pz = sport.get("pace_zones", [])
            if pz and threshold > 0:
                for i, val in enumerate(pz):
                    if val > 500: continue
                    zones_summary["run_pace"].append(f"Z{i+1} {mps_to_pace((val / 100) * threshold)}/km")
            hz = sport.get("hr_zones", [])
            if hz:
                prev = 0
                for i, val in enumerate(hz):
                    zones_summary["run_hr"].append(f"Z{i+1} {prev}-{int(val)}bpm")
                    prev = int(val) + 1

    return zones_summary
