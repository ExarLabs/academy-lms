# GEMINI.md

## Project Overview

This project is a Learning Management System (LMS) called Ignis Academy. It is a full-stack web application built with the Frappe framework for the backend and Vue.js for the frontend. The application features include course and lesson management, user and batch management, an AI Tutor Chat, SCORM support, and more.

### Technologies

*   **Backend:** Frappe (Python)
*   **Frontend:** Vue.js, `frappe-ui`
*   **Testing:** Cypress (E2E)

### Architecture

The project is a monorepo containing the Frappe app (`lms`) and the frontend app (`frontend`).

*   The `lms` directory contains the Frappe application, which provides the backend API and serves the frontend.
*   The `frontend` directory contains the Vue.js application, which is the user interface for the LMS.
*   The `cypress` directory contains the end-to-end tests for the application.

## Building and Running

### Prerequisites

*   Frappe Framework
*   Node.js and Yarn

### Installation

1.  Follow the Frappe Framework installation guide.
2.  Clone the `lms` app into your Frappe bench.
3.  Install the app on your site.

### Running the Development Server

To run the development server for both the backend and frontend, use the following command:

```bash
bench start
```

This will start the Frappe development server and the Vite development server for the frontend.

### Building for Production

To build the frontend for production, use the following command:

```bash
npm run build
```

This will create a production-ready build of the frontend in the `frontend/dist` directory.

### Running Tests

To run the Cypress end-to-end tests, use the following command:

```bash
npm run test-local
```

## Development Conventions

### Code Style

*   **Python:** The project uses `flake8` for linting.
*   **JavaScript/Vue:** The project uses `eslint` and `prettier` for linting and formatting.

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code style and run linters before committing code. The configuration can be found in the `.pre-commit-config.yaml` file.

### Contribution Guidelines

Please refer to the `Contribution.md` file for contribution guidelines.
