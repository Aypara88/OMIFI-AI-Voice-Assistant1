"""
Screenshot module for the OMIFI assistant.
"""

import os
import time
import logging
import subprocess
from PIL import ImageGrab

logger = logging.getLogger(__name__)

class ScreenshotManager:
    """
    Handles capturing and saving screenshots.
    """
    
    def __init__(self, storage):
        """
        Initialize the screenshot manager.
        
        Args:
            storage: Storage instance for saving screenshots
        """
        self.storage = storage
    
    def take_screenshot(self):
        """
        Capture the current screen and save it.
        
        Returns:
            str: Path to the saved screenshot
        """
        try:
            # Capture screenshot using PIL
            screenshot = ImageGrab.grab()
            
            # Save to storage
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            
            filepath = self.storage.save_screenshot(screenshot, filename)
            
            if filepath:
                logger.info(f"Screenshot saved to {filepath}")
                
            return filepath
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def open_last_screenshot(self):
        """
        Open the most recent screenshot with the default image viewer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        filepath = self.storage.get_last_screenshot()
        
        if not filepath or not os.path.exists(filepath):
            logger.warning("No screenshot available to open")
            return False
        
        try:
            # Try to open with system default viewer
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # Linux, macOS
                subprocess.Popen(['xdg-open', filepath])
            
            logger.info(f"Opened screenshot: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening screenshot: {e}")
            return False