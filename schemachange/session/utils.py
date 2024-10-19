from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import structlog
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = structlog.getLogger(__name__)


def get_private_key_password() -> bytes | None:
    private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")

    if private_key_password:
        return private_key_password.encode()

    logger.debug(
        "No private key passphrase provided. Assuming the key is not encrypted."
    )

    return None


def get_private_key_bytes(snowflake_private_key_path: Path) -> bytes:
    private_key_password = get_private_key_password()
    with snowflake_private_key_path.open("rb") as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=private_key_password,
            backend=default_backend(),
        )

    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_oauth_token(oauth_config: dict):
    req_info = {
        "url": oauth_config["token-provider-url"],
        "headers": oauth_config["token-request-headers"],
        "data": oauth_config["token-request-payload"],
    }
    token_name = oauth_config["token-response-name"]
    response = requests.post(**req_info)
    response_dict = json.loads(response.text)
    try:
        return response_dict[token_name]
    except KeyError:
        keys = ", ".join(response_dict.keys())
        errormessage = f"Response Json contains keys: {keys} \n but not {token_name}"
        # if there is an error passed with the response include that
        if "error_description" in response_dict.keys():
            errormessage = f"{errormessage}\n error description: {response_dict['error_description']}"
        raise KeyError(errormessage)
