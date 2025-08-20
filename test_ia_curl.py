#!/usr/bin/env python3
"""
Test IA endpoints with curl commands
"""
import json

# Test commands to verify IA functionality
test_commands = {
    "health": "curl -X GET http://localhost:8000/api/ia/health",
    "status": "curl -X GET http://localhost:8000/api/ia/status", 
    "ask": '''curl -X POST http://localhost:8000/api/ia/ask \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Hello, can you help me test the system?"}'''',
    "selfcheck": "curl -X GET http://localhost:8000/api/ia/selfcheck"
}

print("=== TESTS CURL POUR IA SERVICE ===")
print()

for name, cmd in test_commands.items():
    print(f"## Test {name.upper()}")
    print(f"```bash")
    print(cmd)
    print("```")
    print()

print("=== TESTS POWERSHELL (Windows) ===")
print()

powershell_commands = {
    "health": "Invoke-RestMethod -Uri 'http://localhost:8000/api/ia/health' -Method Get",
    "status": "Invoke-RestMethod -Uri 'http://localhost:8000/api/ia/status' -Method Get",
    "ask": '''$body = @{question = "Hello, can you help me test the system?"} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/ia/ask' -Method Post -Body $body -ContentType 'application/json' ''',
    "selfcheck": "Invoke-RestMethod -Uri 'http://localhost:8000/api/ia/selfcheck' -Method Get"
}

for name, cmd in powershell_commands.items():
    print(f"## Test {name.upper()} (PowerShell)")
    print(f"```powershell")
    print(cmd)
    print("```")
    print()

print("=== RÉSULTATS ATTENDUS ===")
print("""
1. /api/ia/health -> {"status": "healthy", "openai_available": true}
2. /api/ia/status -> {"mode": "auto", "openai_status": "available", ...}
3. /api/ia/ask -> {"response": "...", "status": "success"}
4. /api/ia/selfcheck -> {"status": "ok", "openai_test": "success"}
""")
