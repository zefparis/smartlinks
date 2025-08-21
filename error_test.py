import sys
import traceback

print("=== Error Test Script ===")
print("Python version:", sys.version)
print("Platform:", sys.platform)
print("=========================")

try:
    print("Attempting to run autopilot module...")
    from src.soft.autopilot.__main__ import main
    print("Import successful, calling main()...")
    main()
    print("Main function executed successfully")
except Exception as e:
    print("ERROR OCCURRED:")
    print("Type:", type(e).__name__)
    print("Message:", str(e))
    print("Full traceback:")
    traceback.print_exc()
except SystemExit as e:
    print("SystemExit caught:")
    print("Code:", e.code)
    traceback.print_exc()
