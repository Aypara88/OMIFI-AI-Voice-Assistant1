"""
OMIFI Voice Assistant Desktop Application

A desktop AI voice assistant that operates in the background and activates when
called with the wake word "Hey OMIFI".
"""

import os
import sys
import signal
import logging
import threading
from PyQt5.QtWidgets import QApplication
import time

from omifi.storage import Storage
from omifi.command_processor import CommandProcessor
from omifi.voice_recognition import VoiceRecognizer
from omifi.ui.system_tray import OmifiSystemTray

# Setup logging
def create_assets_directory():
    """Create the assets directory structure if it doesn't exist."""
    # Create base directory
    base_dir = os.path.expanduser("~/.omifi")
    os.makedirs(base_dir, exist_ok=True)
    
    # Create logs directory
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create assets directory
    assets_dir = os.path.join(base_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create screenshots directory
    screenshots_dir = os.path.join(base_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Create clipboard directory
    clipboard_dir = os.path.join(base_dir, "clipboard")
    os.makedirs(clipboard_dir, exist_ok=True)
    
    return base_dir, logs_dir

def setup_logging(logs_dir):
    """Setup logging configuration."""
    log_file = os.path.join(logs_dir, "omifi.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def signal_handler(sig, frame):
    """Handle signals to properly exit the application."""
    logging.info("Shutting down OMIFI assistant...")
    sys.exit(0)

def main():
    """Initialize and run the OMIFI voice assistant application."""
    # Create directories
    base_dir, logs_dir = create_assets_directory()
    
    # Setup logging
    setup_logging(logs_dir)
    
    # Set signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Initialize storage
    storage = Storage(base_dir)
    
    # Initialize command processor
    command_processor = CommandProcessor(storage)
    
    # Welcome message
    command_processor.text_to_speech.speak("OMIFI assistant is starting", block=True)
    
    # Initialize voice recognizer
    voice_recognizer = VoiceRecognizer(command_processor)
    
    # Start voice recognition in a background thread
    voice_recognizer.start()
    
    # Create system tray
    tray = OmifiSystemTray(app, voice_recognizer, storage)
    
    # Show welcome message
    tray.showMessage(
        "OMIFI Voice Assistant",
        "OMIFI is now running in the background. Say 'Hey OMIFI' to activate.",
        tray.Information,
        5000
    )
    
    # Start Qt event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()