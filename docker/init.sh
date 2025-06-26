#!/bin/bash

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common-functions.sh"

# Init github authentication
mkdir -p ~/.ssh

# Check if SSH keys exist in workspace and copy them
SSH_KEY_AVAILABLE=false

if [ -f "/workspace/ssh/id_ed25519" ]; then
    cp /workspace/ssh/id_ed25519 ~/.ssh/id_ed25519
    chmod 600 ~/.ssh/id_ed25519
    echo "SSH private key copied successfully"
    SSH_KEY_AVAILABLE=true
else
    echo "Warning: SSH private key not found at /workspace/ssh/id_ed25519"
fi

if [ -f "/workspace/ssh/known_hosts" ]; then
    cp /workspace/ssh/known_hosts ~/.ssh/known_hosts
    chmod 644 ~/.ssh/known_hosts
    echo "SSH known_hosts copied successfully"
else
    echo "Warning: SSH known_hosts not found at /workspace/ssh/known_hosts"
fi

# Only start SSH agent and add key if private key was successfully copied
if [ "$SSH_KEY_AVAILABLE" = true ]; then
    # Start SSH agent
    eval "$(ssh-agent -s)"
    
    # Add SSH key to agent
    if ssh-add ~/.ssh/id_ed25519; then
        echo "SSH key added to agent successfully"
        
        # Test SSH connection to GitHub
        echo "Testing SSH connection to GitHub..."
        if ssh -T git@github.com -o StrictHostKeyChecking=no -o ConnectTimeout=10 2>&1 | grep -q "successfully authenticated"; then
            echo "SSH connection to GitHub successful"
        else
            echo "Warning: SSH connection to GitHub failed, but continuing..."
            # Add GitHub to known_hosts if not present
            ssh-keyscan -H github.com >> ~/.ssh/known_hosts 2>/dev/null
        fi
    else
        echo "Warning: Failed to add SSH key to agent"
        SSH_KEY_AVAILABLE=false
    fi
else
    echo "Warning: SSH private key not available, using HTTPS for git operations"
fi

export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
else
    echo "Creating new bench..."

    bench init --skip-redis-config-generation frappe-bench

    cd frappe-bench

    # Use containers instead of localhost
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    # Remove redis, watch from Procfile
    sed -i '/redis/d' ./Procfile
    sed -i '/watch/d' ./Procfile

    # Create a new site with the specified configurations
    bench new-site ${SITE_NAME} \
    --force \
    --mariadb-root-password ${MARIADB_ROOT_PASSWORD} \
    --admin-password ${ADMIN_PASSWORD} \
    --no-mariadb-socket
fi

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
supervisorctl restart all

# Clear cache for all sites
clear_cache_all_sites

# Set default site
bench use ${SITE_NAME}

# Only start bench if not in production mode
if [ "${PRODUCTION_MODE:-false}" != "true" ]; then
    echo "Starting bench..."
    bench start
else
    echo "Production mode detected, skipping bench start"
fi
