from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.snapshot import AthleteSnapshot
from app.domain.metrics import extract_record_val, vdot_from_5k_minutes, vdot_from_wkg, format_seconds_to_pace

class SotaPassportMetric:
    def __init__(self, value: Any, source_type: str, annotation: str):
        """
        source_type:
          - 'MEASURED': Bezpośredni pomiar z urządzenia (czujnik mocy, zegarek GPS, pasek HR)
          - 'ESTIMATED': Wartość wyliczona z matematycznych modeli / algorytmów (np. Morton 3P, VDOT z 5k)
          - 'USER_DECLARED': Wartość wpisana ręcznie przez użytkownika w profilu
        """
        self.value = value
        self.source_type = source_type
        self.annotation = annotation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "source_type": self.source_type,
            "annotation": self.annotation
        }


class SotaService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def extract_power_duration_curve_metrics(pc_bike_year: Any) -> Dict[str, Dict[str, Any]]:
        """
        Wyciąga z zrzutu krzywej mocy faktycznie zmierzone rekordy na rowerze z podziałem na źródła pomiarowe:
        5s (sprint), 1m (anaerobic), 5m (VO2Max), 20m (CP20), 1h (FTP).
        """
        targets = [
            ("5s", 5, "Moc maksymalna sprint (zmierzona z mocomierza)"),
            ("1m", 60, "Moc 1-minutowa beztlenowa (zmierzona z mocomierza)"),
            ("5m", 300, "Moc 5-minutowa VO2Max (zmierzona z mocomierza)"),
            ("20m", 1200, "Moc 20-minutowa CP20 (zmierzona z mocomierza)"),
            ("1h", 3600, "Moc 1-godzinna (zmierzona z mocomierza)")
        ]
        res = {}
        for key, secs, label in targets:
            val_str = extract_record_val(pc_bike_year, secs, is_pace=False)
            if val_str != "N/A":
                res[key] = SotaPassportMetric(val_str, "MEASURED", label).to_dict()
            else:
                res[key] = SotaPassportMetric("N/A", "ESTIMATED", f"Brak bezpośredniego pomiaru mocomierza dla {key} (Estymowano)").to_dict()
        return res

    @staticmethod
    def extract_pace_curve_metrics(pc_run_year: Any) -> Dict[str, Dict[str, Any]]:
        """
        Wyciąga z zrzutu krzywej tempa zmierzone rekordy w biegu (z zegarka GPS):
        400m, 1k, 5k, 10k, 21k.
        """
        targets = [
            ("400m", 400, "Tempo 400m (zmierzone z zegarka GPS)"),
            ("1k", 1000, "Tempo 1 km (zmierzone z zegarka GPS)"),
            ("5k", 5000, "Tempo 5 km (zmierzone z zegarka GPS)"),
            ("10k", 10000, "Tempo 10 km (zmierzone z zegarka GPS)"),
            ("21k", 21097, "Tempo półmaraton (zmierzone z zegarka GPS)")
        ]
        res = {}
        for key, meters, label in targets:
            val_str = extract_record_val(pc_run_year, meters, is_pace=True)
            if val_str != "N/A":
                res[key] = SotaPassportMetric(val_str, "MEASURED", label).to_dict()
            else:
                res[key] = SotaPassportMetric("N/A", "ESTIMATED", f"Brak bezpośredniego pomiaru GPS dla {key} (Estymowano)").to_dict()
        return res

    @staticmethod
    def determine_ftp_and_vdot(intervals_data: Dict[str, Any]) -> Tuple[SotaPassportMetric, SotaPassportMetric]:
        """
        Oblicza FTP oraz VDOT jednoznacznie oznaczając, czy pochodzą z bezpośrednich pomiarów mocomierza / GPS,
        czy są estymowane z modeli matematycznych, czy wpisane ręcznie przez użytkownika.
        """
        athlete = intervals_data.get("athlete", {})
        pc_bike_42d = intervals_data.get("pc_bike_42d")
        pc_bike_year = intervals_data.get("pc_bike_year")
        pc_run_year = intervals_data.get("pc_run_year")

        # 1. FTP
        ftp_val = 0.0
        ftp_source = "ESTIMATED"
        ftp_annotation = "Estymacja FTP"

        for pc_data in [pc_bike_42d, pc_bike_year]:
            if isinstance(pc_data, dict) and "list" in pc_data and len(pc_data["list"]) > 0:
                curve = pc_data["list"][0]
                models = curve.get("powerModels") or []
                if models:
                    m_ftp = float(models[0].get("ftp") or models[0].get("criticalPower") or 0.0)
                    if m_ftp > 0:
                        ftp_val = m_ftp
                        ftp_source = "ESTIMATED"
                        ftp_annotation = f"Estymowano z modelu mocowo-czasowego ({models[0].get('type', 'Morton 3P')})"
                        break

        if ftp_val == 0.0:
            sport_settings = athlete.get("sportSettings", [])
            for s in sport_settings:
                if "Ride" in s.get("types", []):
                    s_ftp = float(s.get("ftp") or 0.0)
                    if s_ftp > 0:
                        ftp_val = s_ftp
                        ftp_source = "USER_DECLARED"
                        ftp_annotation = "Wartość zadeklarowana przez użytkownika w ustawieniach kolarstwa"
                        break

        if ftp_val == 0.0:
            user_ftp = float(athlete.get("icu_ftp") or athlete.get("ftp") or 0.0)
            if user_ftp > 0:
                ftp_val = user_ftp
                ftp_source = "USER_DECLARED"
                ftp_annotation = "Wartość zadeklarowana przez użytkownika w profilu ogólnym"

        if ftp_val == 0.0:
            ftp_annotation = "Brak pomiaru i brak zadeklarowanego FTP (Wartość domyślna)"

        ftp_metric = SotaPassportMetric(round(ftp_val, 1), ftp_source, ftp_annotation)

        # 2. VDOT (Wyłącznie z biegów – VDOT to wskaźnik biegowy Danielsa)
        vdot_val = 0.0
        vdot_source = "ESTIMATED"
        vdot_annotation = "Brak zarejestrowanych aktywności biegowych w oknie czasowym (Brak VDOT)"

        if isinstance(pc_run_year, dict) and "list" in pc_run_year and len(pc_run_year["list"]) > 0:
            curve = pc_run_year["list"][0]
            dists = curve.get("distance", [])
            vals = curve.get("values", [])

            if dists and vals and len(dists) == len(vals):
                closest_idx = min(range(len(dists)), key=lambda i: abs(dists[i] - 5000.0))
                if abs(dists[closest_idx] - 5000.0) / 5000.0 <= 0.15:
                    total_sec = float(vals[closest_idx])
                    if total_sec > 0:
                        vdot_val = vdot_from_5k_minutes(total_sec / 60.0)
                        vdot_source = "MEASURED"
                        vdot_annotation = f"Wyliczono z najlepiej zmierzonego biegu na 5km ({format_seconds_to_pace(total_sec / 5.0)} /km z zegarka GPS)"


        if vdot_val == 0.0:
            # Sprawdź czy użytkownik ma zadeklarowany LTHR/strefy biegu w profilu
            sport_settings = athlete.get("sportSettings", [])
            for s in sport_settings:
                if "Run" in s.get("types", []):
                    lthr = float(s.get("lthr") or 0.0)
                    if lthr > 0:
                        vdot_annotation = f"Brak bezpośredniego biegu 5km GPS (LTHR biegu: {int(lthr)} bpm z ustawień)"
                        break

        vdot_metric = SotaPassportMetric(round(vdot_val, 1) if vdot_val > 0 else "N/A", vdot_source, vdot_annotation)


        return ftp_metric, vdot_metric

    @staticmethod
    def identify_strengths_and_limiters(
        pdc: Dict[str, Dict[str, Any]],
        pace: Dict[str, Dict[str, Any]],
        ftp_metric: SotaPassportMetric,
        vdot_metric: SotaPassportMetric
    ) -> Tuple[List[str], List[str]]:
        """
        Analizuje profil fizjologiczny i wyciąga mocne strony oraz limitery z jasnymi adnotacjami.
        """
        strengths = []
        limiters = []

        p20 = pdc.get("20m", {}).get("value")
        p5 = pdc.get("5m", {}).get("value")

        if p20 != "N/A" and p5 != "N/A":
            try:
                w20 = float(str(p20).replace("W", ""))
                w5 = float(str(p5).replace("W", ""))
                if w5 > 0 and (w20 / w5) >= 0.85:
                    strengths.append("Wysoka odporność zmęczeniowa i silny profil progowy Z4 (zmierzona z mocomierza)")
                elif w5 > 0 and (w20 / w5) < 0.75:
                    limiters.append("Niska moc progowa Z4 w stosunku do potencjału VO2Max (zmierzona z mocomierza)")
            except: pass

        if vdot_metric.value > 48.0:
            annot = "z zmierzonego biegu GPS" if vdot_metric.source_type == "MEASURED" else "estymowana z modelu"
            strengths.append(f"Wysoki wskaźnik VDOT ({vdot_metric.value} - {annot})")
        elif vdot_metric.value > 0 and vdot_metric.value < 38.0:
            annot = "z zmierzonego biegu GPS" if vdot_metric.source_type == "MEASURED" else "estymowana z modelu"
            limiters.append(f"Wymaga rozbudowy bazy tlenowej (VDOT {vdot_metric.value} - {annot})")

        if not strengths:
            strengths.append("Baza w trakcie rozbudowy")
        if not limiters:
            limiters.append("Brak wyraźnego wąskiego gardła")

        return strengths, limiters

    def build_and_save_snapshot(
        self,
        user_id: int,
        intervals_data: Dict[str, Any]
    ) -> AthleteSnapshot:
        """
        Buduje pełny paszport fizjologiczny, wzbogaca o adnotacje źródeł pomiaru (MEASURED vs ESTIMATED vs USER_DECLARED)
        i aktualizuje wpis w bazie danych PostgreSQL/SQLite.
        """
        athlete = intervals_data.get("athlete", {})
        wellness = intervals_data.get("wellness") or []
        latest_w = wellness[-1] if wellness else {}

        pc_bike_year = intervals_data.get("pc_bike_year")
        pc_run_year = intervals_data.get("pc_run_year")

        pdc_metrics = self.extract_power_duration_curve_metrics(pc_bike_year)
        pace_metrics = self.extract_pace_curve_metrics(pc_run_year)
        ftp_metric, vdot_metric = self.determine_ftp_and_vdot(intervals_data)
        strengths, limiters = self.identify_strengths_and_limiters(pdc_metrics, pace_metrics, ftp_metric, vdot_metric)

        weight_raw = athlete.get("weight") or latest_w.get("weight")
        weight_source = "MEASURED" if latest_w.get("weight") else "USER_DECLARED" if athlete.get("weight") else "ESTIMATED"
        weight = float(weight_raw or 75.0)

        snapshot_data = {
            "pdc_metrics": pdc_metrics,
            "pace_metrics": pace_metrics,
            "ftp_metric": ftp_metric.to_dict(),
            "vdot_metric": vdot_metric.to_dict(),
            "weight_metric": SotaPassportMetric(weight, weight_source, "Waga zawodnika").to_dict(),
            "strengths": strengths,
            "limiters": limiters
        }

        today = date.today()
        snapshot = self.db.query(AthleteSnapshot).filter(
            AthleteSnapshot.user_id == user_id,
            AthleteSnapshot.date == today
        ).first()

        if not snapshot:
            snapshot = AthleteSnapshot(user_id=user_id, date=today)
            self.db.add(snapshot)

        snapshot.resting_hr = int(latest_w.get("restingHR") or latest_w.get("resting_hr") or 0)
        snapshot.hrv = float(latest_w.get("hrv") or 0.0)
        snapshot.sleep_score = float(latest_w.get("sleepScore") or latest_w.get("sleep_score") or 0.0)
        snapshot.ctl = int(round(float(latest_w.get("ctl") or 0.0)))
        snapshot.atl = int(round(float(latest_w.get("atl") or 0.0)))
        snapshot.tsb = int(round(float(latest_w.get("tsb") or (snapshot.ctl - snapshot.atl))))

        snapshot.estimated_ftp = ftp_metric.value
        snapshot.estimated_vdot = vdot_metric.value
        snapshot.weight = weight
        snapshot.power_curve_year = pdc_metrics
        snapshot.pace_curve_year = pace_metrics
        snapshot.stats_year = snapshot_data

        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
