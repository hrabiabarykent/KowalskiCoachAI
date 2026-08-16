import asyncio
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.training_plan import TrainingPlan, PlanStatus
from app.models.planned_workout import PlannedWorkout, WorkoutStatus
from app.models.goal import TrainingGoal as Goal
from app.integrations.intervals_client import IntervalsClient
from pydantic import BaseModel

from app.domain.metrics import calculate_compliance
from app.domain.wellness_evaluator import check_tactical_overrides, WellnessEvaluator
from app.domain.prompt_builders import build_daily_autonomous_revision_prompt, build_sota_markdown_prompt_context
from app.domain.workout_compiler import build_event_payload
from app.services.sota_service import SotaService
from app.integrations.llm_client import GeminiClient

from app.models.revision_log import RevisionLog

class RevisionDecision(BaseModel):
    compliance_score: int
    wellness_assessment: str
    decision: str
    modified_workout_description: str

class DailyRevisionService:
    def __init__(self, db: Session):
        self.db = db

    async def execute_daily_revision_for_user(self, user_id: int):
        """Uruchamia proces audytu i ewentualnego replanowania dla jednego gracza/zawodnika"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.intervals_api_key:
            return
            
        client = IntervalsClient(api_key=user.intervals_api_key)
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 1. Pobierz Wellness (ostatnie 30 dni)
        start_date_30d = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
        wellness_data = await client.get_wellness(start_date_30d, end_date)
        
        # 2. Pobierz aktywności i plany z Intervals
        yesterday_str = yesterday.isoformat()
        today_str = today.isoformat()
        
        y_activities = await client.get_activities(yesterday_str, yesterday_str)
        y_act_detail = None
        if y_activities:
            y_act_detail = await client.get_activity_detail(str(y_activities[0].get("id")))
            
        y_events = await client.get_events(yesterday_str, yesterday_str)
        t_events = await client.get_events(today_str, today_str)
        
        # 3. WARSTWA 1: Obliczenia w Pythonie (Pre-computed Facts)
        compliance_fact = calculate_compliance(y_events, y_act_detail or y_activities)
        latest_w, hrv_drop, overrides, forced_decision = check_tactical_overrides(
            wellness_data, today_str=today_str, compliance=compliance_fact
        )

        # 4. KONTEKST SOTA ZAWODNIKA
        from app.models.snapshot import AthleteSnapshot
        latest_snapshot = self.db.query(AthleteSnapshot).filter(AthleteSnapshot.user_id == user.id).order_by(AthleteSnapshot.date.desc()).first()
        weight = latest_snapshot.weight if latest_snapshot else 75.0
        ftp = latest_snapshot.estimated_ftp if latest_snapshot else 220.0
        
        goals_query = self.db.query(Goal).filter(Goal.user_id == user.id).all()
        goals_str = ", ".join([f"{g.discipline} {g.event_type} - {g.target_time_minutes} min" for g in goals_query]) if goals_query else "brak celów"
        user_context = f"Zawodnik: {user.username}, Waga: {weight}kg, FTP: {ftp}W. Cele: {goals_str}."

        if latest_snapshot and latest_snapshot.stats_year:
            sota_ctx = build_sota_markdown_prompt_context(latest_snapshot.stats_year)
            user_context += f"\n\n{sota_ctx}"

        # 5. ZBUDOWANIE PROMPTU W MARKDOWN
        prompt = build_daily_autonomous_revision_prompt(
            wellness_data=wellness_data or [],
            yesterday_planned_events=y_events or [],
            yesterday_executed_activities=y_act_detail or y_activities or [],
            today_planned_events=t_events or [],
            user_context=user_context,
            today_str=today_str,
            yesterday_str=yesterday_str,
            compliance_fact=compliance_fact,
            guardrails_overrides=overrides,
            forced_decision=forced_decision
        )
        
        llm = GeminiClient()
        response: RevisionDecision = await llm.generate_structured(prompt, RevisionDecision)
        
        if not response:
             print(f"[{user.username}] Błąd modelu LLM: Brak odpowiedzi.")
             return

        # Jeśli backend narzucił CANCEL, wymuszamy decyzję CANCEL
        if forced_decision == "CANCEL":
            response.decision = "CANCEL"
            response.wellness_assessment += f" [NARRACJA WYMUSZONA PRZEZ GUARDRAILS: {', '.join(overrides)}]"
            response.modified_workout_description = "Całkowity odpoczynek (REST)."

        print(f"[{user.username}] Decyzja wyroczni: {response.decision}")
        print(f"[{user.username}] Ocena wczoraj: {response.compliance_score}/10")
        print(f"[{user.username}] Zdrowie: {response.wellness_assessment}")

        # 💾 TRWAŁY ZAPIS W BAZIE DANYCH POSTGRESQL/SQLITE (RevisionLog)
        rev_log = RevisionLog(
            user_id=user.id,
            compliance_score=response.compliance_score,
            wellness_assessment=response.wellness_assessment,
            decision=response.decision,
            modified_workout_description=response.modified_workout_description,
            forced_decision=forced_decision,
            guardrails_overrides=overrides
        )
        self.db.add(rev_log)
        self.db.commit()

        # 6. WARSTWA 2: PUSH ZMIENIONEGO TRENINGU DO KALENDARZA INTERVALS.ICU (DYNAMIECZNY DSL)
        if response.decision in ["MODIFY", "CANCEL"] and t_events:
            event_type = t_events[0].get("type", "Run")
            dynamic_dsl = response.modified_workout_description if response.decision == "MODIFY" else "REST"
            if not dynamic_dsl.startswith("-") and response.decision == "MODIFY":
                dynamic_dsl = f"- {dynamic_dsl}"

            event_payload = build_event_payload(
                date_iso=today_str,
                workout_name=f"Replan: {response.decision}",
                workout_type=event_type,
                planned_tss=0.0 if response.decision == "CANCEL" else 30.0,
                moving_min=0.0 if response.decision == "CANCEL" else 30.0,
                dsl_text=dynamic_dsl,
                tag="[Kowalski]"
            )
            await client.clean_and_push_events([event_payload], tag="[Kowalski]")
            print(f"[{user.username}] Pomyślnie wysłano zaktualizowany trening ({dynamic_dsl}) do kalendarza Intervals.icu!")

    async def debug_daily_revision_for_user(self, user_id: int):
        """Zwraca co dokładnie widzi The Oracle (Prompt) i co odpowiada (JSON). Nie mutuje bazy."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.intervals_api_key:
            return {"error": "User or API Key not found"}
            
        client = IntervalsClient(api_key=user.intervals_api_key)
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        start_date_30d = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
        wellness_data = await client.get_wellness(start_date_30d, end_date)
        
        y_activities = await client.get_activities(yesterday.isoformat(), yesterday.isoformat())
        y_act_detail = None
        if y_activities:
            y_act_detail = await client.get_activity_detail(str(y_activities[0].get("id")))
            
        y_events = await client.get_events(yesterday.isoformat(), yesterday.isoformat())
        t_events = await client.get_events(today.isoformat(), today.isoformat())
        
        compliance_fact = calculate_compliance(y_events, y_act_detail or y_activities)
        latest_w, hrv_drop, overrides, forced_decision = check_tactical_overrides(
            wellness_data, today_str=today.isoformat(), compliance=compliance_fact
        )

        goals_query = self.db.query(Goal).filter(Goal.user_id == user.id).all()
        goals_str = ", ".join([f"{g.discipline} {g.event_type}" for g in goals_query]) if goals_query else "brak celów"
        
        from app.models.snapshot import AthleteSnapshot
        latest_snapshot = self.db.query(AthleteSnapshot).filter(AthleteSnapshot.user_id == user.id).order_by(AthleteSnapshot.date.desc()).first()
        weight = latest_snapshot.weight if latest_snapshot else "Nieznana"
        ftp = latest_snapshot.estimated_ftp if latest_snapshot else "Nieznane"
        
        user_context = f"Zawodnik: {user.username}, Waga: {weight}kg, FTP: {ftp}W. Cele: {goals_str}."
        if latest_snapshot and latest_snapshot.stats_year:
            user_context += f"\n\n{build_sota_markdown_prompt_context(latest_snapshot.stats_year)}"

        prompt = build_daily_autonomous_revision_prompt(
            wellness_data=wellness_data or [],
            yesterday_planned_events=y_events or [],
            yesterday_executed_activities=y_act_detail or y_activities or [],
            today_planned_events=t_events or [],
            user_context=user_context,
            today_str=today.isoformat(),
            yesterday_str=yesterday.isoformat(),
            compliance_fact=compliance_fact,
            guardrails_overrides=overrides,
            forced_decision=forced_decision
        )
        
        llm = GeminiClient()
        response: RevisionDecision = await llm.generate_structured(prompt, RevisionDecision)
        
        return {
            "prompt_sent_to_llm": prompt,
            "llm_response_json": response.model_dump() if response else None,
            "compliance_fact": compliance_fact,
            "guardrails_overrides": overrides,
            "forced_decision": forced_decision
        }

    async def run_cron_for_all_users(self):
        """Asynchroniczny cron dla wszystkich użytkowników z limitem 5 równoległych zapytan (Semaphore)"""
        users = self.db.query(User).filter(User.intervals_api_key.isnot(None)).all()
        semaphore = asyncio.Semaphore(5)

        async def run_safe(u_id: int):
            async with semaphore:
                try:
                    await self.execute_daily_revision_for_user(u_id)
                except Exception as e:
                    print(f"Błąd rewizji dla użytkownika {u_id}: {e}")

        await asyncio.gather(*(run_safe(u.id) for u in users))

    async def approve_revision_for_plan(self, plan_id: int):
        """Aprobuje proponowane przez AI zmiany dla danego planu"""
        plan = self.db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            return False, "Plan nie istnieje"
        
        plan.status = PlanStatus.ACTIVE
        self.db.commit()
        return True, "Pomyślnie zaaprobowano zmiany w planie"

    async def reject_revision_for_plan(self, plan_id: int):
        """Odrzuca proponowane przez AI zmiany"""
        plan = self.db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            return False, "Plan nie istnieje"
        
        self.db.commit()
        return True, "Odrzucono zmiany w planie"



