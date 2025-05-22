from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from models import Chat, Message
from typing import List

def get_chats_by_user_with_latest_message(db: Session, user_id: str) -> List[dict]:
    # Get all chats for the user
    chats = db.execute(
        select(Chat).where(Chat.user_id == user_id)
    ).scalars().all()
    result = []
    for chat in chats:
        # Get the most recent message for each chat
        latest_message = (
            db.execute(
                select(Message)
                .where(Message.chat_id == chat.id)
                .order_by(desc(Message.created_at))
                .limit(1)
            ).scalar_one_or_none()
        )
        result.append({
            "chat": chat,
            "latestMessage": latest_message
        })
    return result
