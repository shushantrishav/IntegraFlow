# backend/integrations/notion.py

import json
import secrets
import asyncio
import base64
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import requests
import hashlib
from urllib.parse import quote
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from logger import logger
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI")

encoded_client_id_secret = base64.b64encode(
    f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
).decode()
encoded_redirect_uri = quote(REDIRECT_URI, safe="")

authorization_url = (
    f"https://api.notion.com/v1/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&owner=user"
    f"&redirect_uri={encoded_redirect_uri}"
)


async def authorize_notion(user_id, org_id):
    logger.info(f"[Notion] Starting authorization for user='{user_id}', org='{org_id}'")
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(
        f"notion_state:{org_id}:{user_id}", encoded_state, expire=600
    )
    logger.debug(f"[Notion] Saved state in Redis for user='{user_id}'")
    return f"{authorization_url}&state={encoded_state}"


async def oauth2callback_notion(request: Request):
    logger.info("[Notion] OAuth2 callback received")
    if request.query_params.get("error"):
        error = request.query_params.get("error")
        logger.error(
            f"[Notion] OAuth error: {error} | Full query: {request.query_params}"
        )
        raise HTTPException(status_code=400, detail=error)

    try:
        code = request.query_params.get("code")
        encoded_state = request.query_params.get("state")
        state_data = json.loads(encoded_state)

        original_state = state_data.get("state")
        user_id = state_data.get("user_id")
        org_id = state_data.get("org_id")

        saved_state = await get_value_redis(f"notion_state:{org_id}:{user_id}")
        if not saved_state or original_state != json.loads(saved_state).get("state"):
            logger.warning(
                f"[Notion] OAuth2 state mismatch for user='{user_id}', org='{org_id}'"
            )
            raise HTTPException(status_code=400, detail="State validation failed.")

        logger.info(f"[Notion] State validated for user='{user_id}', requesting token")

        async with httpx.AsyncClient() as client:
            response, _ = await asyncio.gather(
                client.post(
                    "https://api.notion.com/v1/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                    },
                    headers={
                        "Authorization": f"Basic {encoded_client_id_secret}",
                        "Content-Type": "application/json",
                    },
                ),
                delete_key_redis(f"notion_state:{org_id}:{user_id}"),
            )

        if response.status_code != 200:
            logger.error(
                f"[Notion] Token exchange failed: {response.status_code} - {response.text}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to exchange authorization code.",
            )

        await add_key_value_redis(
            f"notion_credentials:{org_id}:{user_id}",
            json.dumps(response.json()),
            expire=600,
        )
        logger.info(f"[Notion] Token exchange successful for user='{user_id}'")
        return HTMLResponse(content="<html><script>window.close();</script></html>")

    except Exception as e:
        logger.exception("[Notion] Unexpected error during OAuth callback")
        raise HTTPException(status_code=500, detail="OAuth callback failed.")


async def get_notion_credentials(user_id, org_id):
    logger.info(f"[Notion] Retrieving credentials for user='{user_id}', org='{org_id}'")
    credentials = await get_value_redis(f"notion_credentials:{org_id}:{user_id}")
    if not credentials:
        logger.warning(f"[Notion] No credentials found for user='{user_id}'")
        raise HTTPException(status_code=400, detail="No credentials found.")

    await delete_key_redis(f"notion_credentials:{org_id}:{user_id}")
    logger.debug(f"[Notion] Deleted credentials from Redis for user='{user_id}'")
    return json.loads(credentials)


def _recursive_dict_search(data, target_key):
    if target_key in data:
        return data[target_key]

    for value in data.values():
        if isinstance(value, dict):
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None


async def create_integration_item_metadata_object(
    response_json: dict,
) -> IntegrationItem:
    properties = response_json.get("properties", {})

    def get_plain_text(field):
        val = properties.get(field, {})
        if "rich_text" in val:
            return val["rich_text"][0].get("plain_text") if val["rich_text"] else None
        return None

    def get_title(field):
        val = properties.get(field, {})
        if "title" in val:
            return val["title"][0].get("plain_text") if val["title"] else None
        return None

    def get_phone(field):
        return properties.get(field, {}).get("phone_number")

    def get_email(field):
        return properties.get(field, {}).get("email")

    def extract_plain_text(obj):
        if isinstance(obj, dict):
            if "plain_text" in obj:
                return obj["plain_text"]
            if "name" in obj:
                return obj["name"]
            return json.dumps(obj)
        elif isinstance(obj, list):
            return ", ".join(filter(None, [extract_plain_text(i) for i in obj]))
        return str(obj) if obj is not None else ""

    # Extract fields
    id = str(response_json.get("id"))
    name = extract_plain_text(get_title("Name") or "Untitled")
    email = extract_plain_text(get_email("Email"))
    phone_number = extract_plain_text(get_phone("Contact Number"))
    location = extract_plain_text(get_plain_text("City/Country"))
    creation_time = response_json.get("created_time")

    # Skip invalid rows
    if not all([id, name, email, phone_number, location, creation_time]):
        return None

    return IntegrationItem(
        id=id,
        type="Notion_Companies",
        name=name,
        creation_time=creation_time,
        email=email,
        phone_number=phone_number,
        location=location,
    )


async def get_items_notion(credentials) -> list[dict]:
    logger.info("[Notion] Fetching integration items")

    try:
        credentials = json.loads(credentials)
        access_token = credentials.get("access_token")

        # Hash token to use as Redis key
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        redis_key = f"notion_items_cache:{token_hash}"

        # Check cache
        cached = await get_value_redis(redis_key)
        if cached:
            logger.info("[Notion] Retrieving cached item from redis")
            return json.loads(cached)

        # Fetch from Notion API
        response = requests.post(
            "https://api.notion.com/v1/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28",
            },
        )

        if response.status_code != 200:
            logger.error(
                f"[Notion] Search API failed: {response.status_code} - {response.text}"
            )
            raise HTTPException(
                status_code=response.status_code, detail="Failed to fetch Notion data."
            )

        results = response.json().get("results", [])
        items_raw = await asyncio.gather(
            *[create_integration_item_metadata_object(r) for r in results]
        )
        items = [item.to_clean_dict() for item in items_raw if item]

        # Cache result for 5 mins
        await add_key_value_redis(redis_key, json.dumps(items), expire=300)
        logger.info(f"[Notion] Retrieved and cached {len(items)} items")

        return items

    except Exception as e:
        logger.exception("[Notion] Unexpected error while fetching items")
        raise HTTPException(status_code=500, detail="Notion data fetch failed.")
