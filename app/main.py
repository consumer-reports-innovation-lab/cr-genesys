import socketio
import uuid
from datetime import datetime
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
from utils.chat.initialize_genesys_session import get_available_flows
from models import Memory
from schemas import MemorySchema, MemoryCreateSchema

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
    async_mode='asgi',
    logger=True,
    engineio_logger=True
)

# Import and register socket handlers after sio is created
print(f"========== MAIN.PY: ABOUT TO REGISTER SOCKET HANDLERS ==========")
from sockets.handlers import register_handlers
register_handlers(sio)
print(f"========== MAIN.PY: FINISHED REGISTERING SOCKET HANDLERS ==========")

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

@fastapi_app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cr-genesys-backend"}

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


from routes.webhook import router as webhook_router

# Mount the webhook router
fastapi_app.include_router(webhook_router)

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
    # Generate AI response (which will handle all message emissions including the user message)
    new_message = await generate_chat_message(
        db=db, 
        chat_id=chat_id, 
        system_prompt=message_data.system_prompt, 
        question=message_data.question,
        user_email=current_user.email
    )
    
    # Note: generate_chat_message now handles all socket emissions internally
    # including user message routing decisions and system responses
    
    return new_message

@fastapi_app.get("/chats/{chat_id}/memories")
def get_chat_memories(chat_id: str, _=Depends(chat_ownership_guard), db=Depends(get_db)):
    """
    Get all memories for a specific chat.
    """
    try:
        memories = db.query(Memory).filter(Memory.chat_id == chat_id).order_by(Memory.created_at.asc()).all()
        return [
            MemorySchema(
                id=memory.id,
                content=memory.content,
                chat_id=memory.chat_id,
                created_at=memory.created_at.isoformat(),
                updated_at=memory.updated_at.isoformat()
            ) for memory in memories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memories: {e}")

@fastapi_app.post("/chats/{chat_id}/memories")
def create_chat_memory(chat_id: str, memory_data: MemoryCreateSchema, _=Depends(chat_ownership_guard), db=Depends(get_db)):
    """
    Create a new memory for a specific chat.
    """
    try:
        memory = Memory(
            chat_id=chat_id,
            content=memory_data.content
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        return MemorySchema(
            id=memory.id,
            content=memory.content,
            chat_id=memory.chat_id,
            created_at=memory.created_at.isoformat(),
            updated_at=memory.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating memory: {e}")

@fastapi_app.delete("/chats/{chat_id}/memories/{memory_id}")
def delete_chat_memory(chat_id: str, memory_id: str, _=Depends(chat_ownership_guard), db=Depends(get_db)):
    """
    Delete a specific memory from a chat.
    """
    try:
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.chat_id == chat_id).first()
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        db.delete(memory)
        db.commit()
        
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting memory: {e}")

@fastapi_app.get("/genesys/flows")
def list_flows():
    """
    List available Genesys inbound message flows for debugging/configuration.
    """
    try:
        flows = get_available_flows()
        return {"flows": flows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving flows: {e}")

# Create Socket.IO ASGI app with correct configuration
socket_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path='/ws/socket.io')

# Use the combined app
app = socket_app
