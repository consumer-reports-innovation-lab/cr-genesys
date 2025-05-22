from sqlalchemy.orm import Session
from sqlalchemy import select, asc
from models import Message
from typing import List

def get_chat_messages(db: Session, chat_id: str) -> List[Message]:
    """
    Retrieve all messages for a specific chat, ordered by creation time in ascending order.
    
    Args:
        db (Session): Database session
        chat_id (str): ID of the chat to retrieve messages for
    
    Returns:
        List[Message]: List of messages for the specified chat, sorted by creation time
    """
    messages = db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(asc(Message.created_at))
    ).scalars().all()
    
    return messages
