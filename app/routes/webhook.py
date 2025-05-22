from fastapi import APIRouter, HTTPException, Form, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from utils.chat.generate_chat_message import generate_chat_message
from guards.auth import auth_guard
from guards.chat import chat_ownership_guard
from utils.db import get_db
from utils.chat.get_chat_by_id import get_chat_by_id
from utils.chat.get_chat_messages import get_chat_messages as _get_chat_messages_from_db

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
async def handle_webhook(message: GenesysWebhookMessage):
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
        # Extract recipient ID (this could be a user ID or a room ID)
        recipient_id = message.channel.get("to", {}).get("id")
        
        if not recipient_id:
            raise HTTPException(status_code=400, detail="Recipient ID not found in message")

        # Prepare the message for the client
        client_message = {
            "id": message.id,
            "text": message.text,
            "type": message.type,
            "timestamp": message.channel.get("time"),
            "sender": {
                "id": message.channel.get("from", {}).get("id"),
                "name": message.channel.get("from", {}).get("nickname"),
            }
        }

        # TODO: Implement message handling logic
        # This could include:
        # - Storing the message in the database
        # - Broadcasting to connected clients
        # - Processing the message content
        
        return client_message

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
