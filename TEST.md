# SmartLinks Autopilot - Test Validation Guide

This document provides comprehensive validation commands to test the SmartLinks Autopilot system after cleanup and migration.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Ensure .env file exists with required variables
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

2. **Dependencies Installed**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd src/frontend && npm install
   ```

## Backend API Testing

### 1. Start Backend Server
```bash
# Option 1: Using Python directly
python src/backend/main.py

# Option 2: Using Makefile
make backend

# Option 3: Using run script
python scripts/run_dev.py --backend-only
```

### 2. Health Check Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# Analytics health
curl http://localhost:8000/api/analytics/health

# AI Supervisor status
curl http://localhost:8000/api/ia/status
```

### 3. Analytics Endpoints
```bash
# Device statistics
curl "http://localhost:8000/api/analytics/devices?days=30&limit=10"

# Country statistics  
curl "http://localhost:8000/api/analytics/countries?days=30&limit=10"

# Click history (should not return 500 error)
curl "http://localhost:8000/api/analytics/clicks/history?days=7"

# Traffic by segment
curl "http://localhost:8000/api/analytics/traffic-by-segment?days=30"

# Schema documentation
curl http://localhost:8000/api/analytics/schema
```

### 4. Settings Endpoints
```bash
# Get settings
curl http://localhost:8000/api/settings

# Update settings (POST with JSON)
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"app_name": "SmartLinks Test", "timezone": "UTC"}'
```

### 5. AI Supervisor Endpoints
```bash
# Ask AI a question
curl -X POST http://localhost:8000/api/ia/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the system status?"}'

# System analysis
curl http://localhost:8000/api/ia/analyze

# Get supervisor status
curl http://localhost:8000/api/ia/status

# List available algorithms
curl http://localhost:8000/api/ia/algorithms
```

## Frontend Testing

### 1. Start Frontend Server
```bash
# Option 1: Direct npm command
cd src/frontend && npm run dev

# Option 2: Using Makefile
make frontend

# Option 3: Using run script
python scripts/run_dev.py --frontend-only
```

### 2. Frontend Validation Checklist

**Analytics Dashboard (http://localhost:5173/analytics)**
- [ ] Page loads without 404 errors
- [ ] Traffic chart displays data or "No data available"
- [ ] Device pie chart renders properly
- [ ] Country list shows data or fallback message
- [ ] No console errors related to undefined data
- [ ] API calls return normalized arrays

**Settings Page (http://localhost:5173/settings)**
- [ ] Form loads with default values
- [ ] All form fields are properly mapped to backend config
- [ ] Save button works without form validation errors
- [ ] Service status indicators show proper states
- [ ] Danger zone actions have confirmation modals

**General Frontend**
- [ ] No TypeScript compilation errors (warnings acceptable)
- [ ] Vite proxy correctly forwards /api calls to localhost:8000
- [ ] Dark/light theme switching works
- [ ] Navigation between pages functions properly

## Full Stack Integration Testing

### 1. Start Both Services
```bash
# Option 1: Using development script
python scripts/run_dev.py

# Option 2: Using Makefile
make dev

# Option 3: Manual (two terminals)
# Terminal 1: python src/backend/main.py
# Terminal 2: cd src/frontend && npm run dev
```

### 2. End-to-End Validation
```bash
# Test API proxy through frontend
curl http://localhost:5173/api/health

# Verify CORS headers
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/api/analytics/devices
```

## Database Testing

### 1. Database Operations
```bash
# Seed test data
curl -X POST http://localhost:8000/api/admin/seed

# Check database health
python -c "
from src.soft.database import get_db
from src.soft.models import Click, Conversion
db = next(get_db())
print(f'Clicks: {db.query(Click).count()}')
print(f'Conversions: {db.query(Conversion).count()}')
"
```

### 2. Analytics Data Validation
```bash
# Verify click history returns complete date ranges
curl "http://localhost:8000/api/analytics/clicks/history?days=7" | jq '.history | length'

# Check for proper timestamp handling
curl "http://localhost:8000/api/analytics/clicks/history?days=1" | jq '.history[0]'
```

## AI Supervisor Testing

### 1. OpenAI Integration
```bash
# Test AI connectivity (requires OPENAI_API_KEY)
curl -X POST http://localhost:8000/api/ia/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, are you working?"}'

# Test system analysis
curl http://localhost:8000/api/ia/analyze | jq '.recommendations'
```

### 2. Algorithm Execution
```bash
# List available algorithms
curl http://localhost:8000/api/ia/algorithms | jq '.algorithms'

# Check supervisor logs
curl http://localhost:8000/api/ia/logs | jq '.logs[-5:]'
```

## Performance Testing

### 1. Load Testing (Optional)
```bash
# Install Apache Bench if not available
# Test analytics endpoint performance
ab -n 100 -c 10 http://localhost:8000/api/analytics/devices

# Test click history endpoint
ab -n 50 -c 5 "http://localhost:8000/api/analytics/clicks/history?days=30"
```

### 2. Memory Usage
```bash
# Monitor backend memory usage
ps aux | grep "python.*main.py"

# Check for memory leaks during extended usage
# Run analytics calls in loop and monitor memory
```

## Error Scenarios Testing

### 1. Database Errors
```bash
# Test with invalid date ranges
curl "http://localhost:8000/api/analytics/clicks/history?days=999999"

# Test with missing parameters
curl "http://localhost:8000/api/analytics/devices?limit=invalid"
```

### 2. AI Supervisor Errors
```bash
# Test without OpenAI API key
OPENAI_API_KEY="" curl -X POST http://localhost:8000/api/ia/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

## Cleanup Script Testing

### 1. Dry Run Validation
```bash
# Test cleanup script in dry-run mode
python scripts/cleanup_repo.py --dry-run

# Verify no files are actually deleted
git status
```

### 2. Backup and Restore
```bash
# Create backup before cleanup
python scripts/cleanup_repo.py --backup

# Run actual cleanup
python scripts/cleanup_repo.py --execute

# Verify system still works after cleanup
make dev
```

## Expected Results

### ✅ Success Criteria
- All API endpoints return 200 status codes (not 404/500)
- Frontend loads without console errors
- Analytics data displays properly or shows appropriate fallbacks
- Settings form saves successfully
- AI Supervisor responds to queries (with valid API key)
- Database operations complete without errors
- Vite proxy forwards API calls correctly
- CORS headers allow frontend-backend communication

### ❌ Failure Indicators
- 500 errors on /api/analytics/clicks/history
- 404 errors on any /api endpoints
- Frontend crashes due to undefined data
- TypeScript compilation failures
- Database connection errors
- OpenAI API failures (without proper fallback)
- CORS blocking frontend requests

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 8000 and 5173 are available
2. **Environment variables**: Verify .env file has required keys
3. **Dependencies**: Run `pip install -r requirements.txt` and `npm install`
4. **Database**: Check SQLite file permissions and path
5. **OpenAI**: Verify API key is valid and has credits

### Debug Commands
```bash
# Check backend logs
tail -f autopilot.log

# Check frontend console
# Open browser dev tools and monitor console

# Verify environment
python check_env.py

# Test database connection
python debug_db_connection.py
```

## Deployment Testing

### 1. Docker Testing (Optional)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Test containerized services
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

### 2. Production Readiness
- [ ] Environment variables properly configured
- [ ] Database migrations applied
- [ ] Static files served correctly
- [ ] Error handling graceful
- [ ] Logging configured appropriately
- [ ] Security headers present

---

## Test Completion Checklist

- [ ] Backend starts without errors
- [ ] Frontend builds and serves successfully  
- [ ] All API endpoints respond correctly
- [ ] Analytics dashboard displays data
- [ ] Settings page functions properly
- [ ] AI Supervisor integration works
- [ ] Database operations succeed
- [ ] No critical console errors
- [ ] CORS and proxy configurations work
- [ ] Cleanup script runs safely

**Test Status**: ✅ PASS / ❌ FAIL  
**Date**: ___________  
**Tester**: ___________  
**Notes**: ___________
