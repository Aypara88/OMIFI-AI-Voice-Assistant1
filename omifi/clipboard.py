"""
Clipboard module for the OMIFI assistant.
"""

import os
import logging
from datetime import datetime
import pyperclip

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
        self.logger = logging.getLogger(__name__)
        self.last_content = None
    
    def sense_clipboard(self):
        """
        Get the current clipboard content and save it.
        
        Returns:
            tuple: (str, str) - Content type and clipboard content
        """
        try:
            # Get clipboard content
            clipboard_content = pyperclip.paste()
            
            # Skip empty content
            if not clipboard_content or clipboard_content.strip() == "":
                self.logger.info("Clipboard is empty or contains only whitespace")
                return "text", ""
            
            # Skip if content hasn't changed
            if clipboard_content == self.last_content:
                self.logger.info("Clipboard content unchanged since last check")
                return "text", clipboard_content
            
            # Save the content
            self.last_content = clipboard_content
            filepath = self.storage.save_clipboard_content(clipboard_content, "text")
            
            self.logger.info(f"Saved clipboard content to {filepath}")
            return "text", clipboard_content
            
        except Exception as e:
            self.logger.error(f"Error sensing clipboard: {e}")
            return "text", ""
    
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