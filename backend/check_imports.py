import sys
import os

# Ensure the current directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("--- CHECKING IMPORTS ---")
try:
    print("Checking toolkit.py...")
    import toolkit
    print("✅ toolkit.py OK.")

    print("\nChecking agent_factory.py...")
    import agent_factory
    print("✅ agent_factory.py OK.")

    print("\nChecking main.py...")
    import main
    print("✅ main.py OK.")

    print("\n🎉 All imports successful!")

except Exception as e:
    print("\n❌ IMPORT FAILED. Here is the real error:")
    # Print the full traceback to find the exact line
    import traceback
    traceback.print_exc()