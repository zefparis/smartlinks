import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

try:
    print("Testing basic print functionality...")
    print("Hello World - this should be visible")
    
    # Test importing from src.soft.autopilot
    print("Attempting to import autopilot module...")
    from src.soft.autopilot import __main__
    print("Autopilot module imported successfully")
    
    # Test the main function
    print("Calling main function...")
    __main__.main()
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
