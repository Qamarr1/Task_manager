# Task Manager - Cloud DevOps Project

A cloud-native task management application built with Python Flask.

## Project Status

- Sprint 0: Complete - Local environment set up
- Sprint 1: In Progress - Building core application

## Tech Stack

- Backend: Python Flask
- Database: SQLite (local) → Azure SQL (production)
- Hosting: Azure App Service
- CI/CD: Azure DevOps

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run application:
```bash
python app.py
```

4. Visit http://localhost:8000

## Development

- Flask runs on port 8000
- Debug mode enabled
- Auto-reload on code changes