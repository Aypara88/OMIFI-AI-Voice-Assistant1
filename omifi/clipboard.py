"""
Clipboard module for the OMIFI assistant.
"""

import os
import io
import logging
import base64
from datetime import datetime
from PIL import Image, ImageGrab
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
        self.last_content_type = "text"
    
    def sense_clipboard(self, force_system=False):
        """
        Get the current clipboard content and save it.
        This method tries to detect different types of clipboard content:
        - Text content
        - Image content
        - Binary content (if detectable)

        Args:
            force_system (bool): If True, prioritize system clipboard access without checking content equality

        Returns:
            tuple: (str, str) - Content type and clipboard content
        """
        # Attempt order depends on force_system flag
        if force_system:
            # When forcing system clipboard, try text first as it's most reliable
            text_result = self._try_get_text_clipboard(force_new=True)
            if text_result[1]:  # If we got text content
                return text_result
                
            # If no text, try image
            image_result = self._try_get_image_clipboard()
            if image_result[1]:  # If we got image content
                return image_result
                
            # Both failed, return empty text
            return "text", ""
        else:
            # Normal flow - try image first, then text
            image_result = self._try_get_image_clipboard()
            if image_result[1]:  # If we got image content
                return image_result
                
            # If no image, try text
            return self._try_get_text_clipboard()

    def _try_get_image_clipboard(self):
        """
        Try to get image content from clipboard.
        
        Returns:
            tuple: (content_type, content) - Image content type and data
        """
        try:
            # Try to get image from clipboard (this works on most platforms)
            img = self._get_clipboard_image()
            if img:
                self.logger.info("Image detected in clipboard")
                
                # Convert image to base64 for storage
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Save the image with the storage manager
                filepath = self.storage.save_clipboard_content(
                    img_data, 
                    "image", 
                    filename=f"clipboard_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                
                self.last_content = img_data
                self.last_content_type = "image"
                return "image", img_data
        except Exception as e:
            self.logger.error(f"Error handling clipboard image: {e}")
        
        # Return empty if no image or error
        return "image", ""
    
    def _try_get_text_clipboard(self, force_new=False):
        """
        Try to get text content from clipboard.
        
        Args:
            force_new (bool): If True, ignore if content is the same as previous
        
        Returns:
            tuple: (content_type, content) - Text content type and data
        """
        try:
            # Get clipboard text content
            clipboard_content = pyperclip.paste()
            
            # Skip empty content
            if not clipboard_content or clipboard_content.strip() == "":
                self.logger.info("Clipboard is empty or contains only whitespace")
                return "text", ""
                
            # Detect content type based on the text
            content_type = self._detect_content_type(clipboard_content)
                
            # Skip if content hasn't changed (unless force_new is True)
            if not force_new and clipboard_content == self.last_content and content_type == self.last_content_type:
                self.logger.info("Clipboard content unchanged since last check")
                return content_type, clipboard_content
            
            # Save the content
            self.last_content = clipboard_content
            filepath = self.storage.save_clipboard_content(clipboard_content, "text")
            
            self.logger.info(f"Saved clipboard content to {filepath}")
            return "text", clipboard_content
            
        except Exception as e:
            self.logger.error(f"Error sensing clipboard text: {e}")
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
        
    def _get_clipboard_image(self):
        """
        Try to get an image from the clipboard if one exists.
        
        Returns:
            PIL.Image or None: The clipboard image if found, None otherwise
        """
        try:
            # Try using ImageGrab for direct clipboard access (works on many platforms)
            img = ImageGrab.grabclipboard()
            if img is not None and hasattr(img, 'mode'):  # Check if it's a valid PIL Image
                return img
        except Exception as e:
            self.logger.debug(f"Could not grab clipboard image: {e}")
            pass
            
        return None
        
    def _detect_content_type(self, text):
        """
        Detect the content type based on the text content.
        This checks for common patterns like URLs, code, JSON, etc.
        
        Args:
            text (str): The text content to analyze
            
        Returns:
            str: The detected content type (url, code, json, or text)
        """
        text = text.strip()
        
        # Check if it's a URL
        if text.startswith(('http://', 'https://', 'www.')):
            return "url"
            
        # Check if it's JSON
        if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
            try:
                import json
                json.loads(text)
                return "json"
            except:
                pass
                
        # Check if it looks like code
        code_indicators = ['def ', 'class ', 'function ', 'var ', 'let ', 'const ', 'import ', 'from ', '#include']
        for indicator in code_indicators:
            if indicator in text:
                return "code"
                
        # Default to plain text
        return "text"