from sqlalchemy.orm import Session
from models import Chat
import uuid

def create_chat(db: Session, user_id: str, title: str = None) -> Chat:
    """
    Create a new chat for a user.
    
    Args:
        db (Session): Database session
        user_id (str): ID of the user creating the chat
        title (str, optional): Title of the chat. Defaults to None.
    
    Returns:
        Chat: Newly created chat object
    """
    # Generate a unique chat ID
    chat_id = str(uuid.uuid4())
    
    # Create new chat
    new_chat = Chat(
        id=chat_id,
        user_id=user_id,
        title=title
    )
    
    # Add and commit the new chat
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    return new_chat
