import re
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

class MacrocycleParser:
    @staticmethod
    def parse_markdown(markdown_text: str, plan_start_str: str = None) -> Dict[str, Any]:
        """
        Parsuje wygenerowany raport makrocykl.md z IronTrain do ustrukturyzowanego słownika JSON dla bazy i UI.
        """
        if not markdown_text:
            return {"mesocycles": [], "weeks": [], "mermaid_code": ""}

        # 1. Wyciągnięcie bloku Mermaid Gantt
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)\s*```', markdown_text)
        mermaid_code = mermaid_match.group(1).strip() if mermaid_match else ""

        # 2. Parsowanie Mezocykli / Faz
        mesocycles = []
        phases_raw = re.findall(r'###\s+([^\n]+)\n([\s\S]*?)(?=(?:###|\Z))', markdown_text)

        color_palette = ["#7DBB5E", "#FFCC2F", "#FA932A", "#EB5150", "#A463B1", "#99B1B6"]
        start_w = 1

        for idx, (phase_title, phase_body) in enumerate(phases_raw):

            # Wyciągnięcie celu CTL z tekstu (np. Cel CTL: 10 -> 35 lub CTL: 35 -> 55)
            ctl_match = re.search(r'CTL[^\d]*(\d+)\s*(?:→|->)\s*(\d+)', phase_body, re.IGNORECASE)
            ctl_start = int(ctl_match.group(1)) if ctl_match else 10 + idx * 15
            ctl_end = int(ctl_match.group(2)) if ctl_match else ctl_start + 15

            # Wyciągnięcie tygodni / zakresu
            weeks_count = 8 # Domyślnie 8 tygodni na fazę
            if "Faza I" in phase_title: weeks_count = 12
            elif "Faza V" in phase_title or "BPS" in phase_title: weeks_count = 3

            end_w = start_w + weeks_count - 1

            mesocycles.append({
                "name": phase_title.strip(),
                "start_week": start_w,
                "end_week": end_w,
                "ctl_start": ctl_start,
                "ctl_end": ctl_end,
                "focus": phase_body.strip().replace("\n", " "),

                "color": color_palette[idx % len(color_palette)]
            })
            start_w = end_w + 1

        total_weeks = mesocycles[-1]["end_week"] if mesocycles else 52

        # 3. Wygenerowanie w Pythonie 52-tygodniowej siatki z matematyczną interpolacją CTL (Wzór Friela)
        start_dt = date.fromisoformat(plan_start_str) if plan_start_str else date.today()
        weeks_grid = []

        for w_idx in range(1, total_weeks + 1):
            cur_date = start_dt + timedelta(weeks=w_idx - 1)
            
            # Znajdź odpowiedni mezocykl dla danego tygodnia
            matching_meso = next((m for m in mesocycles if m["start_week"] <= w_idx <= m["end_week"]), None)
            meso_name = matching_meso["name"] if matching_meso else "Baza"
            
            # Liniowa interpolacja CTL
            if matching_meso:
                w_in_meso = w_idx - matching_meso["start_week"] + 1
                total_w_in_meso = max(1, matching_meso["end_week"] - matching_meso["start_week"] + 1)
                progression = w_in_meso / total_w_in_meso
                proj_ctl = int(round(matching_meso["ctl_start"] + (matching_meso["ctl_end"] - matching_meso["ctl_start"]) * progression))
            else:
                proj_ctl = 15 + w_idx * 1

            planned_hrs = 6.0 + (proj_ctl / 10.0)
            planned_tss = int(planned_hrs * 45)

            weeks_grid.append({
                "week_number": w_idx,
                "start_date": cur_date.isoformat(),
                "planned_hours": round(planned_hrs, 1),
                "planned_tss": planned_tss,
                "projected_ctl": proj_ctl,
                "mesocycle": meso_name,
                "key_sessions": f"Z2 objętość, akcent Z3/Z4"
            })

        return {
            "mesocycles": mesocycles,
            "weeks": weeks_grid,
            "mermaid_code": mermaid_code,
            "total_weeks": total_weeks
        }
