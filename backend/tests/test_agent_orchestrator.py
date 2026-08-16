import pytest
from app.agent_graph.schemas import PhysiologyVerdict, WorkoutProposal, CritiqueResult
from app.agent_graph.orchestrator import MultiAgentOrchestrator

def test_agent_graph_schemas():
    verdict = PhysiologyVerdict(
        status="YELLOW",
        max_tss=40.0,
        allowed_zones=["Z1", "Z2"],
        recovery_required=False,
        notes="Lekki spadek TSB"
    )

    assert verdict.status == "YELLOW"
    assert verdict.max_tss == 40.0
    assert "Z2" in verdict.allowed_zones

    proposal = WorkoutProposal(
        workout_name="Tlenowy Bieg Z2",
        workout_type="Run",
        planned_duration_min=45,
        planned_tss=30,
        dsl_text="- 45m Z2",
        reasoning="Budowa bazy w granicach Z2"
    )

    assert proposal.planned_tss <= verdict.max_tss

    critique = CritiqueResult(
        decision="APPROVED",
        violations=[],
        required_fixes=[]
    )

    assert critique.decision == "APPROVED"
