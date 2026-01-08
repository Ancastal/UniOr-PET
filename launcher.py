"""
Heroku Launcher - Routes to appropriate Streamlit app based on environment variable

This launcher allows deploying both translator and manager interfaces
from the same codebase by setting the APP_MODE environment variable.

Usage:
1. For Translator App:
   Set Heroku config: APP_MODE=translator (or leave unset)

2. For Manager App:
   Set Heroku config: APP_MODE=manager

Set environment variable via:
   heroku config:set APP_MODE=manager -a your-manager-app-name
   heroku config:set APP_MODE=translator -a your-translator-app-name
"""
import os
import sys
from streamlit.web import cli as stcli

def main():
    # Check for APP_MODE environment variable (set via Heroku config vars)
    app_mode = os.environ.get('APP_MODE', 'translator')

    # Determine which app to run
    if app_mode == 'manager':
        app_file = 'management/0_🏢_Manager.py'
        print("🏢 Starting Project Manager Dashboard...")
    else:
        app_file = 'app.py'
        print("📝 Starting Translator Interface...")

    # Set up Streamlit CLI arguments
    sys.argv = [
        "streamlit",
        "run",
        app_file,
        "--server.port=" + os.environ.get('PORT', '8501'),
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]

    # Run Streamlit
    sys.exit(stcli.main())

if __name__ == '__main__':
    main()
