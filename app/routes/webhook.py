from fastapi import APIRouter, HTTPException, Form, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from utils.db import get_db
from models import Chat, Message
from sockets.handlers import get_sio
from config import settings

# Configure logging
logger = logging.getLogger(__name__)
sio = get_sio()

router = APIRouter()

class GenesysChannelTo(BaseModel):
    id: str  # Email like "user+chatId@domain.com"
    idType: str  # "Email"

class GenesysChannelFrom(BaseModel):
    nickname: str  # "ConsumerReportsOM"
    id: str  # Deployment ID
    idType: str  # "Opaque"

class GenesysChannel(BaseModel):
    id: str  # Deployment ID
    platform: str  # "Open"
    type: str  # "Private"
    to: GenesysChannelTo
    from_: GenesysChannelFrom = Field(..., alias="from")
    time: str  # ISO timestamp
    messageId: str

class GenesysQuickReply(BaseModel):
    text: str
    payload: str
    action: str = "Message"

class GenesysContent(BaseModel):
    contentType: str  # "QuickReply"
    quickReply: Optional[GenesysQuickReply] = None

class GenesysWebhookMessage(BaseModel):
    """Model for Genesys Cloud Open Messaging webhook payload."""
    id: str
    channel: GenesysChannel
    type: str  # "Text" or "Structured"
    text: str
    content: List[GenesysContent] = []
    originatingEntity: Optional[str] = None  # "Bot"
    direction: str  # "Outbound" 
    conversationId: str

@router.post("/messages")
async def handle_webhook(
    message: GenesysWebhookMessage,
    db: Session = Depends(get_db)
):
    """
    Handle incoming webhook messages from Genesys Cloud Open Messaging.
    
    Expected payload format:
    {
        "id": "message-id",
        "channel": {
            "type": "Open",
            "messageId": "message-id",
            "platform": "Open",
            "to": {
                "id": "recipient-id",
                "nickname": "Recipient Name",
                "type": "Messaging"
            },
            "from": {
                "id": "sender-id",
                "nickname": "Sender Name",
                "type": "Messaging"
            },
            "time": "2023-01-01T00:00:00.000Z"
        },
        "direction": "Inbound",
        "text": "Message content",
        "type": "Text",
        "content": [],
        "metadata": {}
    }
    """
    try:
        logger.info(f"✅ GENESYS WEBHOOK: Received message from {message.originatingEntity or 'Unknown'}: {message.text[:100]}...")
        
        # Extract chat ID from recipient email
        recipient_email = message.channel.to.id
        try:
            # Split email: "user+chatId@domain.com" -> ["user", "chatId@domain.com"]
            local_part, domain = recipient_email.split('@')
            if '+' not in local_part:
                raise ValueError("Email missing chat ID")
            base_local, chat_id = local_part.split('+', 1)
            base_email = f"{base_local}@{domain}"
        except ValueError as e:
            logger.error(f"Invalid email format: {recipient_email}. Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid email format: {str(e)}")

        # Get the chat from the database
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")

        # Verify the base email matches the chat owner's email
        owner_email = chat.user.email.lower()
        if base_email.lower() != owner_email:
            logger.warning(f"Email verification failed. Expected {owner_email}, got {base_email}")
            raise HTTPException(status_code=403, detail="Email verification failed")

        # Create a new message in the database
        db_message = Message(
            content=message.text,
            chat_id=chat_id,
            is_system=False,
            is_markdown=True,
            sent_to_genesys=True,
            genesys_message_id=message.id,
            created_at=datetime.fromisoformat(message.channel.time.rstrip('Z')),
            updated_at=datetime.now()
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Prepare message for Socket.IO with QuickReply buttons if present
        socket_message = {
            'id': str(db_message.id),
            'content': message.text,
            'chatId': chat_id,
            'isSystem': False,
            'isMarkdown': True,
            'sentToGenesys': True,
            'genesysMessageId': message.id,
            'createdAt': db_message.created_at.isoformat(),
            'updatedAt': db_message.updated_at.isoformat()
        }
        
        # Add QuickReply buttons if this is a structured message
        if message.type == "Structured" and message.content:
            quick_replies = []
            for content_item in message.content:
                if content_item.contentType == "QuickReply" and content_item.quickReply:
                    quick_replies.append({
                        'text': content_item.quickReply.text,
                        'payload': content_item.quickReply.payload
                    })
            if quick_replies:
                socket_message['quickReplies'] = quick_replies

        # Broadcast the message to the chat room via Socket.IO
        await sio.emit('new_message', socket_message, room=chat_id)
        logger.info(f"✅ GENESYS: Message broadcasted to chat {chat_id} via Socket.IO")

        return {"status": "success", "messageId": message.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Genesys webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
