"""
Clipboard module for the OMIFI assistant.
"""

import time
import logging
import pyperclip

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
        self.last_content = None
        self.last_content_type = None
    
    def sense_clipboard(self):
        """
        Get the current clipboard content and save it.
        
        Returns:
            tuple: (str, str) - Content type and clipboard content
        """
        try:
            # Get clipboard content
            content = pyperclip.paste()
            
            # If content is empty or same as last sensed content, don't save
            if not content or content == self.last_content:
                logger.debug("Clipboard empty or unchanged")
                return None, None
            
            # Update last content
            self.last_content = content
            self.last_content_type = "text"  # Only supporting text for now
            
            # Save to storage
            filepath = self.storage.save_clipboard_content(
                content, 
                content_type=self.last_content_type
            )
            
            if filepath:
                logger.info(f"Clipboard content saved to {filepath}")
            
            return self.last_content_type, content
            
        except Exception as e:
            logger.error(f"Error sensing clipboard: {e}")
            return None, None
    
    def get_current_clipboard(self):
        """
        Get the most recently sensed clipboard content.
        
        Returns:
            str: Clipboard content or None if not available
        """
        return self.last_content
    
    def get_last_clipboard_content(self):
        """
        Get the most recent clipboard content from storage.
        
        Returns:
            tuple: (str, str) - Filepath and content
        """
        return self.storage.get_last_clipboard_content()