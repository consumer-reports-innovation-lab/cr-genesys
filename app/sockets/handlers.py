import socketio

from guards.socket_auth import get_websocket_user, websocket_auth_required

# Get the Socket.IO server instance from main.py (will be imported later)
sio = None

def register_handlers(socket_server):
    """Register socket handlers with the provided socket server instance"""
    global sio
    sio = socket_server
    
    # Create auth decorator with sio instance
    auth_required = websocket_auth_required(sio)

    # Register Socket event handlers
    @sio.event
    async def connect(sid, environ, auth=None):
        print(f"========== SOCKET.IO CONNECT HANDLER CALLED ==========")
        print(f"DEBUG: sid: {sid}")
        print(f"DEBUG: environ type: {type(environ)}")
        print(f"DEBUG: auth type: {type(auth)}")
        print(f"========== ALLOWING ALL CONNECTIONS FOR TESTING ==========")
        return True
        
        # Original auth code (temporarily disabled)
        # user, _ = await get_websocket_user(environ, auth)
        # if not user:
        #     await sio.emit('unauthorized', {'message': 'Authentication required'}, room=sid)
        #     return False  # Reject the connection
        # 
        # print(f"Authenticated connection: {sid} (user_id: {user.id})")
        # return True

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
        print(f"========== SOCKET.IO DISCONNECT: {sid} ==========")

    @sio.event
    async def test_ping(sid, data):
        print(f"========== RECEIVED TEST PING FROM {sid}: {data} ==========")
        await sio.emit('test_pong', {'message': 'pong from server'}, room=sid)
        return {'status': 'success', 'received': data}

# Function to get the sio instance for use in other modules
def get_sio():
    return sio
