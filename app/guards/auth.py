from fastapi import Depends, HTTPException, status, Request
from utils.user import get_current_user_and_session
from utils.db import get_db
from datetime import datetime, timezone

def auth_guard(request: Request, db = Depends(get_db)):
    user, session = get_current_user_and_session(request, db)
    if not user or not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized. Invalid or missing credentials.',
        )
    
    expires = session.expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        # Optional: Delete the expired session from the database
        # db.delete(session)
        # db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized. Session has expired.',
        )
    return user
