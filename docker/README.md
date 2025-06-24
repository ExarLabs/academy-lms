# Frappe LMS Docker Setup

This directory contains the professional Docker configuration for the Frappe LMS application.

## Files

- `docker-compose.yml` - Docker Compose configuration
- `init.sh` - Initialization script
- `.env` - Environment variables (do not commit!)
- `.env.example` - Environment variables template
- `ssh/` - SSH keys for Git access

## Setup

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your own values:
   ```bash
   # Database Configuration
   MARIADB_ROOT_PASSWORD=your_secure_password
   
   # Site Configuration
   SITE_NAME=academy.local
   ADMIN_PASSWORD=your_admin_password
   
   # Development Configuration
   DEVELOPER_MODE=1
   ```

3. Ensure SSH keys are in the `.ssh/` directory:
   - `id_ed25519` - Private SSH key
   - `id_ed25519.pub` - Public SSH key
   - `known_hosts` - Known host keys
   
   Note: The SSH keys should be in `apps/lms/docker/.ssh/` directory and will be automatically mounted into the container.

## Starting the Application

```bash
docker-compose up -d
```

## Stopping the Application

```bash
docker-compose down
```

## Viewing Logs

```bash
docker-compose logs -f frappe
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MARIADB_ROOT_PASSWORD` | MariaDB root password | 123 |
| `SITE_NAME` | Site name | academy.hu |
| `ADMIN_PASSWORD` | Administrator user login password | admin |
| `DEVELOPER_MODE` | Developer mode | 1 |
| `NODE_VERSION_DEVELOP` | Node.js version | 18 |
| `LMS_REPO_URL` | LMS repository URL | git@github.com:ExarLabs/academy-lms.git |
| `AI_TUTOR_REPO_URL` | AI Tutor repository URL | git@github.com:ExarLabs/academy-ai-tutor-chat.git |
| `AI_TUTOR_API_URL` | AI Tutor API endpoint | http://langchain-api:8000 |

## Security Notes

- Never commit the `.env` file!
- Use strong passwords in production environments
- Keep SSH keys secure
- Disable developer mode in production (`DEVELOPER_MODE=0`)

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Restart services: `docker-compose restart`
3. Full rebuild: `docker-compose down && docker-compose up --build`

## LangChain Integration

This setup is designed to work with a separate LangChain API service. The AI Tutor Chat functionality connects to the LangChain service via the `AI_TUTOR_API_URL` environment variable.

### Network Configuration

The Frappe container connects to the `langchain-network` to communicate with the LangChain API service. Make sure the LangChain service is running and accessible at the configured URL.

### Configuration

The AI Tutor API URL is automatically configured in the Frappe site config during initialization. The chat.py module reads this configuration using:

```python
ai_tutor_api_url = frappe.conf.get("ai_tutor_api_url", "http://localhost:7999")
```

## Production Deployment

For production deployment:

1. Set strong passwords in `.env`
2. Set `DEVELOPER_MODE=0`
3. Configure proper SSL certificates
4. Set up proper backup strategies for MariaDB data
5. Consider using Docker secrets for sensitive data
6. Ensure LangChain API service is properly configured and secured
