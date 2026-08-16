from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatMessageInput, ChatResponse, ChatHistoryResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/send", response_model=ChatResponse)
async def send_chat_message(data: ChatMessageInput, db: Session = Depends(get_db)):
    """Wysyła wiadomość użytkownika do Trenera Kowalskiego i zwraca odpowiedź AI."""
    service = ChatService(db)
    try:
        response = await service.send_user_message(data.user_id, data.message)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd rozmowy z trenerem: {str(e)}")

@router.post("/stream")
async def send_chat_message_stream(data: ChatMessageInput, db: Session = Depends(get_db)):
    """Strumieniuje odpowiedź Trenera Kowalskiego w czasie rzeczywistym (Server-Sent Events)."""
    service = ChatService(db)
    return StreamingResponse(
        service.send_user_message_stream(data.user_id, data.message),
        media_type="text/plain"
    )

@router.get("/history/{user_id}", response_model=ChatHistoryResponse)
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    """Pobiera pełną historię rozmów z Trenerem Kowalskim dla podanego użytkownika."""
    service = ChatService(db)
    return service.get_chat_history(user_id)

