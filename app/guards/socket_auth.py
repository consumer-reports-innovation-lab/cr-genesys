from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from utils.db import get_db
from models import Session as SessionModel, User

async def get_websocket_user(environ, sio) -> Tuple[Optional[User], Optional[SessionModel]]:
    """
    Authenticate WebSocket connection using session token from headers.
    Returns (user, session) tuple if authenticated, (None, None) otherwise.
    """
    # Get session token from headers or auth field
    scope = environ.get('asgi.scope', {})
    headers = dict(scope.get('headers', []))
    auth_header = headers.get(b'authorization', b'').decode('latin1')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        # Try to get token from Socket.IO 'auth' payload
        auth_payload = scope.get('auth')
        if auth_payload and isinstance(auth_payload, dict):
            auth_token = auth_payload.get('token')
            if auth_token and auth_token.startswith('Bearer '):
                token = auth_token.split(' ')[1]

    if not token:
        return None, None
    
    # Get database session
    db = next(get_db())
    try:
        # Verify session token
        session = db.query(SessionModel).filter(SessionModel.token == token).first()
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
    """
    def decorator(handler):
        async def wrapped(sid, *args, **kwargs):
            environ = sio.environ.get(sid, {})
            user, session = await get_websocket_user(environ, sio)
            
            if not user or not session:
                await sio.emit('unauthorized', {'message': 'Authentication required'}, room=sid)
                await sio.disconnect(sid)
                return
                
            # Add user and session to the handler's kwargs
            kwargs['user'] = user
            kwargs['session'] = session
            return await handler(sid, *args, **kwargs)
        return wrapped
    return decorator
