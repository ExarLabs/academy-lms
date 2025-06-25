#!/bin/bash

# Production-ready initialization script for Frappe/LMS deployment
# This script is designed for cloud hosting environments like Hetzner or Digital Ocean

set -e  # Exit on any error

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
        bench --all-sites backup --with-files || log "Backup failed, continuing anyway..."
    fi
}

# Function: health check
health_check() {
    log "Performing health check for all sites..."
    
    if [ -d "/home/frappe/frappe-bench" ]; then
        cd /home/frappe/frappe-bench
        # Check if sites are accessible
        if bench --all-sites doctor >/dev/null 2>&1; then
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
        bench --all-sites set-config maintenance_mode 0
        bench --all-sites set-config allow_tests 0
        bench --all-sites set-config server_script_enabled 0
        bench --all-sites set-config disable_website_cache 0
        
        # Enable compression
        bench --all-sites set-config enable_gzip_compression 1
        
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

# Navigate to bench directory or run main init
if [ -d "/home/frappe/frappe-bench" ]; then
    cd /home/frappe/frappe-bench
    log "Using existing bench directory"
    
    # Backup before any changes
    backup_sites
    
    # Source the main init script functions and run it
    log "Running main initialization script..."
    source /workspace/init.sh
else
    log "Bench directory not found, running main initialization..."
    # Run the main init script
    exec /workspace/init.sh
fi

# Apply production optimizations
setup_production_optimizations

# Setup monitoring
setup_monitoring

# Final health check
health_check

log "Production initialization completed successfully"
