@echo off
echo Testing IA Service Directly...
echo.

echo Testing IA Health:
python -c "import requests; import json; try: r = requests.get('http://localhost:8000/api/ia/health', timeout=5); print('Status:', r.status_code); print('Response:', json.dumps(r.json(), indent=2)); except Exception as e: print('Error:', e)"

echo.
echo Testing IA Status:
python -c "import requests; import json; try: r = requests.get('http://localhost:8000/api/ia/status', timeout=5); print('Status:', r.status_code); print('Response:', json.dumps(r.json(), indent=2)); except Exception as e: print('Error:', e)"

echo.
echo Testing IA Ask:
python -c "import requests; import json; try: r = requests.post('http://localhost:8000/api/ia/ask', json={'question': 'Hello, test message'}, timeout=10); print('Status:', r.status_code); print('Response:', json.dumps(r.json(), indent=2)); except Exception as e: print('Error:', e)"

pause
