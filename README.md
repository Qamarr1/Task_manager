# Task Manager

Lightweight task management web app built with Flask. This repository contains the application, database helpers, tests, and a simple local Docker Compose stack.

**Status:** Local development supported (SQLite). Azure SQL support is present in the codebase but not required for local development.

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/Wilyam390/Task_Manager.git
cd Task_Manager
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```


5. **Initialize the database**
```bash
python init_db.py
```

6. **Run the application**
```bash
python app.py
```

7. **Visit the application**
```
http://localhost:8000
```



## Azure deployment (production)

The production deployment for this project is available as an Azure App Service named **`qamar-taskmgr-web`**. The app in production connects to an Azure SQL database (production configuration).

Azure App Service link (portal):

https://portal.azure.com/#@teciehst.onmicrosoft.com/resource/subscriptions/e0b9cada-61bc-4b5a-bd7a-52c606726b3b/resourceGroups/BCSAI2025-DEVOPS-STUDENT-8B/providers/Microsoft.Web/sites/qamar-taskmgr-web/appServices





# Task Manager - Cloud DevOps Project

A cloud-native task management application built with Python Flask and deployed on Microsoft Azure.

##  Monitoring & Logging

### Application Insights Dashboard

**Key Metrics Tracked:**
- Request count and response times
- Failed requests and exceptions
- Server response time
- Dependency calls (database queries)
- Custom events and traces

**Production:**
- Azure Application Insights

"https://portal.azure.com/#@teciehst.onmicrosoft.com/resource/subscriptions/e0b9cada-61bc-4b5a-bd7a-52c606726b3b/resourceGroups/BCSAI2025-DEVOPS-STUDENT-8B/providers/microsoft.insights/components/appi-qamar-taskmgr/overview"

Response:
```json
{
  "status": "healthy",
  "tasks_count": 5,
  "environment": "production",
  "database": "azure_sql"
}
```

##  Testing

### Run All Tests
```bash
All tests:
pytest -q

Run all tests with coverage (terminal summary):
pytest --cov=. --cov-report=term -q

App tests only:
pytest tests/test_app.py -q

Integration tests only:
pytest tests/test_integration.py -q

Run integration tests (quiet):
pytest tests/test_integration.py -q


```


### Run Tests with Coverage
```bash
pytest --cov=app --cov=config --cov=database --cov-report=term --cov-report=html tests/ -v
```

60 passed



```text
Name                        Stmts   Miss  Cover
-----------------------------------------------
app.py                        560    148    74%
config.py                      21      0   100%
database.py                   142     57    60%
gunicorn_config.py             23     23     0%
init_azure_sql.py              43     43     0%
tests/conftest.py              12      3    75%
tests/test_app.py             449      7    98%
tests/test_config.py           35      0   100%
tests/test_database.py         91      2    98%
tests/test_integration.py     126      7    94%
-----------------------------------------------
TOTAL                        1502    290
```
## Demo accounts (for testing)

- Local (development) demo account —
 username: `led` or email: `led@gamil.com`, password: `123456`. Use this account for local testing only.
- Dev/production demo account, there are 5 , but i will put the 4 usernames and you can choose which one 
 username: `qamar  grace ibr abd`, password: `123456`. These are /demo credentials .


##  Architecture

### Azure Services Used

1. **Azure App Service** - Web application hosting (PaaS)
2. **Azure SQL Database** - Managed relational database
3. **Azure Application Insights** - Application monitoring and telemetry
4. **GitHub Actions** - CI/CD pipelines and automation
5. **Azure Monitor** - Logging and dashboards

### Architecture Diagram

```
┌─────────────────┐
│   Users/Clients │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   Azure App Service         │
│   (Flask Application)       │
│   - Gunicorn WSGI Server    │
│   - Auto-scaling enabled    │
└────────┬──────────┬─────────┘
         │          │
         │          ▼
         │    ┌──────────────────────┐
         │    │ Application Insights │
         │    │ - Telemetry          │
         │    │ - Performance        │
         │    │ - Logging            │
         │    └──────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Azure SQL Database     │
│  - Tasks table          │
│  - Automated backups    │
└─────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11, Flask 3.0
- **Database:** SQLite (local) / Azure SQL (production)
- **Monitoring:** Azure Application Insights, OpenCensus, Prometheus
- **Testing:** Pytest with coverage
- **CI/CD:** GitHub Actions
- **Deployment:** Gunicorn, Azure App Service, Docker
- **Version Control:** Git, GitHub


## Running with Docker (local only)

This project includes a lightweight Docker Compose setup for local testing and monitoring. The Compose file builds a local-friendly image which uses SQLite by default (no external Azure SQL driver required).

1. Build and start the stack:

```bash
docker-compose up --build -d
```

2. Check service status:

```bash
docker-compose ps
```

``` Run container (map port 8000):
docker run --name task-manager -p 8000:8000 -e DB_TYPE=sqlite -d task-manager
```
3. Tail the application logs:

```bash
docker-compose logs -f app
```

4. Health check (after containers are up):

```bash
curl http://localhost:8000/health
```
---

##  Project Structure

```
Task_Manager/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── database.py                 # Database abstraction layer
├── init_db.py                  # Database initialization script
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies       
├── Dockerfile                  # Docker container configuration
├── docker-compose.yml         # Multi-container orchestration         
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── ARCHITECTURE.md            # Detailed system architecture
├── INDIVIDUAL_report.pdf
│
├── .github/
│   └── workflows/
│       └── azure-deploy.yml   # CI/CD pipeline
│
├── static/
│   └── style.css              # Application styles
│
├── templates/
│   ├── index.html             # Main page template
│   └── errors/
│       ├── 404.html           # Not found page
│       └── 500.html           # Server error page
│
└── tests/
    ├── test_app.py            # Application tests
    ├── test_config.py         # Configuration tests
    ├── test_database.py       # Database tests
    └── test_integration.py    # Integration tests
```



