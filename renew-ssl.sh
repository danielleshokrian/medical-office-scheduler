#!/bin/bash

###############################################################################
# SSL Certificate Renewal for chronamed.com
#
# Uses certbot with the webroot method so nginx keeps running during renewal.
# Nginx must already be running and serving port 80 before using this script.
#
# First-time setup (no certs yet):
#   ./renew-ssl.sh setup
#
# Renew an existing (or expired) cert:
#   ./renew-ssl.sh renew
#
# Requirements:
#   - Docker installed
#   - docker-compose up (frontend container must be running)
#   - Ports 80/443 open and pointed at this server
###############################################################################

set -e

DOMAIN="${DOMAIN:-chronamed.com}"
EMAIL="${CERTBOT_EMAIL:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/ssl"
LETSENCRYPT_DIR="${SSL_DIR}/letsencrypt"
WEBROOT_DIR="${SSL_DIR}/webroot"
CERTS_DIR="${SSL_DIR}/certs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Load DOMAIN/CERTBOT_EMAIL from .env if present
if [ -f "${SCRIPT_DIR}/.env" ]; then
    # shellcheck disable=SC1090
    set -a; source "${SCRIPT_DIR}/.env"; set +a
fi

DOMAIN="${DOMAIN:-chronamed.com}"
EMAIL="${CERTBOT_EMAIL:-}"

check_email() {
    if [ -z "$EMAIL" ]; then
        log_error "CERTBOT_EMAIL is required. Add it to your .env file:"
        echo "  CERTBOT_EMAIL=you@example.com"
        exit 1
    fi
}

run_certbot() {
    local subcommand="$1"  # "certonly" or "renew"

    mkdir -p "$LETSENCRYPT_DIR" "$WEBROOT_DIR" "$CERTS_DIR"

    if [ "$subcommand" = "certonly" ]; then
        docker run --rm \
            -v "${LETSENCRYPT_DIR}:/etc/letsencrypt" \
            -v "${WEBROOT_DIR}:/var/www/certbot" \
            certbot/certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --non-interactive \
            --agree-tos \
            --email "$EMAIL" \
            -d "$DOMAIN" \
            -d "www.$DOMAIN"
    else
        docker run --rm \
            -v "${LETSENCRYPT_DIR}:/etc/letsencrypt" \
            -v "${WEBROOT_DIR}:/var/www/certbot" \
            certbot/certbot renew \
            --webroot \
            --webroot-path=/var/www/certbot \
            --non-interactive
    fi
}

copy_certs() {
    log_info "Copying renewed certs to ${CERTS_DIR}..."

    local live_dir="${LETSENCRYPT_DIR}/live/${DOMAIN}"

    if [ ! -f "${live_dir}/fullchain.pem" ]; then
        log_error "Certificate not found at ${live_dir}/fullchain.pem"
        log_error "Did certbot succeed?"
        exit 1
    fi

    cp "${live_dir}/fullchain.pem" "${CERTS_DIR}/fullchain.pem"
    cp "${live_dir}/privkey.pem"   "${CERTS_DIR}/privkey.pem"
    chmod 644 "${CERTS_DIR}/fullchain.pem"
    chmod 600 "${CERTS_DIR}/privkey.pem"

    log_success "Certs copied to ${CERTS_DIR}"
}

reload_nginx() {
    log_info "Reloading nginx..."
    if docker-compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T frontend nginx -s reload; then
        log_success "Nginx reloaded"
    else
        log_warning "nginx reload failed — try: docker-compose restart frontend"
    fi
}

# ── Commands ──────────────────────────────────────────────────────────────────

setup() {
    log_info "Getting initial SSL certificate for ${DOMAIN}..."
    check_email

    # Bootstrap: create a self-signed cert so nginx can start with the HTTPS
    # config before the real cert exists.
    if [ ! -f "${CERTS_DIR}/fullchain.pem" ]; then
        log_info "Creating temporary self-signed cert so nginx can start..."
        mkdir -p "$CERTS_DIR"
        openssl req -x509 -newkey rsa:2048 \
            -keyout "${CERTS_DIR}/privkey.pem" \
            -out    "${CERTS_DIR}/fullchain.pem" \
            -days 1 -nodes \
            -subj "/CN=${DOMAIN}" 2>/dev/null
        log_info "Temporary cert created. Starting nginx..."
        docker-compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d frontend
        sleep 3
    fi

    log_info "Requesting certificate from Let's Encrypt via webroot challenge..."
    run_certbot "certonly"
    copy_certs
    reload_nginx

    log_success "SSL setup complete for ${DOMAIN}!"
    log_info "Add this to your crontab to auto-renew (runs daily at 3am):"
    echo "  0 3 * * * cd ${SCRIPT_DIR} && ./renew-ssl.sh renew >> /var/log/ssl-renew.log 2>&1"
}

renew() {
    log_info "Renewing SSL certificate for ${DOMAIN}..."

    run_certbot "renew"
    copy_certs
    reload_nginx

    log_success "SSL certificate renewed for ${DOMAIN}!"
}

# ── Main ──────────────────────────────────────────────────────────────────────

case "${1:-}" in
    setup)
        setup
        ;;
    renew)
        renew
        ;;
    *)
        echo "SSL Certificate Manager for chronamed.com"
        echo
        echo "Usage: $0 [setup|renew]"
        echo
        echo "  setup   Get the initial certificate (first time, or after expiry)"
        echo "  renew   Renew before expiry (safe to run while nginx is up)"
        echo
        echo "Environment variables (set in .env):"
        echo "  DOMAIN         Domain name (default: chronamed.com)"
        echo "  CERTBOT_EMAIL  Your email for Let's Encrypt notifications (required)"
        echo
        exit 1
        ;;
esac
