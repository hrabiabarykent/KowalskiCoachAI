from datetime import date
from typing import List, Dict, Any

def build_macrocycle_markdown_prompt(
    gender: str, age: int, weight: float, ctl: float,
    estimated_ftp: float, estimated_vdot: float,
    goals_list: str, weekly_hours_available: float,
    summary_365d: str, plan_start: str, plan_end: str,
    total_weeks: int, current_ctl: int
) -> str:
    """
    Tworzy prompt dla Gemini z prośbą o wygenerowanie pełnego, ustrukturyzowanego raportu makrocyklu
    zgodnego z metodyką periodyzacji Joe Friela w ramach KowalskiCoach AI.
    """
    return f"""
# ROLA I ZADANIE
Jesteś elitarnym trenerem sportów wytrzymałościowych (ekspertem periodyzacji Joe Friela w systemie KowalskiCoach AI).
Twoim zadaniem jest stworzenie długoterminowego planu Makrocyklu (`makrocykl.md`) dla zawodnika na okres od {plan_start} do {plan_end} ({total_weeks} tygodni).

# PROFIL I STATYSTYKI ZAWODNIKA
- **Biometria**: {gender}, {age} lat, waga: {weight} kg
- **Aktualna baza (CTL)**: {current_ctl}
- **Rower FTP**: {estimated_ftp} W
- **VDOT (bieganie)**: {estimated_vdot}
- **Dostępność czasowa**: do {weekly_hours_available} h/tydzień

# CELE SPORTOWE
{goals_list if goals_list else "Brak zdefiniowanych celów."}

# HISTORIA ROCZNA (365 DNI)
{summary_365d if summary_365d else "Brak danych z ostatniego roku."}

# STRUKTURA WYMAGANEGO RAPORTU MARKDOWN (ODPOWIEDZ WYŁĄCZNIE W TYM FORMACIE MARKDOWN):

# Makrocykl Treningowy: Długoterminowy Plan Sezonu

## 1. Ustrukturyzowany Plan Długoterminowy
- **Główny cel A**: [Nazwa celu A i dystans]
- **Data docelowa**: {plan_end} (pozostało {total_weeks} tygodni)
- **Scenariusz**: 🔴 **Ambitny** / 🟡 **Realistyczny** / 🟢 **Bezpieczny**
- **Punkt wyjścia ({plan_start})**: CTL: {current_ctl} | VDOT: {estimated_vdot} | FTP Rower: {estimated_ftp} W

## 2. Podział na Fazy i Mezocykle

```mermaid
gantt
    title Plan Przygotowań Sezon {plan_start[:4]} / {plan_end[:4]}
    dateFormat  YYYY-MM-DD
    section Fazy Sezonu
    Faza I: Adaptacja i Baza Tlenowa :active, faza1, {plan_start}, 8w
    Faza II: Rozbudowa Ogólna :faza2, after faza1, 10w
    Faza III: Specjalizacja i Objętość :faza3, after faza2, 8w
    Faza IV: Szczyt Formy i Symulacje :faza4, after faza3, 4w
    Faza V: BPS i Tapering :faza5, after faza4, {plan_end}
```

### Faza I: Adaptacja i Budowa Bazy Tlenowej
- **Cel CTL**: {current_ctl} → {current_ctl + 20}
- **Główne priorytety**:
  - Łagodne budowanie objętości tlenowej Z2.
  - Trening siłowy i stabilizacja pod prewencję kontuzji.

### Faza II: Rozbudowa Ogólna
- **Cel CTL**: {current_ctl + 20} → {current_ctl + 40}
- **Główne priorytety**:
  - Praca w strefach Sweet Spot / Tempo Z3.
  - Rozbudowa specyfiki dyscypliny.

### Faza III: Specjalizacja i Objętość
- **Cel CTL**: {current_ctl + 40} → {current_ctl + 55}
- **Główne priorytety**:
  - Akcenty w tempie docelowym wyścigu i treningi specyficzne.

### Faza IV: Szczyt Formy i Symulacje
- **Cel CTL**: {current_ctl + 55} → {current_ctl + 65}
- **Główne priorytety**:
  - Szczytowa objętość i symulacje wyścigu.

### Faza V: BPS i Tapering
- **Cel CTL**: Tapering (TSB +10 do +15 na dzień startu)
- **Główne priorytety**:
  - Redukcja objętości o 40-50% przy zachowaniu dynamiki i intensywności.

Wygeneruj kompletny, profesjonalny raport po polsku w powyższej strukturze Markdown.
"""
