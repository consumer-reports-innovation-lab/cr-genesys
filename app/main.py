import socketio
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional

from config import settings
from utils.chat.generate_chat_message import generate_chat_message
from purecloud_client import get_purecloud_client, get_permissions
import PureCloudPlatformClientV2

from utils.db import get_db
from guards.auth import auth_guard
from guards.chat import chat_ownership_guard
from utils.chat.get_chat_by_id import get_chat_by_id
from utils.chat.get_chats_by_user_with_latest_message import get_chats_by_user_with_latest_message
from utils.chat.create_chat import create_chat
from utils.chat.get_chat_messages import get_chat_messages as _get_chat_messages_from_db

# Create FastAPI app
fastapi_app = FastAPI(
    title="Consumer Reports API",
    description="API for Consumer Reports Genesis Prototype",
    version="1.0.0"
)

# Add CORS middleware to FastAPI app
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a simple test endpoint
@fastapi_app.get("/test-socket")
async def test_socket():
    return {"message": "FastAPI is working", "socket_io_available": True}

# Initialize Socket.IO with simplified configuration
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Import and register socket handlers after sio is created
from sockets.handlers import register_handlers
register_handlers(sio)

# Pydantic model for the request body
class ChatMessageCreate(BaseModel):
    system_prompt: str
    question: str

@fastapi_app.get("/")
def read_root():
    return {
        "message": "Hello from FastAPI",
        "database_url": settings.DATABASE_URL,
        "socket_io_enabled": True
    }

@fastapi_app.get("/purecloud/permissions")
def purecloud_permissions():
    """
    Returns the Genesys Cloud permissions for the current app credentials.
    """
    try:
        perms = get_permissions()
        # perms is a PermissionsEntityListing object; convert to dict for JSON
        return perms.to_dict() if hasattr(perms, 'to_dict') else perms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Genesys Cloud error: {e}")


from typing import List
from routes.webhook import router as webhook_router

@fastapi_app.get("/chats")
def get_user_chats(current_user=Depends(auth_guard), db=Depends(get_db)):
    """
    Get all chats for the authenticated user, each with the most recent message.
    """
    user_id = current_user.id
    return get_chats_by_user_with_latest_message(db, user_id)

@fastapi_app.post("/chats")
def create_new_chat(current_user=Depends(auth_guard), db=Depends(get_db)):
    """
    Create a new chat for the authenticated user.
    """
    new_chat = create_chat(db, current_user.id)
    return new_chat


@fastapi_app.get("/chats/{chat_id}")
def get_chat(
    chat_id: str, 
    include_chat_history: bool = True,
    _=Depends(chat_ownership_guard), 
    db=Depends(get_db)
):
    """
    Get a chat by id for the authenticated user.
    
    Args:
        chat_id: The ID of the chat to retrieve
        include_chat_history: Whether to include chat messages in the response (default: True)
    """
    chat_info = get_chat_by_id(db, chat_id, include_messages=include_chat_history)
    return chat_info


@fastapi_app.get("/chats/{chat_id}/messages")
def get_chat_messages(chat_id: str, _=Depends(chat_ownership_guard), db=Depends(get_db)):
    """
    Get all messages for a specific chat, ordered by creation time.
    """
    messages = _get_chat_messages_from_db(db, chat_id)
    return messages

@fastapi_app.post("/chats/{chat_id}/messages")
async def create_chat_message(chat_id: str, message_data: ChatMessageCreate, current_user=Depends(chat_ownership_guard), db=Depends(get_db)):
    """
    Generate a new message for a specific chat using AI.
    """
    new_message = generate_chat_message(
        db=db, 
        chat_id=chat_id, 
        system_prompt=message_data.system_prompt, 
        question=message_data.question,
        user_email=current_user.email
    )
    
    # Emit the new message through Socket.IO
    await sio.emit("new_message", {
        "chat_id": chat_id,
        "message": new_message
    }, room=str(current_user.id))  # Ensure user_id is a string
    
    return new_message

# Create Socket.IO ASGI app with correct configuration
socket_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path='/ws/socket.io')

# Use the combined app
app = socket_app
