#!/bin/bash

# Production-ready initialization script for Frappe/LMS deployment
# This script is designed for cloud hosting environments like Hetzner or Digital Ocean

set -e  # Exit on any error

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common-functions.sh"

# Function: log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function: check if database is accessible
check_database() {
    log "Checking database connectivity..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if mysql -h mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "SELECT 1;" >/dev/null 2>&1; then
            log "Database connection successful"
            return 0
        fi
        log "Database connection attempt $attempt/$max_attempts failed, retrying in 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "ERROR: Could not connect to database after $max_attempts attempts"
    return 1
}

# Function: check if Redis is accessible
check_redis() {
    log "Checking Redis connectivity..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if redis-cli -h redis ping >/dev/null 2>&1; then
            log "Redis connection successful"
            return 0
        fi
        log "Redis connection attempt $attempt/$max_attempts failed, retrying in 3 seconds..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log "ERROR: Could not connect to Redis after $max_attempts attempts"
    return 1
}

# Function: backup sites before major operations
backup_sites() {
    if [ -d "/home/frappe/frappe-bench/sites" ]; then
        log "Creating backup for all sites..."
        cd /home/frappe/frappe-bench
        
        SITES=$(get_all_sites)
        if [ -z "$SITES" ]; then
            log "No existing sites found, backing up ${SITE_NAME} only"
            bench --site ${SITE_NAME} backup --with-files || log "Backup failed, continuing anyway..."
        else
            for site in $SITES; do
                log "Backing up site: $site"
                bench --site $site backup --with-files || log "Backup failed for $site, continuing anyway..."
            done
        fi
    fi
}

# Function: health check
health_check() {
    log "Performing health check for all sites..."
    
    if [ -d "/home/frappe/frappe-bench" ]; then
        cd /home/frappe/frappe-bench
        
        SITES=$(get_all_sites)
        local health_check_passed=true
        
        if [ -z "$SITES" ]; then
            log "No existing sites found, checking ${SITE_NAME} only"
            if ! bench --site ${SITE_NAME} doctor >/dev/null 2>&1; then
                health_check_passed=false
            fi
        else
            for site in $SITES; do
                log "Health check for site: $site"
                if ! bench --site $site doctor >/dev/null 2>&1; then
                    log "WARNING: Health check failed for site $site"
                    health_check_passed=false
                fi
            done
        fi
        
        if [ "$health_check_passed" = true ]; then
            log "Sites health check passed"
            return 0
        else
            log "WARNING: Sites health check failed"
            return 1
        fi
    else
        log "Bench directory not found, skipping health check"
        return 1
    fi
}

# Function: setup production optimizations
setup_production_optimizations() {
    log "Setting up production optimizations..."
    
    if [ -d "/home/frappe/frappe-bench" ]; then
        cd /home/frappe/frappe-bench
        
        # Set production configurations for all sites
        apply_config_to_all_sites maintenance_mode 0
        apply_config_to_all_sites allow_tests 0
        apply_config_to_all_sites server_script_enabled 0
        apply_config_to_all_sites disable_website_cache 0
        
        # Enable compression
        apply_config_to_all_sites enable_gzip_compression 1
        
        log "Production optimizations applied"
    fi
}

# Function: setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create log rotation configuration
    sudo tee /etc/logrotate.d/frappe > /dev/null << EOF
/home/frappe/frappe-bench/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
    
    log "Monitoring setup completed"
}

# Main execution starts here
log "Starting production initialization..."

# Validate required environment variables
required_vars=("SITE_NAME" "MARIADB_ROOT_PASSWORD" "ADMIN_PASSWORD" "LMS_REPO_URL" "AI_TUTOR_REPO_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

# Check dependencies
check_database
check_redis

# Initialize SSH availability (production environments typically use HTTPS)
SSH_KEY_AVAILABLE=false

# Check if SSH keys are available
if [ -f "/workspace/ssh/id_ed25519" ]; then
    SSH_KEY_AVAILABLE=true
    log "SSH keys detected, will use SSH for git operations"
else
    log "No SSH keys found, will use HTTPS for git operations"
fi

# Navigate to bench directory or run main init
if [ -d "/home/frappe/frappe-bench" ] && [ -f "/home/frappe/frappe-bench/sites/common_site_config.json" ]; then
    cd /home/frappe/frappe-bench
    log "Using existing valid bench directory"
    
    # Backup before any changes
    backup_sites
    
    # Load common functions and run app updates directly
    log "Running app updates..."
    
    # Install/Update the LMS app on all sites
    if [ "$SSH_KEY_AVAILABLE" = true ]; then
        update_apps_on_all_sites lms ${LMS_REPO_URL}
    else
        # Use HTTPS URLs if SSH is not available
        LMS_HTTPS_URL=$(echo ${LMS_REPO_URL} | sed 's/git@github.com:/https:\/\/github.com\//')
        update_apps_on_all_sites lms ${LMS_HTTPS_URL}
    fi

    # Install/Update the AI Tutor Chat app on all sites
    if [ "$SSH_KEY_AVAILABLE" = true ]; then
        update_apps_on_all_sites ai_tutor_chat ${AI_TUTOR_REPO_URL}
    else
        # Use HTTPS URLs if SSH is not available
        AI_TUTOR_HTTPS_URL=$(echo ${AI_TUTOR_REPO_URL} | sed 's/git@github.com:/https:\/\/github.com\//')
        update_apps_on_all_sites ai_tutor_chat ${AI_TUTOR_HTTPS_URL}
    fi

    # Set configurations for all sites
    apply_config_to_all_sites developer_mode ${DEVELOPER_MODE}
    apply_config_to_all_sites ai_tutor_api_url ${AI_TUTOR_API_URL}
    
    # Clear cache for all sites
    clear_cache_all_sites
else
    log "Bench directory not found or invalid, running main initialization..."
    # Run the main init script which will properly initialize the bench
    log "Executing init.sh script..."
    
    # Set production mode to prevent bench start
    export PRODUCTION_MODE=true
    bash "${SCRIPT_DIR}/init.sh"
    
    # Check if init.sh was successful
    if [ $? -eq 0 ]; then
        log "Main initialization completed successfully"
    else
        log "ERROR: Main initialization failed"
        exit 1
    fi
fi

# Apply production optimizations
setup_production_optimizations

# Setup monitoring
setup_monitoring

# Final health check
health_check

log "Production initialization completed successfully"
