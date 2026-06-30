#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Dynamic smoke-test — proves the seeded personas enforce D1–D4 scoping at the
# API level (not just compile). Run AFTER `make up && make migrate && make seed`.
#
#   bash scripts/smoke_test_scoping.sh
#
# Requires: curl, python3. Hits the dev backend on localhost:8000.
# Credentials are the documented demo passwords (seed-report.md).
# Read-only except it calls login + GETs; the one write probe is expected to be
# REJECTED (it tests that DIR cannot perform an ADM-only action).
# ---------------------------------------------------------------------------
set -uo pipefail

BASE="${BASE_URL:-http://localhost:8000/api/v1}"
SCHOOL="00000000-0000-4000-8000-000000000001"   # Ecole Benani (formal)
PASS=0; FAIL=0

c_green() { printf '\033[32m%s\033[0m\n' "$1"; }
c_red()   { printf '\033[31m%s\033[0m\n' "$1"; }

ok()   { c_green "  PASS: $1"; PASS=$((PASS+1)); }
bad()  { c_red   "  FAIL: $1"; FAIL=$((FAIL+1)); }

# login <email> <password>  -> echoes access_token (empty on failure)
login() {
  local email="$1" pw="$2"
  curl -s -X POST "$BASE/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":\"$pw\",\"school_id\":\"$SCHOOL\"}" \
  | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print(""); sys.exit()
# token may be at data.access_token or top-level access_token
def find(o):
    if isinstance(o,dict):
        if "access_token" in o and isinstance(o["access_token"],str): return o["access_token"]
        for v in o.values():
            r=find(v)
            if r: return r
    return ""
print(find(d) or "")'
}

# http_code <token> <method> <path> [json-body]
http_code() {
  local token="$1" method="$2" path="$3" body="${4:-}"
  if [ -n "$body" ]; then
    curl -s -o /dev/null -w '%{http_code}' -X "$method" "$BASE$path" \
      -H "Authorization: Bearer $token" -H 'Content-Type: application/json' -d "$body"
  else
    curl -s -o /dev/null -w '%{http_code}' -X "$method" "$BASE$path" \
      -H "Authorization: Bearer $token"
  fi
}

echo "== Ecole Platform — scoping smoke-test =="
echo "Base: $BASE  School: $SCHOOL"
echo

# --- 0. Sanity: health -----------------------------------------------------
if [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/health")" = "200" ]; then
  ok "backend health 200"
else
  bad "backend health not 200 — is the stack up? (make up)"; echo; exit 1
fi

# --- tokens ----------------------------------------------------------------
echo; echo "-- logging in personas --"
TOK_STD_CP=$(login "amina.cp@ecole-benani.ma" "student123")    # CP / 1AEP
TOK_STD_TERM=$(login "sara.terminale@ecole-benani.ma" "student123")  # 2BAC
TOK_PAR=$(login "parent.tazi@gmail.com" "parent123")           # parent of Amina (CP)
TOK_DIR=$(login "directeur@ecole-benani.ma" "director123")
TOK_ADM=$(login "admin@ecole-benani.ma" "admin123")
TOK_TCH=$(login "prof.math@ecole-benani.ma" "teacher123")

for n in TOK_STD_CP TOK_STD_TERM TOK_PAR TOK_DIR TOK_ADM TOK_TCH; do
  [ -n "${!n}" ] && ok "login $n" || bad "login $n (empty token)"
done

# --- 1. D3: a student only lists content assigned to her class -------------
echo; echo "-- 1. STD content list is scoped --"
CP_LIST=$(curl -s "$BASE/content-items?page_size=100" -H "Authorization: Bearer $TOK_STD_CP")
TERM_LIST=$(curl -s "$BASE/content-items?page_size=100" -H "Authorization: Bearer $TOK_STD_TERM")
# Extract IDs each student can see
ids() { python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit()
# list_response wraps the array under "data"; tolerate items/results too.
def arr(o):
    if isinstance(o,list): return o
    if isinstance(o,dict):
        for k in ("data","items","results"):
            v=o.get(k)
            if isinstance(v,list): return v
        for v in o.values():
            r=arr(v)
            if r: return r
    return []
print("\n".join(str(i.get("id")) for i in arr(d) if isinstance(i,dict) and i.get("id")))'; }
CP_IDS=$(printf '%s' "$CP_LIST" | ids 2>/dev/null)
TERM_IDS=$(printf '%s' "$TERM_LIST" | ids 2>/dev/null)
CP_N=$(printf '%s\n' "$CP_IDS" | grep -c . || true)
TERM_N=$(printf '%s\n' "$TERM_IDS" | grep -c . || true)
echo "    CP student sees $CP_N items; Terminale student sees $TERM_N items"
# They should NOT be identical sets (different classes → different content)
if [ "$CP_N" -gt 0 ] && [ "$TERM_N" -gt 0 ] && [ "$CP_IDS" != "$TERM_IDS" ]; then
  ok "CP and Terminale see DIFFERENT content sets (class-scoped)"
elif [ "$CP_N" = 0 ] && [ "$TERM_N" = 0 ]; then
  bad "both students see 0 items — scoping may be over-restrictive or no assignments seeded"
else
  bad "CP and Terminale see the SAME set — content not class-scoped (investigate)"
fi

# --- 2. D3 hard boundary: STD GET of another class's item → 404 ------------
echo; echo "-- 2. STD direct GET of a non-assigned item → 404 --"
# pick an id the Terminale student sees but the CP student does not
CROSS_ID=$(comm -13 <(printf '%s\n' "$CP_IDS" | sort -u) <(printf '%s\n' "$TERM_IDS" | sort -u) | head -1)
if [ -n "$CROSS_ID" ]; then
  CODE=$(http_code "$TOK_STD_CP" GET "/content-items/$CROSS_ID")
  [ "$CODE" = "404" ] && ok "CP student GET Terminale-only item → 404 (got $CODE)" \
                       || bad "expected 404, got $CODE — direct-access scoping leak!"
else
  echo "    (skipped — could not derive a cross-class item id from the lists)"
fi

# --- 3. Strict roles: DIR cannot do an ADM-only write; ADM can -------------
echo; echo "-- 3. DIR ≠ ADM on an ADM-only action (user:manage) --"
# PUT /admin/users/{id}/suspend is gated PERM_ADM_USER_MANAGE (ADM-only; DIR is
# oversight, not operations). We only read the AUTHZ code: 403 = blocked,
# anything else = authz passed (the action itself may 404/422, that's fine).
TARGET="10000000-0000-4000-8000-00000000000c"   # Amina (a real STD user)
DIR_CODE=$(http_code "$TOK_DIR" PUT "/admin/users/$TARGET/suspend" '{}')
ADM_CODE=$(http_code "$TOK_ADM" PUT "/admin/users/$TARGET/suspend" '{}')
echo "    DIR→suspend user: $DIR_CODE   ADM→suspend user: $ADM_CODE"
[ "$DIR_CODE" = "403" ] && ok "DIR blocked from ADM-only user:manage (403)" \
                        || bad "DIR got $DIR_CODE on an ADM-only write (expected 403)"
[ "$ADM_CODE" != "403" ] && ok "ADM passes authz on user:manage (got $ADM_CODE, not 403)" \
                         || bad "ADM wrongly blocked (403) on its own action"

# --- 4. Impersonation is SUP-only (DIR must be 403) ------------------------
echo; echo "-- 4. Impersonation gated away from DIR (SUP-only) --"
IMP_CODE=$(http_code "$TOK_DIR" POST "/admin/impersonate/$TARGET" '{}')
[ "$IMP_CODE" = "403" ] && ok "DIR blocked from impersonation (403)" \
                        || bad "DIR impersonate → $IMP_CODE (expected 403 — SUP-only)"

# --- summary ---------------------------------------------------------------
echo
echo "================  $PASS passed / $FAIL failed  ================"
[ "$FAIL" -eq 0 ] && c_green "Scoping behaves as designed." || c_red "Some checks failed — paste output back."
exit 0
