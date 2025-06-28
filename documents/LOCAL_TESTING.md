# Local Testing Guide for Chores Tracker Backend

This guide provides comprehensive instructions for testing the Chores Tracker backend locally, including the newly enhanced API documentation.

## Table of Contents
- [Quick Start with Docker](#quick-start-with-docker)
- [Alternative: Python Virtual Environment](#alternative-python-virtual-environment)
- [Accessing the API Documentation](#accessing-the-api-documentation)
- [Testing the API](#testing-the-api)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

## Quick Start with Docker

This is the recommended approach as it ensures consistent environment setup.

### 1. Prerequisites
- Docker Desktop installed and running
- Git (to clone the repository)
- A text editor or IDE

### 2. Environment Setup

```bash
# If you haven't already, copy the environment template
cp .env.sample .env

# Generate a secure JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edit `.env` and update with your generated secret key:
```env
# MySQL Configuration
MYSQL_ROOT_PASSWORD=rootpassword123
MYSQL_DATABASE=chores_db
MYSQL_USER=chores_user
MYSQL_PASSWORD=chorespass123

# API Configuration
DATABASE_URL=mysql+aiomysql://chores_user:chorespass123@mysql:3306/chores_db
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE
DEBUG=True
ENVIRONMENT=development
BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
ACCESS_TOKEN_EXPIRE_MINUTES=11520
```

### 3. Start the Application

```bash
# Start all services (MySQL + API)
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f api
```

The API will be available at `http://localhost:8000`

### 4. Verify Setup

```bash
# Check health endpoint
curl http://localhost:8000/api/v1/healthcheck

# Expected response:
# {"status":"ok"}
```

## Alternative: Python Virtual Environment

For faster development iteration without Docker:

### 1. Install MySQL locally
```bash
# macOS with Homebrew
brew install mysql@5.7
brew services start mysql@5.7

# Create database and user
mysql -u root -e "CREATE DATABASE chores_db;"
mysql -u root -e "CREATE USER 'chores_user'@'localhost' IDENTIFIED BY 'chorespass123';"
mysql -u root -e "GRANT ALL PRIVILEGES ON chores_db.* TO 'chores_user'@'localhost';"
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 3. Update .env for Local MySQL
```env
DATABASE_URL=mysql+aiomysql://chores_user:chorespass123@localhost:3306/chores_db
```

### 4. Run Migrations
```bash
cd backend
alembic upgrade head
```

### 5. Start the API
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Accessing the API Documentation

### Interactive Documentation (Swagger UI)
Open your browser and navigate to:
```
http://localhost:8000/docs
```

Here you can:
- View all endpoints with descriptions and examples
- Try out API calls directly from the browser
- See request/response schemas
- View authentication requirements

### Alternative Documentation (ReDoc)
For a different documentation style:
```
http://localhost:8000/redoc
```

### OpenAPI Schema
Raw OpenAPI JSON specification:
```
http://localhost:8000/api/v1/openapi.json
```

## Testing the API

### 1. Register a Parent Account
```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testparent&password=TestPass123&email=parent@example.com&is_parent=true"

# Using httpie (install with: pip install httpie)
http --form POST localhost:8000/api/v1/users/register \
  username=testparent \
  password=TestPass123 \
  email=parent@example.com \
  is_parent=true
```

### 2. Login to Get Token
```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testparent&password=TestPass123"

# Save the token from response
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Create a Child Account
```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer $TOKEN" \
  -d "username=testchild&password=ChildPass123&is_parent=false"
```

### 4. Create a Chore
```bash
curl -X POST http://localhost:8000/api/v1/chores/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Clean Room",
    "description": "Vacuum and organize",
    "reward": 5.0,
    "assignee_id": 2,
    "is_recurring": true,
    "cooldown_days": 7
  }'
```

### 5. View All Endpoints in Documentation
Visit `http://localhost:8000/docs` to see all available endpoints with examples!

## Running Tests

### With Docker
```bash
# Run all tests
docker-compose exec api python -m pytest

# Run with coverage
docker-compose exec api python -m pytest --cov=backend/app --cov-report=html

# Run specific test file
docker-compose exec api python -m pytest backend/tests/api/v1/test_users.py

# Run tests with output
docker-compose exec api python -m pytest -vv -s
```

### Without Docker (in virtual environment)
```bash
cd backend

# Set testing environment
export TESTING=true
export DATABASE_URL=sqlite+aiosqlite:///:memory:

# Run tests
python -m pytest

# Run with coverage report
python -m pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# Or: start htmlcov/index.html  # Windows
```

## Common API Testing Scenarios

### Test Chore Workflow
```bash
# 1. Parent creates chore (using saved $TOKEN)
CHORE_ID=$(curl -s -X POST http://localhost:8000/api/v1/chores/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Chore","reward":5,"assignee_id":2}' \
  | jq -r '.id')

# 2. Login as child
CHILD_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/users/login \
  -d "username=testchild&password=ChildPass123" \
  | jq -r '.access_token')

# 3. Child completes chore
curl -X POST http://localhost:8000/api/v1/chores/$CHORE_ID/complete \
  -H "Authorization: Bearer $CHILD_TOKEN"

# 4. Parent approves chore
curl -X POST http://localhost:8000/api/v1/chores/$CHORE_ID/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reward_value": 5.0}'
```

## Troubleshooting

### Docker Issues

1. **Port already in use**
   ```bash
   # Stop services using the ports
   lsof -ti:8000 | xargs kill -9
   lsof -ti:3306 | xargs kill -9
   ```

2. **Database connection errors**
   ```bash
   # Restart services
   docker-compose down
   docker-compose up --build
   ```

3. **Clean restart**
   ```bash
   # Remove volumes and rebuild
   docker-compose down -v
   docker-compose up --build
   ```

### Python Environment Issues

1. **Module import errors**
   ```bash
   # Ensure you're in virtual environment
   which python  # Should show venv path
   
   # Reinstall requirements
   pip install -r requirements.txt
   ```

2. **Database migration errors**
   ```bash
   # Reset database
   cd backend
   alembic downgrade base
   alembic upgrade head
   ```

### API Testing Issues

1. **401 Unauthorized**
   - Check token is correctly set in Authorization header
   - Verify token hasn't expired (8 days by default)
   - Ensure "Bearer " prefix is included

2. **422 Validation Error**
   - Check request body matches schema
   - View detailed error in response body
   - Refer to `/docs` for correct schema

3. **View Logs**
   ```bash
   # Docker logs
   docker-compose logs -f api
   
   # Or check Python console output if running directly
   ```

## Useful Commands Summary

```bash
# Start services
docker-compose up

# View API docs
open http://localhost:8000/docs

# Run tests
docker-compose exec api python -m pytest

# View logs
docker-compose logs -f api

# Access MySQL
docker-compose exec mysql mysql -u root -p

# Stop everything
docker-compose down
```

## Next Steps

1. Explore the interactive API documentation at `/docs`
2. Run the test suite to ensure everything works
3. Try creating a complete chore workflow
4. Check the enhanced schema documentation
5. Test the HTMX endpoints for the web interface

For more details, see:
- [CLAUDE.md](./CLAUDE.md) - Development instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Tests](./backend/tests) - Example test implementations