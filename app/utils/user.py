from fastapi import Depends, Request
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select
from typing import Optional
from models import Session, User
from datetime import datetime

# Utility to fetch current user and session from session token
def get_current_user_and_session(request: Request, db: DBSession = Depends()):
    auth_header: Optional[str] = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, None
    token = auth_header.split(' ', 1)[1]
    
    session_obj = db.execute(select(Session).where(Session.session_token == token)).scalar_one_or_none()
    if not session_obj:
        return None, None # No session found for token
        
    user_obj = db.execute(select(User).where(User.id == session_obj.user_id)).scalar_one_or_none()
    if not user_obj:
        # Session exists but user doesn't; treat as invalid session
        return None, None 
        
    return user_obj, session_obj
