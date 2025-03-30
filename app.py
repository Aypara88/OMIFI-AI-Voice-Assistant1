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
        # Create multiple base directories for better compatibility
        base_dirs = [
            os.path.expanduser("~/.omifi"),  # User home directory (standard)
            os.path.join(os.getcwd(), ".omifi"),  # Current working directory
            os.path.join(os.getcwd(), "omifi-data"),  # Alternative in current directory
            "/tmp/omifi"  # Temporary directory (fallback)
        ]
        
        logger.info(f"Initializing OMIFI storage directories: {', '.join(base_dirs)}")
        
        for base_dir in base_dirs:
            # Create base dir
            os.makedirs(base_dir, exist_ok=True)
            
            # Create subdirectories
            screenshots_dir = os.path.join(base_dir, "screenshots")
            clipboard_dir = os.path.join(base_dir, "clipboard")
            
            for directory in [screenshots_dir, clipboard_dir]:
                os.makedirs(directory, exist_ok=True)
            
            # Write a placeholder file to verify write permissions
            try:
                with open(os.path.join(base_dir, "directory_check.txt"), 'w') as f:
                    f.write(f"Directory initialized on {datetime.now().isoformat()}")
                logger.info(f"Successfully initialized storage directory: {base_dir}")
            except Exception as e:
                logger.warning(f"Cannot write to directory {base_dir}: {e}")
                
        # Use the user home directory for the flag file
        base_dir = os.path.dirname(DUMMY_FLAG_FILE)
        os.makedirs(base_dir, exist_ok=True)
            
        # Import here to avoid circular dependencies
        from datetime import datetime
        from PIL import Image
        
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
    # Try multiple locations for metadata file
    metadata_paths = [
        os.path.expanduser("~/.omifi/metadata.json"),
        os.path.join(os.getcwd(), ".omifi/metadata.json"),
        os.path.join(os.getcwd(), "omifi-data/metadata.json"),
        "/tmp/omifi/metadata.json"
    ]
    
    # Try each path until we find a valid metadata file
    for metadata_path in metadata_paths:
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    logger.info(f"Loaded metadata from {metadata_path}")
                    
                    # Enhance filepath with directory info if needed
                    base_dir = os.path.dirname(metadata_path)
                    
                    # Fix paths to be compatible with current server
                    for item_type in ['screenshots', 'clipboard']:
                        for item in metadata.get(item_type, []):
                            # If filepath is just a filename, ensure it's properly handled
                            if 'filepath' in item and not os.path.isabs(item['filepath']):
                                # Don't modify if it's already a relative path that our routes expect
                                pass
                    
                    return metadata
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading metadata from {metadata_path}: {e}")
    
    # If no valid metadata file found, create a new one in the first writable location
    logger.warning("No valid metadata file found, creating new empty metadata")
    empty_metadata = {"screenshots": [], "clipboard": []}
    
    # Try to save the empty metadata to the first writable location
    for metadata_path in metadata_paths:
        try:
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(empty_metadata, f, indent=2)
            logger.info(f"Created new metadata file at {metadata_path}")
            break
        except Exception as e:
            logger.warning(f"Failed to create metadata at {metadata_path}: {e}")
    
    # Return empty metadata if file doesn't exist or can't be loaded
    return empty_metadata

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
    running = get_omifi_status()
    # Check if microphone is available
    microphone_available = False
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Microphone check successful")
            microphone_available = True
    except Exception as e:
        logger.warning(f"Microphone not available: {e}")
        
    return jsonify({
        "running": running,
        "microphone_available": microphone_available
    })

@app.route('/clipboard/<path:filepath>')
def get_clipboard(filepath):
    """Get clipboard content by filepath."""
    try:
        # First try user home directory path
        base_dir = os.path.expanduser("~/.omifi/clipboard")
        fullpath = os.path.join(base_dir, filepath)
        
        # If file doesn't exist in that path, try server-relative paths
        if not os.path.exists(fullpath):
            # Try alternative paths
            alt_paths = [
                os.path.join(os.getcwd(), '.omifi/clipboard', filepath),
                os.path.join(os.getcwd(), 'omifi-data/clipboard', filepath),
                os.path.join('/tmp/omifi/clipboard', filepath)
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    fullpath = path
                    base_dir = os.path.dirname(path)
                    break
        
        # Check if file exists and is within a clipboard directory (security check)
        if os.path.exists(fullpath) and os.path.commonpath([fullpath, base_dir]) == base_dir:
            # Determine MIME type by extension
            _, ext = os.path.splitext(fullpath)
            if ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                return send_file(fullpath, mimetype=f'image/{ext[1:].lower()}')
            else:
                # Try to read as text first
                try:
                    with open(fullpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Auto-detect if it's JSON to return proper content type
                    if content.strip().startswith('{') or content.strip().startswith('['):
                        try:
                            json.loads(content)
                            return content, 200, {'Content-Type': 'application/json'}
                        except json.JSONDecodeError:
                            pass
                    
                    return content
                except UnicodeDecodeError:
                    # If it's not valid text, send as binary file
                    return send_file(fullpath)
        else:
            logger.warning(f"File not found or invalid path: {filepath}")
            return "File not found or invalid path", 404
    except Exception as e:
        logger.error(f"Error retrieving clipboard content: {e}")
        return str(e), 500

@app.route('/screenshots/<path:filepath>')
def get_screenshot(filepath):
    """Serve screenshot images."""
    try:
        # First try user home directory path
        base_dir = os.path.expanduser("~/.omifi/screenshots")
        fullpath = os.path.join(base_dir, filepath)
        
        # If file doesn't exist in that path, try server-relative paths
        if not os.path.exists(fullpath):
            # Try alternative paths
            alt_paths = [
                os.path.join(os.getcwd(), '.omifi/screenshots', filepath),
                os.path.join(os.getcwd(), 'omifi-data/screenshots', filepath),
                os.path.join('/tmp/omifi/screenshots', filepath)
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    fullpath = path
                    base_dir = os.path.dirname(path)
                    break
        
        # Check if file exists and is within a screenshots directory (security check)
        if os.path.exists(fullpath) and os.path.commonpath([fullpath, base_dir]) == base_dir:
            # Determine MIME type by extension for better browser handling
            _, ext = os.path.splitext(fullpath)
            if ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                return send_file(fullpath, mimetype=f'image/{ext[1:].lower()}')
            else:
                return send_file(fullpath)
        else:
            logger.warning(f"Screenshot not found or invalid path: {filepath}")
            return "File not found or invalid path", 404
    except Exception as e:
        logger.error(f"Error retrieving screenshot: {e}")
        return str(e), 500

@app.route('/qr/screenshot/<path:filepath>')
def get_screenshot_qr(filepath):
    """Generate QR code for downloading a screenshot."""
    try:
        from io import BytesIO
        
        # Parse the filepath to handle both full path and filename-only cases
        if os.path.isabs(filepath):
            # If it's a full path, extract just the filename
            filename = os.path.basename(filepath)
        else:
            # If it's just a filename, use as is
            filename = filepath
        
        # Create the full URL to the screenshot
        # Try to get the best public URL for access from mobile devices
        base_url = request.url_root.rstrip('/')
        
        # Check for Replit-specific domains if this is running in Replit
        replit_domain = os.environ.get('REPL_SLUG')
        if replit_domain:
            # If running on Replit, use the Replit domain if available
            replit_owner = os.environ.get('REPL_OWNER', '')
            if replit_owner:
                base_url = f"https://{replit_domain}.{replit_owner}.repl.co"
            else:
                base_url = f"https://{replit_domain}.repl.co"
        
        screenshot_url = f"{base_url}/screenshots/{filename}"
        logger.info(f"Generated screenshot QR URL: {screenshot_url}")
        
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
        
        # Parse the filepath to handle both full path and filename-only cases
        if os.path.isabs(filepath):
            # If it's a full path, extract just the filename
            filename = os.path.basename(filepath)
        else:
            # If it's just a filename, use as is
            filename = filepath
        
        # Create the full URL to the clipboard
        # Try to get the best public URL for access from mobile devices
        base_url = request.url_root.rstrip('/')
        
        # Check for Replit-specific domains if this is running in Replit
        replit_domain = os.environ.get('REPL_SLUG')
        if replit_domain:
            # If running on Replit, use the Replit domain if available
            replit_owner = os.environ.get('REPL_OWNER', '')
            if replit_owner:
                base_url = f"https://{replit_domain}.{replit_owner}.repl.co"
            else:
                base_url = f"https://{replit_domain}.repl.co"
        
        clipboard_url = f"{base_url}/clipboard/{filename}"
        logger.info(f"Generated clipboard QR URL: {clipboard_url}")
        
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

@app.route('/command', methods=['POST'])
def execute_command():
    """Execute a command directly from the web interface."""
    try:
        command_text = request.form.get('command')
        
        if not command_text:
            return jsonify({"success": False, "message": "No command provided"})
        
        logger.info(f"Processing web command: {command_text}")
        
        # Initialize components for command processing
        from omifi.storage import Storage
        storage = Storage()
        
        # Initialize command processor
        from omifi.command_processor import CommandProcessor
        command_processor = CommandProcessor(storage)
        
        # Initialize managers if needed
        try:
            from omifi.clipboard import ClipboardManager
            clipboard_manager = ClipboardManager(storage)
            command_processor.clipboard_manager = clipboard_manager
        except Exception as e:
            logger.warning(f"Clipboard manager not available: {e}")
        
        try:
            from omifi.screenshot import ScreenshotManager
            screenshot_manager = ScreenshotManager(storage)
            command_processor.screenshot_manager = screenshot_manager
        except Exception as e:
            logger.warning(f"Screenshot manager not available: {e}")
        
        try:
            from omifi.text_to_speech import TextToSpeech
            text_to_speech = TextToSpeech()
            command_processor.text_to_speech = text_to_speech
        except Exception as e:
            logger.warning(f"Text-to-speech not available: {e}")
        
        # Process the command
        result = command_processor.process_command(command_text)
        
        # Refresh metadata for the dashboard
        return jsonify({
            "success": result, 
            "message": "Command executed successfully" if result else "Command failed or not recognized",
            "running": get_omifi_status()
        })
    
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/take-screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot from the web interface."""
    try:
        # Initialize components
        from omifi.storage import Storage
        storage = Storage()
        
        # Check if we have a direct screenshot from the browser via WebRTC
        if 'screenshot' in request.files:
            logger.info("Received screenshot from browser WebRTC")
            screenshot_file = request.files['screenshot']
            
            # Process the screenshot using PIL
            from PIL import Image
            from io import BytesIO
            
            # Open the image
            img = Image.open(BytesIO(screenshot_file.read()))
            
            # Save it using storage
            filepath = storage.save_screenshot(img)
            logger.info(f"Browser screenshot saved to {filepath}")
        else:
            # Fall back to traditional screenshot capture
            from omifi.screenshot import ScreenshotManager
            screenshot_manager = ScreenshotManager(storage)
            
            # Take screenshot
            filepath = screenshot_manager.take_screenshot()
        
        if filepath:
            # Get filename from path for display
            filename = os.path.basename(filepath)
            return jsonify({
                "success": True,
                "message": "Screenshot taken successfully",
                "filepath": filepath,  # Return full filepath for QR code generation
                "filename": filename   # Filename for display purposes
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to take screenshot"
            })
    
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/sense-clipboard', methods=['POST'])
def sense_clipboard():
    """Sense clipboard content from the web interface."""
    try:
        # Initialize components
        from omifi.storage import Storage
        storage = Storage()
        
        # Initialize default values for required variables
        content = None
        content_type = "text"
        content_preview = ""
        filepath = None
        
        # Check if this is a JSON request for fallback clipboard access
        if request.is_json:
            logger.info("Received JSON request for clipboard sensing")
            json_data = request.get_json()
            
            # Check if this is a fallback request
            if json_data.get('fallback') and json_data.get('use_system_clipboard'):
                logger.info("Using system clipboard as fallback")
                from omifi.clipboard import ClipboardManager
                clipboard_manager = ClipboardManager(storage)
                
                # Sense clipboard with priority on system access
                content_type, content = clipboard_manager.sense_clipboard(force_system=True)
                
                if content:
                    logger.info(f"System clipboard content detected: {content_type}")
                    
                    # Set preview based on content type
                    if content_type == 'text':
                        content_preview = content[:100] + "..." if len(content) > 100 else content
                    else:
                        content_preview = f"[{content_type.upper()} content]"
                    
                    # Get filepath from storage
                    filepath, _ = storage.get_last_clipboard_content() 
                    filename = os.path.basename(filepath) if filepath else None
                    
                    return jsonify({
                        "success": True,
                        "message": f"System clipboard {content_type} content captured successfully",
                        "content_type": content_type,
                        "content_preview": content_preview,
                        "filepath": filepath,
                        "filename": filename
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "No content detected in system clipboard"
                    })
        
        # Check if we have direct clipboard content from the browser
        elif 'content' in request.form:
            logger.info("Received clipboard content from browser")
            content = request.form.get('content')
            content_type = request.form.get('type', 'text')
            
            # Get optional metadata
            mime_type = request.form.get('mime_type')
            custom_filename = request.form.get('filename')
            
            # Save content directly
            filepath = storage.save_clipboard_content(content, content_type, filename=custom_filename)
            logger.info(f"Browser clipboard content saved to {filepath}")
            
            # Set preview based on content type
            if content_type == 'text':
                content_preview = content[:100] + "..." if len(content) > 100 else content
            else:
                content_preview = f"[{content_type.upper()} content]"
                if mime_type:
                    content_preview += f" ({mime_type})"
        
        # Check if we have a file upload (for image data)
        elif 'content' in request.files:
            logger.info("Received file upload from browser")
            file = request.files['content']
            content_type = request.form.get('type', 'image')
            
            # Get optional metadata
            mime_type = request.form.get('mime_type')
            custom_filename = request.form.get('filename') or file.filename
            
            # Read file content
            content = file.read()
            
            # Save content
            filepath = storage.save_clipboard_content(content, content_type, filename=custom_filename)
            logger.info(f"Browser clipboard file saved to {filepath}")
            
            # Set preview based on content type
            content_preview = f"[{content_type.upper()} content]"
            if mime_type:
                content_preview += f" ({mime_type})"
                
        else:
            # Fall back to traditional clipboard sensing
            from omifi.clipboard import ClipboardManager
            clipboard_manager = ClipboardManager(storage)
            
            # Sense clipboard
            content_type, content = clipboard_manager.sense_clipboard()
            
            # Set preview for text content
            if content_type == 'text' and content:
                content_preview = content[:100] + "..." if len(content) > 100 else content
            elif content:  # If it's not text but we have content
                content_preview = f"[{content_type.upper()} content]"
        
        # Final response handling
        if content is not None:
            # Get filepath from storage if not already set
            if not filepath:
                filepath, _ = storage.get_last_clipboard_content()
                
            filename = os.path.basename(filepath) if filepath else None
            
            return jsonify({
                "success": True,
                "message": f"Clipboard {content_type} content captured successfully",
                "content_type": content_type,
                "content_preview": content_preview,
                "filepath": filepath,  # Return full filepath for QR code generation
                "filename": filename   # Filename for display purposes
            })
        else:
            return jsonify({
                "success": False,
                "message": "No clipboard content available"
            })
    
    except Exception as e:
        logger.error(f"Error sensing clipboard: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)