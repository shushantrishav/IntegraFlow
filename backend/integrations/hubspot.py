import os
import json
import secrets
import asyncio
import hashlib
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from dotenv import load_dotenv
from urllib.parse import unquote
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from logger import logger

load_dotenv()

CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")
SCOPES = os.getenv("HUBSPOT_SCOPES")
AUTH_URL = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES.replace(" ", "%20")}'


async def authorize_hubspot(user_id, org_id):
    logger.info(
        f"[HubSpot] Starting authorization for user='{user_id}', org='{org_id}'"
    )
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(
        f"hubspot_state:{org_id}:{user_id}", encoded_state, expire=600
    )
    logger.debug(f"[HubSpot] Saved state in Redis for user='{user_id}'")

    return f"{AUTH_URL}&state={encoded_state}"

from urllib.parse import unquote

async def oauth2callback_hubspot(request: Request):
    logger.info("[HubSpot] OAuth2 callback received")
    if request.query_params.get("error"):
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description", "Unknown error during authorization.")
        logger.error(f"[HubSpot] OAuth error: {error} | Description: {error_description}")
        raise HTTPException(status_code=400, detail=f"HubSpot OAuth error: {error_description}")

    try:
        code = request.query_params.get("code")
        encoded_state = request.query_params.get("state")
        
        # Log the encoded state to check if it's correct
        logger.debug(f"[HubSpot] Encoded state: {encoded_state}")

        # URL-decode the state parameter before parsing
        decoded_state = unquote(encoded_state)

        # Replace any '+' with spaces (URL decoding issue) and log the decoded state
        decoded_state = decoded_state.replace('+', ' ')
        
        # Log the decoded state to check if it's properly decoded
        logger.debug(f"[HubSpot] Decoded state: {decoded_state}")

        state_data = json.loads(decoded_state)

        original_state = state_data.get("state")
        user_id = state_data.get("user_id")
        org_id = state_data.get("org_id")

        # Validate the state against what was saved in Redis
        saved_state = await get_value_redis(f"hubspot_state:{org_id}:{user_id}")
        if not saved_state or original_state != json.loads(saved_state).get("state"):
            logger.warning(f"[HubSpot] OAuth2 state mismatch for user='{user_id}', org='{org_id}'")
            raise HTTPException(status_code=400, detail="State validation failed.")

        logger.info(f"[HubSpot] State validated for user='{user_id}', requesting token")

        # Fetch the token now
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error(f"[HubSpot] Token exchange failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to exchange authorization code.")

        credentials = response.json()

        # Save the credentials to Redis
        await add_key_value_redis(
            f"hubspot_credentials:{org_id}:{user_id}",
            json.dumps(credentials),
            expire=600,
        )
        logger.info(f"[HubSpot] Token exchange successful for user='{user_id}'")

        return HTMLResponse(content="<html><script>window.close();</script></html>")

    except Exception as e:
        logger.exception("[HubSpot] Unexpected error during OAuth callback")
        raise HTTPException(status_code=500, detail="OAuth callback failed.")


async def get_hubspot_credentials(user_id, org_id):
    logger.info(
        f"[HubSpot] Retrieving credentials for user='{user_id}', org='{org_id}'"
    )
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        logger.warning(f"[HubSpot] No credentials found in Redis for user='{user_id}'")
        raise HTTPException(status_code=400, detail="No credentials found.")

    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")
    logger.debug(f"[HubSpot] Deleted credentials from Redis for user='{user_id}'")
    return json.loads(credentials)


async def create_integration_item_metadata_object(response_json):
    properties = response_json.get("properties", {})
    return IntegrationItem(
        id=response_json.get("id"),
        type="HubSpot_Contact",
        name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
        creation_time=properties.get("createdAt"),
        email=properties.get("email"),
        phone_number=properties.get("phone"),
        company_name=properties.get("company"),
        employment_role=properties.get("jobtitle"),
        lead_status=properties.get("hs_lead_status"),
    )

async def get_items_hubspot(credentials) -> list[dict]:
    logger.info("[HubSpot] Loading contact list")
    try:
        credentials = json.loads(credentials)
        access_token = credentials.get("access_token")

        # Hash token to use as Redis key
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        redis_key = f"hubspot_items_cache:{token_hash}"

        # Check cache
        cached = await get_value_redis(redis_key)
        if cached:
            logger.info("[HubSpot] Retrieving cached contacts from Redis")
            return json.loads(cached)

        # Fetch from HubSpot API
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        params = {
            "limit": 100,
            "properties": "firstname,lastname,email,phone,company,jobtitle,hs_lead_status,createdAt",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(f"[HubSpot] Contact fetch failed: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch HubSpot contacts",
            )

        contacts = response.json().get("results", [])
        items = [
            await create_integration_item_metadata_object(contact)
            for contact in contacts
        ]
        items_cleaned = [item.to_clean_dict() for item in items]

        # Cache result for 5 mins
        await add_key_value_redis(redis_key, json.dumps(items_cleaned), expire=300)
        logger.info(f"[HubSpot] Retrieved and cached {len(items_cleaned)} contacts")
        return items_cleaned

    except Exception as e:
        logger.exception("[HubSpot] Unexpected error while fetching contacts")
        raise HTTPException(status_code=500, detail="HubSpot data fetch failed.")
