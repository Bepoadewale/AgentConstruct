#!/usr/bin/env bash
set -euo pipefail

: "${COGNITO_USER_POOL_ID:?Set COGNITO_USER_POOL_ID}"
: "${GOOGLE_CLIENT_ID:?Set GOOGLE_CLIENT_ID}"

keychain_service="${GOOGLE_CLIENT_SECRET_KEYCHAIN_SERVICE:-agentconstruct-google-oauth-client-secret}"
secret="$(security find-generic-password -a "${USER}" -s "${keychain_service}" -w)"
payload="$(mktemp "${TMPDIR:-/tmp}/agentconstruct-google-idp.XXXXXX.json")"

cleanup() {
  secret=""
  case "${payload}" in
    "${TMPDIR:-/tmp}"/agentconstruct-google-idp.*.json) rm -f -- "${payload}" ;;
    *) printf 'Refusing to clean unexpected path: %s\n' "${payload}" >&2 ;;
  esac
}
trap cleanup EXIT
chmod 600 "${payload}"

if aws cognito-idp describe-identity-provider \
  --user-pool-id "${COGNITO_USER_POOL_ID}" \
  --provider-name Google >/dev/null 2>&1; then
  jq -n \
    --arg pool "${COGNITO_USER_POOL_ID}" \
    --arg client "${GOOGLE_CLIENT_ID}" \
    --arg secret "${secret}" \
    '{UserPoolId:$pool,ProviderName:"Google",ProviderDetails:{client_id:$client,client_secret:$secret,authorize_scopes:"openid email profile"},AttributeMapping:{email:"email",email_verified:"email_verified",name:"name"}}' \
    >"${payload}"
  aws cognito-idp update-identity-provider --cli-input-json "file://${payload}" >/dev/null
  printf 'Updated Cognito Google identity provider.\n'
else
  jq -n \
    --arg pool "${COGNITO_USER_POOL_ID}" \
    --arg client "${GOOGLE_CLIENT_ID}" \
    --arg secret "${secret}" \
    '{UserPoolId:$pool,ProviderName:"Google",ProviderType:"Google",ProviderDetails:{client_id:$client,client_secret:$secret,authorize_scopes:"openid email profile"},AttributeMapping:{email:"email",email_verified:"email_verified",name:"name"}}' \
    >"${payload}"
  aws cognito-idp create-identity-provider --cli-input-json "file://${payload}" >/dev/null
  printf 'Created Cognito Google identity provider.\n'
fi
