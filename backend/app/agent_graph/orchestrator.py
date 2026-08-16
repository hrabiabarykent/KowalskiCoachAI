import logging
from typing import Dict, Any, List, Optional
from app.agent_graph.schemas import PhysiologyVerdict, WorkoutProposal, CritiqueResult
from app.agent_graph.agents import PhysiologyAnalystAgent, WorkoutPlannerAgent, CriticGuardrailAgent

logger = logging.getLogger("agent_orchestrator")

class MultiAgentOrchestrator:
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.analyst = PhysiologyAnalystAgent()
        self.planner = WorkoutPlannerAgent()
        self.critic = CriticGuardrailAgent()

    async def run(
        self,
        wellness_data: list,
        user_context: str,
        compliance_fact: dict,
        today_planned: list,
        microcycle_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Główna pętla wieloagentowa DAG:
        1. PhysiologyAnalyst -> Wylicza twarde granice
        2. WorkoutPlanner -> Tworzy propozycję z uwzględnieniem mikrocyklu
        3. CriticGuardrail -> Audytuje. Jeśli REJECTED -> pętla do Planner z uwagami (max 3 próby).
        4. Jeśli pętla przekroczona -> Safe Fallback.
        """
        # Krok 1: Analiza fizjologiczna
        verdict: PhysiologyVerdict = await self.analyst.analyze(wellness_data, user_context, compliance_fact)
        logger.info(f"🤖 [Agent 1: Analyst] Status: {verdict.status} | Max TSS: {verdict.max_tss} | Strefy: {verdict.allowed_zones}")

        # Jeśli sam analityk zarządził odpoczynek
        if verdict.recovery_required:
            fallback_proposal = WorkoutProposal(
                workout_name="Odpoczynek Regeneracyjny",
                workout_type="Rest",
                planned_duration_min=0,
                planned_tss=0,
                dsl_text="REST",
                reasoning=f"Wymuszony odpoczynek przez analityka fizjologii: {verdict.notes}"
            )
            return {
                "verdict": verdict.model_dump(),
                "proposal": fallback_proposal.model_dump(),
                "iterations": 1,
                "status": "APPROVED_RECOVERY"
            }

        # Krok 2 & 3: Pętla Planner <-> Critic
        required_fixes: List[str] = []
        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1
            logger.info(f"🔄 [Orchestrator] Próba {iterations}/{self.max_iterations}...")

            proposal: WorkoutProposal = await self.planner.plan(verdict, today_planned, required_fixes, microcycle_context=microcycle_context)
            critique: CritiqueResult = await self.critic.audit(verdict, proposal)

            if critique.decision == "APPROVED":
                logger.info(f"✅ [Agent 3: Critic] ZATWIERDZONO: {proposal.workout_name} ({proposal.dsl_text})")
                return {
                    "verdict": verdict.model_dump(),
                    "proposal": proposal.model_dump(),
                    "iterations": iterations,
                    "status": "APPROVED"
                }

            logger.warning(f"❌ [Agent 3: Critic] ODRZUCONO! Naruszenia: {critique.violations}")
            required_fixes = critique.required_fixes or critique.violations

        # Fallback po przekroczeniu limitu pętli (Hard Safety Fallback)
        logger.error(f"🚨 [Orchestrator] Przekroczono limit {self.max_iterations} prób! Uruchamiam bezpieczny Fallback.")
        safe_fallback = WorkoutProposal(
            workout_name="Bezpieczny Aktywny Odpoczynek",
            workout_type="Run",
            planned_duration_min=30,
            planned_tss=15,
            dsl_text="- 30m Z1 Mobility",
            reasoning="Bezpieczny fallback aktywnej regeneracji po niepowodzeniu pętli agentów."
        )

        return {
            "verdict": verdict.model_dump(),
            "proposal": safe_fallback.model_dump(),
            "iterations": iterations,
            "status": "SAFE_FALLBACK"
        }
