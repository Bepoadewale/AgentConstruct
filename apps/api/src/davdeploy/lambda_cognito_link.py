"""Cognito pre-sign-up trigger for safe Google and native account linking."""

from __future__ import annotations

from typing import Any

import boto3


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if event.get("triggerSource") != "PreSignUp_ExternalProvider":
        return event
    attributes = event.get("request", {}).get("userAttributes", {})
    email = str(attributes.get("email", "")).strip().lower()
    verified = str(attributes.get("email_verified", "")).lower() == "true"
    username = str(event.get("userName", ""))
    if not email or not verified or "_" not in username:
        raise ValueError("external identity requires a verified email")

    provider, provider_user_id = username.split("_", 1)
    if provider.lower() != "google":
        raise ValueError("only the configured Google identity provider can be linked")

    client = boto3.client("cognito-idp")
    users = client.list_users(
        UserPoolId=event["userPoolId"],
        Filter=f'email = "{email}"',
        Limit=2,
    ).get("Users", [])
    native = next(
        (user for user in users if user.get("Username") and "_" not in user["Username"]),
        None,
    )
    if native:
        client.admin_link_provider_for_user(
            UserPoolId=event["userPoolId"],
            DestinationUser={
                "ProviderName": "Cognito",
                "ProviderAttributeValue": native["Username"],
            },
            SourceUser={
                "ProviderName": "Google",
                "ProviderAttributeName": "Cognito_Subject",
                "ProviderAttributeValue": provider_user_id,
            },
        )
    event.setdefault("response", {})["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True
    return event
