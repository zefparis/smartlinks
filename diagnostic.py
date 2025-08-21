import sys
import os
import importlib

print("=== Diagnostic Script ===")
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)
print("=========================")

# Check if the autopilot module exists
print("Checking autopilot module...")
try:
    spec = importlib.util.find_spec("src.soft.autopilot")
    if spec is None:
        print("Module src.soft.autopilot not found")
    else:
        print("Module src.soft.autopilot found at:", spec.origin)
except Exception as e:
    print("Error finding module:", e)

# Check if the __main__.py file exists in autopilot directory
autopilot_main_path = os.path.join("src", "soft", "autopilot", "__main__.py")
print(f"Checking {autopilot_main_path}...")
if os.path.exists(autopilot_main_path):
    print(f"{autopilot_main_path} exists")
else:
    print(f"{autopilot_main_path} does not exist")

# Try to run the module
print("Attempting to run module...")
try:
    import subprocess
    result = subprocess.run([sys.executable, "-m", "src.soft.autopilot"], 
                          cwd=os.getcwd(), capture_output=True, text=True, timeout=10)
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except Exception as e:
    print("Error running module:", e)
