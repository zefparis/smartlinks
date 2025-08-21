import sys
import os

# Write output to a file to bypass terminal issues
output_file = "autopilot_test_output.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== Autopilot Module Test ===\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write("=============================\n")
    
    try:
        f.write("Attempting to import autopilot __main__ module...\n")
        from src.soft.autopilot.__main__ import main
        f.write("Import successful\n")
        
        f.write("Calling main function...\n")
        main()
        f.write("Main function executed\n")
        
    except Exception as e:
        f.write(f"Error occurred: {e}\n")
        import traceback
        f.write("Traceback:\n")
        f.write(traceback.format_exc())
        
print(f"Test results written to {output_file}")
