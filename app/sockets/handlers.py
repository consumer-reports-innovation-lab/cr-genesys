import socketio

from guards.socket_auth import get_websocket_user, websocket_auth_required

# Get the Socket.IO server instance from main.py (will be imported later)
sio = None

# Store authenticated users per session
user_sessions = {}

def register_handlers(socket_server):
    """Register socket handlers with the provided socket server instance"""
    print(f"========== REGISTERING SOCKET HANDLERS ==========")
    print(f"DEBUG: socket_server: {socket_server}")
    
    global sio
    sio = socket_server
    
    # Create auth decorator with sio instance
    auth_required = websocket_auth_required(sio)

    print(f"========== ABOUT TO REGISTER EVENT HANDLERS ==========")
    # Register Socket event handlers INSIDE the function so they have access to the sio instance
    # Register on /ws namespace to match client connection
    @socket_server.event(namespace='/ws')
    async def connect(sid, environ, auth=None):
        try:
            print(f"========== SOCKET.IO CONNECT HANDLER CALLED ==========")
            print(f"DEBUG: sid: {sid}")
            print(f"DEBUG: environ type: {type(environ)}")
            print(f"DEBUG: auth type: {type(auth)}")
            print(f"DEBUG: auth data: {auth}")
            
            # TESTING MODE: Allow all connections without auth
            # Remove this block and uncomment the authentication code below for production
            print(f"========== ALLOWING ALL CONNECTIONS FOR TESTING ==========")
            print(f"DEBUG: Returning True from connect handler")
            return True
        except Exception as e:
            print(f"========== EXCEPTION IN CONNECT HANDLER: {e} ==========")
            import traceback
            traceback.print_exc()
            return False
        
        # PRODUCTION MODE: Uncomment this for proper authentication
        # user, session = await get_websocket_user(environ, auth)
        # if not user or not session:
        #     await socket_server.emit('unauthorized', {'message': 'Authentication required'}, room=sid)
        #     return False  # Reject the connection
        # 
        # # Store user session for this socket ID
        # user_sessions[sid] = {'user': user, 'session': session}
        # print(f"Authenticated connection: {sid} (user_id: {user.id})")
        # return True

    @socket_server.event(namespace='/ws')
    # @auth_required  # Temporarily disabled for testing - matches connect handler
    async def join(sid, data):
        """Join a room. For testing mode, we'll use the chat_id from data."""
        print(f"========== JOIN EVENT CALLED ==========")
        print(f"DEBUG: sid: {sid}")
        print(f"DEBUG: data: {data}")
        print(f"DEBUG: data type: {type(data)}")
        
        try:
            chat_id = data.get('chat_id') if data else None
            print(f"DEBUG: Extracted chat_id: {chat_id}")
            
            if not chat_id:
                error_response = {"status": "error", "message": "chat_id is required"}
                print(f"DEBUG: Returning error response: {error_response}")
                return error_response
            
            socket_server.enter_room(sid, chat_id, namespace='/ws')
            success_response = {"status": "success", "room": chat_id}
            print(f"DEBUG: {sid} joined room {chat_id}")
            print(f"DEBUG: Returning success response: {success_response}")
            return success_response
            
        except Exception as e:
            error_response = {"status": "error", "message": f"Error joining room: {str(e)}"}
            print(f"DEBUG: Exception in join handler: {e}")
            print(f"DEBUG: Returning exception response: {error_response}")
            return error_response

    @socket_server.event(namespace='/ws')
    async def disconnect(sid):
        print(f"========== SOCKET.IO DISCONNECT: {sid} ==========")
        # Clean up user session data when client disconnects
        if sid in user_sessions:
            del user_sessions[sid]
            print(f"Cleaned up session data for {sid}")

    @socket_server.event(namespace='/ws')
    async def test_ping(sid, data):
        print(f"========== RECEIVED TEST PING FROM {sid}: {data} ==========")
        await socket_server.emit('test_pong', {'message': 'pong from server'}, room=sid, namespace='/ws')
        return {'status': 'success', 'received': data}
    
    print(f"========== FINISHED REGISTERING ALL HANDLERS ==========")
    print(f"DEBUG: Registered handlers on /: {list(socket_server.handlers.get('/', {}).keys())}")
    print(f"DEBUG: Registered handlers on /ws: {list(socket_server.handlers.get('/ws', {}).keys())}")
    print(f"DEBUG: All namespaces: {list(socket_server.handlers.keys())}")

def get_user_session(sid):
    """Get stored user session for a socket ID"""
    return user_sessions.get(sid)

# Function to get the sio instance for use in other modules
def get_sio():
    return sio
