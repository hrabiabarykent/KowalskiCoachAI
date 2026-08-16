from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    user_id: int
    force_refresh: bool = False
