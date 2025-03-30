"""
OMIFI Voice Assistant - Web Dashboard

A Flask web application that serves as a web dashboard for the OMIFI assistant.
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "omifi-dev-secret-key")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_omifi_status():
    """Check if the OMIFI desktop application is running."""
    try:
        # Check for running OMIFI process (platform-specific)
        if sys.platform == 'win32':
            # Windows
            cmd = 'tasklist /FI "IMAGENAME eq python.exe" /FO CSV'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            return "omifi" in output.lower() or "main.py" in output.lower()
        else:
            # Linux/macOS
            cmd = 'ps aux | grep -i "python.*main.py" | grep -v grep'
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
            return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking OMIFI status: {e}")
        return False

def load_metadata():
    """Load the OMIFI metadata file."""
    metadata_path = os.path.expanduser("~/.omifi/metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading metadata: {e}")
    
    # Return empty metadata if file doesn't exist or can't be loaded
    return {"screenshots": [], "clipboard": []}

@app.route('/')
def index():
    """Render the main dashboard page."""
    is_running = get_omifi_status()
    metadata = load_metadata()
    screenshots = metadata.get("screenshots", [])
    clipboard = metadata.get("clipboard", [])
    
    # Sort by timestamp (newest first)
    screenshots = sorted(screenshots, key=lambda x: x.get("timestamp", ""), reverse=True)
    clipboard = sorted(clipboard, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return render_template(
        'dashboard.html',
        is_running=is_running,
        screenshots=screenshots[:10],  # Limit to 10 most recent
        clipboard=clipboard[:10]       # Limit to 10 most recent
    )

@app.route('/start')
def start_omifi():
    """Start the OMIFI desktop application."""
    if not get_omifi_status():
        try:
            # Start OMIFI in the background
            subprocess.Popen([sys.executable, "main.py"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             start_new_session=True)
            time.sleep(2)  # Give it time to start
        except Exception as e:
            logger.error(f"Error starting OMIFI: {e}")
    
    return redirect(url_for('index'))

@app.route('/stop')
def stop_omifi():
    """Stop the OMIFI desktop application."""
    if get_omifi_status():
        try:
            # This is a simplistic approach - in a real app, you'd use a proper IPC mechanism
            if sys.platform == 'win32':
                # Windows
                subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/T"], check=False)
            else:
                # Linux/macOS
                subprocess.run("pkill -f 'python.*main.py'", shell=True, check=False)
        except Exception as e:
            logger.error(f"Error stopping OMIFI: {e}")
    
    return redirect(url_for('index'))

@app.route('/status')
def status():
    """Get the status of the OMIFI desktop application."""
    return jsonify({"running": get_omifi_status()})

@app.route('/clipboard/<path:filepath>')
def get_clipboard(filepath):
    """Get clipboard content by filepath."""
    try:
        fullpath = os.path.join(os.path.expanduser("~/.omifi/clipboard"), filepath)
        # Check if file exists and is within the clipboard directory
        if os.path.exists(fullpath) and os.path.commonpath([fullpath, os.path.expanduser("~/.omifi/clipboard")]) == os.path.expanduser("~/.omifi/clipboard"):
            with open(fullpath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "File not found or invalid path", 404
    except Exception as e:
        logger.error(f"Error retrieving clipboard content: {e}")
        return str(e), 500

@app.route('/screenshots/<path:filepath>')
def get_screenshot(filepath):
    """Serve screenshot images."""
    try:
        fullpath = os.path.join(os.path.expanduser("~/.omifi/screenshots"), filepath)
        # Check if file exists and is within the screenshots directory
        if os.path.exists(fullpath) and os.path.commonpath([fullpath, os.path.expanduser("~/.omifi/screenshots")]) == os.path.expanduser("~/.omifi/screenshots"):
            return send_file(fullpath)
        else:
            return "File not found or invalid path", 404
    except Exception as e:
        logger.error(f"Error retrieving screenshot: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)