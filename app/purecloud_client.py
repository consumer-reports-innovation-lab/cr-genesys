import os
import logging
import requests
from config import settings
import PureCloudPlatformClientV2

# Configure logging
logger = logging.getLogger(__name__)

# Env-based configuration
GENESYS_DEPLOYMENT_ID = settings.GENESYS_OPEN_MESSAGING_DEPLOYMENT_ID
GENESYS_REGION = "mypurecloud"  # Updated for mypurecloud.com region
BASE_URL = f"https://api.{GENESYS_REGION}.com"

def get_purecloud_client():
    """
    Authenticates with Genesys using client credentials and returns an authenticated ApiClient.
    """
    logger.info("🔍 DEBUG: Attempting Genesys OAuth authentication...")
    
    client_id = os.environ.get("GENESYS_CLOUD_CLIENT_ID")
    client_secret = os.environ.get("GENESYS_CLOUD_CLIENT_SECRET")
    
    logger.info(f"🔍 DEBUG: OAuth credentials - client_id: {'SET' if client_id else 'MISSING'}, client_secret: {'SET' if client_secret else 'MISSING'}")
    
    if not client_id or not client_secret:
        logger.error("❌ GENESYS: Missing OAuth credentials - GENESYS_CLOUD_CLIENT_ID or GENESYS_CLOUD_CLIENT_SECRET not set")
        raise ValueError("Missing Genesys OAuth credentials")
    
    logger.info(f"🚀 GENESYS: Authenticating with Genesys Cloud using client_id: {client_id[:8]}...")
    api_client = PureCloudPlatformClientV2.api_client.ApiClient()
    api_client.get_client_credentials_token(client_id, client_secret)
    logger.info("✅ GENESYS: OAuth authentication successful!")
    return api_client

def get_access_token():
    """
    Retrieves the OAuth access token for HTTP requests.
    """
    return get_purecloud_client().access_token

# === Open Messaging API Functions ===

def send_open_message(
    from_address: str,
    to_address: str,
    message_content: str,
    deployment_id: str = None,
    use_existing_conversation: bool = False
):
    """
    Sends an agentless outbound message via Genesys Open Messaging (agentless API).
    Uses /api/v2/conversations/messages/agentless endpoint.
    See: https://developer.genesys.cloud/commdigital/digital/openmessaging/outboundMessages

    Args:
        from_address (str): The sender address (e.g., business phone/email/ID)
        to_address (str): The recipient address (e.g., customer phone/email/ID)
        message_content (str): The message body
        deployment_id (str, optional): Open Messaging deployment ID. Defaults to global setting.
        use_existing_conversation (bool, optional): Attach to existing conversation if possible. Default False.

    Returns:
        dict: Response from Genesys API
    """
    deployment_id = deployment_id or GENESYS_DEPLOYMENT_ID
    access_token = get_access_token()
    # Try the standard agentless endpoint first
    url = f"{BASE_URL}/api/v2/conversations/messages/agentless"
    
    # Alternative endpoint to try if the first fails
    alt_url = f"{BASE_URL}/api/v2/conversations/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "fromAddress": from_address,
        "toAddress": to_address,
        "textBody": message_content,
        "messengerType": "open",
        "messenger_type": "open", # Try underscore version
        "MessengerType": "open",  # Try uppercase version
        "deploymentId": deployment_id,
        "useExistingConversation": use_existing_conversation
    }

    logger.info(f"🚀 GENESYS: Sending agentless Open Messaging message to {to_address}: {message_content[:50]}...")
    logger.info(f"🔍 DEBUG: OpenMessaging API URL: {url}")
    logger.info(f"🔍 DEBUG: Full JSON Payload: {payload}")
    logger.info(f"🔍 DEBUG: Request headers: {headers}")
    response = requests.post(url, headers=headers, json=payload)
    
    logger.info(f"🔍 DEBUG: Response status: {response.status_code}")
    logger.info(f"🔍 DEBUG: Response headers: {dict(response.headers)}")

    if response.status_code not in (200, 202):
        logger.error(f"Error sending agentless message: {response.status_code} - {response.text}")
        raise Exception(f"Send failed: {response.text}")

    return response.json() if response.content else {}

def list_open_messaging_deployments():
    """
    Lists all Open Messaging deployments in your Genesys org.
    """
    access_token = get_access_token()
    url = f"{BASE_URL}/api/v2/conversations/messaging/integrations"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Error listing deployments: {response.status_code} - {response.text}")
        raise Exception(f"List deployments failed: {response.text}")

    deployments = response.json().get("entities", [])
    return [d for d in deployments if d.get("messengerType") == "open"]

def create_open_messaging_deployment(name: str) -> str:
    """
    Creates a new Open Messaging deployment and returns its ID.
    """
    access_token = get_access_token()
    url = f"{BASE_URL}/api/v2/conversations/messaging/integrations/open"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "supportedContent": {
            "contentOffers": False
        },
        "messengerType": "open"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 201:
        logger.error(f"Error creating deployment: {response.status_code} - {response.text}")
        raise Exception(f"Create deployment failed: {response.text}")

    deployment_id = response.json().get("id")
    logger.info(f"Created Open Messaging deployment: {deployment_id}")
    return deployment_id


def get_permissions():
    """
    Uses SDK to retrieve Genesys platform permissions.
    """
    api_client = get_purecloud_client()
    auth_api = PureCloudPlatformClientV2.AuthorizationApi(api_client)
    return auth_api.get_authorization_permissions()

# === InboundMessageFlow Functions ===

def list_inbound_message_flows():
    """
    Lists all inbound message flows in your Genesys org.
    """
    access_token = get_access_token()
    url = f"{BASE_URL}/api/v2/flows"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "type": "inboundShortMessage",
        "pageSize": 100
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        logger.error(f"Error listing inbound message flows: {response.status_code} - {response.text}")
        raise Exception(f"List flows failed: {response.text}")
    
    flows = response.json().get("entities", [])
    return flows

def trigger_flow_action(conversation_id: str, action_data: dict):
    """
    Triggers a specific action within a Genesys flow.
    
    Args:
        conversation_id (str): The conversation ID
        action_data (dict): Data to send to the flow action
        
    Returns:
        dict: Response from Genesys API
    """
    access_token = get_access_token()
    url = f"{BASE_URL}/api/v2/conversations/messages/{conversation_id}/actions"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=action_data)
    
    if response.status_code not in (200, 202):
        logger.error(f"Error triggering flow action: {response.status_code} - {response.text}")
        raise Exception(f"Flow action failed: {response.text}")
    
    return response.json() if response.content else {}
