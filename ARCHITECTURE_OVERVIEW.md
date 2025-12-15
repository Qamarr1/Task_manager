# Architecture Overview

## System Pieces
- **Flask web app (`app.py`)**: Handles routing, session-based auth, task CRUD, health/metrics endpoints, and server-side rendering via Jinja templates in `templates/` with styling from `static/style.css`.
- **Configuration layer (`config.py`)**: Loads environment-driven settings (SQLite vs Azure SQL, secrets, instrumentation keys) and feeds them into the Flask app at startup.
- **Data layer (`database.py`, `schema.sql`)**: Provides a small repository abstraction that can talk to local SQLite (default) or Azure SQL (production) using the same CRUD interface; `init_azure_sql.py` and `schema.sql` bootstrap schema.
- **Observability**: Structured logs to stdout and `app.log`; optional OpenCensus exporters to Azure Application Insights; Prometheus counters/histograms exposed at `/metrics`; health probe at `/health`.
- **Containerization & runtime**: Gunicorn process model (`gunicorn_config.py`) inside the Docker image (`Dockerfile`/`Dockerfile.simple`); `docker-compose.yml` optionally adds Prometheus and Grafana alongside the app.
- **CI/CD & delivery**: GitHub Actions workflow builds/tests the app, builds the container, and deploys to Azure App Service with environment variables for Azure SQL and Application Insights.

**Diagram — Components at a Glance**
```text
[Users/Browsers]
    |
    v
[Flask (app.py)]
    |-- Config load -> [config.py]
    |-- Templates/CSS -> [templates/, static/]
    |-- CRUD + Auth -> [database.py -> SQLite | Azure SQL]
    |-- Health/Metrics -> [/health, /metrics]
    |
    |--> Logs/Traces -> [App Insights*]
    '-- Metrics -> [Prometheus] -> [Grafana]

[CI/CD: GitHub Actions] -> [Docker Image] -> [Azure App Service]
```

## Textual System Diagram
```text
[Users/Browsers]
    |
    | HTTPS
    v
[Flask UI + API (app.py) running via Gunicorn]
    |-- Serves HTML/CSS (templates/, static/)
    |-- Auth + task CRUD + health/metrics endpoints
    |
    |--> Read/write -> [SQLite (dev) | Azure SQL (prod)]
    |
    |--> Logs + traces -> [Azure Application Insights]*        (*when key set)
    |
    '-- Metrics (/metrics) -> [Prometheus] -> [Grafana dashboards]

[CI/CD: GitHub Actions] -> build/test -> Docker image -> deploy to [Azure App Service]
```

## Layered Stack
- **Presentation**: Jinja templates (`templates/index.html`, `templates/errors/*`) and `static/style.css` deliver the UI for task lists, filters, and auth.
- **Application/Service**: Flask routes in `app.py` manage sessions, validation, task operations, status transitions, and serialize responses (HTML or JSON).
- **Data/Repository**: `database.py` chooses SQLite or Azure SQL based on environment; `schema.sql` and `ensure_schema_columns()` keep schema aligned across environments.
- **Observability & Quality**: Logging + optional App Insights exporters, Prometheus client metrics, health endpoint, and automated tests in `tests/` executed by CI.
- **Infrastructure/Delivery**: Gunicorn process manager, Docker image, `docker-compose.yml` for local app+Prometheus+Grafana stack, and Azure App Service hosting backed by Azure SQL.

**Diagram — Layered View**
```text
┌──────────────────────────────────────────┐
│ Presentation: templates/, static/style.css│
├──────────────────────────────────────────┤
│ Application: Flask routes in app.py       │
│  - Auth, task CRUD, filters, search       │
│  - Health/metrics endpoints               │
├──────────────────────────────────────────┤
│ Data/Repository: database.py              │
│  - get_db_connection() selects SQLite/Azure│
│  - schema.sql + ensure_schema_columns()    │
├──────────────────────────────────────────┤
│ Observability/Quality: logging, App Insights│
│  Prometheus client, tests/ in CI           │
├──────────────────────────────────────────┤
│ Infrastructure/Delivery: Gunicorn, Docker, │
│  docker-compose, Azure App Service + SQL   │
└──────────────────────────────────────────┘
```

## High-Level System Architecture
- Requests arrive from browsers to Azure App Service (or Docker runtime), are served by Gunicorn workers that dispatch into Flask route handlers.
- On startup, the app reads environment variables to pick the config profile and database driver; each request requiring data calls `get_db_connection()` to obtain the correct SQLite or Azure SQL connection.
- Task operations (create/edit/delete/toggle/move) manipulate the `tasks` table, with user ownership enforced via session `user_id`; `ensure_schema_columns()` guards against missing optional columns across database flavors.
- Cross-cutting concerns: logging is emitted for all key events; `/health` enables liveness/readiness checks; `/metrics` exposes Prometheus counters/histograms when the client library is installed.
- Monitoring topology: in compose-based dev, Prometheus scrapes the app and Grafana visualizes dashboards; in Azure, OpenCensus sends telemetry to Application Insights while App Service handles process management and scaling.
- CI/CD pipeline runs tests, builds the container, and deploys to Azure with a startup command (`gunicorn --config gunicorn_config.py app:app`); environment variables provide secrets, DB connectivity, and instrumentation keys.

**Diagram — Request, Data, and Observability Flow**
```text
   HTTPS
Users ────────────────► Azure App Service (Gunicorn)
                         |
                         | Flask routes/app.py
                         v
                  SQLite (dev) │ Azure SQL (prod)
                         |
                         | Logs/Traces*        Metrics
                         |                     (/metrics)
                         v                     v
               Application Insights*      Prometheus -> Grafana

CI/CD: GitHub Actions -> Docker build -> Deploy to Azure App Service
* App Insights active when instrumentation key is set
```
