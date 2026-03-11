AI Hardware Watchdog
A real-time, always-on-top system monitor built for Ubuntu Linux. Designed specifically for live broadcasting environments, this app tracks hardware thermals, network speeds, and disk capacity. It leverages Google's Gemini AI to automatically translate cryptic Linux sensor names and provides instant, actionable IT diagnostics if a system component begins to overheat or fail.
Features
 * Real-Time Telemetry: Tracks CPU temperatures, main drive capacity, and live network upload/download speeds.
 * Smart UI: Borderless, dark-theme interface that stays pinned to the top of your screen. Click the "X" to hide specific sensors, and click "Restore All" to bring them back.
 * AI Auto-Naming: Automatically pings the Gemini API in the background to rename ugly Linux outputs (like coretemp Package id 0) into human-readable names.
 * AI Diagnostics & Alerting: If a sensor crosses a critical threshold (e.g., CPU hits 80°C or disk hits 90% full), the app halts background processes and generates a 3-sentence diagnostic and resolution plan.
 * Silent Logging: Automatically timestamps and saves all AI diagnostic warnings to a local text file (stream_diagnostics.log) so you can review system hiccups after a stream ends.
Prerequisites
Before running the Python script, your Ubuntu system needs the underlying Linux sensor tools installed to read motherboard data.
Open your terminal and run:
sudo apt update
sudo apt install lm-sensors python3-venv
sudo sensors-detect --auto

Installation & Setup
1. Create a Virtual Environment
Navigate to the project folder and create an isolated Python environment:
python3 -m venv env

2. Activate the Environment
source env/bin/activate

3. Install the Required Python Libraries
pip install psutil customtkinter google-genai

Configuration
Before launching the app, you must add your Google Gemini API key to the top of the monitor.py script.
 * Open monitor.py in your text editor.
 * Locate line 9: client = genai.Client(api_key="YOUR_API_KEY_HERE")
 * Replace "YOUR_API_KEY_HERE" with your actual API key.
Adjusting Thresholds:
By default, the AI will only alert you if a temperature sensor exceeds 80.0°C or if your main disk exceeds 90.0% capacity. You can change these limits by modifying self.temp_threshold and self.disk_threshold in the __init__ function.
Usage
To start the monitor, ensure your virtual environment is active, then run the script:
python3 monitor.py

Note: The app will run in a continuous loop until you close the window.
Reviewing Logs
Whenever the AI triggers an alert, it outputs the advice to the UI and writes it to a file for later review. You will find this file in the same directory as your script:
stream_diagnostics.log

