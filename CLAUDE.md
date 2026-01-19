# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ignis Academy LMS - A learning management system built on Frappe Framework with a Vue 3 frontend. The app provides course management, batches, certifications, quizzes, assignments, and an AI Tutor integration.

## Development Commands

### Starting Development Server
```bash
bench start  # Run from ignis_academy directory, starts all services
```
Access the site at `http://academy.local:8000/lms` (requires hosts file entry for academy.local)

### Frontend Development
```bash
cd frontend && yarn dev     # Vite dev server with HMR
cd frontend && yarn build   # Production build
```

### Running Tests
```bash
# Backend tests (Frappe test framework)
bench --site academy.local run-tests --app lms --coverage

# Single test module
bench --site academy.local run-tests --app lms --module lms.lms.test_utils

# Cypress UI tests (headless)
bench --site academy.local run-ui-tests lms --headless

# Cypress interactive mode
yarn test-local
```

### Linting and Formatting
```bash
# Python - uses Ruff
ruff check lms/                    # Lint
ruff format lms/                   # Format
ruff check --select=I --fix lms/   # Sort imports

# Frontend - uses Prettier/ESLint
cd frontend && npx prettier --write src/
cd frontend && npx eslint src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Database and Site Management
```bash
bench --site academy.local backup           # Create backup
bench --site academy.local restore <file>   # Restore backup
bench --site academy.local doctor           # Check site status
bench --site academy.local list-apps        # List installed apps
```

## Architecture

### Backend (Frappe App)
- **Framework**: Frappe (Python web framework with ORM)
- **App Name**: `frappe_lms` (hooks.py defines this)
- **Python**: ≥3.10

Key directories:
- `lms/lms/doctype/` - Frappe doctypes (data models with controllers)
- `lms/lms/api.py` - Main API endpoints
- `lms/lms/ai_tutor.py` - AI Tutor proxy to external LangChain service
- `lms/hooks.py` - App configuration, routes, scheduled tasks
- `lms/patches/` - Database migration scripts

### Frontend (Vue SPA)
- **Framework**: Vue 3 + Vite + Vue Router
- **UI Library**: Frappe UI (`frappe-ui` package)
- **State**: Pinia stores in `frontend/src/stores/`
- **Styling**: TailwindCSS with Frappe UI preset

Key directories:
- `frontend/src/pages/` - Page components (route targets)
- `frontend/src/components/` - Reusable components
- `frontend/src/router.js` - Route definitions

### AI Tutor Integration
The AI Tutor is a chat feature integrated into lesson pages:
- Backend: `lms/lms/ai_tutor.py` - `ask_tutor()` proxies to external LangChain service
- Frontend: `frontend/src/components/AiTutorChat.vue` - Chat UI component
- Config: Set `ai_tutor_api_url` in site config (default: http://localhost:7999)

### URL Routing
Frontend routes are under `/lms/*` and handled by Vue Router. Key patterns:
- `/lms/courses/:courseName` - Course detail
- `/lms/courses/:courseName/learn/:chapterNumber-:lessonNumber` - Lesson view
- `/lms/batches/:batchName` - Batch detail

Backend routes and redirects are configured in `hooks.py` (website_route_rules, website_redirects).

## Code Style

### Python
- **Indentation**: Tabs
- **Line length**: 110 chars
- **Quotes**: Double quotes
- **Formatter**: Ruff
- **Import sorting**: Ruff with isort-style grouping

### JavaScript/Vue
- **Indentation**: Tabs
- **Quotes**: Single quotes
- **Semicolons**: None
- **Formatter**: Prettier

### Git Commits
Uses conventional commits (enforced by CI):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code refactoring
- `test:` test changes
