@echo off
echo Setting up SmartLinks Autopilot RCP system...

echo.
echo Step 1: Testing Python and dependencies...
python -c "import sys; print('Python version:', sys.version)"

echo.
echo Step 2: Testing Alembic installation...
python -c "import alembic; print('Alembic available')" 2>nul || (
    echo Installing Alembic...
    pip install alembic
)

echo.
echo Step 3: Running database migrations...
python -c "
from alembic.config import Config
from alembic import command
import os

try:
    alembic_cfg = Config('alembic.ini')
    command.upgrade(alembic_cfg, 'head')
    print('✅ Migrations completed successfully!')
except Exception as e:
    print(f'❌ Migration error: {e}')
"

echo.
echo Step 4: Testing RCP imports...
python -c "
try:
    from src.soft.pac.schemas import PacPolicy
    from src.soft.rcp.api import router
    print('✅ RCP modules imported successfully!')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo.
echo Step 5: Starting server test...
echo You can now run: python start_debug.py
echo API documentation will be available at: http://localhost:8000/docs

pause
