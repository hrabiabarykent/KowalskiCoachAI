import pytest
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageDTO, ChatHistoryResponse, ChatResponse
from datetime import datetime, timezone

def test_chat_message_dto_conversion():
    now = datetime.now(timezone.utc)
    msg = ChatMessage(
        id=1,
        user_id=10,
        sender="USER",
        message="Cześć trenerze!",
        timestamp=now
    )

    dto = ChatMessageDTO.model_validate(msg)
    assert dto.id == 1
    assert dto.user_id == 10
    assert dto.sender == "USER"
    assert dto.message == "Cześć trenerze!"

def test_chat_history_response_structure():
    now = datetime.now(timezone.utc)
    dtos = [
        ChatMessageDTO(id=1, user_id=10, sender="USER", message="Pytanie", timestamp=now),
        ChatMessageDTO(id=2, user_id=10, sender="COACH", message="Odpowiedź", timestamp=now)
    ]
    resp = ChatHistoryResponse(status="success", messages=dtos)
    assert resp.status == "success"
    assert len(resp.messages) == 2
    assert resp.messages[1].sender == "COACH"
