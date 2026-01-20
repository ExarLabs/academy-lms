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
- `lms/lms/langchain_integrations.py` - LangChain event broker (quiz/assignment/enrollment/certificate events)
- `lms/hooks.py` - App configuration, routes, scheduled tasks, doc_events
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

### LangChain Event Broker System
An event-driven system that sends LMS events to an external LangChain service for AI processing:

**Architecture:**
1. Document events (quiz, assignment, enrollment, certificate) trigger handlers in `lms/lms/langchain_integrations.py`
2. Handlers enqueue background jobs via `frappe.enqueue()` (requires Redis workers)
3. Background job sends structured payload to LangChain AI Tutor API
4. Response received synchronously and stored via `post_langchain_response`
5. Response stored in `Langchain Responses` DocType and pushed via `frappe.publish_realtime()`
6. Frontend receives real-time update via Socket.IO

**Key files:**
- `lms/lms/langchain_integrations.py` - Event handlers, message builder, and response storage
- `lms/lms/doctype/langchain_responses/` - DocType for storing AI responses
- `lms/hooks.py` - Document event hooks (`doc_events` section)

**Document event hooks:**
- `LMS Course Progress.on_update` → `handle_course_progress_update`
- `LMS Quiz Submission.after_insert` → `handle_quiz_submission`
- `LMS Assignment Submission.after_insert` → `handle_assignment_submission`
- `LMS Assignment Submission.on_update` → `handle_assignment_status_update`
- `LMS Enrollment.after_insert` → `handle_enrollment`
- `LMS Certificate.after_insert` → `handle_certificate_issued`

**Config:** `LANGCHAIN_SERVICE_URL` constant (default: http://langchain-service:7999/api/v1/ai/tutor/chat)

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

### CLAUDE.md Auto-Update Hook
A pre-commit hook in `.claude/hooks/pre-commit` uses Claude Code CLI to automatically update this file when architectural changes are committed. Enable with:
```bash
git config core.hooksPath .claude/hooks
```
Skip with `git commit --no-verify` for minor changes.
