from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class DayAllocation(BaseModel):
    day_of_week: int # 0 = Poniedziałek, 6 = Niedziela
    date: date
    available_hours: float
    is_key_accent: bool
    intensity_category: str # REST, RECOVERY, AEROBIC_BASE, TEMPO, THRESHOLD, VO2MAX
    workout_type: str # Bike, Run, Swim, Strength, Rest
    suggested_name: str
    target_tss: float
    target_duration_minutes: int
    focus_notes: str

class MicrocycleTemplate(BaseModel):
    phase: str
    target_weekly_tss: float
    days: List[DayAllocation]

class MicrocycleAllocator:
    """
    Deterministyczny alokator mikrocyklu oparty na periodyzacji Joe Friela:
    1. Respektuje dni dostępności zawodnika (0h = Dzień wolny / Rest).
    2. Przestrzega reguły Hard / Easy (akcenty oddzielone dniami o niskiej intensywności).
    3. Dopasowuje akcenty do fazy mezocyklu (Base -> Tlen/Siła, Build -> Próg/VO2max, Peak -> Specyfika, Taper -> Redukcja).
    4. Uwzględnia dyscyplinę wiodącą z Celu (Bike, Run, Triathlon).
    """

    DEFAULT_AVAILABILITY = {
        0: 0.0,  # Poniedziałek: Wolne / Regeneracja
        1: 1.5,  # Wtorek: Akcent 1
        2: 1.0,  # Środa: Baza Z2 / Tlen
        3: 1.5,  # Czwartek: Akcent 2
        4: 0.0,  # Piątek: Wolne / Aktywna regeneracja
        5: 3.0,  # Sobota: Długi trening / Objętość
        6: 2.0   # Niedziela: Baza tlenowa / Trening uzupełniający
    }

    @classmethod
    def allocate_week(
        cls,
        start_date: date,
        phase: str = "Base",
        target_tss: float = 400.0,
        primary_discipline: str = "Bike",
        goal_priority: str = "A",
        availability_map: Optional[Dict[int, float]] = None
    ) -> List[DayAllocation]:
        avail = availability_map or cls.DEFAULT_AVAILABILITY
        phase_normalized = phase.lower()
        days_allocation: List[DayAllocation] = []

        # 1. Określenie profilu akcentów w zależności od fazy
        if "build" in phase_normalized:
            accent_1_type = "THRESHOLD"
            accent_1_name = f"{primary_discipline} - Sweet Spot / Próg Beztlenowy"
            accent_2_type = "VO2MAX" if goal_priority == "A" else "THRESHOLD"
            accent_2_name = f"{primary_discipline} - Interwały VO2Max"
            long_day_type = "TEMPO"
            long_day_name = f"{primary_discipline} - Długa Jazda Objętościowa Z2/Z3"
        elif "peak" in phase_normalized:
            accent_1_type = "VO2MAX"
            accent_1_name = f"{primary_discipline} - Symulacja Tempa Startowego"
            accent_2_type = "THRESHOLD"
            accent_2_name = f"{primary_discipline} - Pobudzenie Przedstartowe"
            long_day_type = "AEROBIC_BASE"
            long_day_name = f"{primary_discipline} - Umiarkowana Objętość"
        elif "taper" in phase_normalized or "recovery" in phase_normalized:
            accent_1_type = "TEMPO"
            accent_1_name = f"{primary_discipline} - Krótkie Przebudzenie Z3"
            accent_2_type = "RECOVERY"
            accent_2_name = "Aktywna Regeneracja Z1"
            long_day_type = "AEROBIC_BASE"
            long_day_name = f"{primary_discipline} - Spokojne Rozkręcenie Z2"
            target_tss = target_tss * 0.6  # Redukcja TSS w taperze o 40%
        else:  # Base
            accent_1_type = "TEMPO"
            accent_1_name = f"{primary_discipline} - Praca nad Kadencją i Tempem Z3"
            accent_2_type = "AEROBIC_BASE"
            accent_2_name = f"{primary_discipline} - Baza Tlenowa Z2 + Przebieżki"
            long_day_type = "AEROBIC_BASE"
            long_day_name = f"{primary_discipline} - Długie Wybieganie / Rozjazd Z2"

        # 2. Wyznaczenie dostępnych slotów i sumy godzin
        total_avail_hours = sum(avail.get(i, 0.0) for i in range(7))
        if total_avail_hours <= 0:
            total_avail_hours = 8.0  # Fallback

        # Szacunkowy bazowy TSS na godzinę w zależności od intensywności:
        # Z1: ~35 TSS/h, Z2: ~50-55 TSS/h, Z3: ~65-70 TSS/h, Z4/Z5: ~80-90 TSS/h
        # 3. Przypisanie dni (0=Poniedziałek do 6=Niedziela)
        last_was_accent = False

        for day_idx in range(7):
            current_date = start_date + timedelta(days=day_idx)
            hours = avail.get(day_idx, 0.0)

            if hours <= 0.0:
                # Dzień wolny / Rest
                days_allocation.append(DayAllocation(
                    day_of_week=day_idx,
                    date=current_date,
                    available_hours=0.0,
                    is_key_accent=False,
                    intensity_category="REST",
                    workout_type="Rest",
                    suggested_name="Dzień Wolny / Pełna Regeneracja",
                    target_tss=0.0,
                    target_duration_minutes=0,
                    focus_notes="Dzień bez treningu fizycznego. Regeneracja układu nerwowego."
                ))
                last_was_accent = False
                continue

            # Przypisanie ról dni w oparciu o pozycję w tygodniu i regułę Hard/Easy
            if day_idx == 1 and not last_was_accent:  # Wtorek - Akcent 1
                is_key = True
                cat = accent_1_type
                name = accent_1_name
                tss_rate = 75.0
                notes = "Główny akcent tygodnia. Wymagana wysoka koncentracja i wypoczęcie."
                last_was_accent = True
            elif day_idx == 3 and not last_was_accent:  # Czwartek - Akcent 2
                is_key = True
                cat = accent_2_type
                name = accent_2_name
                tss_rate = 70.0
                notes = "Drugi akcent jakościowy. Utrzymanie zadanych stref mocy/tętna."
                last_was_accent = True
            elif day_idx == 5:  # Sobota - Długi trening objętościowy
                is_key = ("build" in phase_normalized or "base" in phase_normalized)
                cat = long_day_type
                name = long_day_name
                tss_rate = 55.0
                notes = "Budowa wytrzymałości tlenowej i pojemności glikogenowej."
                last_was_accent = False
            elif day_idx == 6:  # Niedziela
                is_key = False
                cat = "AEROBIC_BASE"
                name = f"{primary_discipline} - Regeneracyjny Rozjazd / Bieg Z2"
                tss_rate = 45.0
                notes = "Lekki trening tlenowy kończący mikrocykl."
                last_was_accent = False
            else:  # Środa, Piątek lub inne luźniejsze dni
                is_key = False
                cat = "RECOVERY" if last_was_accent else "AEROBIC_BASE"
                name = f"{primary_discipline} - Aktywna Regeneracja / Baza Z1-Z2"
                tss_rate = 40.0
                notes = "Utrzymanie adaptacji naczyniowych bez generowania długu zmęczeniowego."
                last_was_accent = False

            # Obliczenie czasu i TSS
            duration_min = int(round(hours * 60))
            calculated_tss = round((hours * tss_rate), 1)

            days_allocation.append(DayAllocation(
                day_of_week=day_idx,
                date=current_date,
                available_hours=hours,
                is_key_accent=is_key,
                intensity_category=cat,
                workout_type=primary_discipline,
                suggested_name=name,
                target_tss=calculated_tss,
                target_duration_minutes=duration_min,
                focus_notes=notes
            ))

        # Skalowanie TSS proporcjonalnie do zadanego target_tss (jeśli suma odbiega)
        current_sum_tss = sum(d.target_tss for d in days_allocation)
        if current_sum_tss > 0 and target_tss > 0:
            scale = target_tss / current_sum_tss
            for d in days_allocation:
                if d.target_tss > 0:
                    d.target_tss = round(d.target_tss * scale, 1)

        return days_allocation
