import logging
import os
import uuid
import openai
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from instructor import patch
from models import Message, Chat, Memory
from utils.chat.get_chat_messages import get_chat_messages
from utils.adaptors.convert_messages_to_chat_history import convert_messages_to_chat_history
from utils.validators.is_markdown import is_markdown
from purecloud_client import send_open_message
from utils.chat.initialize_genesys_session import initialize_genesys_session


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patch OpenAI client to support instructor tools
client = patch(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

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


# === LLM Decision Tools ===

class MessageRoutingDecision(BaseModel):
    should_respond_to_user: bool = Field(..., description="Whether to respond directly to the user")
    should_send_to_genesys: bool = Field(..., description="Whether to send the message to Genesys")
    user_response: Optional[str] = Field(None, description="Response to send to the user if should_respond_to_user is True")
    genesys_message: Optional[str] = Field(None, description="Message to send to Genesys if should_send_to_genesys is True")
    explanation: str = Field(..., description="Brief explanation of the routing decision")

class GenesysResponseDecision(BaseModel):
    should_respond_to_genesys: bool = Field(..., description="Whether to respond directly to Genesys")
    should_ask_user: bool = Field(..., description="Whether to ask the user for more information")
    genesys_response: Optional[str] = Field(None, description="Response to send to Genesys if should_respond_to_genesys is True")
    user_question: Optional[str] = Field(None, description="Question to ask the user if should_ask_user is True")
    explanation: str = Field(..., description="Brief explanation of the response decision")

class CheckGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to check for an active Genesys session")

class CreateGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to create a Genesys session for")
    customer_id: Optional[str] = Field(None, description="Optional customer identifier")

class GenesysSessionResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    session_id: Optional[str] = Field(None, description="Session ID if successful")

def decide_message_routing(user_message: str, chat_history: list, db: Session, chat_id: str) -> MessageRoutingDecision:
    """
    Use LLM to decide how to route a user message - respond directly, send to Genesys, or both.
    """
    # Get chat context to understand if Genesys session is active
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    has_genesys_session = chat and chat.genesys_open_message_active and chat.genesys_open_message_session_id
    
    system_prompt = f"""You are an intelligent message router for Consumer Reports customer support. Your job is to decide how to handle incoming user messages.

Context:
- Genesys session active: {has_genesys_session}
- You can either respond directly to the user, send a message to Genesys (live agent), or do both
- You should send to Genesys for: complex issues, billing questions, refunds, technical problems requiring human intervention
- You should respond directly for: simple questions, general information, FAQs, greetings
- You can do both when: starting a Genesys conversation (inform user you're connecting them), or providing immediate help while escalating

CRITICAL: When sending to Genesys, you must speak AS THE CUSTOMER, not as an agent or intermediary. Write the message exactly as the customer would say it to the live agent. Be direct, natural, and authentic. 

When Genesys asks for specific information, provide ONLY that information requested:
- For vendor name: just the vendor name (e.g., "Amazon")
- For account ID: just the account ID (e.g., "12345678")
- For confirmations: just "yes" or "no"
- For phone numbers: just the number (e.g., "555-123-4567")
- For names: just the name requested
- For any specific detail: provide only that detail without extra explanation

Decision guidelines:
1. If user explicitly asks for "human", "agent", "representative" -> send to Genesys + inform user
2. For complex technical issues, billing, or complaints -> send to Genesys + optionally inform user  
3. For simple greetings, basic info, FAQ-type questions -> respond directly
4. For end-of-conversation responses (user says "that's all", "no thanks", etc.) when Genesys session active -> send to Genesys (closing message) + provide summary to user
5. If uncertain -> respond directly with helpful info but offer to connect to agent

You must respond with a JSON object containing these exact fields:
- should_respond_to_user: boolean (required)
- should_send_to_genesys: boolean (required) 
- explanation: string (required)
- user_response: string or null (optional)
- genesys_message: string or null (optional)

Examples:
{{"should_respond_to_user": true, "should_send_to_genesys": false, "explanation": "Simple greeting", "user_response": "Hi! How can I help you today?", "genesys_message": null}}

{{"should_respond_to_user": true, "should_send_to_genesys": true, "explanation": "User requested human agent", "user_response": "I'm contacting customer support for you.", "genesys_message": "Hi, I need help with my account and would like to speak with someone"}}

{{"should_respond_to_user": false, "should_send_to_genesys": true, "explanation": "Billing complaint needs agent", "user_response": null, "genesys_message": "I was charged twice for my subscription this month and need this fixed. Can you help me get a refund for the duplicate charge?"}}

{{"should_respond_to_user": true, "should_send_to_genesys": true, "explanation": "User ending conversation", "user_response": "Your customer service session is now complete. Here's a summary of what was accomplished: [provide brief summary based on chat history]", "genesys_message": "that's all I needed, thank you"}}

Note: When Genesys later asks for specific details like vendor name or account ID, respond with only that information (e.g., "Amazon" or "12345678").

Respond only with valid JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *chat_history[-5:],  # Include recent context
                {"role": "user", "content": f"User message to route: {user_message}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        import json
        decision_data = json.loads(response.choices[0].message.content)
        return MessageRoutingDecision(**decision_data)
        
    except Exception as e:
        logger.error(f"Error in message routing decision: {e}")
        # Default fallback: respond directly to user
        return MessageRoutingDecision(
            should_respond_to_user=True,
            should_send_to_genesys=False,
            user_response="I understand you're looking for help. Let me assist you with that.",
            explanation="Fallback decision due to routing error"
        )

def decide_genesys_response(genesys_message: str, chat_history: list, user_context: str = None) -> GenesysResponseDecision:
    """
    Use LLM to decide how to respond to a Genesys message - respond directly to Genesys or ask user for info.
    """
    system_prompt = """You are responding to a Genesys customer service agent on behalf of a customer. A message has come from the agent, and you need to decide how to handle it.

You can either:
1. Respond directly to Genesys AS THE CUSTOMER if you have enough information from the conversation context
2. Ask the user for more information if Genesys needs specific details you don't have

CRITICAL: When responding to Genesys, speak AS THE CUSTOMER directly. Use natural, authentic customer language. 

When the agent asks for specific information, provide ONLY what they requested:
- For vendor name: just the vendor name (e.g., "Amazon")
- For account ID: just the account ID (e.g., "12345678") 
- For confirmations: just "yes" or "no"
- For phone numbers: just the number (e.g., "555-123-4567")
- For names: just the name requested
- For email: just the email address
- For any specific detail: provide only that detail without additional context or explanation

Decision guidelines:
- Respond directly to Genesys for: confirmations, acknowledgments, providing info you have from chat history, simple yes/no answers
- Ask user for info when: Genesys requests specific personal details, account numbers, preferences, or decisions only the customer can provide
- For agent asking "anything else?", "is that all?", etc.: respond "no" or "no thank you" to Genesys AND provide summary to user
- For agent farewell messages ("thanks and have a great day", "we're all set", etc.): do NOT respond to Genesys, just provide summary to user
- Always be helpful and maintain the conversation flow

Consider the conversation context and determine the best approach.

You must respond with a JSON object containing these exact fields:
- should_respond_to_genesys: boolean (required)
- should_ask_user: boolean (required) 
- explanation: string (required)
- genesys_response: string or null (optional)
- user_question: string or null (optional)

Examples:
- Agent asks "Can you confirm your email?" and you have it: {{"should_respond_to_genesys": true, "should_ask_user": false, "explanation": "Have email from context", "genesys_response": "user@example.com", "user_question": null}}
- Agent asks "What's your account ID?" and you have it: {{"should_respond_to_genesys": true, "should_ask_user": false, "explanation": "Have account ID from context", "genesys_response": "12345678", "user_question": null}}
- Agent asks "Is this correct?" about something you can verify: {{"should_respond_to_genesys": true, "should_ask_user": false, "explanation": "Can confirm from context", "genesys_response": "yes", "user_question": null}}
- Agent asks "Is there anything else I can help you with?": {{"should_respond_to_genesys": true, "should_ask_user": true, "explanation": "Agent asking for more needs", "genesys_response": "no thank you", "user_question": "Your customer service session is complete. Let me provide you with a summary of what was accomplished."}}
- Agent says "We successfully collected your feedback. Thanks and have a great day.": {{"should_respond_to_genesys": false, "should_ask_user": true, "explanation": "Agent farewell message", "genesys_response": null, "user_question": "Your customer service session is complete. Let me provide you with a summary of what was accomplished."}}
- Agent asks "Would you like a refund?" - only customer can decide: {{"should_respond_to_genesys": false, "should_ask_user": true, "explanation": "Customer decision needed", "genesys_response": null, "user_question": "The agent is asking if you'd like a refund for this issue. What would you prefer?"}}

Respond only with valid JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                *chat_history[-5:],  # Include recent context
                {"role": "user", "content": f"Genesys agent message: {genesys_message}\nUser context: {user_context or 'None available'}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        import json
        decision_data = json.loads(response.choices[0].message.content)
        return GenesysResponseDecision(**decision_data)
        
    except Exception as e:
        logger.error(f"Error in Genesys response decision: {e}")
        # Default fallback: ask user
        return GenesysResponseDecision(
            should_respond_to_genesys=False,
            should_ask_user=True,
            user_question=f"The agent says: {genesys_message}\n\nHow would you like me to respond?",
            explanation="Fallback decision due to response error"
        )

# === Genesys Open Messaging Tools ===

class CheckGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to check for an active Genesys session")

class CreateGenesysSessionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID to create a Genesys session for")
    customer_id: Optional[str] = Field(None, description="Optional customer identifier")

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

# class FeedbackEmailRequest(BaseModel):
#     chat_id: str = Field(..., description="Chat ID to update after feedback is submitted")
#     message_body: str = Field(
#         ..., 
#         max_length=1000, 
#         description="Feedback content to send to support (max 1000 characters)"
#     )

# class FeedbackResponse(BaseModel):
#     message: str

# # Send feedback via SMTP with Mailchimp Transactional, from the user's reply_to address
# def send_feedback_email(data: FeedbackEmailRequest, db: Session, user_email: str = None) -> FeedbackResponse:
#     recipient = "feedbackroute@consumerreports.mypurecloud.com"
#     subject   = "User Feedback Submission"
#     sender_email = "jamal.jackson.consultant@consumer.org"
#     reply_to  = "jamal.jackson.consultant@consumer.org" or user_email or "noreply@yourdomain.com"
#     preview   = data.message_body.strip().replace("\n", " ")[:50]

#     # Create message
#     message = MIMEMultipart("alternative")
#     message["Subject"] = subject
#     message["From"] = sender_email
#     message["To"] = recipient
#     message["Reply-To"] = sender_email

#     # Add text content
#     text_content = data.message_body
#     part1 = MIMEText(text_content, "plain")
#     message.attach(part1)

#     # Add HTML content
#     html_content = f"<p>{data.message_body}</p>"
#     part2 = MIMEText(html_content, "html")
#     message.attach(part2)

#     try:
#         logger.info(f"Sending feedback email via SMTP to {recipient} from {sender_email}")
#         server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
#         server.starttls()  # Secure the connection
#         server.login(SMTP_USERNAME, MAILCHIMP_API_KEY)
#         server.sendmail(sender_email, recipient, message.as_string())
#         server.quit()
#         logger.info("Email sent successfully!")
#     except Exception as e:
#         logger.error(f"SMTP email failed: {e}")
#         raise RuntimeError("Failed to send feedback email")

#     # Log assistant confirmation message (system message)
#     confirmation_msg = Message(
#         chat_id=data.chat_id,
#         content="Your feedback has been sent.",
#         is_system=True,
#         is_markdown=False
#     )
#     db.add(confirmation_msg)

#     # Set chat status to CLOSED
#     chat = db.query(Chat).filter(Chat.id == data.chat_id).first()
#     if chat:
#         chat.status = "CLOSED"
#         logger.info(f"Chat {data.chat_id} marked as CLOSED.")

#     db.commit()
#     db.refresh(confirmation_msg)

#     return FeedbackResponse(message=f'Feedback submitted: "{preview}"...')

# # Prepare the tool schema for send_feedback_email
# SEND_FEEDBACK_EMAIL_SCHEMA = {
#     "type": "function",
#     "function": {
#         "name": "send_feedback_email",
#         "description": "Sends feedback provided by the user via email to the support team.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "message_body": {
#                     "type": "string",
#                     "description": "Feedback content to send to support (max 1000 characters)",
#                 }
#             },
#             "required": ["message_body"]
#         }
#     }
# }


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

def extract_memory_from_message(user_message: str, chat_history: list) -> Optional[str]:
    """
    Use LLM to extract potential memories from user messages.
    Returns the memory content if found, None otherwise.
    """
    system_prompt = """You are an intelligent memory extraction system for customer support conversations. Your job is to identify and extract important information that should be remembered for future reference.

Extract memories for:
- User information (names, contact details, preferences)
- Vendor names and companies the user mentions
- Part numbers, model numbers, product names
- Account information
- Important facts about the user's situation or context

DO NOT extract:
- General questions or requests for help
- Temporary conversation context
- Simple acknowledgments or greetings

When you extract a memory, format it as a clear, factual statement. Examples:
- "SharkNinja is a vendor that the user wants to give feedback to"
- "User's account ID is 12345678"
- "User prefers email communication over phone calls"
- "Product model number is XYZ-123"

If no important information should be remembered, respond with exactly: "NO_MEMORY"

User message: "{user_message}"

What memory, if any, should be extracted from this message?"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt.format(user_message=user_message)},
                *chat_history[-5:],  # Include last 5 messages for context
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        memory_content = response.choices[0].message.content.strip()
        
        if memory_content and memory_content != "NO_MEMORY":
            logger.info(f"🧠 MEMORY: Extracted memory: {memory_content}")
            return memory_content
        else:
            logger.info("🧠 MEMORY: No memory to extract from this message")
            return None
            
    except Exception as e:
        logger.error(f"🧠 MEMORY: Error extracting memory: {e}")
        return None

def get_chat_memories(db: Session, chat_id: str) -> list:
    """
    Retrieve all memories for a specific chat.
    Returns a list of memory content strings.
    """
    try:
        memories = db.query(Memory).filter(Memory.chat_id == chat_id).order_by(Memory.created_at.asc()).all()
        return [memory.content for memory in memories]
    except Exception as e:
        logger.error(f"🧠 MEMORY: Error retrieving memories: {e}")
        return []

async def generate_chat_message(
    db: Session, 
    chat_id: str, 
    system_prompt: str, 
    question: str, 
    user_email: str = None
) -> Message:
    logger.info(f"Generating response for chat_id: {chat_id}, question: {question}")
    logger.info(f"🔍 DEBUG: user_email={user_email}")

    # Import sio here to avoid circular imports
    from sockets.handlers import get_sio
    sio = get_sio()

    # Save the user's question as a Message (never sent to Genesys directly)
    user_message = Message(
        chat_id=chat_id,
        content=question,
        is_system=False,
        is_markdown=False,
        sent_to_genesys=False  # User messages are never sent directly to Genesys
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Extract memory from the user message using LLM (in separate transaction to avoid conflicts)
    try:
        # Get current chat history for context
        messages = get_chat_messages(db, chat_id)
        chat_history = convert_messages_to_chat_history(messages)
        
        memory_content = extract_memory_from_message(question, chat_history)
        
        if memory_content:
            # Use a separate database session for memory operations to avoid transaction conflicts
            from utils.db import get_db
            memory_db = next(get_db())
            try:
                # Save the extracted memory to the database
                memory = Memory(
                    chat_id=chat_id,
                    content=memory_content
                )
                memory_db.add(memory)
                memory_db.commit()
                logger.info(f"🧠 MEMORY: Saved memory for chat {chat_id}: {memory_content}")
            except Exception as memory_error:
                memory_db.rollback()
                logger.error(f"🧠 MEMORY: Error saving memory to database: {memory_error}")
                raise memory_error
            finally:
                memory_db.close()
            
    except Exception as e:
        logger.error(f"🧠 MEMORY: Error processing memory extraction: {e}")
        # Don't fail the entire message processing if memory extraction fails
    
    # Emit the user message
    if sio:
        user_socket_message = {
            'id': str(user_message.id),
            'content': user_message.content,
            'chatId': chat_id,
            'isSystem': False,
            'isMarkdown': False,
            'sentToGenesys': False,
            'genesysMessageId': None,
            'createdAt': user_message.created_at.isoformat(),
            'updatedAt': user_message.updated_at.isoformat()
        }
        await sio.emit('new_message', user_socket_message, room=chat_id)
    
    # Get the chat object
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logger.error(f"Chat {chat_id} not found")
        raise ValueError(f"Chat {chat_id} not found")

    # Get current chat history for LLM decision making
    messages = get_chat_messages(db, chat_id)
    chat_history = convert_messages_to_chat_history(messages)

    # Use LLM to decide how to route this message
    logger.info("🤖 ROUTING: Using LLM to decide message routing...")
    routing_decision = decide_message_routing(question, chat_history, db, chat_id)
    logger.info(f"🤖 ROUTING DECISION: should_respond_to_user={routing_decision.should_respond_to_user}, should_send_to_genesys={routing_decision.should_send_to_genesys}")
    logger.info(f"🤖 ROUTING EXPLANATION: {routing_decision.explanation}")

    # Handle sending LLM-generated message to Genesys if decided
    if routing_decision.should_send_to_genesys and routing_decision.genesys_message:
        logger.info("✅ GENESYS: LLM decided to send a message to Genesys")
        ensure_genesys_session_id(chat, db)
        
        try:
            # Construct address for Genesys Open Messaging
            to_address = None
            if user_email and '@' in user_email:
                local_part, domain = user_email.split('@', 1)
                to_address = f"{local_part}+{chat_id}@{domain}"
                logger.info(f"✅ GENESYS: Constructed to_address='{to_address}'")
            else:
                logger.warning(f"❌ GENESYS: Cannot construct to_address - user_email is invalid or missing")
            
            if to_address:
                # Send the LLM-generated message to Genesys
                message_to_send = routing_decision.genesys_message
                logger.info(f"🚀 GENESYS: Sending LLM-generated message to OpenMessaging API: {message_to_send[:50]}...")
                
                genesys_response = send_open_message(
                    to_address=to_address,
                    message_content=message_to_send
                )
                
                # Create a separate message record for the LLM's message to Genesys
                genesys_message = Message(
                    chat_id=chat_id,
                    content=message_to_send,
                    is_system=True,
                    is_markdown=is_markdown(message_to_send),
                    sent_to_genesys=True,
                    genesys_message_id=getattr(genesys_response, 'id', None)
                )
                db.add(genesys_message)
                db.commit()
                db.refresh(genesys_message)
                
                # Emit the LLM's message to Genesys to the chat
                if sio:
                    genesys_socket_message = {
                        'id': str(genesys_message.id),
                        'content': genesys_message.content,
                        'chatId': chat_id,
                        'isSystem': True,
                        'isMarkdown': genesys_message.is_markdown,
                        'sentToGenesys': True,
                        'genesysMessageId': getattr(genesys_response, 'id', None),
                        'createdAt': genesys_message.created_at.isoformat(),
                        'updatedAt': genesys_message.updated_at.isoformat()
                    }
                    await sio.emit('new_message', genesys_socket_message, room=chat_id)
                
                logger.info(f"✅ GENESYS: LLM message sent successfully to Genesys for chat {chat_id}")
            else:
                logger.warning(f"❌ GENESYS: Cannot send to Genesys: user_email not provided or invalid for chat {chat_id}")
        except Exception as e:
            logger.error(f"❌ GENESYS: Failed to send message to Genesys: {e}")
            # Continue with user response even if Genesys fails
            routing_decision.should_respond_to_user = True
    elif routing_decision.should_send_to_genesys:
        logger.warning(f"🔄 GENESYS: LLM decided to send to Genesys but no genesys_message provided")
    else:
        logger.info(f"🔄 GENESYS: LLM decided not to send anything to Genesys")

    # Handle user response if decided
    if not routing_decision.should_respond_to_user:
        logger.info("🔄 RESPONSE: LLM decided not to respond to user, message forwarded to Genesys only")
        return user_message

    # Generate user response if LLM decided to respond to user
    logger.info("🤖 RESPONSE: Generating response to user...")
    
    # Use LLM's suggested response if available, otherwise generate one
    if routing_decision.user_response:
        content = routing_decision.user_response
        logger.info("🤖 Using LLM's pre-generated user response")
    else:
        # Generate response using OpenAI with tools
        system_tool_hint = {
            "role": "system",
            "content": (
                "When users provide feedback, complaints, or suggestions, acknowledge their input and "
                "let them know their feedback will be processed. For example: "
                "'Thank you for your feedback. I've received your message and it will be reviewed by our team.'\n\n"
                "Focus on being helpful and responsive to their immediate needs."
            )
        }

        try:
            # Load memories for this chat to include in the response context
            memories = get_chat_memories(db, chat_id)
            memory_context = ""
            if memories:
                memory_context = "\n\nRemembered information about this conversation:\n" + "\n".join([f"- {memory}" for memory in memories])
                logger.info(f"🧠 MEMORY: Including {len(memories)} memories in response context")
            
            # Create system message with memory context
            enhanced_system_prompt = system_prompt + memory_context
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    system_tool_hint,
                    *chat_history,
                    {"role": "user", "content": question}
                ],
                tools=[
                    DUMMY_TOOL_SCHEMA, 
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
                    
            if function_name == "check_genesys_session":
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
        is_markdown=is_markdown(content),
        sent_to_genesys=False  # This is a response to the user, not sent to Genesys
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Emit the system response
    if sio:
        system_socket_message = {
            'id': str(new_message.id),
            'content': new_message.content,
            'chatId': chat_id,
            'isSystem': True,
            'isMarkdown': new_message.is_markdown,
            'sentToGenesys': False,
            'genesysMessageId': None,
            'createdAt': new_message.created_at.isoformat(),
            'updatedAt': new_message.updated_at.isoformat()
        }
        await sio.emit('new_message', system_socket_message, room=chat_id)
    
    logger.info(f"Successfully created new message for chat {chat_id}")
    return new_message
