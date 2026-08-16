import json

def build_athlete_assessment_prompt(gender: str, age: int, weight: float, estimated_ftp: float,
                                    estimated_vdot: float, ctl: float, total_y: float) -> str:
    return f"Jesteś trenerem Kowalskim. Oceń zawodnika: {gender}, {age} lat, {weight}kg. Silnik: FTP {estimated_ftp}W, VDOT {estimated_vdot}. Baza CTL: {ctl}. Historia roczna TSS: {total_y}. Podaj poziom, mocną stronę i limiter w 3 zdaniach po polsku."


def build_raw_assessment_prompt(gender: str, age: int, weight: float, power_raw: dict, pace_raw: dict) -> str:
    return f"""
    Oceń zawodnika: {gender}, {age} lat, {weight}kg.
    DANE DO ANALIZY (RAW JSON):

    POWER CURVE YEAR (ROWER):
    {json.dumps(power_raw)}

    PACE CURVE YEAR (BIEG):
    {json.dumps(pace_raw)}
    """

def build_goal_evaluation_prompt(discipline: str, event_type: str, event_name: str, 
                                 weeks_left: float, target_desc: str,
                                 formatted_activities: str,
                                 avg_weekly_h: float, ctl: float,
                                 gender: str, age: int, weight: float, resting_hr: int,
                                 estimated_ftp: float, p1h: str, estimated_vdot: float) -> str:
    return f"""
    Jesteś trenerem Kowalskim. Oceń realność celu zawodnika wg protokołu 8 kroków.
    CEL: {discipline} - {event_type} ("{event_name}") za {weeks_left} tyg. Ambicja: {target_desc}.
    
    SZCZEGÓŁOWA LISTA TRENINGÓW (OSTATNIE 42 DNI):
    {formatted_activities if formatted_activities else "Brak treningów w ostatnim cyklu."}
    
    PODSUMOWANIE BAZY ROCZNEJ (365 DNI):
    - Średnia objętość: {avg_weekly_h} h/tydzień.
    - Całkowite Fitness (CTL): {ctl}

    PROFIL I SILNIK:
    - {gender}, {age} lat, {weight}kg, RHR: {resting_hr}
    - Rower FTP: {estimated_ftp}W, Moc 1h: {p1h}
    - VDOT (bieganie): {estimated_vdot}

    TWOJE ZADANIE - RAPORT:
    A. Analiza Konkurencji (Czy ostatnie 42 dni pracy pasują do wymagań celu?)
    B. Scenariusze: 🔴 Ambitny, 🟡 Realistyczny, 🟢 Bezpieczny
    C. Kluczowe Braki i Zagrożenia
    D. Werdykt i Plan działania na {weeks_left} tygodni.
    
    Pisz konkretnie, technicznie, po polsku.
    """

def build_annual_training_plan_prompt(gender: str, age: int, weight: float, ctl: float, 
                                      estimated_ftp: float, estimated_vdot: float,
                                      goals_list: str, weekly_hours_available: float,
                                      history_90d: str, summary_365d: str,
                                      training_availability: dict = None,
                                      plan_start: str = None, plan_end: str = None,
                                      total_weeks: int = 0, current_ctl: int = 0) -> str:
    # Format availability schedule
    availability_str = ""
    if training_availability:
        days_pl = {"Monday": "Poniedziałek", "Tuesday": "Wtorek", "Wednesday": "Środa", "Thursday": "Czwartek", 
                   "Friday": "Piątek", "Saturday": "Sobota", "Sunday": "Niedziela"}
        
        schedule = []
        total_planned_hours = 0
        for day, data in training_availability.items():
            if data.get("enabled"):
                hrs = data.get("max_hours", 0)
                sports = ", ".join(data.get("sports", []))
                schedule.append(f"- {days_pl.get(day, day)}: do {hrs}h ({sports})")
                total_planned_hours += hrs
        
        if schedule:
            availability_str = f"SZCZEGÓŁOWA DOSTĘPNOŚĆ W TYGODNIU (Max: {total_planned_hours}h):\n" + "\n".join(schedule)
    
    return f"""
    Jesteś elitarnym trenerem sportów wytrzymałościowych, ekspertem w metodyce Joe Friela.
    Twoim zadaniem jest stworzenie Planu Treningowego z podziałem na mezocykle od {plan_start} do {plan_end} ({total_weeks} tygodni).
    
    PROFIL ZAWODNIKA:
    - {gender}, {age} lat, waga: {weight} kg
    - Aktualna baza tlenowa (CTL): {current_ctl}
    - Rower FTP: {estimated_ftp}W
    - VDOT (bieg): {estimated_vdot}
    - Maksymalna Dostępność czasu na trening: {weekly_hours_available} h/tydzień
    
    {availability_str}
    
    PODSUMOWANIE ROKU (365 dni):
    {summary_365d if summary_365d else "Brak danych z ostatniego roku."}
    
    HISTORIA TRENINGOWA (Ostatnie 90 dni):
    {history_90d if history_90d else "Brak zarejestrowanych aktywności."}
    
    CELE SPORTOWE (TYLKO PRZYSZŁE):
    {goals_list if goals_list else "Brak zdefiniowanych celów."}
    
    ZASADY PROJEKCJI CTL:
    - CTL startuje od {current_ctl} w tygodniu 1
    - CTL zmienia się wg wzoru: new_ctl ≈ old_ctl + (weekly_tss - old_ctl * 7) / 42
    - W tygodniach regeneracyjnych CTL lekko spada (niższy TSS)
    - Przed wyścigiem A-priority CTL powinien osiągnąć plateau, TSB powinien być pozytywny (taper)
    - Bądź REALISTYCZNY — CTL nie rośnie szybciej niż 3-5 pkt/tydzień w fazie budowy
    
    ZADANIE:
    Stwórz plan z podziałem na mezocykle (Prep, Base 1-3, Build 1-2, Peak, Race, Transition wg Friela).
    Dla KAŻDEGO tygodnia podaj realistycznie przeliczoną projekcję CTL.
    
    ODPOWIEDZ WYŁĄCZNIE zwięzłym, czystym obiektem JSON (bez tekstu wstępnego, bez markdown):
    {{
      "mesocycles": [
        {{
          "name": "Base 1",
          "start_week": 1,
          "end_week": 4,
          "focus": "Baza Z2",
          "color": "#7DBB5E"
        }}
      ],
      "weeks": [
        {{
          "week_number": 1,
          "start_date": "{plan_start}",
          "planned_hours": 8.0,
          "planned_tss": 350,
          "projected_ctl": {current_ctl},
          "mesocycle": "Base 1",
          "key_sessions": "2x Z2 90m, 1x tempo"
        }}
      ]
    }}
    
    Kolory mezocykli:
    - Prep: "#99B1B6"
    - Base: "#7DBB5E" 
    - Build: "#FFCC2F"
    - Peak: "#FA932A"
    - Race: "#EB5150"
    - Transition: "#A463B1"
    
    Wpisz BARDZO ZWIĘŹLE (max 5 słów na tydzień w key_sessions) WSZYSTKIE {total_weeks} tygodni.
    """


def build_daily_autonomous_revision_prompt(
    wellness_data: list, 
    yesterday_planned_events: list,
    yesterday_executed_activities: list,
    today_planned_events: list,
    user_context: str,
    today_str: str,
    yesterday_str: str,
    compliance_fact: dict = None,
    guardrails_overrides: list = None,
    forced_decision: str = None
) -> str:
    wellness_table = build_wellness_md_table(wellness_data) if isinstance(wellness_data, list) else str(wellness_data)
    y_planned_table = build_activities_md_table(yesterday_planned_events) if isinstance(yesterday_planned_events, list) else str(yesterday_planned_events)
    y_executed_table = build_activities_md_table(yesterday_executed_activities) if isinstance(yesterday_executed_activities, list) else str(yesterday_executed_activities)
    t_planned_table = build_activities_md_table(today_planned_events) if isinstance(today_planned_events, list) else str(today_planned_events)

    compliance_str = "Brak pre-obliczeń compliance."
    if compliance_fact:
        compliance_str = (
            f"Status: {compliance_fact.get('status_type')}, Ocena matematyczna: {compliance_fact.get('score')}/10, "
            f"Planowany TSS: {compliance_fact.get('planned_tss')}, Wykonany TSS: {compliance_fact.get('actual_tss')}, "
            f"Delta TSS: {compliance_fact.get('delta_tss')}, Dryf kardio: {compliance_fact.get('decoupling') or 'Brak'}"
        )

    overrides_str = ", ".join(guardrails_overrides) if guardrails_overrides else "Brak flag ryzyka"
    decision_hint = f"SZTYWNY NAKAZ BACKENDOWY: {forced_decision}" if forced_decision else "Model LLM decyduje w granicach normy"

    return f"""
    Jesteś elitarnym systemem eksperckim Kowalski Coach dla sportowców wytrzymałościowych.
    Twoim zadaniem jest ocena compliance wczorajszego dnia, ocena dzisiejszej regeneracji oraz wygenerowanie decyzji i notatki dla zawodnika.
    
    WAŻNE DATY:
    Dzisiaj (today): {today_str}
    Wczoraj (yesterday): {yesterday_str}
    
    KONTEKST ZAWODNIKA:
    {user_context}
    
    =========== OBIEKTYWNE WYNIKI MATEMATYCZNE PYTHON (PRE-COMPUTED FACTS) ===========
    - Zgodność z planem (Compliance): {compliance_str}
    - Flagi ryzyka (Guardrails Overrides): {overrides_str}
    - Rygor wyroczni: {decision_hint}
    
    =========== DANE O ZDROWIU (WELLNESS OSTATNIE 30 DNI) ===========
    {wellness_table}
    
    =========== WCZORAJSZY PLAN (ZADANIE DOMOWE) ===========
    {y_planned_table}
    
    =========== WCZORAJSZE WYKONANIE (FAKTYCZNA PRACA) ===========
    {y_executed_table}
    
    =========== DZISIEJSZY ZAPLANOWANY TRENING ===========
    {t_planned_table}
    
    =========== TWOJE ZADANIE ===========
    1. Przedstaw zawodnikowi obiektywną ocenę wykonania wczorajszego treningu.
    2. Przedstaw empatyczne uzasadnienie decyzji na dziś na podstawie wskaźników wellness (HRV, RHR, Sen).
    3. Zwróć ostateczną decyzję (ACCEPT, MODIFY, CANCEL) oraz zwięzły opis ewentualnie nowego treningu.
    """



def build_wellness_md_table(wellness_list: list) -> str:
    """Konwertuje listę wpisów wellness do czytelnej tabeli Markdown."""
    if not wellness_list:
        return "*Brak danych z dziennika wellness.*"

    headers = ["Data", "HRV", "RHR", "Sleep", "CTL", "ATL", "TSB"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]

    for w in wellness_list[-30:]:
        if not isinstance(w, dict): continue
        d_str = str(w.get("date") or w.get("id") or "–")
        hrv = w.get("hrv") or "–"
        rhr = w.get("restingHR") if w.get("restingHR") is not None else w.get("resting_hr", "–")
        sleep = w.get("sleepScore") if w.get("sleepScore") is not None else w.get("sleepQuality", "–")
        ctl = w.get("ctl", "–")
        atl = w.get("atl", "–")
        tsb = w.get("tsb", "–")
        lines.append(f"| {d_str} | {hrv} | {rhr} | {sleep} | {ctl} | {atl} | {tsb} |")

    return "\n".join(lines)


def build_activities_md_table(activities_list: list) -> str:
    """Konwertuje listę aktywności do czytelnej tabeli Markdown."""
    if not activities_list:
        return "*Brak zarejestrowanych aktywności.*"

    headers = ["Data", "Nazwa", "Typ", "Dystans (km)", "Czas (m)", "TSS", "Decoupling"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]

    for a in activities_list[-30:]:
        if not isinstance(a, dict): continue
        d_str = str(a.get("start_date_local") or a.get("date") or "–")[:10]
        name = str(a.get("name") or "Aktywność")[:25]
        atype = str(a.get("type") or "Other")
        dist = a.get("distance")
        dist_km = f"{float(dist)/1000.0:.1f}" if dist else "–"
        dur = a.get("moving_time") or a.get("duration_min")
        dur_m = f"{int(float(dur)/60)}" if dur and float(dur) > 100 else f"{dur}" if dur else "–"
        tss = a.get("icu_training_load") or a.get("training_load") or a.get("tss") or "–"
        dec = a.get("decoupling")
        dec_str = f"{float(dec):.1f}%" if dec is not None else "–"

        lines.append(f"| {d_str} | {name} | {atype} | {dist_km} | {dur_m} | {tss} | {dec_str} |")

    return "\n".join(lines)


def build_sota_markdown_prompt_context(sota_dict: dict) -> str:
    """Konwertuje obiekt paszportu SOTA z SotaService na zwięzły format Markdown idealny dla Gemini LLM."""
    if not sota_dict:
        return "*Brak paszportu SOTA.*"

    out = []
    out.append("### PASZPORT FIZJOLOGICZNY ZAWODNIKA (SOTA)")

    summary = sota_dict.get("metrics_summary") or {}
    ftp_info = summary.get("ftp") or {}
    vdot_info = summary.get("vdot") or {}
    weight_info = summary.get("weight") or {}

    out.append(f"- **FTP Rower**: **{ftp_info.get('value', 'N/A')}W** [{ftp_info.get('source_type', 'N/A')}] ({ftp_info.get('annotation', '')})")
    out.append(f"- **VDOT Bieganie**: **{vdot_info.get('value', 'N/A')}** [{vdot_info.get('source_type', 'N/A')}] ({vdot_info.get('annotation', '')})")
    out.append(f"- **Waga**: **{weight_info.get('value', 'N/A')} kg** [{weight_info.get('source_type', 'N/A')}]")
    out.append(f"- **PMC Status**: CTL `{summary.get('ctl', '–')}` | ATL `{summary.get('atl', '–')}` | TSB `{summary.get('tsb', '–')}`\n")

    pdc = sota_dict.get("power_duration_curve_pdc") or {}
    if pdc:
        out.append("#### Rekordowe Waty Kolarstwo (PDC)")
        headers = ["Czas", "Waty", "Źródło", "Adnotacja"]
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        for k, v in pdc.items():
            if isinstance(v, dict):
                lines.append(f"| {k} | {v.get('value', 'N/A')} | {v.get('source_type', 'N/A')} | {v.get('annotation', '')} |")
        out.append("\n".join(lines) + "\n")

    pace_run = sota_dict.get("pace_curve_run") or {}
    if pace_run:
        out.append("#### Rekordowe Tempa Bieganie (Pace Curve)")
        headers = ["Dystans", "Tempo", "Źródło", "Adnotacja"]
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        for k, v in pace_run.items():
            if isinstance(v, dict):
                lines.append(f"| {k} | {v.get('value', 'N/A')} | {v.get('source_type', 'N/A')} | {v.get('annotation', '')} |")
        out.append("\n".join(lines) + "\n")

    diag = sota_dict.get("physiological_diagnosis") or {}
    if diag.get("strengths"):
        out.append("**Mocne strony**: " + " • ".join(diag["strengths"]))
    if diag.get("limiters"):
        out.append("**Wąskie gardła / Limitery**: " + " • ".join(diag["limiters"]))

    return "\n".join(out)


def build_ai_wellness_evaluation_prompt(wellness_data: list, activities_data: list, planned_today: list) -> str:
    wellness_table = build_wellness_md_table(wellness_data) if isinstance(wellness_data, list) else str(wellness_data)
    activities_table = build_activities_md_table(activities_data) if isinstance(activities_data, list) else str(activities_data)
    planned_table = build_activities_md_table(planned_today) if isinstance(planned_today, list) else str(planned_today)

    return f"""
    Jesteś trenerem Kowalskim. Oceń czy dzisiejszy plan treningowy wymaga modyfikacji/interwencji z powodu stanu zdrowia i regeneracji.
    
    WELLNESS (Ostatnie 30 dni):
    {wellness_table}
    
    AKTYWNOŚCI (Ostatnie 30 dni):
    {activities_table}
    
    PLAN NA DZIŚ:
    {planned_table}
    
    Zwróć odpowiedź w formacie JSON zgodnym ze schematem: needs_revision (bool), reason (str).
    """



