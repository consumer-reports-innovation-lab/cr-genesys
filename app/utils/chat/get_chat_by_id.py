from sqlalchemy.orm import Session
from sqlalchemy import select, asc
from models import Chat, Message
from typing import Optional

def get_chat_by_id(db: Session, chat_id: str, include_messages: bool = True) -> Optional[dict]:
    chat = db.execute(select(Chat).where(Chat.id == chat_id)).scalar_one_or_none()
    if not chat:
        return None
    
    result = {"chat": chat}
    
    if include_messages:
        messages = db.execute(
            select(Message).where(Message.chat_id == chat_id).order_by(asc(Message.created_at))
        ).scalars().all()
        result["messages"] = messages
    
    return result
