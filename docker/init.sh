#!bin/bash

# Function: get or update app
get_or_update_app() {
    APP_NAME=$1
    REPO_URL=$2
    SITE=$3

    if [ -d "apps/${APP_NAME}" ]; then
        echo "App ${APP_NAME} already exists. Pulling latest changes..."
        cd apps/${APP_NAME}
        git pull origin main || git pull origin master || echo "Failed to pull latest changes, continuing with existing version"
        cd ../../
    else
        echo "App ${APP_NAME} not found. Cloning from ${REPO_URL}..."
        if ! bench get-app ${APP_NAME} ${REPO_URL}; then
            echo "Failed to clone ${APP_NAME} from ${REPO_URL}"
            return 1
        fi
    fi

    # Install app on site
    echo "Installing ${APP_NAME} on site ${SITE}..."
    if ! bench --site ${SITE} install-app ${APP_NAME}; then
        echo "Failed to install ${APP_NAME} on site ${SITE}"
        return 1
    fi
    
    echo "${APP_NAME} successfully installed on ${SITE}"
}


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
    bench start
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

# Install the LMS app
get_or_update_app lms ${LMS_REPO_URL} ${SITE_NAME}

# Install the AI Tutor Chat app
get_or_update_app ai_tutor_chat ${AI_TUTOR_REPO_URL} ${SITE_NAME}

bench --site ${SITE_NAME} set-config developer_mode ${DEVELOPER_MODE}
bench --site ${SITE_NAME} clear-cache
bench use ${SITE_NAME}

bench start
