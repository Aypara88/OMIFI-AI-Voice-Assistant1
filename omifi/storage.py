"""
Storage module for the OMIFI assistant.
"""

import os
import json
import time
import logging
from datetime import datetime
from PIL import Image

logger = logging.getLogger(__name__)

class Storage:
    """
    Manages storage and retrieval of screenshots and clipboard content.
    """
    
    def __init__(self, base_dir=None):
        """
        Initialize the storage system.
        
        Args:
            base_dir (str, optional): Base directory for storage. Defaults to user's home directory.
        """
        if base_dir is None:
            self.base_dir = os.path.expanduser("~/.omifi")
        else:
            self.base_dir = base_dir
            
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Create subdirectories
        self.screenshots_dir = os.path.join(self.base_dir, "screenshots")
        self.clipboard_dir = os.path.join(self.base_dir, "clipboard")
        
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.clipboard_dir, exist_ok=True)
        
        # Metadata file path
        self.metadata_path = os.path.join(self.base_dir, "metadata.json")
        
        # Load metadata
        self.metadata = self._load_metadata()
        
    def _load_metadata(self):
        """
        Load metadata from file or create a new metadata structure.
        
        Returns:
            dict: Metadata dictionary
        """
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        # Default metadata structure
        return {
            "screenshots": [],
            "clipboard": []
        }
        
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def save_screenshot(self, screenshot, filename=None):
        """
        Save a screenshot to storage.
        
        Args:
            screenshot: PIL Image object
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved screenshot
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
        
        filepath = os.path.join(self.screenshots_dir, filename)
        
        try:
            screenshot.save(filepath)
            
            # Add to metadata
            screenshot_meta = {
                "filepath": filepath,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "width": screenshot.width,
                "height": screenshot.height
            }
            
            self.metadata["screenshots"].append(screenshot_meta)
            self._save_metadata()
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None
    
    def save_clipboard_content(self, content, content_type="text", filename=None):
        """
        Save clipboard content to storage.
        
        Args:
            content: Clipboard content (text for now)
            content_type: Type of content (text, image, etc.)
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved content
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"clipboard_{timestamp}.txt"
        
        filepath = os.path.join(self.clipboard_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            
            # Add to metadata
            clipboard_meta = {
                "filepath": filepath,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "type": content_type
            }
            
            self.metadata["clipboard"].append(clipboard_meta)
            self._save_metadata()
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving clipboard content: {e}")
            return None
    
    def get_last_screenshot(self):
        """
        Get the path to the most recent screenshot.
        
        Returns:
            str: Path to the most recent screenshot or None if not available
        """
        if not self.metadata["screenshots"]:
            return None
            
        # Sort by timestamp (newest first)
        sorted_screenshots = sorted(
            self.metadata["screenshots"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        if sorted_screenshots:
            return sorted_screenshots[0]["filepath"]
            
        return None
    
    def get_last_clipboard_content(self):
        """
        Get the most recent clipboard content.
        
        Returns:
            tuple: (filepath, content) or (None, None) if not available
        """
        if not self.metadata["clipboard"]:
            return None, None
            
        # Sort by timestamp (newest first)
        sorted_clipboard = sorted(
            self.metadata["clipboard"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        if sorted_clipboard:
            filepath = sorted_clipboard[0]["filepath"]
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                return filepath, content
            except Exception as e:
                logger.error(f"Error reading clipboard content: {e}")
                
        return None, None
    
    def get_screenshots(self, limit=10):
        """
        Get recent screenshots.
        
        Args:
            limit (int): Maximum number of screenshots to return
            
        Returns:
            list: List of screenshot metadata
        """
        # Sort by timestamp (newest first)
        sorted_screenshots = sorted(
            self.metadata["screenshots"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        return sorted_screenshots[:limit]
    
    def get_clipboard_items(self, limit=10):
        """
        Get recent clipboard items.
        
        Args:
            limit (int): Maximum number of items to return
            
        Returns:
            list: List of clipboard metadata
        """
        # Sort by timestamp (newest first)
        sorted_clipboard = sorted(
            self.metadata["clipboard"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        return sorted_clipboard[:limit]