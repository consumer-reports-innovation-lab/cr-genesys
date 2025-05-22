import socketio

from guards.socket_auth import get_websocket_user, websocket_auth_required

# Create Socket.IO server instance
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create auth decorator with sio instance
auth_required = websocket_auth_required(sio)

# Socket event handlers
@sio.event
async def connect(sid, environ):
    user, _ = await get_websocket_user(environ)
    if not user:
        await sio.emit('unauthorized', {'message': 'Authentication required'}, room=sid)
        return False  # Reject the connection
    
    print(f"Authenticated connection: {sid} (user_id: {user.id})")
    return True

@sio.event
@auth_required
async def join(sid, data, user, session):
    """Join a room. The room ID is typically the user's ID."""
    user_id = str(user.id)
    await sio.enter_room(sid, user_id)
    print(f"{sid} joined room {user_id}")
    return {"status": "success", "room": user_id}

@sio.event
async def disconnect(sid):
    print(f"Disconnected: {sid}")

# Function to get the sio instance for use in other modules
def get_sio():
    return sio
