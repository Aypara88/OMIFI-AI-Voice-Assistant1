import sys
import logging
from PyQt5.QtWidgets import QApplication

from omifi.ui.system_tray import OmifiSystemTray
from omifi.voice_recognition import VoiceRecognizer
from omifi.command_processor import CommandProcessor
from omifi.storage import Storage

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize and run the OMIFI voice assistant application."""
    logger.info("Starting OMIFI Voice Assistant")
    
    # Initialize the application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Allow app to run in the background
    
    # Initialize storage
    storage = Storage()
    
    # Initialize command processor
    command_processor = CommandProcessor(storage)
    
    # Initialize voice recognizer and start listening
    voice_recognizer = VoiceRecognizer(command_processor)
    
    # Initialize system tray
    tray = OmifiSystemTray(app, voice_recognizer, storage)
    
    # Start voice recognition in a separate thread
    voice_recognizer.start()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
