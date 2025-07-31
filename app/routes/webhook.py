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
from utils.chat.generate_chat_message import decide_genesys_response
from utils.chat.get_chat_messages import get_chat_messages
from utils.adaptors.convert_messages_to_chat_history import convert_messages_to_chat_history
from purecloud_client import send_open_message

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
        logger.info(f"✅ GENESYS WEBHOOK: Received {message.originatingEntity or 'system'} message: {message.text[:100]}...")
        
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

        # Create a new message in the database (mark as system since it's from Genesys/bot)
        db_message = Message(
            content=message.text,
            chat_id=chat_id,
            is_system=True,  # Mark as system message since it's from Genesys bot
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
            'isSystem': True,  # Mark as system message for frontend
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
        logger.info(f"✅ GENESYS: {message.originatingEntity or 'System'} message broadcasted to chat {chat_id} via Socket.IO")

        # Use LLM to decide how to respond to this Genesys message
        logger.info("🤖 GENESYS RESPONSE: Using LLM to decide how to handle Genesys message...")
        
        # Get chat history for context
        messages = get_chat_messages(db, chat_id)
        chat_history = convert_messages_to_chat_history(messages)
        
        # Get user context (email from chat owner)
        user_context = f"User email: {chat.user.email}" if chat.user else None
        
        # Make decision
        response_decision = decide_genesys_response(message.text, chat_history, user_context)
        logger.info(f"🤖 GENESYS DECISION: should_respond_to_genesys={response_decision.should_respond_to_genesys}, should_ask_user={response_decision.should_ask_user}")
        logger.info(f"🤖 GENESYS EXPLANATION: {response_decision.explanation}")

        # Handle responding to Genesys if decided
        if response_decision.should_respond_to_genesys and response_decision.genesys_response:
            logger.info("✅ GENESYS RESPONSE: LLM decided to respond directly to Genesys")
            try:
                # Construct to_address for responding to Genesys
                user_email = chat.user.email
                if user_email and '@' in user_email:
                    local_part, domain = user_email.split('@', 1)
                    to_address = f"{local_part}+{chat_id}@{domain}"
                    
                    # Send response to Genesys
                    logger.info(f"🚀 GENESYS RESPONSE: Sending response to Genesys: {response_decision.genesys_response[:50]}...")
                    genesys_response = send_open_message(
                        to_address=to_address,
                        message_content=response_decision.genesys_response
                    )
                    
                    # Save the response as a system message sent to Genesys
                    response_message = Message(
                        content=response_decision.genesys_response,
                        chat_id=chat_id,
                        is_system=True,
                        is_markdown=True,
                        sent_to_genesys=True,
                        genesys_message_id=getattr(genesys_response, 'id', None),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(response_message)
                    db.commit()
                    db.refresh(response_message)
                    
                    # Emit the response message to the chat
                    response_socket_message = {
                        'id': str(response_message.id),
                        'content': response_decision.genesys_response,
                        'chatId': chat_id,
                        'isSystem': True,
                        'isMarkdown': True,
                        'sentToGenesys': True,
                        'genesysMessageId': getattr(genesys_response, 'id', None),
                        'createdAt': response_message.created_at.isoformat(),
                        'updatedAt': response_message.updated_at.isoformat()
                    }
                    await sio.emit('new_message', response_socket_message, room=chat_id)
                    logger.info(f"✅ GENESYS RESPONSE: Response sent to Genesys and broadcasted to chat {chat_id}")
                else:
                    logger.warning(f"❌ GENESYS RESPONSE: Cannot send response - invalid user email")
            except Exception as e:
                logger.error(f"❌ GENESYS RESPONSE: Failed to send response to Genesys: {e}")

        # Handle asking user for more info if decided
        if response_decision.should_ask_user and response_decision.user_question:
            logger.info("✅ USER QUESTION: LLM decided to ask user for more information")
            try:
                # Save the question as a system message to the user
                user_question_message = Message(
                    content=response_decision.user_question,
                    chat_id=chat_id,
                    is_system=True,
                    is_markdown=True,
                    sent_to_genesys=False,  # This is for the user, not Genesys
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(user_question_message)
                db.commit()
                db.refresh(user_question_message)
                
                # Emit the question to the user
                question_socket_message = {
                    'id': str(user_question_message.id),
                    'content': response_decision.user_question,
                    'chatId': chat_id,
                    'isSystem': True,
                    'isMarkdown': True,
                    'sentToGenesys': False,
                    'genesysMessageId': None,
                    'createdAt': user_question_message.created_at.isoformat(),
                    'updatedAt': user_question_message.updated_at.isoformat()
                }
                await sio.emit('new_message', question_socket_message, room=chat_id)
                logger.info(f"✅ USER QUESTION: Question sent to user in chat {chat_id}")
            except Exception as e:
                logger.error(f"❌ USER QUESTION: Failed to send question to user: {e}")

        return {"status": "success", "messageId": message.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Genesys webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
