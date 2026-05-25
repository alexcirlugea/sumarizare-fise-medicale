from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    message: str
    selected_ids: List[int] = []

class RecordTranslateRequest(BaseModel):
    id: int
    original_text: str
    summary: str