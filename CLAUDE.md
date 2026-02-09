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
- `lms/langchain/` - LangChain integration module (AI Tutor, event broker)
- `lms/shared_data_service/` - Shared data service integration (profiles, statistics)
- `lms/hooks.py` - App configuration, routes, scheduled tasks, doc_events
- `lms/patches/` - Database migration scripts

### Frontend (Vue SPA)
- **Framework**: Vue 3 + Vite + Vue Router
- **UI Library**: Frappe UI (`frappe-ui` package)
- **State**: Pinia stores in `frontend/src/stores/`
- **Styling**: TailwindCSS with Frappe UI preset

Key directories:
- `frontend/src/pages/` - Page components (route targets)
  - `LearnerAnalytics.vue` - Admin dashboard for learner statistics
- `frontend/src/components/` - Reusable components
- `frontend/src/router.js` - Route definitions
- `frontend/src/utils/index.js` - Sidebar menu configuration

### LangChain Integration Module (`lms/langchain/`)
A modular integration with external LangChain service for AI features:

**Module structure:**
```
lms/langchain/
├── __init__.py                    # Package exports
├── config.py                      # Configuration helpers (use_redis_mode, get_langchain_service_url, get_ai_tutor_url)
├── repositories.py                # Data persistence layer (save_langchain_response, response_exists)
├── communication/                 # Infrastructure (HTTP + Redis)
│   ├── http/
│   │   ├── client.py              # HTTP client for LangChain API (with retry/backoff)
│   │   └── messages.py            # Event message builder (build_event_message)
│   └── redis/
│       ├── client.py              # Redis client + pubsub helpers
│       └── pubsub/
│           └── publisher.py       # Redis pub/sub publisher
├── lms_events/                    # LMS document events feature
│   ├── api.py                     # send_frontend_event() endpoint for frontend-triggered events
│   ├── broker.py                  # LangchainMessageBroker - uses Strategy pattern with pluggable transports
│   ├── events.py                  # EventType enum - centralized event type definitions
│   ├── handlers.py                # 6 document event handlers (use EventType enum)
│   ├── subscriber.py              # Redis pub/sub subscriber for LangChain responses
│   └── transports/                # Pluggable transport layer (Strategy pattern)
│       ├── base.py                # EventTransport abstract base class
│       ├── http.py                # HttpEventTransport - async via Frappe queue
│       └── redis.py               # RedisEventTransport - direct pub/sub with HTTP fallback
├── tutor_chat/                    # AI Tutor chat feature
│   ├── api.py                     # ask_tutor() chat endpoint, post_langchain_response() callback
│   ├── streaming.py               # Streaming response orchestration (subscribe_and_forward_to_socketio)
│   ├── stream_subscriber.py       # TutorStreamSubscriber for AI Tutor streaming via Redis Streams
│   └── adapters/
│       └── socketio.py            # SocketIOStreamAdapter - bridges streaming to Socket.IO
└── utils/                         # Cross-cutting utilities
    └── resilience.py              # retry_on_exception decorator, RetryContext
```

**AI Tutor:**
- Backend: `lms/langchain/tutor_chat/api.py` - `ask_tutor()` proxies to external LangChain service
- Frontend: `frontend/src/components/AiTutorChat.vue` - Chat UI component
- Config: Set `ai_tutor_api_url` in site config (default: http://localhost:7999)

**Event Broker Architecture:**
1. Document events trigger handlers in `lms/langchain/lms_events/handlers.py`
2. Handlers use `LangchainMessageBroker` which selects transport via Strategy pattern:
   - **HTTP transport** (default): Enqueues background job via `frappe.enqueue()`, sends HTTP POST with retry/backoff
   - **Redis transport**: Publishes directly to Redis pub/sub (faster), falls back to HTTP on failure
3. `EventResponseSubscriber` listens on Redis pub/sub for LangChain responses (started via `before_request` hook in web workers)
4. Response stored and pushed via `frappe.publish_realtime()` to specific user
5. Frontend receives real-time update via Socket.IO

**Document event hooks (configured in `hooks.py`):**
- `LMS Course Progress.on_update` → `lms.langchain.lms_events.handlers.handle_course_progress_update`
- `LMS Quiz Submission.after_insert` → `lms.langchain.lms_events.handlers.handle_quiz_submission`
- `LMS Assignment Submission.after_insert` → `lms.langchain.lms_events.handlers.handle_assignment_submission`
- `LMS Assignment Submission.on_update` → `lms.langchain.lms_events.handlers.handle_assignment_status_update`
- `LMS Enrollment.after_insert` → `lms.langchain.lms_events.handlers.handle_enrollment`
- `LMS Certificate.after_insert` → `lms.langchain.lms_events.handlers.handle_certificate_issued`

**Config:** Set `langchain_service_url` in site config (default: http://localhost:7999)

### Shared Data Service Integration (`lms/shared_data_service/`)

HTTP client for communicating with `academy-shared-data-service` (MongoDB-backed):

```
lms/shared_data_service/
├── client.py    # HTTP client with retry logic for profiles and statistics API
└── api.py       # Frappe whitelisted endpoints for admin dashboard
```

**Client functions:**
- `get_user_profile(frappe_user_id)` - Get profile by user ID
- `create_user_profile(...)` - Create new profile
- `update_user_profile(...)` - Partial update (metadata merged)
- `get_stats_overview()` - Aggregated statistics
- `get_learners_stats(skip, limit, search, sort_by)` - Paginated learner list
- `get_learner_detail(user_id)` - Single learner detail

**API endpoints (require admin/instructor role):**
- `lms.shared_data_service.api.get_profile_stats_overview`
- `lms.shared_data_service.api.get_profile_learners_stats`
- `lms.shared_data_service.api.get_profile_learner_detail`

**Config:** Set `shared_data_service_url` and `shared_data_api_key` in site config.

### URL Routing
Frontend routes are under `/lms/*` and handled by Vue Router. Key patterns:
- `/lms/courses/:courseName` - Course detail
- `/lms/courses/:courseName/learn/:chapterNumber-:lessonNumber` - Lesson view
- `/lms/batches/:batchName` - Batch detail
- `/lms/learner-analytics` - Admin dashboard for learner statistics

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
