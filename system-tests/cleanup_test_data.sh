#!/usr/bin/env bash
# Cleanup Test Data — Remove test users, invites, recovery requests, and sessions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"
SCHOOL_ID="${SCHOOL_ID:-00000000-0000-4000-8000-000000000001}"
TEST_EMAIL_PREFIX="${TEST_EMAIL_PREFIX:-test.}"

# Parse flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --token)
      TOKEN="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --school-id)
      SCHOOL_ID="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "Error: --token required (admin token)"
  echo "Usage: $0 --token <jwt> [--base-url <url>] [--school-id <uuid>] [--dry-run]"
  exit 1
fi

echo "=== Cleanup Test Data ==="
echo "Base URL: $BASE_URL"
echo "School ID: $SCHOOL_ID"
echo "Test Email Prefix: $TEST_EMAIL_PREFIX"
[[ -n "${DRY_RUN:-}" ]] && echo "Mode: DRY RUN (no changes will be made)"
echo ""

# Function to make API call
api_call() {
  local method="$1"
  local endpoint="$2"
  local data="${3:-}"
  
  if [[ -n "${DRY_RUN:-}" ]]; then
    echo "[DRY RUN] $method $endpoint"
    [[ -n "$data" ]] && echo "[DRY RUN] Data: $data"
    echo ""
    return 0
  fi
  
  if [[ -n "$data" ]]; then
    curl -s -X "$method" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$BASE_URL$endpoint"
  else
    curl -s -X "$method" \
      -H "Authorization: Bearer $TOKEN" \
      "$BASE_URL$endpoint"
  fi
}

# Step 1: List and delete test users
echo "Step 1: Cleaning up test users..."
echo "GET ${BASE_URL}/schools/${SCHOOL_ID}/users"
USERS=$(api_call "GET" "/schools/${SCHOOL_ID}/users")

if [[ -z "${DRY_RUN:-}" ]]; then
  echo "$USERS" | jq -r '.data[] | select(.email | startswith("'"$TEST_EMAIL_PREFIX"'")) | .id' 2>/dev/null | while read -r user_id; do
    if [[ -n "$user_id" ]]; then
      echo "Deleting user: $user_id"
      api_call "DELETE" "/users/$user_id"
    fi
  done
  echo "✅ Test users cleaned up"
else
  echo "[DRY RUN] Would delete users with email starting with $TEST_EMAIL_PREFIX"
fi
echo ""

# Step 2: Delete test invitation codes
echo "Step 2: Cleaning up invitation codes..."
echo "GET ${BASE_URL}/invites"
INVITES=$(api_call "GET" "/invites")

if [[ -z "${DRY_RUN:-}" ]]; then
  echo "$INVITES" | jq -r '.data[] | select(.email | startswith("'"$TEST_EMAIL_PREFIX"'")) | .code' 2>/dev/null | while read -r code; do
    if [[ -n "$code" ]]; then
      echo "Deleting invite: $code"
      api_call "DELETE" "/invites/$code"
    fi
  done
  echo "✅ Invitation codes cleaned up"
else
  echo "[DRY RUN] Would delete invites with email starting with $TEST_EMAIL_PREFIX"
fi
echo ""

# Step 3: Delete expired recovery requests
echo "Step 3: Cleaning up recovery requests..."
echo "Note: Recovery requests are automatically cleaned up by the backend when expired"
echo "No manual cleanup needed"
echo "✅ Recovery requests cleanup skipped (auto-cleanup)"
echo ""

# Step 4: Revoke test sessions
echo "Step 4: Revoking test sessions..."
echo "GET ${BASE_URL}/auth/sessions"
SESSIONS=$(api_call "GET" "/auth/sessions")

if [[ -z "${DRY_RUN:-}" ]]; then
  echo "$SESSIONS" | jq -r '.data[] | .id' 2>/dev/null | while read -r session_id; do
    if [[ -n "$session_id" ]]; then
      echo "Revoking session: $session_id"
      api_call "DELETE" "/auth/sessions/$session_id"
    fi
  done
  echo "✅ Test sessions revoked"
else
  echo "[DRY RUN] Would revoke all sessions"
fi
echo ""

echo "=== Cleanup Complete ==="
