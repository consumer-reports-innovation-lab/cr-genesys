from typing import List, Dict, Any
from models import Message

def convert_messages_to_chat_history(messages: List[Message]) -> List[Dict[str, Any]]:
    """
    Convert database Message models to OpenAI-compatible chat history format.
    
    Args:
        messages (List[Message]): List of Message models from the database
    
    Returns:
        List[Dict[str, Any]]: Chat history in OpenAI/pydantic-ai compatible format
    """
    chat_history = []
    for message in messages:
        # Determine the role based on the message sender
        # Assumes 'user_id' indicates a user message, otherwise it's an assistant message
        role = 'assistant' if message.is_system else 'user'
        
        chat_history.append({
            'role': role,
            'content': message.content
        })
    
    return chat_history
