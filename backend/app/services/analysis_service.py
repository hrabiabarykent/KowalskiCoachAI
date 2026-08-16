import logging
from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.snapshot import AthleteSnapshot
from app.domain.snapshot import SnapshotBuilder
from app.domain.prompt_builders import build_athlete_assessment_prompt
from app.integrations.llm_client import GeminiClient, LLMError

logger = logging.getLogger("analysis_service")

class AnalysisService:
    def __init__(self, llm_client: GeminiClient, deep_llm_client: GeminiClient = None):
        self.llm_client = llm_client
        self.deep_llm_client = deep_llm_client or llm_client
        self.snapshot_builder = SnapshotBuilder()

    async def create_or_update_snapshot(self, db: Session, user_id: int, intervals_data: Dict[str, Any]) -> Optional[AthleteSnapshot]:
        try:
            today = date.today()
            snap_dto = self.snapshot_builder.build(user_id, intervals_data, today)
            
            snap = db.query(AthleteSnapshot).filter_by(user_id=user_id, date=today).first()
            if not snap:
                snap = AthleteSnapshot(user_id=user_id, date=today)
                db.add(snap)

            snap.all_activities_year = snap_dto.activities_year
            snap.activities_42d = snap_dto.activities_42d
            snap.weight = snap_dto.weight
            snap.ctl = snap_dto.ctl
            snap.atl = snap_dto.atl
            snap.tsb = snap_dto.tsb
            snap.resting_hr = snap_dto.resting_hr
            snap.gender = snap_dto.gender
            snap.age = snap_dto.age
            snap.estimated_ftp = snap_dto.estimated_ftp
            snap.estimated_vdot = snap_dto.estimated_vdot
            snap.stats_year = snap_dto.stats_year
            snap.power_curve_year = snap_dto.power_curve_year
            snap.pace_curve_year = snap_dto.pace_curve_year
            
            db.commit()

            logger.info(f"🚀 [Snapshot Updated] User {user_id} | CTL: {snap.ctl} | ATL: {snap.atl} | TSB: {snap.tsb} | FTP: {snap.estimated_ftp}W | VDOT: {snap.estimated_vdot}")
            return snap
            
        except Exception as e:
            logger.exception(f"❌ [Snapshot Error] Błąd podczas budowania snapshotu dla usera {user_id}: {e}")
            db.rollback()
            return None

    async def generate_athlete_assessment(self, snap: AthleteSnapshot) -> str:
        try:
            stats_y = snap.stats_year or {}
            total_y = {}
            for sport, data in stats_y.items():
                if isinstance(data, dict):
                    total_y[sport] = f"{data.get('h', 0)}h, {data.get('km', 0)}km, {data.get('tss', 0)} TSS"

            prompt = build_athlete_assessment_prompt(
                gender=snap.gender,
                age=snap.age,
                weight=snap.weight,
                estimated_ftp=snap.estimated_ftp,
                estimated_vdot=snap.estimated_vdot,
                ctl=snap.ctl,
                total_y=total_y
            )
            return await self.llm_client.generate(prompt, task_name="athlete_assessment")
        except LLMError as e:
            logger.error(f"❌ [Assessment Error] Błąd AI: {e}")
            return f"Podsumowanie analityczne chwilowo niedostępne ({str(e)})."

    async def generate_atp(self, snap: AthleteSnapshot, goals: list, weekly_hours: float = 12.0, 
                           training_availability: dict = None, plan_start: str = None, 
                           plan_end: str = None, total_weeks: int = 0) -> dict:
        try:
            from app.domain.macrocycle_generator import build_macrocycle_markdown_prompt
            from app.domain.macrocycle_parser import MacrocycleParser
            
            goals_list = "\n".join([f"- {g.priority} Cel: {g.event_name} ({g.event_type}) - {g.event_date}" for g in goals])
            
            stats_y = snap.stats_year or {}
            total_h = sum([v.get("h", 0) for v in stats_y.values() if isinstance(v, dict)])
            total_tss = sum([v.get("tss", 0) for v in stats_y.values() if isinstance(v, dict)])
            summary_str = f"Roczny czas: {total_h}h, Roczny TSS: {total_tss}"
            
            current_ctl = int(snap.ctl or 0)
            
            prompt = build_macrocycle_markdown_prompt(
                gender=snap.gender,
                age=snap.age,
                weight=snap.weight,
                ctl=snap.ctl,
                estimated_ftp=snap.estimated_ftp,
                estimated_vdot=snap.estimated_vdot,
                goals_list=goals_list,
                weekly_hours_available=weekly_hours,
                summary_365d=summary_str,
                plan_start=plan_start,
                plan_end=plan_end,
                total_weeks=total_weeks,
                current_ctl=current_ctl
            )
            
            logger.debug(f"Generowanie makrocyklu dla zawodnika CTL: {current_ctl}, Cele: {len(goals)}")
            raw_markdown = await self.deep_llm_client.generate(prompt, task_name="macrocycle_generation")
            
            parsed = MacrocycleParser.parse_markdown(raw_markdown, plan_start_str=plan_start)
            parsed["raw_markdown"] = raw_markdown

            logger.info(f"✅ [ATP Success] Wygenerowano makrocykl: {len(parsed['mesocycles'])} faz, {len(parsed['weeks'])} tygodni")
            return {"type": "structured", "data": parsed}
            
        except Exception as e:
            logger.exception(f"❌ [ATP Error] Błąd generowania ATP: {e}")
            return {"type": "error", "data": f"Błąd generowania ATP: {e}"}
