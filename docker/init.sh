#!/bin/bash

# Function: check if app is installed on site
is_app_installed() {
    APP_NAME=$1
    SITE=$2
    
    # Check if app is listed in the site's installed apps
    # Use a more flexible grep pattern to handle different output formats
    if bench --site ${SITE} list-apps | grep -q "${APP_NAME}"; then
        return 0  # App is installed
    else
        return 1  # App is not installed
    fi
}

# Function: get or update app
get_or_update_app() {
    APP_NAME=$1
    REPO_URL=$2
    SITE=$3

    # Check if app directory exists
    if [ -d "apps/${APP_NAME}" ]; then
        echo "App ${APP_NAME} directory already exists."
        
        # Check if app is installed on the site
        if is_app_installed ${APP_NAME} ${SITE}; then
            echo "App ${APP_NAME} is already installed on site ${SITE}. Updating..."
            cd apps/${APP_NAME}
            
            # Configure git pull strategy to handle divergent branches
            git config pull.rebase true
            git pull ${REPO_URL} docker || git pull ${REPO_URL} master || echo "Failed to pull latest changes, continuing with existing version"
            
            cd ../../
            
            # Update the app on the site (migrate and rebuild)
            echo "Migrating ${APP_NAME} on site ${SITE}..."
            bench --site ${SITE} migrate --skip-failing || echo "Migration completed with some warnings"
            echo "Building assets for ${APP_NAME}..."
            bench build --app ${APP_NAME} || echo "Asset build completed with warnings"
        else
            echo "App ${APP_NAME} exists but not installed on site ${SITE}. Installing..."
            if ! bench --site ${SITE} install-app ${APP_NAME}; then
                echo "Failed to install ${APP_NAME} on site ${SITE}"
                return 1
            fi
        fi
    else
        echo "App ${APP_NAME} not found. Cloning from ${REPO_URL}..."
        if ! bench get-app ${APP_NAME} ${REPO_URL}; then
            echo "Failed to clone ${APP_NAME} from ${REPO_URL}"
            return 1
        fi
        
        # Install app on site
        echo "Installing ${APP_NAME} on site ${SITE}..."
        if ! bench --site ${SITE} install-app ${APP_NAME}; then
            echo "Failed to install ${APP_NAME} on site ${SITE}"
            return 1
        fi
    fi
    
    echo "${APP_NAME} successfully processed on ${SITE}"
}

# Function: check if site exists
site_exists() {
    SITE=$1
    if [ -d "sites/${SITE}" ] && [ -f "sites/${SITE}/site_config.json" ]; then
        return 0  # Site exists
    else
        return 1  # Site does not exist
    fi
}

# Function: get all existing sites
get_all_sites() {
    # List all directories in sites/ that have site_config.json
    for site_dir in sites/*/; do
        if [ -d "$site_dir" ] && [ -f "${site_dir}site_config.json" ]; then
            basename "$site_dir"
        fi
    done
}

# Function: update apps on all sites
update_apps_on_all_sites() {
    APP_NAME=$1
    REPO_URL=$2
    
    echo "Getting list of all existing sites..."
    SITES=$(get_all_sites)
    
    if [ -z "$SITES" ]; then
        echo "No existing sites found, will install on ${SITE_NAME} only"
        get_or_update_app ${APP_NAME} ${REPO_URL} ${SITE_NAME}
    else
        echo "Found existing sites, updating ${APP_NAME} on all sites..."
        for site in $SITES; do
            echo "Processing ${APP_NAME} for site: $site"
            get_or_update_app ${APP_NAME} ${REPO_URL} $site
        done
    fi
}

# Function: apply configuration to all sites
apply_config_to_all_sites() {
    CONFIG_KEY=$1
    CONFIG_VALUE=$2
    
    echo "Setting ${CONFIG_KEY} configuration for all sites..."
    SITES=$(get_all_sites)
    
    if [ -z "$SITES" ]; then
        echo "No existing sites found, setting config on ${SITE_NAME} only"
        bench --site ${SITE_NAME} set-config ${CONFIG_KEY} ${CONFIG_VALUE}
    else
        for site in $SITES; do
            echo "Setting ${CONFIG_KEY} for site: $site"
            bench --site $site set-config ${CONFIG_KEY} ${CONFIG_VALUE}
        done
    fi
}

# Function: clear cache for all sites
clear_cache_all_sites() {
    echo "Clearing cache for all sites..."
    SITES=$(get_all_sites)
    
    if [ -z "$SITES" ]; then
        echo "No existing sites found, clearing cache on ${SITE_NAME} only"
        bench --site ${SITE_NAME} clear-cache
    else
        for site in $SITES; do
            echo "Clearing cache for site: $site"
            bench --site $site clear-cache
        done
    fi
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

echo "Starting bench..."
bench start
