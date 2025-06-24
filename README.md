<div align="center" markdown="1">

<img src=".github/lms-logo.png" alt="Frappe Learning logo" width="80" height="80"/>
<h1>Ignis Academy</h1>

</div>

# Installation Options

## 🐳 Docker Installation (Recommended)

For a quick and easy setup using Docker, see the [Docker Setup Guide](docker/README.md).

### Quick Start with Docker:

1. Navigate to the docker directory:
   ```bash
   cd docker
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your configuration:
   ```bash
   # Database Configuration
   MARIADB_ROOT_PASSWORD=your_secure_password
   MYSQL_ROOT_PASSWORD=your_secure_password
   
   # Site Configuration
   SITE_NAME=your_site_name
   ADMIN_PASSWORD=your_admin_password
   
   # Development Configuration
   DEVELOPER_MODE=1
   ```

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access your site at `http://localhost:8000`

For detailed Docker setup instructions, troubleshooting, and configuration options, see the [Docker README](docker/README.md).

---

# Manual Installation (Local Setup)

If you prefer to install Frappe Framework manually on your local machine, follow the instructions below:

## Install Frappe Framework

## 1. Install Ubuntu on Windows using WSL(Windows Subsystem for Linux):
 
  `wsl --install`

## 2. Follow the instructions from the documentation (section Debian/Ubuntu)

https://docs.frappe.io/framework/user/en/installation

### ⚠️ Note: At the last step, run this command: `bench init ignis_academy` ⚠️

>## ⚙️ Frappe Setup Notes (if something fails)
>
>This README documents common errors encountered during the setup of Frappe Framework inside WSL on Windows, and how they were resolved.
>
>---
>
>### ❗ Error 1: `mariadb-secure-installation` — Access Denied for Root
>
>**Message:**
>```
>ERROR 1698 (28000): Access denied for user 'root'@'localhost'
>```
>
>**Cause:**
>MariaDB uses `unix_socket` authentication for `root`, so you can't log in as root unless you're the Linux root user.
>
>**Solution:**
>Run the following:
>
>```bash
>sudo mariadb-secure-installation
>```
>
>---
>
>### ❗ Error 2: `npm` Error After Installing `nvm`
>
>**Message:**
>```
>npm ERR! enoent ENOENT: no such file or directory, lstat 'C:\Users\Attila\AppData\Roaming\npm'
>```
>
>**Cause:**
>A conflict between Windows and WSL environments; WSL is trying to access Windows paths.
>
>**Solution:**
>Ignore the error if you're in WSL. Instead, use `nvm` to install Node.js inside WSL:
>
>```bash
>export NVM_DIR="$HOME/.nvm"
>[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
>
>nvm install --lts
>nvm use --lts
>```
>
>---
>
>### ❗ Error 3: `wkhtmltox` Dependency Problem
>
>**Message:**
>```
>wkhtmltox depends on xfonts-75dpi; however:
>Package xfonts-75dpi is not installed.
>```
>
>**Solution:**
>Install the missing dependency first:
>
>```bash
>sudo apt update
>sudo apt install -y xfonts-75dpi
>```
>
>Then re-install the `.deb` package:
>
>```bash
>sudo dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb
>```
>
>---
>
>### ❗ Error 4: `pip install frappe-bench` Blocked
>
>**Message:**
>```
>error: externally-managed-environment
>```
>
>**Cause:**
>Ubuntu protects system Python; pip cannot install globally.
>
>**Solution 1: Use pipx**
>```bash
>sudo apt install pipx
>pipx install frappe-bench
>```
>
>---
>
>### ❗ Error 5: Git Extensions → WSL Git Fails to Read Config
>
>**Message:**
>```
>External program returned non-zero exit code.
>git config --includes --get user.name
>```
>
>**Cause:**
>- WSL Git isn't configured
>- Git Extensions can't access WSL properly
>- Wrong WSL distro name
>
>**Solution:**
>1. Ensure Git is installed in WSL:
>   ```bash
>   sudo apt install git
>   ```
>
>2. Set Git config inside WSL:
>   ```bash
>   git config --global user.name "Your Name"
>   git config --global user.email "you@example.com"
>   ```
>---
>
>### ✅ Notes
>
>- Copy files to Ubuntu with the following command: `cp /mnt/c/<path to file in windows> .`


## 3. Set hosts file

You have to add the following line to the hosts file in `C:/Windows/system32/drivers/etc` folder:
```
127.0.0.1 academy.local
```

## 4. Install our LMS app

```bash
cd ignis_academy
# Clone your custom Academy LMS app from private repository
bench get-app lms git@github.com:ExarLabs/academy-lms.git
```

Alternative for HTTPS:
```bash
# If SSH is not configured, use HTTPS (requires token for private repos)
bench get-app lms https://github.com/ExarLabs/academy-lms.git
```

## 5. Database User Setup

```bash
# Access MySQL as root
sudo mysql -u root

# Create frappe user with full privileges
CREATE USER 'frappe'@'localhost' IDENTIFIED BY 'pass';
GRANT ALL PRIVILEGES ON *.* TO 'frappe'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

## 6. MySQL Configuration

```bash
# Edit MySQL configuration file
sudo nano /etc/mysql/my.cnf

# Add the following configuration:
[client]
user = frappe
password = pass
```

**Purpose**: Configures default MySQL credentials for bench operations.

**Potential Issues**:
- ⚠️ **File Location**: On some systems, config might be in `/etc/mysql/mysql.conf.d/mysqld.cnf`

## 7. Create site

```bash
bench new-site academy.local
```

## 8. Install App on Site

```bash
# Install the LMS app on your academy.local site
bench --site academy.local install-app lms
```

**Purpose**: Installs the LMS application on the specified site.


## 9. Database Restoration

```bash
# Restore database from backup file
bench --site academy.local restore db_backups/20250603_164306-academy_local-database.sql.gz
```

**Purpose**: Restores a previously backed up database.

**Potential Issues**:
- ⚠️ **File Path**: Ensure backup file exists at specified location

## 10. Start Development Server

```bash
# Start bench development server (run in separate terminal)
bench start
```

**Purpose**: Starts the development server for testing.

**Note**: This should be run in a separate terminal tab/window as it's a blocking process.

## Verification Steps

After setup, verify everything works:

```bash
# Check site status
bench --site academy.local doctor

# List installed apps
bench --site academy.local list-apps

# Access the site
# Frappe editor: http://academy.local:8000/app/lms
# The page itself: http://academy.local:8000/lms
```

## Backup Commands

```bash
# Create database backup
bench --site academy.local backup (--with-files)

# List backups
bench --site academy.local list-backups

# Restore specific backup
bench --site academy.local restore [backup-file]
```

## 11. Install AI Tutor Chat App
- Download the app:
    - `bench get-app ai_tutor_chat git@github.com/ExarLabs/academy-ai-tutor-chat` or `bench get-app ai_tutor_chat https://github.com/ExarLabs/academy-ai-tutor-chat`, then:
- Install the app:
    - `bench --site academy.local install-app ai_tutor_chat`

### Description
This Frappe application contains the backend implementation of the AI Tutor Chat.
It defines the endpoints that are called by the AI Tutor Chat Vue component integrated into the LMS app.
This application will act as a proxy between the LMS app and the LangChain service.
