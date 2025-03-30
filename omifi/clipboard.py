import logging
import pyperclip
from datetime import datetime

logger = logging.getLogger(__name__)

class ClipboardManager:
    """
    Manages clipboard sensing and storage.
    """
    
    def __init__(self, storage):
        """
        Initialize the clipboard manager.
        
        Args:
            storage: Storage instance for saving clipboard content
        """
        self.storage = storage
        self.current_clipboard = None
    
    def sense_clipboard(self):
        """
        Get the current clipboard content and save it.
        
        Returns:
            tuple: (str, str) - Content type and clipboard content
        """
        try:
            logger.info("Sensing clipboard...")
            
            # Get the current clipboard content
            clipboard_content = pyperclip.paste()
            
            if not clipboard_content:
                logger.info("Clipboard is empty")
                return None, None
            
            # Generate a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine the content type and store it
            # For now, we'll just handle text content
            content_type = "text"
            filename = f"clipboard_{timestamp}.txt"
            
            # Save the clipboard content
            filepath = self.storage.save_clipboard_content(clipboard_content, filename)
            
            logger.info(f"Clipboard content saved: {filepath}")
            self.current_clipboard = clipboard_content
            
            return content_type, clipboard_content
            
        except Exception as e:
            logger.error(f"Error sensing clipboard: {e}")
            return None, None
    
    def get_current_clipboard(self):
        """
        Get the most recently sensed clipboard content.
        
        Returns:
            str: Clipboard content or None if not available
        """
        return self.current_clipboard
    
    def get_last_clipboard_content(self):
        """
        Get the most recent clipboard content from storage.
        
        Returns:
            tuple: (str, str) - Filepath and content
        """
        return self.storage.get_last_clipboard_content()
