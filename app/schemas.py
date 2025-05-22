from pydantic import BaseModel
from typing import Optional

class MessageSchema(BaseModel):
    id: str
    content: str
    chat_id: str
    created_at: str
    is_system: Optional[bool]
    is_markdown: Optional[bool]

class ChatSchema(BaseModel):
    id: str
    title: Optional[str]
    status: str
    user_id: str
    created_at: str
    updated_at: str

class ChatWithLatestMessageSchema(BaseModel):
    chat: ChatSchema
    latest_message: Optional[MessageSchema]
