import subprocess
import os
import sys


def run_script(script_path):
    print(f"--- Running {script_path} ---")
    result = subprocess.run([sys.executable, script_path],
                            capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Errors in {script_path}:")
        print(result.stderr)
    return result.returncode == 0


def main():
    # 1. Init Database
    if not run_script('db/init_db.py'):
        print("Failed to initialize database.")
        return

    # 2. Fetch data from Open Food Facts
    if not run_script('scripts/fetch_off.py'):
        print("Failed to fetch data from Open Food Facts.")

    # 3. Fetch data from USDA (Note: Requires API key in .env or DEMO_KEY will be used)
    if not run_script('scripts/fetch_usda.py'):
        print("Failed to fetch data from USDA.")

    # 4. Init Vector Database
    if not run_script('db/init_vector.py'):
        print("Failed to initialize vector database.")

    print("--- Pipeline execution completed ---")


if __name__ == "__main__":
    main()
