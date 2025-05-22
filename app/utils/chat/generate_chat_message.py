import logging
import os
import uuid
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from instructor import patch
from models import Message, Chat
from utils.chat.get_chat_messages import get_chat_messages
from utils.adaptors.convert_messages_to_chat_history import convert_messages_to_chat_history
from utils.validators.is_markdown import is_markdown
from purecloud_client import send_open_message, GENESYS_DEPLOYMENT_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patch OpenAI client to support instructor tools
client = patch(openai.OpenAI())

# Mailchimp Transactional SMTP configuration
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_TRANSACTIONAL_API_KEY")
SMTP_SERVER = "smtp.mandrillapp.com"
SMTP_PORT = 587
SMTP_USERNAME = "CR"  # Using CR as the username as specified


# === Dummy Tool ===

class DummyToolRequest(BaseModel):
    message: str = Field(..., description="Message to process")

# Define the actual tool function (no decorator needed)
def dummy_tool(message: str):
    return {"result": f"Processed: {message}"}

# Prepare the tool schema for OpenAI function calling
DUMMY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "dummy_tool",
        "description": "Process a message and return a result.",
        "parameters": DummyToolRequest.schema()
    }
}


# === Genesys Open Messaging Tools ===

class CheckGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to check for an active Genesys session")

class CreateGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to create a Genesys session for")
    customer_id: str = Field(None, description="Optional customer identifier")

class GenesysSessionResponse(BaseModel):
    success: bool
    message: str
    session_id: str = None

def check_genesys_session(data: CheckGenesysSessionRequest, db: Session) -> GenesysSessionResponse:
    """
    Check if a chat has an active Genesys Open Messaging session
    """
    from utils.chat.get_chat_by_id import get_chat_by_id
    
    chat_data = get_chat_by_id(db, data.chat_id, include_messages=False)
    if not chat_data or not chat_data.get("chat"):
        return GenesysSessionResponse(
            success=False,
            message=f"Chat {data.chat_id} not found"
        )
    
    chat = chat_data["chat"]
    if chat.genesys_open_message_active and chat.genesys_open_message_session_id:
        return GenesysSessionResponse(
            success=True,
            message=f"Chat has an active Genesys session",
            session_id=chat.genesys_open_message_session_id
        )
    else:
        return GenesysSessionResponse(
            success=False,
            message=f"Chat does not have an active Genesys session"
        )

def create_genesys_session(data: CreateGenesysSessionRequest, db: Session) -> GenesysSessionResponse:
    """
    Create a new Genesys Open Messaging session for a chat
    """
    from utils.chat.initialize_genesys_session import initialize_genesys_session
    
    # First check if there's already a session
    check_result = check_genesys_session(CheckGenesysSessionRequest(chat_id=data.chat_id), db)
    if check_result.success:
        return check_result
    
    # Initialize a new session
    success = initialize_genesys_session(db, data.chat_id, data.customer_id)
    
    # Get the chat to return the session ID
    from utils.chat.get_chat_by_id import get_chat_by_id
    chat_data = get_chat_by_id(db, data.chat_id, include_messages=False)
    
    if success and chat_data and chat_data.get("chat") and chat_data["chat"].genesys_open_message_session_id:
        return GenesysSessionResponse(
            success=True,
            message=f"Successfully created Genesys session",
            session_id=chat_data["chat"].genesys_open_message_session_id
        )
    else:
        return GenesysSessionResponse(
            success=False,
            message=f"Failed to create Genesys session"
        )

# Prepare the tool schemas for OpenAI function calling
CHECK_GENESYS_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_genesys_session",
        "description": "Check if a chat has an active Genesys Open Messaging session.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID to check for an active Genesys session"
                }
            },
            "required": ["chat_id"]
        }
    }
}

CREATE_GENESYS_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_genesys_session",
        "description": "Create a new Genesys Open Messaging session for a chat to connect with a live agent.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID to create a Genesys session for"
                },
                "customer_id": {
                    "type": "string",
                    "description": "Optional customer identifier"
                }
            },
            "required": ["chat_id"]
        }
    }
}


# === Feedback Email Tool ===

class FeedbackEmailRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to update after feedback is submitted")
    message_body: str = Field(
        ..., 
        max_length=1000, 
        description="Feedback content to send to support (max 1000 characters)"
    )

class FeedbackResponse(BaseModel):
    message: str

# Send feedback via SMTP with Mailchimp Transactional, from the user's reply_to address
def send_feedback_email(data: FeedbackEmailRequest, db: Session, user_email: str = None) -> FeedbackResponse:
    recipient = "feedbackroute@consumerreports.mypurecloud.com"
    subject   = "User Feedback Submission"
    sender_email = "jamal.jackson.consultant@consumer.org"
    reply_to  = "jamal.jackson.consultant@consumer.org" or user_email or "noreply@yourdomain.com"
    preview   = data.message_body.strip().replace("\n", " ")[:50]

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    message["Reply-To"] = sender_email

    # Add text content
    text_content = data.message_body
    part1 = MIMEText(text_content, "plain")
    message.attach(part1)

    # Add HTML content
    html_content = f"<p>{data.message_body}</p>"
    part2 = MIMEText(html_content, "html")
    message.attach(part2)

    try:
        logger.info(f"Sending feedback email via SMTP to {recipient} from {sender_email}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SMTP_USERNAME, MAILCHIMP_API_KEY)
        server.sendmail(sender_email, recipient, message.as_string())
        server.quit()
        logger.info("Email sent successfully!")
    except Exception as e:
        logger.error(f"SMTP email failed: {e}")
        raise RuntimeError("Failed to send feedback email")

    # Log assistant confirmation message (system message)
    confirmation_msg = Message(
        chat_id=data.chat_id,
        content="Your feedback has been sent.",
        is_system=True,
        is_markdown=False
    )
    db.add(confirmation_msg)

    # Set chat status to CLOSED
    chat = db.query(Chat).filter(Chat.id == data.chat_id).first()
    if chat:
        chat.status = "CLOSED"
        logger.info(f"Chat {data.chat_id} marked as CLOSED.")

    db.commit()
    db.refresh(confirmation_msg)

    return FeedbackResponse(message=f'Feedback submitted: "{preview}"...')

# Prepare the tool schema for send_feedback_email
SEND_FEEDBACK_EMAIL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_feedback_email",
        "description": "Sends feedback provided by the user via email to the support team.",
        "parameters": {
            "type": "object",
            "properties": {
                "message_body": {
                    "type": "string",
                    "description": "Feedback content to send to support (max 1000 characters)",
                }
            },
            "required": ["message_body"]
        }
    }
}


# === Chat Message Generator ===

def ensure_genesys_session_id(chat, db):
    """
    Ensure chat.genesys_open_message_session_id exists. If not, generate and persist a new UUID.
    """
    if not chat.genesys_open_message_session_id:
        chat.genesys_open_message_session_id = str(uuid.uuid4())
        db.commit()

def call_openai_with_tool(messages):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=[DUMMY_TOOL_SCHEMA],
        tool_choice="auto",
    )
    return response

def generate_chat_message(
    db: Session, 
    chat_id: str, 
    system_prompt: str, 
    question: str, 
    user_email: str = None
) -> Message:
    logger.info(f"Generating response for chat_id: {chat_id}, question: {question}")

    # Save the user's question as a Message
    user_message = Message(
        chat_id=chat_id,
        content=question,
        is_system=False,
        is_markdown=False
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get the chat object
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logger.error(f"Chat {chat_id} not found")
        raise ValueError(f"Chat {chat_id} not found")
    
    # Forward user message to Genesys if integration is active for this chat
    if GENESYS_DEPLOYMENT_ID and chat.genesys_open_message_active:
        needs_refresh = not chat.genesys_open_message_session_id
        ensure_genesys_session_id(chat, db)
        if needs_refresh:
            db.refresh(chat)
        try:
            # Send message to Genesys Open Messaging
            genesys_response = send_open_message(
                user_token=chat.genesys_open_message_session_id,
                message_content=question
            )
            # Update the message record to indicate it was sent to Genesys
            user_message.sent_to_genesys = True
            if hasattr(genesys_response, 'id'):
                user_message.genesys_message_id = genesys_response.id
            db.commit()
            logger.info(f"Message sent to Genesys for chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message to Genesys: {e}")
            # Continue with local processing even if Genesys fails

    messages = get_chat_messages(db, chat_id)
    chat_history = convert_messages_to_chat_history(messages)

    system_tool_hint = {
        "role": "system",
        "content": (
            "If the user asks to give feedback (e.g., 'how can I leave feedback?', 'I want to share feedback'), "
            "respond with: 'Please share your feedback.' and wait for the user's next message. "
            "Then, call the send_feedback_email tool using that feedback message.\n\n"
            "If the user spontaneously provides feedback, a complaint, or a suggestion, "
            "directly call the send_feedback_email tool with their message.\n\n"
            "You may consider the most recent assistant response as a cue — if the user responds to it with something emotional or critical, "
            "it's likely feedback and should be sent."
        )
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                system_tool_hint,
                *chat_history,
                {"role": "user", "content": question}
            ],
            tools=[
                DUMMY_TOOL_SCHEMA, 
                SEND_FEEDBACK_EMAIL_SCHEMA,
                CHECK_GENESYS_SESSION_SCHEMA,
                CREATE_GENESYS_SESSION_SCHEMA
            ],
            tool_choice="auto"
        )
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise RuntimeError(f"Failed to get response from OpenAI: {e}")

    response_message = response.choices[0].message

    # Check if the chat is already closed
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat and chat.status == "CLOSED":
        logger.info(f"Chat {chat_id} is closed. Skipping message creation.")
        return None

    if response_message.tool_calls:
        import json
        tool_call = response_message.tool_calls[0]
        function_name = getattr(tool_call.function, "name", "unknown")
        logger.info(f"Tool call detected: {function_name}")

        if function_name == "send_feedback_email":
            try:
                args = json.loads(tool_call.function.arguments)
                args['chat_id'] = chat_id
                req = FeedbackEmailRequest(**args)
                result = send_feedback_email(req, db=db, user_email=user_email)
                content = result.message
            except Exception as e:
                logger.error(f"Failed to manually invoke send_feedback_email: {e}")
                content = "[Failed to execute feedback tool]"
                
        elif function_name == "check_genesys_session":
            try:
                args = json.loads(tool_call.function.arguments)
                # If chat_id is not in args, use the current chat_id
                if 'chat_id' not in args:
                    args['chat_id'] = chat_id
                    
                req = CheckGenesysSessionRequest(**args)
                result = check_genesys_session(req, db=db)
                
                if result.success:
                    content = f"This chat is connected to a live agent support session. Your messages will be forwarded to the agent."
                else:
                    content = f"This chat is not currently connected to a live agent. Would you like me to connect you with a live agent?"
            except Exception as e:
                logger.error(f"Failed to invoke check_genesys_session: {e}")
                content = "[Failed to check Genesys session status]"
                
        elif function_name == "create_genesys_session":
            try:
                args = json.loads(tool_call.function.arguments)
                # If chat_id is not in args, use the current chat_id
                if 'chat_id' not in args:
                    args['chat_id'] = chat_id
                # If customer_id is not in args but we have user_email, use that
                if 'customer_id' not in args and user_email:
                    args['customer_id'] = user_email
                    
                req = CreateGenesysSessionRequest(**args)
                result = create_genesys_session(req, db=db)
                
                if result.success:
                    content = "You've been connected with a live agent support session. Your messages will be forwarded to the agent who will respond shortly."
                else:
                    content = "I wasn't able to connect you with a live agent at this time. Please try again later or let me help you with your question."
            except Exception as e:
                logger.error(f"Failed to invoke create_genesys_session: {e}")
                content = "[Failed to create Genesys session]"
                
        else:
            function_result = getattr(tool_call.function, "result", None)
            content = function_result or f"[Tool executed: {function_name}]"
    else:
        content = response_message.content or ""
        logger.info("Standard text response received")

    # Check again before adding message in case chat was closed after tool call
    if chat.status == "CLOSED":
        logger.info(f"Chat {chat_id} is closed after tool call. Skipping message creation.")
        return None

    # Create a new assistant message
    new_message = Message(
        chat_id=chat_id,
        content=content,
        is_system=True,
        is_markdown=is_markdown(content)
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Forward assistant response to Genesys if integration is active
    if GENESYS_DEPLOYMENT_ID and chat.genesys_open_message_active:
        needs_refresh = not chat.genesys_open_message_session_id
        ensure_genesys_session_id(chat, db)
        if needs_refresh:
            db.refresh(chat)
        try:
            # Send message to Genesys Open Messaging
            genesys_response = send_open_message(
                user_token=chat.genesys_open_message_session_id,
                message_content=content
            )
            # Update the message record to indicate it was sent to Genesys
            new_message.sent_to_genesys = True
            if hasattr(genesys_response, 'id'):
                new_message.genesys_message_id = genesys_response.id
            db.commit()
            logger.info(f"Assistant response sent to Genesys for chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send assistant response to Genesys: {e}")
            # Continue even if sending to Genesys fails

    logger.info(f"Successfully created new message for chat {chat_id}")
    return new_message
