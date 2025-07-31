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

class GenesysWebhookMessage(BaseModel):
    """Model for Genesys Cloud Open Messaging webhook payload."""
    id: str
    channel: dict
    direction: str
    text: str
    type: str = "Text"
    content: list = []
    metadata: dict = {}
    to: dict
    from_: dict = Field(..., alias="from")
    time: str
    message: dict = {}

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
        # Extract flow information if available
        flow_id = message.metadata.get("flowId")
        flow_name = message.metadata.get("flowName")
        
        # Log flow information for debugging
        if flow_id or flow_name:
            logger.info(f"Message processed through Genesys flow: {flow_name} (ID: {flow_id})")
            
            # Specific handling for InboundMessageFeedbackFlow
            if flow_name == "InboundMessageFeedbackFlow" or flow_id == "2f2c833f-edf0-4c44-8979-afd75d94ed55":
                logger.info("✅ FEEDBACK FLOW DETECTED: Message came through InboundMessageFeedbackFlow - feedback collection workflow activated")
                # The flow will handle bot interaction and feedback collection automatically
                # Our webhook just needs to process the message normally
        
        # Extract and validate recipient email
        recipient_email = message.channel.get("to", {}).get("id")
        if not recipient_email:
            raise HTTPException(status_code=400, detail="Recipient email not found in message")

        # Parse email and extract chat ID and base email
        try:
            # Split email into parts
            email_parts = recipient_email.split('@')
            if len(email_parts) != 2:
                raise ValueError("Invalid email format")
            
            local_part, domain = email_parts
            
            # Extract base email and chat ID from local part
            if '+' in local_part:
                base_local, chat_id = local_part.split('+', 1)
                base_email = f"{base_local}@{domain}"
            else:
                raise ValueError("Email missing chat ID (expected format: user+CHAT_ID@domain.com)")
            
            if not chat_id:
                raise ValueError("Could not extract chat ID from email")
                
        except ValueError as e:
            logger.error(f"Invalid email format: {recipient_email}. Error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email format. Expected format: user+CHAT_ID@domain.com. Error: {str(e)}"
            )

        # Get the chat from the database
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")

        # Verify the base email matches the chat owner's email
        owner_email = chat.user.email.lower()
        if base_email.lower() != owner_email:
            logger.warning(f"Email verification failed. Expected owner email {owner_email}, got {base_email}")
            raise HTTPException(
                status_code=403,
                detail="Email verification failed: Email does not match chat owner"
            )

        # Check if chat has a Genesys session ID
        if not chat.genesys_open_message_session_id:
            raise HTTPException(status_code=400, detail="Chat does not have an active Genesys session")

        # Get sender info
        sender_id = message.channel.get("from", {}).get("id")
        sender_name = message.channel.get("from", {}).get("nickname", "Unknown")

        # Create a new message in the database
        db_message = Message(
            id=message.id,
            content=message.text,
            chat_id=chat_id,
            is_system=False,
            is_markdown=True,
            sent_to_genesys=True,
            genesys_message_id=message.id,
            created_at=datetime.fromisoformat(message.time.rstrip('Z')) if message.time else datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Broadcast the message to the chat room via Socket.IO
        try:
            # Emit the message to the chat room
            await sio.emit('new_message', {
                'id': db_message.id,  # Use the database-generated ID
                'content': message.text,
                'chatId': chat_id,
                'isSystem': False,
                'isMarkdown': True,
                'sentToGenesys': True,
                'genesysMessageId': message.id,
                'createdAt': db_message.created_at.isoformat(),
                'updatedAt': db_message.updated_at.isoformat()
            }, room=chat_id)
            logger.info(f"Message broadcasted to chat {chat_id} via Socket.IO")
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")

        # Prepare the response
        client_message = {
            "id": message.id,
            "text": message.text,
            "type": message.type,
            "timestamp": message.channel.get("time"),
            "sender": {
                "id": sender_id,
                "name": sender_name,
            }
        }
        
        return client_message

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
