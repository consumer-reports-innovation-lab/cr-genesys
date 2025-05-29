import os
import logging
import requests
from config import settings
import PureCloudPlatformClientV2

# Configure logging
logger = logging.getLogger(__name__)

# Env-based configuration
GENESYS_DEPLOYMENT_ID = settings.GENESYS_OPEN_MESSAGING_DEPLOYMENT_ID
GENESYS_REGION = "us-east-1"  # Change this if you're using a different Genesys Cloud region
BASE_URL = f"https://api.{GENESYS_REGION}.pure.cloud"

def get_purecloud_client():
    """
    Authenticates with Genesys using client credentials and returns an authenticated ApiClient.
    """
    client_id = os.environ["GENESYS_CLOUD_CLIENT_ID"]
    client_secret = os.environ["GENESYS_CLOUD_CLIENT_SECRET"]
    api_client = PureCloudPlatformClientV2.api_client.ApiClient()
    api_client.get_client_credentials_token(client_id, client_secret)
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
    url = f"{BASE_URL}/api/v2/conversations/messages/agentless"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "fromAddress": from_address,
        "toAddress": to_address,
        "textBody": message_content,
        "deploymentId": deployment_id,
        "useExistingConversation": use_existing_conversation
    }

    logger.info(f"Sending agentless Open Messaging message: {message_content[:50]}...")
    response = requests.post(url, headers=headers, json=payload)

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
