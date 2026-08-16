import pytest
from app.domain.macrocycle_parser import MacrocycleParser

def test_parse_macrocycle_markdown():
    sample_md = """
# Makrocykl Treningowy: Ironman 70.3 Kraków 2027

## 1. Ustrukturyzowany Plan Długoterminowy
- **Główny cel A**: Ironman 70.3 Kraków
- **Scenariusz**: 🔴 **Ambitny**

```mermaid
gantt
    title Plan Przygotowań Ironman 70.3 Kraków 2027
    dateFormat YYYY-MM-DD
    section Fazy
    Faza I: Adaptacja :active, faza1, 2026-08-05, 2026-10-31
```

### Faza I: Adaptacja i Budowa Bazy Tlenowej (Sierpień 2026 – Październik 2026)
- **Cel CTL**: 10 → 35
- **Główne priorytety**: Baza Z2 i siła.

### Faza II: Rozbudowa Ogólna (Listopad 2026 – Luty 2027)
- **Cel CTL**: 35 → 55
- **Główne priorytety**: Sweet Spot i pływanie.
"""

    parsed = MacrocycleParser.parse_markdown(sample_md, plan_start_str="2026-08-06")

    assert len(parsed["mesocycles"]) == 2
    assert parsed["mesocycles"][0]["name"] == "Faza I: Adaptacja i Budowa Bazy Tlenowej (Sierpień 2026 – Październik 2026)"
    assert parsed["mesocycles"][0]["ctl_start"] == 10
    assert parsed["mesocycles"][0]["ctl_end"] == 35

    assert parsed["mesocycles"][1]["ctl_start"] == 35
    assert parsed["mesocycles"][1]["ctl_end"] == 55

    assert len(parsed["weeks"]) > 0
    assert "gantt" in parsed["mermaid_code"]
