# backend/integrations/airtable.py
import os
import datetime
import json
import secrets
import base64
import hashlib
import asyncio
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import requests
from dotenv import load_dotenv
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from logger import logger

load_dotenv()

CLIENT_ID = os.getenv("AIRTABLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AIRTABLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("AIRTABLE_REDIRECT_URI")

authorization_url = (
    f"https://airtable.com/oauth2/v1/authorize"
    f"?client_id={CLIENT_ID}&response_type=code"
    f"&owner=user&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fintegrations%2Fairtable%2Foauth2callback"
)
encoded_client_id_secret = base64.b64encode(
    f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
).decode()
scope = "data.records:read data.records:write data.recordComments:read data.recordComments:write schema.bases:read schema.bases:write"


async def authorize_airtable(user_id, org_id):
    logger.info(
        f"[Airtable] Starting authorization for user='{user_id}', org='{org_id}'"
    )
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode())
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode().replace("=", "")

    auth_url = f"{authorization_url}&state={encoded_state}&code_challenge={code_challenge}&code_challenge_method=S256&scope={scope}"

    await asyncio.gather(
        add_key_value_redis(
            f"airtable_state:{org_id}:{user_id}", json.dumps(state_data), expire=600
        ),
        add_key_value_redis(
            f"airtable_verifier:{org_id}:{user_id}", code_verifier, expire=600
        ),
    )
    logger.debug(
        f"[Airtable] Saved state and code_verifier in Redis for user='{user_id}'"
    )
    return auth_url


async def oauth2callback_airtable(request: Request):
    logger.info("[Airtable] OAuth2 callback received")

    if request.query_params.get("error"):
        error_description = request.query_params.get(
            "error_description", "Unknown error"
        )
        logger.error(f"[Airtable] OAuth error: {error_description}")
        raise HTTPException(status_code=400, detail=error_description)

    try:
        code = request.query_params.get("code")
        encoded_state = request.query_params.get("state")
        state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode())

        user_id = state_data.get("user_id")
        org_id = state_data.get("org_id")
        original_state = state_data.get("state")

        saved_state, code_verifier = await asyncio.gather(
            get_value_redis(f"airtable_state:{org_id}:{user_id}"),
            get_value_redis(f"airtable_verifier:{org_id}:{user_id}"),
        )

        if not saved_state or original_state != json.loads(saved_state).get("state"):
            logger.warning(f"[Airtable] OAuth2 state mismatch for user='{user_id}'")
            raise HTTPException(status_code=400, detail="State does not match.")

        logger.info(
            f"[Airtable] State validated, requesting token for user='{user_id}'"
        )

        async with httpx.AsyncClient() as client:
            response, _, _ = await asyncio.gather(
                client.post(
                    "https://airtable.com/oauth2/v1/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                        "client_id": CLIENT_ID,
                        "code_verifier": code_verifier.decode(),
                    },
                    headers={
                        "Authorization": f"Basic {encoded_client_id_secret}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                ),
                delete_key_redis(f"airtable_state:{org_id}:{user_id}"),
                delete_key_redis(f"airtable_verifier:{org_id}:{user_id}"),
            )

        await add_key_value_redis(
            f"airtable_credentials:{org_id}:{user_id}",
            json.dumps(response.json()),
            expire=600,
        )
        logger.info(f"[Airtable] Token exchange successful for user='{user_id}'")

        return HTMLResponse(content="<html><script>window.close();</script></html>")

    except Exception:
        logger.exception("[Airtable] Unexpected error during OAuth callback")
        raise HTTPException(status_code=500, detail="OAuth callback failed.")


async def get_airtable_credentials(user_id, org_id):
    logger.info(
        f"[Airtable] Retrieving credentials for user='{user_id}', org='{org_id}'"
    )
    credentials = await get_value_redis(f"airtable_credentials:{org_id}:{user_id}")
    if not credentials:
        logger.warning(f"[Airtable] No credentials found for user='{user_id}'")
        raise HTTPException(status_code=400, detail="No credentials found.")
    await delete_key_redis(f"airtable_credentials:{org_id}:{user_id}")
    logger.debug(f"[Airtable] Deleted credentials from Redis for user='{user_id}'")
    return json.loads(credentials)


def create_integration_item_metadata_object(
    response_json, item_type, parent_id=None, parent_name=None
) -> IntegrationItem:
    parent_id = None if parent_id is None else parent_id + "_Base"
    return IntegrationItem(
        id=response_json.get("id", "") + "_" + item_type,
        name=response_json.get("name"),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )


def fetch_items(access_token, url, aggregated_response: list, offset=None):
    params = {"offset": offset} if offset else {}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json().get("bases", [])
        offset = response.json().get("offset")

        aggregated_response.extend(results)

        if offset:
            fetch_items(access_token, url, aggregated_response, offset)
    else:
        logger.error(
            f"[Airtable] Failed to fetch bases: {response.status_code} - {response.text}"
        )


async def get_items_airtable(credentials) -> list[dict]:
    logger.info("[Airtable] Fetching integration items")
    try:
        credentials = json.loads(credentials)
        access_token = credentials.get("access_token")

        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        redis_key = f"airtable_items_cache:{token_hash}"

        # Check Redis cache
        cached = await get_value_redis(redis_key)
        if cached:
            logger.info("[Airtable] Retrieving cached item from redis")
            return json.loads(cached)

        url = "https://api.airtable.com/v0/meta/bases"
        responses = []
        items = []

        fetch_items(access_token, url, responses)

        for base in responses:
            items.append(
                create_integration_item_metadata_object(base, "Base").to_clean_dict()
            )
            tables_response = requests.get(
                f'https://api.airtable.com/v0/meta/bases/{base["id"]}/tables',
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if tables_response.status_code == 200:
                for table in tables_response.json().get("tables", []):
                    items.append(
                        create_integration_item_metadata_object(
                            table, "Table", base.get("id"), base.get("name")
                        ).to_clean_dict()
                    )
            else:
                logger.error(
                    f"[Airtable] Failed to fetch tables for base {base['id']}: {tables_response.text}"
                )

        await add_key_value_redis(redis_key, json.dumps(items), expire=300)
        logger.info(f"[Airtable] Retrieved and cached {len(items)} items")

        return items

    except Exception:
        logger.exception("[Airtable] Unexpected error while fetching items")
        raise HTTPException(status_code=500, detail="Airtable data fetch failed.")
