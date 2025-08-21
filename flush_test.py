import sys

print("Testing output flush...")
print("This message should be visible")
sys.stdout.flush()

# Test importing the autopilot module
try:
    from src.soft.autopilot.__main__ import main
    print("Import successful")
    sys.stdout.flush()
except Exception as e:
    print(f"Import error: {e}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
