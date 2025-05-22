import logging
import os
from sqlalchemy.orm import Session
from models import Chat
from purecloud_client import create_open_messaging_session, send_open_message, GENESYS_DEPLOYMENT_ID

# Configure logging
logger = logging.getLogger(__name__)

def initialize_genesys_session(db: Session, chat_id: str, user_email: str = None):
    """
    Initialize a Genesys Open Messaging session for a chat.
    
    Args:
        db (Session): Database session
        chat_id (str): The chat ID to associate with Genesys
        user_email (str, optional): User's email for customer identification
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Retrieve the chat from database
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logger.error(f"Chat {chat_id} not found")
        return False
    
    # Skip if no deployment ID is configured
    if not GENESYS_DEPLOYMENT_ID:
        logger.warning("No Genesys Open Messaging deployment ID configured, skipping initialization")
        return False
    
    try:
        # Create a new Open Messaging session
        customer_id = user_email or f"user-{chat.user_id}"
        session_id = create_open_messaging_session(GENESYS_DEPLOYMENT_ID, customer_id)
        
        if not session_id:
            logger.error("Failed to create Genesys Open Messaging session, no session ID returned")
            return False
        
        # Update the chat with Genesys session information
        chat.genesys_open_message_session_id = session_id
        chat.genesys_open_message_active = True
        db.commit()
        
        # Send an initial message to Genesys to establish the conversation
        initial_message = f"Chat {chat_id} initiated by user {customer_id}"
        send_open_message(GENESYS_DEPLOYMENT_ID, session_id, initial_message)
        
        logger.info(f"Successfully initialized Genesys Open Messaging session for chat {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Genesys Open Messaging session: {e}")
        return False
