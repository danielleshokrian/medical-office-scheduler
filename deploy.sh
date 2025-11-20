#!/bin/bash

 

###############################################################################

# Medical Office Scheduler - Deployment Script

###############################################################################

#

# This script automates the deployment of the Medical Office Scheduler

# using Docker Compose.

#

# Usage:

#   ./deploy.sh [command]

#

# Commands:

#   setup       - Initial setup (first time deployment)

#   start       - Start all services

#   stop        - Stop all services

#   restart     - Restart all services

#   logs        - View logs

#   status      - Check service status

#   backup      - Backup database

#   restore     - Restore database from backup

#   clean       - Clean up (WARNING: removes all data!)

#

###############################################################################

 

set -e  # Exit on error

 

# Colors for output

RED='\033[0;31m'

GREEN='\033[0;32m'

YELLOW='\033[1;33m'

BLUE='\033[0;34m'

NC='\033[0m' # No Color

 

# Helper functions

log_info() {

    echo -e "${BLUE}[INFO]${NC} $1"

}

 

log_success() {

    echo -e "${GREEN}[SUCCESS]${NC} $1"

}

 

log_warning() {

    echo -e "${YELLOW}[WARNING]${NC} $1"

}

 

log_error() {

    echo -e "${RED}[ERROR]${NC} $1"

}

 

# Check if docker and docker-compose are installed

check_requirements() {

    log_info "Checking requirements..."

 

    if ! command -v docker &> /dev/null; then

        log_error "Docker is not installed. Please install Docker first."

        exit 1

    fi

 

    if ! command -v docker-compose &> /dev/null; then

        log_error "Docker Compose is not installed. Please install Docker Compose first."

        exit 1

    fi

 

    log_success "All requirements met!"

}

 

# Generate secure secrets

generate_secrets() {

    log_info "Generating secure secrets..."

 

    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)

 

    echo "$DB_PASSWORD"

    echo "$SECRET_KEY"

}

 

# Setup for first-time deployment

setup() {

    log_info "Starting initial setup..."

 

    check_requirements

 

    # Check if .env already exists

    if [ -f .env ]; then

        log_warning ".env file already exists!"

        read -p "Do you want to overwrite it? (y/N) " -n 1 -r

        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then

            log_info "Keeping existing .env file"

            return

        fi

    fi

 

    # Create .env file

    log_info "Creating .env file..."

 

    # Generate secrets

    SECRETS=$(generate_secrets)

    DB_PASSWORD=$(echo "$SECRETS" | sed -n 1p)

    SECRET_KEY=$(echo "$SECRETS" | sed -n 2p)

 

    # Get OpenAI API key

    echo

    log_warning "You need an OpenAI API key for AI scheduling features."

    log_info "Get one at: https://platform.openai.com/api-keys"

    echo

    read -p "Enter your OpenAI API key (or press Enter to skip): " OPENAI_KEY

    if [ -z "$OPENAI_KEY" ]; then

        OPENAI_KEY="sk-your-openai-api-key-here"

        log_warning "You can add your OpenAI key later in the .env file"

    fi

 

    # Get domain name

    echo

    read -p "Enter your domain name (or press Enter for localhost): " DOMAIN

    if [ -z "$DOMAIN" ]; then

        API_URL="http://localhost:5001"

        log_info "Using localhost for development"

    else

        API_URL="https://$DOMAIN/api"

        log_info "Using production domain: $DOMAIN"

    fi

 

    # Create .env file

    cat > .env << EOF

# Database

DB_PASSWORD=$DB_PASSWORD

 

# Flask

SECRET_KEY=$SECRET_KEY

FLASK_ENV=production

 

# OpenAI

OPENAI_API_KEY=$OPENAI_KEY

 

# API URL

REACT_APP_API_URL=$API_URL

EOF

 

    log_success ".env file created!"

 

    # Create SSL directory

    mkdir -p ssl/certs

    log_info "Created ssl/certs directory for SSL certificates"

 

    # Create backups directory

    mkdir -p backups

    log_info "Created backups directory"

 

    # Display next steps

    echo

    log_success "Setup complete!"

    echo

    log_info "Next steps:"

    echo "  1. Review and update .env file if needed"

    echo "  2. If using custom domain, set up SSL certificates (see SSL-SETUP.md)"

    echo "  3. Run: ./deploy.sh start"

    echo

}

 

# Start services

start() {

    log_info "Starting services..."

 

    check_requirements

 

    if [ ! -f .env ]; then

        log_error ".env file not found. Run './deploy.sh setup' first."

        exit 1

    fi

 

    # Build and start containers

    log_info "Building Docker images..."

    docker-compose build

 

    log_info "Starting containers..."

    docker-compose up -d

 

    # Wait for database to be ready

    log_info "Waiting for database to be ready..."

    sleep 5

 

    # Run migrations

    log_info "Running database migrations..."

    docker-compose exec -T backend flask db upgrade || true

 

    echo

    log_success "Deployment complete!"

    echo

    log_info "Services are running:"

    docker-compose ps

    echo

    log_info "Access your application:"

    echo "  - Frontend: http://localhost (or your domain)"

    echo "  - Backend API: http://localhost:5001"

    echo "  - Health check: http://localhost:5001/health"

    echo

    log_info "View logs: ./deploy.sh logs"

    echo

}

 

# Stop services

stop() {

    log_info "Stopping services..."

    docker-compose down

    log_success "Services stopped"

}

 

# Restart services

restart() {

    log_info "Restarting services..."

    stop

    start

}

 

# View logs

view_logs() {

    SERVICE=$1

    if [ -z "$SERVICE" ]; then

        docker-compose logs -f

    else

        docker-compose logs -f "$SERVICE"

    fi

}

 

# Check status

status() {

    log_info "Service status:"

    docker-compose ps

 

    echo

    log_info "Checking health endpoints..."

 

    # Check backend health

    if curl -f http://localhost:5001/health > /dev/null 2>&1; then

        log_success "Backend is healthy"

    else

        log_error "Backend is not responding"

    fi

 

    # Check frontend

    if curl -f http://localhost > /dev/null 2>&1; then

        log_success "Frontend is accessible"

    else

        log_error "Frontend is not responding"

    fi

}

 

# Backup database

backup() {

    log_info "Creating database backup..."

 

    BACKUP_FILE="backups/scheduler_$(date +%Y%m%d_%H%M%S).sql"

 

    docker-compose exec -T postgres pg_dump -U scheduler_user medical_scheduler > "$BACKUP_FILE"

 

    if [ -f "$BACKUP_FILE" ]; then

        # Compress backup

        gzip "$BACKUP_FILE"

        log_success "Backup created: ${BACKUP_FILE}.gz"

    else

        log_error "Backup failed"

        exit 1

    fi

}

 

# Restore database

restore() {

    log_warning "This will restore the database from a backup."

    log_warning "ALL CURRENT DATA WILL BE LOST!"

    echo

 

    # List available backups

    log_info "Available backups:"

    ls -lh backups/*.sql.gz 2>/dev/null || log_error "No backups found"

 

    echo

    read -p "Enter backup file path: " BACKUP_FILE

 

    if [ ! -f "$BACKUP_FILE" ]; then

        log_error "Backup file not found: $BACKUP_FILE"

        exit 1

    fi

 

    read -p "Are you sure you want to restore from $BACKUP_FILE? (yes/NO) " -r

    echo

    if [[ ! $REPLY =~ ^yes$ ]]; then

        log_info "Restore cancelled"

        exit 0

    fi

 

    log_info "Restoring database..."

 

    # Decompress if needed

    if [[ $BACKUP_FILE == *.gz ]]; then

        gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U scheduler_user medical_scheduler

    else

        docker-compose exec -T postgres psql -U scheduler_user medical_scheduler < "$BACKUP_FILE"

    fi

 

    log_success "Database restored!"

}

 

# Clean up (remove all data)

clean() {

    log_warning "This will remove ALL containers, volumes, and data!"

    echo

    read -p "Are you sure? Type 'yes' to confirm: " -r

    echo

 

    if [[ ! $REPLY =~ ^yes$ ]]; then

        log_info "Clean cancelled"

        exit 0

    fi

 

    log_info "Stopping and removing containers..."

    docker-compose down -v

 

    log_info "Removing images..."

    docker-compose down --rmi all

 

    log_success "Cleanup complete"

}

 

# Main script

case "$1" in

    setup)

        setup

        ;;

    start)

        start

        ;;

    stop)

        stop

        ;;

    restart)

        restart

        ;;

    logs)

        view_logs "$2"

        ;;

    status)

        status

        ;;

    backup)

        backup

        ;;

    restore)

        restore

        ;;

    clean)

        clean

        ;;

    *)

        echo "Medical Office Scheduler - Deployment Script"

        echo

        echo "Usage: $0 [command]"

        echo

        echo "Commands:"

        echo "  setup       - Initial setup (first time deployment)"

        echo "  start       - Start all services"

        echo "  stop        - Stop all services"

        echo "  restart     - Restart all services"

        echo "  logs        - View logs (add service name for specific service)"

        echo "  status      - Check service status"

        echo "  backup      - Backup database"

        echo "  restore     - Restore database from backup"

        echo "  clean       - Clean up (WARNING: removes all data!)"

        echo

        echo "Examples:"

        echo "  $0 setup                # First time setup"

        echo "  $0 start                # Start all services"

        echo "  $0 logs backend         # View backend logs"

        echo "  $0 backup               # Create database backup"

        echo

        exit 1

        ;;

esac