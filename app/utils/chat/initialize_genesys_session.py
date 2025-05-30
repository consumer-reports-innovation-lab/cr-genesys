import logging
import os
from sqlalchemy.orm import Session
from models import Chat
from purecloud_client import send_open_message, GENESYS_DEPLOYMENT_ID

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

    # Construct to_address as user+chatid@email.com if user_email is provided
    to_address = None
    if user_email and '@' in user_email:
        local_part, domain = user_email.split('@', 1)
        to_address = f"{local_part}+{chat_id}@{domain}"
        logger.info(f"Constructed to_address for Genesys session: {to_address}")
    else:
        logger.warning("User email not provided or invalid; to_address will not be set.")
    
    # Skip if no deployment ID is configured
    if not GENESYS_DEPLOYMENT_ID:
        logger.warning("No Genesys Open Messaging deployment ID configured, skipping initialization")
        return False
    
    try:
        # Create a new Open Messaging session
        # Send an initial message to Genesys to establish the conversation
        from_address = os.environ.get("GENESYS_FROM_ADDRESS", "noreply@example.com")
        if not to_address:
            logger.error("Cannot send Genesys Open Messaging message: to_address is not set.")
            return False
        initial_message = f"Chat {chat_id} initiated by user {user_email or chat.user_id}"
        try:
            response = send_open_message(
                from_address=from_address,
                to_address=to_address,
                message_content=initial_message,
                deployment_id=GENESYS_DEPLOYMENT_ID
            )
            logger.info(f"Successfully sent initial Genesys Open Messaging message for chat {chat_id}. Response: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Genesys Open Messaging message: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error initializing Genesys Open Messaging session: {e}")
        return False
