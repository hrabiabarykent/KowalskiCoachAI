from datetime import date, timedelta, datetime
from typing import Dict, Any, List

from app.domain.metrics import extract_record_val, vdot_from_wkg, vdot_from_5k_minutes

class SnapshotDTO:
    def __init__(self,
                 activities_year: List[Dict[str, Any]],
                 activities_42d: List[Dict[str, Any]],
                 weight: float,
                 ctl: float,
                 atl: float,
                 tsb: float,
                 resting_hr: int,
                 gender: str,
                 age: int,
                 estimated_ftp: float,
                 estimated_vdot: float,
                 stats_year: Dict[str, Dict[str, float]],
                 power_curve_year: Any,
                 pace_curve_year: Any):
        self.activities_year = activities_year
        self.activities_42d = activities_42d
        self.weight = weight
        self.ctl = ctl
        self.atl = atl
        self.tsb = tsb
        self.resting_hr = resting_hr
        self.gender = gender
        self.age = age
        self.estimated_ftp = estimated_ftp
        self.estimated_vdot = estimated_vdot
        self.stats_year = stats_year
        self.power_curve_year = power_curve_year
        self.pace_curve_year = pace_curve_year

class SnapshotBuilder:
    def build(self, user_id: int, intervals_data: Dict[str, Any], today: date = date.today()) -> SnapshotDTO:
        limit_42d = today - timedelta(days=42)
        
        athlete = intervals_data.get("athlete", {})
        wellness = intervals_data.get("wellness") or []
        latest = wellness[-1] if wellness else {}
        
        activities_year_raw = intervals_data.get("activities_year") or []
        recent_activities_for_ai = []
        stats_year = {
            "Ride": {"tss": 0.0, "h": 0.0}, "Run": {"tss": 0.0, "h": 0.0}, 
            "Swim": {"tss": 0.0, "h": 0.0}, "Other": {"tss": 0.0, "h": 0.0}
        }

        for act in activities_year_raw:
            try:
                a_date_str = act.get("start_date_local", "")[:10]
                if not a_date_str: continue
                
                a_date = datetime.strptime(a_date_str, "%Y-%m-%d").date()
                load = act.get("icu_training_load") or act.get("training_load") or 0.0
                duration_h = (act.get("moving_time") or 0.0) / 3600.0
                atype_raw = act.get("type", "")
                a_type = "Ride" if "Ride" in atype_raw else "Run" if "Run" in atype_raw else "Swim" if "Swim" in atype_raw else "Other"
                
                stats_year[a_type]["tss"] += load
                stats_year[a_type]["h"] += duration_h
                
                if a_date >= limit_42d:
                    recent_activities_for_ai.append({
                        "date": a_date_str,
                        "name": act.get("name"),
                        "type": a_type,
                        "tss": load,
                        "duration_min": round(duration_h * 60)
                    })
            except Exception:
                continue

        # 1. VDOT from VDOT 5k (last year)
        vdot_run = 0.0
        pc_run_year = intervals_data.get("pc_run_year")
        
        # Parallel arrays extraction (Intervals logic)
        if isinstance(pc_run_year, dict) and "list" in pc_run_year and len(pc_run_year["list"]) > 0:
            curve = pc_run_year["list"][0]
            dists = curve.get("distance", [])
            vals = curve.get("values", [])
            
            if dists and vals and len(dists) == len(vals):
                closest_idx = min(range(len(dists)), key=lambda i: abs(dists[i] - 5000.0))
                
                # Check 15% offset (4250m to 5750m)
                if abs(dists[closest_idx] - 5000.0) / 5000.0 <= 0.15:
                    total_time_seconds = float(vals[closest_idx])
                    if total_time_seconds > 0:
                        total_minutes = total_time_seconds / 60.0
                        vdot_run = vdot_from_5k_minutes(total_minutes)
        
        # Fallback to direct pace string if format was flat (redundant but safe)
        if vdot_run == 0.0:
            pace_5k_str = extract_record_val(pc_run_year, 5000, True)
            if pace_5k_str != "N/A":
                from app.domain.metrics import parse_pace_str
                pace_sec = parse_pace_str(pace_5k_str)
                if pace_sec:
                    total_minutes = (pace_sec * 5.0) / 60.0
                    vdot_run = vdot_from_5k_minutes(total_minutes)
        
        latest_wellness_weight = None
        for w in reversed(wellness):
            if w.get("weight"):
                latest_wellness_weight = w.get("weight")
                break

        # 2. FTP from Power Models (eFTP) or sportSettings
        ftp = 0.0
        pc_bike_year = intervals_data.get("pc_bike_year")
        pc_bike_42d = intervals_data.get("pc_bike_42d")
        
        # Try finding eFTP in power models first
        for pc_data in [pc_bike_42d, pc_bike_year]:
            if isinstance(pc_data, dict) and "list" in pc_data and len(pc_data["list"]) > 0:
                curve = pc_data["list"][0]
                models = curve.get("powerModels") or []
                if models:
                    # Intervals.icu usually provides Morton's 3P or similar model
                    ftp = float(models[0].get("ftp") or models[0].get("criticalPower") or 0.0)
                    if ftp > 0:
                        break
        
        if ftp == 0.0:
            sport_settings = athlete.get("sportSettings", [])
            for s in sport_settings:
                if "Ride" in s.get("types", []):
                    ftp = float(s.get("ftp") or 0.0)
                    break
        
        if ftp == 0.0:
            ftp = float(athlete.get("icu_ftp") or athlete.get("ftp") or 0.0)
            
        weight = float(latest_wellness_weight or athlete.get("weight") or 75.0)
        
        ctl = int(round(float(latest.get("ctl", 0.0))))
        atl = int(round(float(latest.get("atl", 0.0))))
        tsb_raw = latest.get("tsb")
        tsb = int(round(float(tsb_raw))) if tsb_raw is not None else int(round(float(ctl - atl)))
        
        gender = str(athlete.get("sex", ""))
        dob = athlete.get("icu_date_of_birth")
        age = today.year - datetime.strptime(dob[:10], "%Y-%m-%d").year if dob else 0
        
        estimated_vdot = float(vdot_run)

        return SnapshotDTO(
            activities_year=activities_year_raw,
            activities_42d=recent_activities_for_ai,
            weight=weight,
            ctl=ctl,
            atl=atl,
            tsb=tsb,
            resting_hr=int(latest.get("restingHR", 0) or 0),
            gender=gender,
            age=age,
            estimated_ftp=ftp,
            estimated_vdot=estimated_vdot,
            stats_year=stats_year,
            power_curve_year=intervals_data.get("pc_bike_year"),
            pace_curve_year=intervals_data.get("pc_run_year")
        )
