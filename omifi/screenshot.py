"""
Screenshot module for the OMIFI assistant.
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from PIL import ImageGrab

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
        self.logger = logging.getLogger(__name__)
    
    def take_screenshot(self):
        """
        Capture the current screen and save it.
        
        Returns:
            str: Path to the saved screenshot
        """
        try:
            # Capture screenshot
            self.logger.info("Capturing screenshot...")
            screenshot = ImageGrab.grab()
            
            # Save it using storage
            filepath = self.storage.save_screenshot(screenshot)
            self.logger.info(f"Screenshot saved to {filepath}")
            
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None
    
    def open_last_screenshot(self):
        """
        Open the most recent screenshot with the default image viewer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the most recent screenshot path
            screenshot_path = self.storage.get_last_screenshot()
            
            if not screenshot_path or not os.path.exists(screenshot_path):
                self.logger.warning("No screenshots available to open")
                return False
            
            # Open the screenshot with the default viewer
            self.logger.info(f"Opening screenshot: {screenshot_path}")
            
            # Platform-specific opening
            if sys.platform == 'win32':
                os.startfile(screenshot_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', screenshot_path], check=False)
            else:  # Linux
                subprocess.run(['xdg-open', screenshot_path], check=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening screenshot: {e}")
            return False