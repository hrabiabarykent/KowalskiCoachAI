from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ChatMessageInput(BaseModel):
    user_id: int
    message: str

class ChatMessageDTO(BaseModel):
    id: int
    user_id: int
    sender: str # "USER" lub "COACH"
    message: str
    timestamp: datetime
    suggested_action: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    status: str
    user_message: ChatMessageDTO
    coach_response: ChatMessageDTO

class ChatHistoryResponse(BaseModel):
    status: str
    messages: List[ChatMessageDTO]
