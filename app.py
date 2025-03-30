"""
OMIFI Voice Assistant - Web Dashboard

A Flask web application that serves as a web dashboard for the OMIFI assistant.
"""

import os
import json
import logging
import subprocess
import threading
from datetime import datetime

from flask import Flask, render_template, jsonify, send_file, redirect, url_for

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "omifi_dev_secret")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
METADATA_PATH = os.path.expanduser("~/.omifi/metadata.json")
SCREENSHOTS_DIR = os.path.expanduser("~/.omifi/screenshots")
CLIPBOARD_DIR = os.path.expanduser("~/.omifi/clipboard")
LOG_FILE = os.path.expanduser("~/.omifi/logs/omifi.log")

# Status tracking
omifi_process = None

def get_omifi_status():
    """Check if the OMIFI desktop application is running."""
    global omifi_process
    
    if omifi_process and omifi_process.poll() is None:
        return True
    
    # Try to find OMIFI process using pgrep
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*main.py"],
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception as e:
        logger.error(f"Error checking OMIFI status: {e}")
        return False

def load_metadata():
    """Load the OMIFI metadata file."""
    try:
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
    
    # Default metadata structure
    return {
        "screenshots": [],
        "clipboard": []
    }

@app.route('/')
def index():
    """Render the main dashboard page."""
    metadata = load_metadata()
    
    # Sort screenshots by timestamp (newest first)
    screenshots = sorted(
        metadata.get("screenshots", []),
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:20]  # Limit to 20 most recent
    
    # Sort clipboard items by timestamp (newest first)
    clipboard_items = sorted(
        metadata.get("clipboard", []),
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:50]  # Limit to 50 most recent
    
    # Format timestamps
    for item in screenshots + clipboard_items:
        if "timestamp" in item:
            try:
                dt = datetime.fromisoformat(item["timestamp"])
                item["formatted_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                item["formatted_time"] = item["timestamp"]
    
    # Check OMIFI status
    omifi_running = get_omifi_status()
    
    return render_template(
        'dashboard.html',
        screenshots=screenshots,
        clipboard_items=clipboard_items,
        omifi_running=omifi_running
    )

@app.route('/start', methods=['POST'])
def start_omifi():
    """Start the OMIFI desktop application."""
    global omifi_process
    
    if get_omifi_status():
        return jsonify({"status": "already_running"})
    
    try:
        # Start OMIFI in the background
        omifi_process = subprocess.Popen(
            ["python", "main.py"],
            start_new_session=True
        )
        
        # Give it a moment to start
        import time
        time.sleep(2)
        
        status = "started" if get_omifi_status() else "failed"
        return jsonify({"status": status})
    
    except Exception as e:
        logger.error(f"Error starting OMIFI: {e}")
        return jsonify({"status": "failed", "error": str(e)})

@app.route('/stop', methods=['POST'])
def stop_omifi():
    """Stop the OMIFI desktop application."""
    global omifi_process
    
    if not get_omifi_status():
        return jsonify({"status": "not_running"})
    
    try:
        # Try to terminate gracefully first
        subprocess.run(
            ["pkill", "-f", "python.*main.py"],
            check=False
        )
        
        # Give it a moment to stop
        import time
        time.sleep(1)
        
        # Force kill if still running
        if get_omifi_status():
            subprocess.run(
                ["pkill", "-9", "-f", "python.*main.py"],
                check=False
            )
        
        omifi_process = None
        return jsonify({"status": "stopped"})
    
    except Exception as e:
        logger.error(f"Error stopping OMIFI: {e}")
        return jsonify({"status": "failed", "error": str(e)})

@app.route('/status')
def status():
    """Get the status of the OMIFI desktop application."""
    return jsonify({"running": get_omifi_status()})

@app.route('/clipboard/<path:filepath>')
def get_clipboard(filepath):
    """Get clipboard content by filepath."""
    try:
        # Ensure the path is within the clipboard directory
        full_path = os.path.join(CLIPBOARD_DIR, os.path.basename(filepath))
        
        if not os.path.exists(full_path):
            return "File not found", 404
            
        with open(full_path, 'r') as f:
            content = f.read()
            
        return content
    
    except Exception as e:
        logger.error(f"Error reading clipboard content: {e}")
        return f"Error: {str(e)}", 500

@app.route('/screenshot/<path:filepath>')
def get_screenshot(filepath):
    """Serve screenshot images."""
    try:
        # Ensure the path is within the screenshots directory
        full_path = os.path.join(SCREENSHOTS_DIR, os.path.basename(filepath))
        
        if not os.path.exists(full_path):
            return "Image not found", 404
            
        return send_file(full_path)
    
    except Exception as e:
        logger.error(f"Error serving screenshot: {e}")
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)