#      Task Manager - Cloud DevOps Project

A cloud-native task management application built with Python Flask and deployed on Microsoft Azure.

## 📚 Documentation Quick Links

| Document | Description |
|----------|-------------|
| **[README.md](README.md)** | Project overview, setup, and usage (this file) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Detailed system architecture and design |
| **[SCRUM_DOCUMENTATION.md](SCRUM_DOCUMENTATION.md)** | Complete Scrum artifacts and sprint history |
| **[DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md)** | Quality criteria for all work items |
| **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** | Presentation guide for demo |
| **[INDIVIDUAL_CONTRIBUTION_TEMPLATE.md](INDIVIDUAL_CONTRIBUTION_TEMPLATE.md)** | Template for individual submissions |
| **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** | Docker deployment instructions |

---

## 🚀 Project Overview

This is a full-stack web application demonstrating modern DevOps practices including CI/CD, cloud deployment, monitoring, and automated testing. Built as part of IE University's Software Development and DevOps course.

**Team Members:** Development Team  
**Sprint Status:** Sprint 4 Complete - Enhanced Features & Demo Ready  
**Demo Date:** December 4, 2025

---

## 🏗️ Architecture

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

---

## 📋 Features

### Core Functionality
- ✅ Create, read, update, and delete tasks
- ✅ Mark tasks as complete/incomplete
- ✅ Task due dates with overdue highlighting
- ✅ Filter tasks (All/Active/Completed)
- ✅ Search tasks by title
- ✅ Responsive UI with modern design

### DevOps Features
- ✅ Automated CI/CD pipeline
- ✅ Comprehensive logging (INFO, WARNING, ERROR)
- ✅ Application monitoring with Azure Insights
- ✅ Health check endpoint (`/health`)
- ✅ Error handling with custom error pages
- ✅ Environment-based configuration
- ✅ Database abstraction (SQLite + Azure SQL)

---

## 🐳 Docker Deployment

### Build and Run with Docker

**Build the Docker image:**
```bash
docker build -t task-manager:latest .
```

**Run the container:**
```bash
# Run with SQLite (development)
docker run -p 8000:8000 \
  -e ENVIRONMENT=development \
  -e SECRET_KEY=your-secret-key \
  task-manager:latest

# Run with Azure SQL (production)
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY=your-secret-key \
  -e AZURE_SQL_CONNECTION_STRING="your-connection-string" \
  -e APPINSIGHTS_INSTRUMENTATION_KEY="your-instrumentation-key" \
  task-manager:latest
```

**Access the application:**
- Web UI: http://localhost:8000
- Health check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Docker Compose (with Monitoring)

**Start all services (app + Prometheus + Grafana):**
```bash
docker-compose up -d
```

**Access services:**
- **Task Manager**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

**Stop services:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f app
```

---

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/test_app.py -v
```

### Run Integration Tests
```bash
python -m pytest tests/test_integration.py -v
```

### Run All Tests with Coverage
```bash
python -m pytest --cov=app --cov=config --cov=database \
  --cov-report=term --cov-report=html tests/ -v
```

**View coverage report:**
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Coverage Requirements:**
- Minimum: 70%
- Current: 74% (app.py)

---

## 🚦 Getting Started

### Prerequisites

- Python 3.11+
- pip
- Virtual environment tool
- Azure account (for production deployment)

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

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
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

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Tests with Coverage
```bash
pytest --cov=app --cov=config --cov=database --cov-report=term --cov-report=html tests/ -v
```

### View Coverage Report
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Current Test Stats:**
- ✅ **34 tests** passing
- ✅ **72% code coverage** (exceeds 70% requirement)
- ✅ Tests cover: app.py (72%), config.py (100%), database.py (59%)
- ✅ Test types: Unit tests, Integration tests, Configuration tests

---

## ☁️ Azure Deployment

### Prerequisites

1. Azure subscription
2. GitHub account with repository access
3. Azure CLI installed

### Step 1: Create Azure Resources

```bash
# Login to Azure
az login

# Create resource group
az group create --name taskmanager-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name taskmanager-plan \
  --resource-group taskmanager-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group taskmanager-rg \
  --plan taskmanager-plan \
  --name taskmanager-app \
  --runtime "PYTHON:3.11"

# Create Azure SQL Server
az sql server create \
  --name taskmanager-server \
  --resource-group taskmanager-rg \
  --location eastus \
  --admin-user sqladmin \
  --admin-password <YourStrongPassword>

# Create Azure SQL Database
az sql db create \
  --resource-group taskmanager-rg \
  --server taskmanager-server \
  --name taskmanager-db \
  --service-objective S0

# Create Application Insights
az monitor app-insights component create \
  --app taskmanager-insights \
  --location eastus \
  --resource-group taskmanager-rg \
  --application-type web
```

### Step 2: Configure App Settings

```bash
az webapp config appsettings set \
  --resource-group taskmanager-rg \
  --name taskmanager-app \
  --settings \
    ENVIRONMENT=production \
    DB_TYPE=azure_sql \
    AZURE_SQL_SERVER=taskmanager-server.database.windows.net \
    AZURE_SQL_DATABASE=taskmanager-db \
    AZURE_SQL_USERNAME=sqladmin \
    AZURE_SQL_PASSWORD=<YourPassword> \
    APPINSIGHTS_INSTRUMENTATION_KEY=<YourKey>  # Use this exact name (with underscores)
```

### Step 3: Set Startup Command

```bash
az webapp config set \
  --resource-group taskmanager-rg \
  --name taskmanager-app \
  --startup-file "gunicorn --config gunicorn_config.py app:app"
```

### Step 4: Deploy via GitHub Actions

1. Configure GitHub Secrets in repository settings:
   - `AZURE_CREDENTIALS`
   - `AZURE_WEBAPP_NAME`
   - `AZURE_RESOURCE_GROUP`
   - `AZURE_SQL_CONNECTION_STRING`
   - `APPINSIGHTS_INSTRUMENTATIONKEY`
2. Push to `main` branch to trigger deployment
3. Monitor workflow in GitHub Actions tab

---

## 📊 Monitoring & Logging

### Application Insights Dashboard

Access metrics at: `https://portal.azure.com`

**Key Metrics Tracked:**
- Request count and response times
- Failed requests and exceptions
- Server response time
- Dependency calls (database queries)
- Custom events and traces

### Log Locations

**Local Development:**
- Console output (stdout)
- `app.log` file

**Production:**
- Azure Application Insights
- Azure App Service logs
- Stream logs: `az webapp log tail --name taskmanager-app --resource-group taskmanager-rg`

### Grafana Dashboard (Prometheus)

- Dashboard JSON: `monitoring/grafana-dashboard.json`
- Data source: Prometheus scraping the app at `/metrics` (matches `prometheus.yml` target `app:8000`)
- Import: Grafana → Dashboards → Import → Upload `grafana-dashboard.json`
- Panels: request rate by status, error rate, request latency (p50/p95), task operations rate
- Refresh: 30s; default time range 1h

### Health Check

Monitor application health:
```bash
curl https://taskmanager-app.azurewebsites.net/health
```

Response:
```json
{
  "status": "healthy",
  "tasks_count": 5,
  "environment": "production",
  "database": "azure_sql"
}
```

---

## 📁 Project Structure

```
Task_Manager/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── database.py                 # Database abstraction layer
├── init_db.py                  # Database initialization script
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies
├── gunicorn_config.py         # Production server config
├── Dockerfile                  # Docker container configuration
├── docker-compose.yml         # Multi-container orchestration
├── prometheus.yml             # Prometheus monitoring config
├── monitoring/                # Monitoring assets (Grafana dashboards)
│   └── grafana-dashboard.json # Prometheus-backed service overview
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── ARCHITECTURE.md            # Detailed system architecture
├── SCRUM_DOCUMENTATION.md     # Complete Scrum artifacts
├── DEFINITION_OF_DONE.md      # Quality criteria
├── DEMO_SCRIPT.md             # Presentation guide
├── INDIVIDUAL_CONTRIBUTION_TEMPLATE.md  # Submission template
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

---

## 🔄 CI/CD Pipeline

### Pipeline Stages

1. **Build Stage**
   - Install Python dependencies
   - Run linting (optional)
   - Execute unit tests (34 tests)
   - Generate coverage reports (72% coverage)
   - Build Docker image
   - Archive application

2. **Deploy Stage**
   - Download build artifacts
   - Deploy to Azure App Service
   - Configure environment variables
   - Set startup command (Gunicorn)
   - Restart web app
   - Run health checks

### Pipeline Triggers

- Automatic on push to `main` branch
- Manual trigger available (`workflow_dispatch`)
- Pull request validation

**Pipeline Config:** `.github/workflows/azure-deploy.yml`

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | Environment name (development/production) | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `DB_TYPE` | Database type (sqlite/azure_sql) | Yes |
| `AZURE_SQL_SERVER` | Azure SQL server hostname | Production only |
| `AZURE_SQL_DATABASE` | Database name | Production only |
| `AZURE_SQL_USERNAME` | Database username | Production only |
| `AZURE_SQL_PASSWORD` | Database password | Production only |
| `APPINSIGHTS_INSTRUMENTATION_KEY` | Application Insights key | Production only |

---

## 📝 Sprint History

### Sprint 0 - Preparation
- ✅ Team formation and role assignment
- ✅ Project idea selection
- ✅ Azure subscription setup
- ✅ Initial repository creation

### Sprint 1 - Foundation
- ✅ MVP scope definition
- ✅ Azure environment setup
- ✅ Basic Flask application
- ✅ SQLite database integration
- ✅ Initial deployment

### Sprint 2 - Core Features
- ✅ Complete CRUD operations
- ✅ Frontend UI design
- ✅ Automated testing
- ✅ Basic CI/CD pipeline

### Sprint 3 - Integration & Monitoring
- ✅ Azure SQL Database integration
- ✅ Application Insights monitoring
- ✅ Comprehensive logging
- ✅ Error handling and custom error pages
- ✅ Production-ready deployment automation
- ✅ Environment-based configuration

### Sprint 4 - Enhanced Features & Polish (Complete)
- ✅ Task due dates implementation
- ✅ Task filtering (All/Active/Completed)
- ✅ Search functionality
- ✅ Overdue task highlighting
- ✅ UI enhancements and polish
- ✅ Docker compose with monitoring stack
- ✅ Demo preparation and documentation
- ✅ Comprehensive Scrum artifacts documentation

---

## 📋 Assignment Requirements Checklist

### Core Requirements (100 points)

| Category | Points | Status | Evidence |
|----------|--------|--------|----------|
| **Development & Functionality** | 25 | ✅ | Full-stack Flask app with CRUD, filters, search |
| **Cloud Infrastructure** | 20 | ✅ | 5 Azure services (App Service, SQL, Insights, Monitor, Actions) |
| **DevOps Pipeline** | 20 | ✅ | GitHub Actions CI/CD with build→test→deploy→monitor |
| **Testing & Code Quality** | 15 | ✅ | 34 tests, 72% coverage, automated in pipeline |
| **Monitoring & Logging** | 10 | ✅ | App Insights, Prometheus, structured logging |
| **Documentation & Process** | 10 | ✅ | Complete README, architecture, Scrum docs |

### Optional Extensions (Bonus)

- ✅ **Docker Containerization** - Multi-stage Dockerfile + docker-compose
- ✅ **Infrastructure as Code** - Configuration files ready
- ✅ **Advanced Monitoring** - Prometheus + Grafana stack
- ✅ **Enhanced Features** - Due dates, priorities, categories, filters

**Total Score:** 100+ points (exceeds requirements)

---

## 🎯 Definition of Done

See [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) for complete criteria.

**Summary:**
- [x] Code is written and committed to repository
- [x] Unit tests written and passing (72% coverage)
- [x] Code reviewed by at least one team member
- [x] Application deployed to Azure (or deployment-ready)
- [x] Monitoring and logging configured
- [x] Documentation updated
- [x] Sprint Review conducted

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest tests/`
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature/your-feature`
6. Create a Pull Request

---

## 📞 Support & Contact

For questions or issues:
- Create an issue in the repository
- Contact the development team
- Check GitHub Issues and Projects board

---

## 📜 License

This project is created for educational purposes as part of IE University's BCSAI program.

---

## 🙏 Acknowledgments

- **IE University** - Course materials and guidance
- **Microsoft Azure** - Cloud platform and services
- **Flask Community** - Web framework
- **OpenCensus** - Monitoring and telemetry

---

**Last Updated:** November 30, 2025  
**Project Demo:** December 4, 2025
