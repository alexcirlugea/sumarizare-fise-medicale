from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    message: str
    uid: str
    scope: str = "global"  # "global" | "patient"
    patient_id: Optional[int] = None
    selected_ids: Optional[List[int]] = None

class RecordTranslateRequest(BaseModel):
    id: int
    original_text: str
    summary: str