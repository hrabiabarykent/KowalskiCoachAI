import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.agent_graph.schemas import PhysiologyVerdict, WorkoutProposal, CritiqueResult

logger = logging.getLogger("agent_graph")

class PhysiologyAnalystAgent:
    """Agent 1: Analityk Fizjologii. Wylicza twarde ograniczenia (Temperature: 0.1)."""
    def __init__(self, model_name: str = 'gemini-3.6-flash'):
        self.model_name = model_name
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_testing"
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception:
            self.client = None

    async def analyze(self, wellness_data: list, user_context: str, compliance_fact: dict) -> PhysiologyVerdict:
        prompt = f"""
Jesteś chłodnym, ultra-konserwatywnym Analitykiem Fizjologii Sportu.
Twoim celem jest wyliczenie TWARDYCH GRANIC FIZJOLOGICZNYCH na dzisiaj.

KONTEKST ZAWODNIKA:
{user_context}

DANE WELLNESS & COMPLIANCE:
Compliance: {compliance_fact}
Wellness (ostatnie dni): {json.dumps(wellness_data, ensure_ascii=False)}

ZASADY:
- Jeśli HRV spadło poniżej progu lub RHR wzrosło o >= 5 bpm -> RED, max_tss = 0, allowed_zones = ['REST'], recovery_required = true.
- Jeśli TSB jest bardzo niskie (<-20) -> YELLOW, max_tss = 30, allowed_zones = ['Z1', 'Z2'], recovery_required = false.
- Jeśli stan jest dobry -> GREEN, max_tss = 100, allowed_zones = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5'], recovery_required = false.

Zwróć wyliczenie w formacie JSON zgodnym z PhysiologyVerdict.
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PhysiologyVerdict,
            temperature=0.1
        )
        res = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            ),
            timeout=60.0
        )
        return PhysiologyVerdict.model_validate_json(res.text)


class WorkoutPlannerAgent:
    """Agent 2: Architekt Treningowy. Tworzy propozycję treningu w ramach granic (Temperature: 0.5)."""
    def __init__(self, model_name: str = 'gemini-3.6-flash'):
        self.model_name = model_name
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_testing"
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception:
            self.client = None

    async def plan(
        self,
        verdict: PhysiologyVerdict,
        today_planned: list,
        required_fixes: List[str] = None,
        microcycle_context: Optional[str] = None
    ) -> WorkoutProposal:
        fixes_str = "\n".join([f"- {f}" for f in required_fixes]) if required_fixes else "Brak"
        micro_str = f"\nKONTEKST MIKROCYKLU I CELU:\n{microcycle_context}\n" if microcycle_context else ""

        prompt = f"""
Jesteś Kreatywnym Architektem Treningowym.
Twoim zadaniem jest zaplanowanie sesji treningowej ŚCIŚLE W RAMACH GRANIC wyznaczonych przez Analityka Fizjologii.{micro_str}

TWARDE GRANICE FIZJOLOGICZNE:
- Status: {verdict.status}
- Max TSS: {verdict.max_tss}
- Dopuszczalne strefy: {verdict.allowed_zones}
- Wymagany odpoczynek: {verdict.recovery_required}

ODRZUCONE POPRZEDNIE PROPOZYCJE (POPRAWKI OD KRYTYKA):
{fixes_str}

ZADANIE:
Zaplanuj trening. Twój kod `dsl_text` MUSI opierać się WYŁĄCZNIE na dopuszczalnych strefach {verdict.allowed_zones} i nie przekraczać {verdict.max_tss} TSS.
Jeśli recovery_required == true, dsl_text MUSI wynosić "REST".

Zwróć odpowiedź zgodną z WorkoutProposal.
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WorkoutProposal,
            temperature=0.5
        )
        res = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            ),
            timeout=60.0
        )
        return WorkoutProposal.model_validate_json(res.text)


class CriticGuardrailAgent:
    """Agent 3: Sędzia Bezpieczeństwa / Krytyk. Audytuje propozycję bez kontekstu kreatywnego (Temperature: 0.0)."""
    def __init__(self, model_name: str = 'gemini-3.6-flash'):
        self.model_name = model_name
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_testing"
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception:
            self.client = None

    async def audit(self, verdict: PhysiologyVerdict, proposal: WorkoutProposal) -> CritiqueResult:
        prompt = f"""
Jesteś Niezależnym, Bezwzględnym Sędzią Bezpieczeństwa (Critic). Zero kontekstu kreatywnego.
Twoim jedynym zadaniem jest weryfikacja, czy WorkoutProposal nie łamie TWARDYCH GRANIC z PhysiologyVerdict.

TWARDE GRANICE FIZJOLOGICZNE:
- Max TSS: {verdict.max_tss}
- Dopuszczalne strefy: {verdict.allowed_zones}
- Recovery Required: {verdict.recovery_required}

PROPOZYCJA TRENINGU DO AUDYTU:
- Planned TSS: {proposal.planned_tss}
- DSL Text: {proposal.dsl_text}

ZASADY SĘDZIOWSKIE:
1. Jeśli proposal.planned_tss > verdict.max_tss -> REJECTED.
2. Jeśli w dsl_text użyto strefy spoza allowed_zones -> REJECTED.
3. Jeśli verdict.recovery_required == true a proposal.dsl_text != "REST" -> REJECTED.
4. W przeciwnym razie -> APPROVED.

Zwróć odpowiedź zgodną z CritiqueResult.
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CritiqueResult,
            temperature=0.0
        )
        res = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            ),
            timeout=60.0
        )
        return CritiqueResult.model_validate_json(res.text)
