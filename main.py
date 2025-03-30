"""
OMIFI Voice Assistant - Main Application Entry Point

This file serves as the entry point for both the desktop application
and the web interface. It imports the Flask app from app.py for the web interface.
"""

import os
import sys
import logging
import signal
import threading
import atexit
from datetime import datetime

# Import the Flask app for the web interface
from app import app as flask_app

# Create a flag to track if running as desktop app or web server
is_desktop_app = __name__ == "__main__"

def setup_logging():
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    return logger

def create_assets_directory():
    """Create the assets directory structure if it doesn't exist."""
    base_dir = os.path.expanduser("~/.omifi")
    screenshots_dir = os.path.join(base_dir, "screenshots")
    clipboard_dir = os.path.join(base_dir, "clipboard")
    
    for directory in [base_dir, screenshots_dir, clipboard_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

def signal_handler(sig, frame):
    """Handle signals to properly exit the application."""
    logger.info("Signal received, shutting down...")
    sys.exit(0)

def run_desktop_app():
    """Initialize and run the OMIFI voice assistant desktop application."""
    logger.info("Starting OMIFI desktop application...")
    
    # Import PyQt5 components here to avoid loading them when running as a web server
    try:
        from PyQt5.QtWidgets import QApplication
        
        # Import OMIFI components
        from omifi.storage import Storage
        from omifi.clipboard import ClipboardManager
        from omifi.screenshot import ScreenshotManager
        from omifi.text_to_speech import TextToSpeech
        from omifi.command_processor import CommandProcessor
        from omifi.voice_recognition import VoiceRecognizer
        from omifi.ui.system_tray import OmifiSystemTray
        
        # Create application instance
        app = QApplication(sys.argv)
        app.setApplicationName("OMIFI Assistant")
        app.setQuitOnLastWindowClosed(False)
        
        # Initialize components
        storage = Storage()
        clipboard_manager = ClipboardManager(storage)
        screenshot_manager = ScreenshotManager(storage)
        text_to_speech = TextToSpeech()
        
        # Initialize command processor
        command_processor = CommandProcessor(storage)
        command_processor.clipboard_manager = clipboard_manager
        command_processor.screenshot_manager = screenshot_manager
        command_processor.text_to_speech = text_to_speech
        
        # Initialize voice recognizer
        voice_recognizer = VoiceRecognizer(command_processor)
        voice_recognizer.daemon = True
        voice_recognizer.start()
        
        # Initialize system tray
        tray = OmifiSystemTray(app, voice_recognizer, storage)
        tray.show()
        
        # Clean up on exit
        def cleanup():
            logger.info("Cleaning up resources...")
            if voice_recognizer:
                voice_recognizer.stop()
        
        atexit.register(cleanup)
        
        # Start the application event loop
        logger.info("OMIFI desktop application started")
        sys.exit(app.exec_())
    
    except ImportError as e:
        logger.error(f"Failed to import PyQt5 components: {e}")
        logger.error("Desktop application requires PyQt5. Please install it with 'pip install PyQt5'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting desktop application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    
    # Create required directories
    create_assets_directory()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the desktop application
    run_desktop_app()
else:
    # When imported as a module (e.g., by Flask), setup logging
    logger = setup_logging()
    
    # Create required directories
    create_assets_directory()