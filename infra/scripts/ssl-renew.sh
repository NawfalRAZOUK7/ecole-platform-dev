#!/usr/bin/env bash
# ssl-renew.sh — Let's Encrypt certificate management
#
# Reference: Phase 7A — TLS certificate management
#
# Usage:
#   ./infra/scripts/ssl-renew.sh obtain <domain>     # First-time cert
#   ./infra/scripts/ssl-renew.sh renew                # Renew all certs
#   ./infra/scripts/ssl-renew.sh status               # Check cert expiry
#
# Cron (auto-renew twice daily):
#   0 3,15 * * * /path/to/infra/scripts/ssl-renew.sh renew >> /var/log/ssl-renew.log 2>&1
#
# Prerequisites:
#   - Nginx running with ACME challenge location
#   - Port 80 reachable from the internet
#   - Docker Compose with certbot service

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$INFRA_DIR")"
COMPOSE_FILE="$INFRA_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"
CERTS_DIR="$INFRA_DIR/certs"
LOG_FILE="$INFRA_DIR/ssl-renew.log"

# Notification email for Let's Encrypt
CERT_EMAIL="${CERT_EMAIL:-admin@ecole-platform.example}"

# Domains (override via env)
API_DOMAIN="${API_DOMAIN:-api.ecole-platform.example}"
WEB_DOMAIN="${WEB_DOMAIN:-ecole-platform.example}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "$(date '+%Y-%m-%d %H:%M:%S') [INFO]  $*" | tee -a "$LOG_FILE"; }
warn()  { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARN]${NC}  $*" | tee -a "$LOG_FILE"; }
error() { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"; }
ok()    { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[OK]${NC}    $*" | tee -a "$LOG_FILE"; }

compose() {
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

# ─────────────────────────── Obtain ───────────────────────────
obtain_cert() {
    local domain="${1:?Usage: ssl-renew.sh obtain <domain>}"
    log "Obtaining certificate for: $domain"

    # Ensure nginx is running for ACME challenge
    compose up -d nginx

    # Run certbot
    docker run --rm \
        -v "$CERTS_DIR:/etc/letsencrypt" \
        -v "$INFRA_DIR/../certbot_webroot:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$domain" \
        --email "$CERT_EMAIL" \
        --agree-tos \
        --non-interactive \
        --no-eff-email

    if [ $? -eq 0 ]; then
        ok "Certificate obtained for $domain"
        log "Certificate path: $CERTS_DIR/live/$domain/"

        # Reload nginx to pick up new cert
        compose exec nginx nginx -s reload 2>/dev/null || true
        ok "Nginx reloaded with new certificate"
    else
        error "Failed to obtain certificate for $domain"
        exit 1
    fi
}

# ─────────────────────────── Renew ───────────────────────────
renew_certs() {
    log "Renewing all certificates..."

    docker run --rm \
        -v "$CERTS_DIR:/etc/letsencrypt" \
        -v "$INFRA_DIR/../certbot_webroot:/var/www/certbot" \
        certbot/certbot renew \
        --webroot \
        -w /var/www/certbot \
        --quiet \
        --no-random-sleep-on-renew

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        ok "Certificate renewal check complete"

        # Reload nginx to pick up any renewed certs
        compose exec nginx nginx -s reload 2>/dev/null || true
        ok "Nginx reloaded"
    else
        error "Certificate renewal failed (exit code: $exit_code)"
        exit 1
    fi
}

# ─────────────────────────── Status ───────────────────────────
check_status() {
    log "Checking certificate status..."

    local has_certs=false

    for domain_dir in "$CERTS_DIR/live"/*/; do
        if [ ! -d "$domain_dir" ]; then continue; fi

        local domain
        domain=$(basename "$domain_dir")
        local cert_file="$domain_dir/fullchain.pem"

        if [ ! -f "$cert_file" ]; then
            warn "No certificate found for $domain"
            continue
        fi

        has_certs=true

        # Check expiry
        local expiry
        expiry=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        local expiry_epoch
        expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" +%s 2>/dev/null || echo "0")
        local now_epoch
        now_epoch=$(date +%s)
        local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

        if [ "$days_left" -lt 0 ]; then
            error "  $domain: EXPIRED ($expiry)"
        elif [ "$days_left" -lt 7 ]; then
            error "  $domain: CRITICAL — expires in ${days_left} days ($expiry)"
        elif [ "$days_left" -lt 30 ]; then
            warn "  $domain: expires in ${days_left} days ($expiry)"
        else
            ok "  $domain: valid for ${days_left} days (expires: $expiry)"
        fi

        # Show certificate details
        local subject
        subject=$(openssl x509 -subject -noout -in "$cert_file" 2>/dev/null | sed 's/subject=//')
        local issuer
        issuer=$(openssl x509 -issuer -noout -in "$cert_file" 2>/dev/null | sed 's/issuer=//')
        log "    Subject: $subject"
        log "    Issuer:  $issuer"
    done

    if [ "$has_certs" = false ]; then
        warn "No certificates found in $CERTS_DIR/live/"
        warn "Run: ./ssl-renew.sh obtain $WEB_DOMAIN"
        warn "Run: ./ssl-renew.sh obtain $API_DOMAIN"
    fi
}

# ─────────────────────────── Main ───────────────────────────
case "${1:-help}" in
    obtain)
        obtain_cert "${2:-}"
        ;;
    renew)
        renew_certs
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: ssl-renew.sh <command>"
        echo ""
        echo "Commands:"
        echo "  obtain <domain>  Obtain a new certificate for a domain"
        echo "  renew            Renew all existing certificates"
        echo "  status           Check certificate expiry status"
        echo ""
        echo "Environment variables:"
        echo "  CERT_EMAIL   Email for Let's Encrypt notifications"
        echo "  API_DOMAIN   API domain (default: api.ecole-platform.example)"
        echo "  WEB_DOMAIN   Web domain (default: ecole-platform.example)"
        exit 1
        ;;
esac
