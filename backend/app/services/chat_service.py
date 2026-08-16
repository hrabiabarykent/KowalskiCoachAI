from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat_message import ChatMessage
from app.models.snapshot import AthleteSnapshot
from app.models.goal import TrainingGoal
from app.schemas.chat import ChatMessageDTO, ChatResponse, ChatHistoryResponse
from app.domain.prompt_builders import build_sota_markdown_prompt_context
from app.integrations.llm_client import GeminiClient

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_client = GeminiClient('gemini-3.6-flash')

    async def send_user_message(self, user_id: int, message_text: str) -> ChatResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Nie odnaleziono użytkownika.")

        # 1. Zapis wiadomości użytkownika w bazie danych
        user_msg = ChatMessage(
            user_id=user_id,
            sender="USER",
            message=message_text,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        # 2. Pobranie historii rozmowy (ostatnie 10 wiadomości)
        history = self.db.query(ChatMessage)\
            .filter(ChatMessage.user_id == user_id)\
            .order_by(ChatMessage.timestamp.desc())\
            .limit(10).all()
        history.reverse()

        history_str = "\n".join([f"{m.sender}: {m.message}" for m in history])

        # 3. Zbudowanie kontekstu paszportu SOTA i celów zawodnika
        snapshot = self.db.query(AthleteSnapshot)\
            .filter(AthleteSnapshot.user_id == user_id)\
            .order_by(AthleteSnapshot.date.desc()).first()

        goals = self.db.query(TrainingGoal).filter(TrainingGoal.user_id == user_id).all()
        goals_str = ", ".join([f"{g.discipline} {g.event_type}" for g in goals]) if goals else "Brak"
        sota_ctx = build_sota_markdown_prompt_context(snapshot.stats_year) if snapshot and snapshot.stats_year else ""

        ctl = snapshot.ctl if snapshot else "–"
        vdot = snapshot.estimated_vdot if snapshot else "–"
        ftp = snapshot.estimated_ftp if snapshot else "–"

        # 4. Konstrukcja Promptu dla Trenera Kowalskiego
        prompt = f"""
Jesteś Trenerem Kowalskim – elitarnym, empatycznym i wysoce doświadczonym trenerem sportów wytrzymałościowych (kolarstwo, bieganie, triathlon).
Twoim celem jest prowadzenie dialogu z zawodnikiem, odpowiadanie na jego wątpliwości treningowe, regeneracyjne i sprzętowe, z zachowaniem chłodnej logiki fizjologicznej oraz ciepłego wsparcia mentorskiego.

PROFIL ZAWODNIKA:
- Użytkownik: {user.username}
- Zdefiniowane cele: {goals_str}
- Aktualna forma: CTL: {ctl} | eVDOT: {vdot} | eFTP: {ftp} W

{sota_ctx}

HISTORIA KONWERSACJI:
{history_str}

AKTUALNA WIADOMOŚĆ ZAWODNIKA:
"{message_text}"

ZASADY ODPOWIEDZI:
1. Odpowiadaj zwięźle, konkretnie i po polsku (max 3-4 akapity).
2. Jeśli zawodnik pyta o modyfikację treningu, wyjaśnij fizjologiczne konsekwencje (np. adaptacja, zmęczenie).
3. Podtrzymuj motywację, ale nie bój się nakazać odpoczynku, jeśli kontekst wskazuje na przeciążenie.
"""

        # 5. Wywołanie Gemini
        coach_text = await self.llm_client.generate(prompt, task_name="coach_chat")

        # 6. Zapis odpowiedzi trenera w bazie danych
        coach_msg = ChatMessage(
            user_id=user_id,
            sender="COACH",
            message=coach_text,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(coach_msg)
        self.db.commit()
        self.db.refresh(coach_msg)

        return ChatResponse(
            status="success",
            user_message=ChatMessageDTO.model_validate(user_msg),
            coach_response=ChatMessageDTO.model_validate(coach_msg)
        )

    async def send_user_message_stream(self, user_id: int, message_text: str):
        """Strumieniowy zapis i wysyłanie wiadomości do Gemini."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            yield "Błąd: Brak użytkownika."
            return

        user_msg = ChatMessage(
            user_id=user_id,
            sender="USER",
            message=message_text,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(user_msg)
        self.db.commit()

        history = self.db.query(ChatMessage)\
            .filter(ChatMessage.user_id == user_id)\
            .order_by(ChatMessage.timestamp.desc())\
            .limit(10).all()
        history.reverse()
        history_str = "\n".join([f"{m.sender}: {m.message}" for m in history])

        snapshot = self.db.query(AthleteSnapshot)\
            .filter(AthleteSnapshot.user_id == user_id)\
            .order_by(AthleteSnapshot.date.desc()).first()

        goals = self.db.query(TrainingGoal).filter(TrainingGoal.user_id == user_id).all()
        goals_str = ", ".join([f"{g.discipline} {g.event_type}" for g in goals]) if goals else "Brak"
        sota_ctx = build_sota_markdown_prompt_context(snapshot.stats_year) if snapshot and snapshot.stats_year else ""

        ctl = snapshot.ctl if snapshot else "–"
        vdot = snapshot.estimated_vdot if snapshot else "–"
        ftp = snapshot.estimated_ftp if snapshot else "–"

        prompt = f"""
Jesteś Trenerem Kowalskim – elitarnym, empatycznym i wysoce doświadczonym trenerem sportów wytrzymałościowych.
PROFIL ZAWODNIKA: {user.username} | Cele: {goals_str} | CTL: {ctl} | VDOT: {vdot} | FTP: {ftp}W

{sota_ctx}

HISTORIA:
{history_str}

Odpowiedz zwięźle, rzetelnie i trenersko na wiadomość: "{message_text}".
"""
        full_response = ""
        async for chunk in self.llm_client.generate_stream(prompt, task_name="coach_chat_stream"):
            full_response += chunk
            yield chunk

        # Zapis końcowej wiadomości w bazie
        coach_msg = ChatMessage(
            user_id=user_id,
            sender="COACH",
            message=full_response,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(coach_msg)
        self.db.commit()

    def get_chat_history(self, user_id: int, limit: int = 50) -> ChatHistoryResponse:
        messages = self.db.query(ChatMessage)\
            .filter(ChatMessage.user_id == user_id)\
            .order_by(ChatMessage.timestamp.asc())\
            .limit(limit).all()

        dtos = [ChatMessageDTO.model_validate(m) for m in messages]
        return ChatHistoryResponse(status="success", messages=dtos)
