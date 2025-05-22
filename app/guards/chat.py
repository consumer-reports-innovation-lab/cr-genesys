from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from utils.user import get_current_user_and_session
from utils.db import get_db
from models import Chat
from datetime import datetime, timezone

def chat_ownership_guard(chat_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Guard to validate user ownership of a specific chat and session validity.
    
    Args:
        chat_id (str): ID of the chat to validate ownership for
        request (Request): Incoming HTTP request
        db (Session): Database session
    
    Raises:
        HTTPException: 401 if user is not authenticated or session is invalid/expired
        HTTPException: 403 if user does not own the chat
    
    Returns:
        User: Current user object
    """
    # First, authenticate the user and validate the session
    user, session = get_current_user_and_session(request, db)
    if not user or not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized. Invalid or missing credentials.',
        )

    if session.expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        # Optional: Delete the expired session from the database
        # db.delete(session)
        # db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized. Session has expired.',
        )
    
    # Check chat ownership
    # Assuming chat_id is a string as per typical model definitions (e.g., UUID)
    # If chat_id is an integer, remove str() conversion if not needed.
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have permission to access this chat.',
        )
    
    return user
