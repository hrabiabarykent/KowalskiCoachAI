import pytest
from unittest.mock import AsyncMock, patch

from app.agent_graph.schemas import PhysiologyVerdict, WorkoutProposal, CritiqueResult
from app.agent_graph.agents import CriticGuardrailAgent
from app.agent_graph.orchestrator import MultiAgentOrchestrator

@pytest.mark.asyncio
async def test_critic_rejects_exceeding_tss():
    """Krytyk odrzuca trening z planned_tss większym niż max_tss analityka fizjologii."""
    critic = CriticGuardrailAgent()
    verdict = PhysiologyVerdict(
        status="YELLOW",
        max_tss=35.0,
        allowed_zones=["Z1", "Z2"],
        recovery_required=False,
        notes="Lekkie zmęczenie po poprzednim akcencie"
    )
    proposal = WorkoutProposal(
        workout_name="Ciężkie 5x5m VO2Max",
        workout_type="Bike",
        planned_duration_min=75,
        planned_tss=85.0,
        dsl_text="5x\n  - 5m Z5 115%\n  - 5m Z1 50%",
        reasoning="Za mocny trening na dzisiejszy stan"
    )

    # Test bezpośredniej logiki krytyka lub zmockowanego wywołania
    with patch.object(critic.client.models, "generate_content") as mock_gen:
        mock_gen.return_value.text = CritiqueResult(
            decision="REJECTED",
            violations=["planned_tss 85.0 przekracza limit max_tss 35.0", "Użyto strefy Z5 zamiast Z1-Z2"],
            required_fixes=["Zredukuj czas do 45min", "Użyj wyłącznie strefy Z2"]
        ).model_dump_json()

        res = await critic.audit(verdict, proposal)
        assert res.decision == "REJECTED"
        assert len(res.violations) >= 1

@pytest.mark.asyncio
async def test_critic_approves_safe_workout():
    """Krytyk zatwierdza poprawną jednostkę w wyznaczonych granicach."""
    critic = CriticGuardrailAgent()
    verdict = PhysiologyVerdict(
        status="GREEN",
        max_tss=90.0,
        allowed_zones=["Z1", "Z2", "Z3", "Z4"],
        recovery_required=False,
        notes="Pełna gotowość do treningu progowego"
    )
    proposal = WorkoutProposal(
        workout_name="Sweet Spot 3x10min",
        workout_type="Bike",
        planned_duration_min=60,
        planned_tss=65.0,
        dsl_text="3x\n  - 10m Z4 90%\n  - 5m Z1 55%",
        reasoning="Idealnie w budżecie 90 TSS"
    )

    with patch.object(critic.client.models, "generate_content") as mock_gen:
        mock_gen.return_value.text = CritiqueResult(
            decision="APPROVED",
            violations=[],
            required_fixes=[]
        ).model_dump_json()

        res = await critic.audit(verdict, proposal)
        assert res.decision == "APPROVED"
        assert len(res.violations) == 0

@pytest.mark.asyncio
async def test_orchestrator_recovery_short_circuit():
    """Orchestrator natychmiast zwraca odpoczynek gdy Analityk zgłasza recovery_required."""
    orchestrator = MultiAgentOrchestrator(max_iterations=3)

    verdict_recovery = PhysiologyVerdict(
        status="RED",
        max_tss=0.0,
        allowed_zones=["REST"],
        recovery_required=True,
        notes="Spadek HRV > 20% i wysokie tętno spoczynkowe"
    )

    with patch.object(orchestrator.analyst, "analyze", new_callable=AsyncMock) as mock_an:
        mock_an.return_value = verdict_recovery

        result = await orchestrator.run(
            wellness_data=[],
            user_context="Zawodnik kolarstwa",
            compliance_fact={},
            today_planned=[],
            microcycle_context="W12 Build 2"
        )

        assert result["status"] == "APPROVED_RECOVERY"
        assert result["proposal"]["dsl_text"] == "REST"
        assert result["iterations"] == 1
