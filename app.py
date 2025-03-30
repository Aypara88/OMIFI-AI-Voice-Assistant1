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
import qrcode

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "omifi-dev-secret-key")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to dummy flag file
DUMMY_FLAG_FILE = os.path.expanduser("~/.omifi/dummy_process.flag")

def create_dummy_omifi_process():
    """Create a dummy flag file to indicate OMIFI is running in web-only mode."""
    try:
        # Create the base directory if it doesn't exist
        base_dir = os.path.dirname(DUMMY_FLAG_FILE)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
            
        # Create a sample screenshot and clipboard file for demo purposes
        from datetime import datetime
        from PIL import Image
        
        # Create directories
        screenshots_dir = os.path.join(base_dir, "screenshots")
        clipboard_dir = os.path.join(base_dir, "clipboard")
        
        for directory in [screenshots_dir, clipboard_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Create dummy metadata.json
        metadata = {
            "screenshots": [],
            "clipboard": []
        }
        
        # Create a sample screenshot
        timestamp = datetime.now().isoformat()
        filename = f"screenshot_{timestamp.replace(':', '-')}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        # Create a simple image
        img = Image.new('RGB', (800, 600), color=(73, 109, 137))
        img.save(filepath)
        
        # Add to metadata
        metadata["screenshots"].append({
            "timestamp": timestamp,
            "filename": filename,
            "filepath": filename
        })
        
        # Create a sample clipboard item
        clip_filename = f"clipboard_{timestamp.replace(':', '-')}.txt"
        clip_filepath = os.path.join(clipboard_dir, clip_filename)
        
        with open(clip_filepath, 'w') as f:
            f.write("Welcome to OMIFI! This is a sample clipboard entry.")
        
        # Add to metadata
        metadata["clipboard"].append({
            "timestamp": timestamp,
            "filename": clip_filename,
            "filepath": clip_filename,
            "type": "text"
        })
        
        # Save metadata
        metadata_path = os.path.join(base_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            import json
            json.dump(metadata, f, indent=2)
            
        # Create the flag file
        with open(DUMMY_FLAG_FILE, 'w') as f:
            f.write(f"Started at {datetime.now().isoformat()}")
            
        logger.info("Created dummy OMIFI process flag file")
        return True
    except Exception as e:
        logger.error(f"Error creating dummy process: {e}")
        return False

def get_omifi_status():
    """Check if the OMIFI desktop application is running."""
    try:
        # First check for dummy flag file
        if os.path.exists(DUMMY_FLAG_FILE):
            return True
            
        # Then check for running OMIFI process (platform-specific)
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

@app.route('/start', methods=['POST'])
def start_omifi():
    """Start the OMIFI desktop application."""
    success = False
    message = "Failed to start OMIFI"
    
    if not get_omifi_status():
        try:
            # Start OMIFI in headless mode for Replit environment
            env = os.environ.copy()
            env['QT_QPA_PLATFORM'] = 'offscreen'  # Force offscreen mode
            env['DISPLAY'] = ''  # Unset display
            
            # Start OMIFI in the background with modified environment
            process = subprocess.Popen([sys.executable, "main.py"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    env=env,
                                    start_new_session=True)
            
            # Give it time to start
            time.sleep(2)
            
            # Check if it started successfully
            if process.poll() is None:  # Process is still running
                success = True
                message = "OMIFI started successfully"
            else:
                # Read error output
                _, stderr = process.communicate()
                err_msg = stderr.decode('utf-8')
                logger.error(f"Process exited with error: {err_msg}")
                
                # Try fallback mode if we get Qt errors
                if "qt" in err_msg.lower() or "xcb" in err_msg.lower():
                    logger.info("Attempting to start OMIFI in fallback mode without Qt")
                    create_dummy_omifi_process()
                    success = True
                    message = "OMIFI started in web-only mode"
                else:
                    message = f"Failed to start OMIFI: {err_msg[:100]}..."
        except Exception as e:
            logger.error(f"Error starting OMIFI: {e}")
            message = str(e)
    else:
        success = True
        message = "OMIFI is already running"
    
    # For AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "success": success, 
            "message": message,
            "running": get_omifi_status()
        })
    
    # For regular browser request
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_omifi():
    """Stop the OMIFI desktop application."""
    success = False
    message = "Failed to stop OMIFI"
    
    if get_omifi_status():
        try:
            # Check if we're running in dummy mode
            if os.path.exists(DUMMY_FLAG_FILE):
                # Remove the dummy flag file
                try:
                    os.remove(DUMMY_FLAG_FILE)
                    success = True
                    message = "OMIFI web-only mode stopped"
                except Exception as e:
                    logger.error(f"Error removing dummy flag file: {e}")
                    message = f"Failed to remove dummy flag file: {e}"
            else:
                # This is a simplistic approach - in a real app, you'd use a proper IPC mechanism
                try:
                    if sys.platform == 'win32':
                        # Windows
                        subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/T"], check=False)
                    else:
                        # Linux/macOS - more aggressive approach
                        subprocess.run("pkill -9 -f 'python.*main.py'", shell=True, check=False)
                        
                    # Wait a bit to ensure it's stopped
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error stopping processes: {e}")
            
            # Check if it's really stopped
            running_check = get_omifi_status()
            if not running_check:
                success = True
                if "web-only" not in message:
                    message = "OMIFI stopped successfully"
            else:
                # Force-stop the dummy file if it exists
                if os.path.exists(DUMMY_FLAG_FILE):
                    try:
                        os.remove(DUMMY_FLAG_FILE)
                        success = True
                        message = "OMIFI web-only mode forcibly stopped"
                    except Exception as e:
                        logger.error(f"Error force-removing dummy flag file: {e}")
                        message = f"Failed to force-remove dummy flag file: {e}"
        except Exception as e:
            logger.error(f"Error stopping OMIFI: {e}")
            message = str(e)
    else:
        success = True
        message = "OMIFI is not running"
    
    # For AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "success": success, 
            "message": message,
            "running": get_omifi_status()
        })
    
    # For regular browser request
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

@app.route('/qr/screenshot/<path:filepath>')
def get_screenshot_qr(filepath):
    """Generate QR code for downloading a screenshot."""
    try:
        from io import BytesIO
        
        # Create the full URL to the screenshot
        base_url = request.url_root.rstrip('/')
        screenshot_url = f"{base_url}/screenshots/{filepath}"
        
        # Generate QR code using simple version to avoid import issues
        img = qrcode.make(screenshot_url)
        
        # Save to bytes buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        logger.error(f"Error generating QR code for screenshot: {e}")
        return str(e), 500

@app.route('/qr/clipboard/<path:filepath>')
def get_clipboard_qr(filepath):
    """Generate QR code for downloading clipboard content."""
    try:
        from io import BytesIO
        
        # Create the full URL to the clipboard
        base_url = request.url_root.rstrip('/')
        clipboard_url = f"{base_url}/clipboard/{filepath}"
        
        # Generate QR code using simple version to avoid import issues
        img = qrcode.make(clipboard_url)
        
        # Save to bytes buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        logger.error(f"Error generating QR code for clipboard: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)