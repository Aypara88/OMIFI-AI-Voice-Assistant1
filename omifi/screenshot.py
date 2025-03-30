import os
import logging
from datetime import datetime
from PIL import ImageGrab
import platform

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
            logger.info("Taking screenshot...")
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            # Take the screenshot using PIL
            screenshot = ImageGrab.grab()
            
            # Save the screenshot using the storage manager
            filepath = self.storage.save_screenshot(screenshot, filename)
            
            logger.info(f"Screenshot saved: {filepath}")
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
        try:
            last_screenshot = self.storage.get_last_screenshot()
            
            if not last_screenshot:
                logger.info("No screenshots available")
                return False
            
            # Open the file with the default application
            logger.info(f"Opening screenshot: {last_screenshot}")
            
            if platform.system() == 'Windows':
                os.startfile(last_screenshot)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{last_screenshot}"')
            else:  # Linux
                os.system(f'xdg-open "{last_screenshot}"')
                
            return True
            
        except Exception as e:
            logger.error(f"Error opening last screenshot: {e}")
            return False
