#!/bin/bash

# Common functions shared between init.sh and production-init.sh
# This file contains all shared functionality to avoid code duplication

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

# Function: get all existing sites
get_all_sites() {
    # List all directories in sites/ that have site_config.json
    for site_dir in sites/*/; do
        if [ -d "$site_dir" ] && [ -f "${site_dir}site_config.json" ]; then
            basename "$site_dir"
        fi
    done
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

# Function: check if site exists
site_exists() {
    SITE=$1
    if [ -d "sites/${SITE}" ] && [ -f "sites/${SITE}/site_config.json" ]; then
        return 0  # Site exists
    else
        return 1  # Site does not exist
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
            
            # Reset any conflicts and discard local changes
            echo "Resetting git state and discarding local changes..."
            git reset --hard HEAD 2>/dev/null || true
            git clean -fd 2>/dev/null || true
            
            # Configure git pull strategy to handle divergent branches
            git config pull.rebase false
            
            # Force fetch and reset to remote branch
            if git fetch ${REPO_URL} master 2>/dev/null && git reset --hard FETCH_HEAD 2>/dev/null; then
                echo "Successfully updated from master branch"
            else
                echo "Failed to pull latest changes, continuing with existing version"
            fi
            
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
