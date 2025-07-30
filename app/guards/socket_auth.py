from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from utils.db import get_db
from models import Session as SessionModel, User

async def get_websocket_user(environ, auth_data) -> Tuple[Optional[User], Optional[SessionModel]]:
    """
    Authenticate WebSocket connection using session token from headers.
    Returns (user, session) tuple if authenticated, (None, None) otherwise.
    """
    # Get session token from Socket.IO auth data
    token = None

    print(f"DEBUG: WebSocket auth - environ: {environ}")
    print(f"DEBUG: WebSocket auth - auth_data: {auth_data}")

    # Check if auth_data contains the token
    if auth_data and isinstance(auth_data, dict):
        auth_token = auth_data.get('token')
        print(f"DEBUG: Auth token from auth_data: {auth_token}")
        if auth_token and auth_token.startswith('Bearer '):
            token = auth_token.split(' ')[1]
            print(f"DEBUG: Extracted token: {token[:20]}...")
        else:
            print(f"DEBUG: Invalid auth token format: {auth_token}")

    if not token:
        print("DEBUG: No valid token found in WebSocket auth data")
        return None, None
    
    # Get database session
    db = next(get_db())
    try:
        # Verify session token
        session = db.query(SessionModel).filter(SessionModel.session_token == token).first()
        if not session:
            return None, None
            
        # Check if session is expired
        expires = session.expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
            
        if expires < datetime.now(timezone.utc):
            return None, None
            
        return session.user, session
    finally:
        db.close()

def websocket_auth_required(sio):
    """
    Decorator factory that returns a decorator to require authentication for WebSocket event handlers.
    The sio instance is passed to access the socket environment.
    
    Note: This decorator expects user session data to be stored during the connect event.
    Import get_user_session from sockets.handlers to access stored session data.
    """
    def decorator(handler):
        async def wrapped(sid, *args, **kwargs):
            # Import here to avoid circular import
            from sockets.handlers import get_user_session
            
            # Get stored user session data
            session_data = get_user_session(sid)
            
            if not session_data:
                await sio.emit('unauthorized', {'message': 'Authentication required'}, room=sid)
                await sio.disconnect(sid)
                return
                
            # Add user and session to the handler's kwargs
            kwargs['user'] = session_data['user']
            kwargs['session'] = session_data['session']
            return await handler(sid, *args, **kwargs)
        return wrapped
    return decorator
