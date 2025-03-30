import os
import logging
from datetime import datetime
import json
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
            # Default to a directory in the user's home folder
            self.base_dir = os.path.join(os.path.expanduser("~"), "OMIFI_Data")
        else:
            self.base_dir = base_dir
            
        # Create subdirectories for different types of data
        self.screenshots_dir = os.path.join(self.base_dir, "Screenshots")
        self.clipboard_dir = os.path.join(self.base_dir, "Clipboard")
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.clipboard_dir, exist_ok=True)
        
        # Metadata file to track stored items
        self.metadata_file = os.path.join(self.base_dir, "metadata.json")
        self.metadata = self._load_metadata()
        
        logger.info(f"Storage initialized at {self.base_dir}")
    
    def _load_metadata(self):
        """
        Load metadata from file or create a new metadata structure.
        
        Returns:
            dict: Metadata dictionary
        """
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        # Create default metadata structure
        return {
            "screenshots": [],
            "clipboard": []
        }
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def save_screenshot(self, screenshot, filename):
        """
        Save a screenshot to storage.
        
        Args:
            screenshot: PIL Image object
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved screenshot
        """
        filepath = os.path.join(self.screenshots_dir, filename)
        
        try:
            # Save the image
            screenshot.save(filepath)
            
            # Update metadata
            screenshot_info = {
                "filename": filename,
                "path": filepath,
                "timestamp": datetime.now().isoformat(),
                "size": os.path.getsize(filepath)
            }
            
            self.metadata["screenshots"].append(screenshot_info)
            self._save_metadata()
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None
    
    def save_clipboard_content(self, content, filename):
        """
        Save clipboard content to storage.
        
        Args:
            content: Clipboard content (text for now)
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved content
        """
        filepath = os.path.join(self.clipboard_dir, filename)
        
        try:
            # Save the content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update metadata
            clipboard_info = {
                "filename": filename,
                "path": filepath,
                "timestamp": datetime.now().isoformat(),
                "size": os.path.getsize(filepath),
                "type": "text"
            }
            
            self.metadata["clipboard"].append(clipboard_info)
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
            
        # Sort by timestamp and get the most recent
        screenshots = sorted(
            self.metadata["screenshots"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        return screenshots[0]["path"] if screenshots else None
    
    def get_last_clipboard_content(self):
        """
        Get the most recent clipboard content.
        
        Returns:
            tuple: (filepath, content) or (None, None) if not available
        """
        if not self.metadata["clipboard"]:
            return None, None
            
        # Sort by timestamp and get the most recent
        clipboard_items = sorted(
            self.metadata["clipboard"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        if not clipboard_items:
            return None, None
            
        filepath = clipboard_items[0]["path"]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return filepath, content
        except Exception as e:
            logger.error(f"Error reading clipboard content: {e}")
            return filepath, None
    
    def get_screenshots(self, limit=10):
        """
        Get recent screenshots.
        
        Args:
            limit (int): Maximum number of screenshots to return
            
        Returns:
            list: List of screenshot metadata
        """
        screenshots = sorted(
            self.metadata["screenshots"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        return screenshots[:limit]
    
    def get_clipboard_items(self, limit=10):
        """
        Get recent clipboard items.
        
        Args:
            limit (int): Maximum number of items to return
            
        Returns:
            list: List of clipboard metadata
        """
        clipboard_items = sorted(
            self.metadata["clipboard"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        return clipboard_items[:limit]
