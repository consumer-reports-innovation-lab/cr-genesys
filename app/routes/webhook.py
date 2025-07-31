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
    request: Request,
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
        # Get the raw JSON payload from Genesys
        payload = await request.json()
        
        # Log the entire payload to understand Genesys's structure
        logger.info(f"🔍 WEBHOOK DEBUG: Received Genesys payload: {payload}")
        logger.info(f"🔍 WEBHOOK DEBUG: Payload type: {type(payload)}")
        logger.info(f"🔍 WEBHOOK DEBUG: Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}")
        
        # Return success for now until we understand the structure
        return {"status": "received", "message": "Payload logged for debugging"}

    except Exception as e:
        logger.error(f"🔍 WEBHOOK DEBUG: Error processing webhook: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Error: {str(e)}"}
