"""
Storage module for the OMIFI assistant.
"""

import os
import json
import time
from datetime import datetime
from PIL import Image

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
        # Set up base directory structure
        self.base_dir = base_dir or os.path.expanduser("~/.omifi")
        self.screenshots_dir = os.path.join(self.base_dir, "screenshots")
        self.clipboard_dir = os.path.join(self.base_dir, "clipboard")
        self.metadata_file = os.path.join(self.base_dir, "metadata.json")
        
        # Create directories if they don't exist
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.clipboard_dir, exist_ok=True)
        
        # Load metadata
        self.metadata = self._load_metadata()
    
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
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading metadata: {e}")
        
        # Return default metadata structure
        return {
            "screenshots": [],
            "clipboard": []
        }
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            print(f"Error saving metadata: {e}")
    
    def save_screenshot(self, screenshot, filename=None):
        """
        Save a screenshot to storage.
        
        Args:
            screenshot: PIL Image object
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved screenshot
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure the filename has a png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Save the screenshot
        filepath = os.path.join(self.screenshots_dir, filename)
        screenshot.save(filepath)
        
        # Update metadata
        screenshot_info = {
            "filename": filename,
            "filepath": filename,  # Relative path for portable storage
            "timestamp": datetime.now().isoformat(),
            "size": os.path.getsize(filepath)
        }
        
        # Add to metadata and save
        self.metadata["screenshots"].append(screenshot_info)
        self._save_metadata()
        
        return filepath
    
    def save_clipboard_content(self, content, content_type="text", filename=None):
        """
        Save clipboard content to storage.
        
        Args:
            content: Clipboard content (text, binary data, etc.)
            content_type: Type of content (text, image, etc.)
            filename: Name for the saved file
            
        Returns:
            str: Path to the saved content
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Set appropriate extension based on content type
            if content_type == "text":
                extension = ".txt"
            elif content_type == "image":
                extension = ".png"  # Default to PNG for images
            else:
                extension = ".bin"  # Binary data for unknown types
                
            filename = f"clipboard_{timestamp}{extension}"
        
        # Ensure the filename has appropriate extension
        if content_type == "text" and not any(filename.lower().endswith(ext) for ext in ['.txt', '.md', '.json', '.csv']):
            filename += '.txt'
        elif content_type == "image" and not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
            filename += '.png'
        
        # Save the content
        filepath = os.path.join(self.clipboard_dir, filename)
        
        # Handle different content types
        if content_type == "text":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        elif content_type == "image":
            # For binary image data
            try:
                # Check if content is a string (base64) or bytes
                if isinstance(content, str) and content.startswith(('data:image', 'http')):
                    # It's likely a data URL or web URL - pass to PIL to handle
                    from PIL import Image
                    import io
                    import base64
                    import re
                    
                    # Handle data URLs (base64)
                    if content.startswith('data:image'):
                        # Extract the base64 content
                        base64_data = re.sub('^data:image/.+;base64,', '', content)
                        image_data = base64.b64decode(base64_data)
                        with open(filepath, 'wb') as f:
                            if isinstance(image_data, bytes):
                                f.write(image_data)
                    else:
                        # It's a URL or something else - try to handle with PIL
                        import urllib.request
                        urllib.request.urlretrieve(content, filepath)
                else:
                    # It's binary data
                    with open(filepath, 'wb') as f:
                        if isinstance(content, bytes):
                            f.write(content)
                        elif isinstance(content, str):
                            f.write(content.encode('utf-8'))
            except Exception as e:
                # Fall back to raw binary writing
                with open(filepath, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    elif isinstance(content, str):
                        f.write(content.encode('utf-8'))
        else:
            # For other binary data types
            with open(filepath, 'wb') as f:
                if isinstance(content, bytes):
                    f.write(content)
                elif isinstance(content, str):
                    f.write(content.encode('utf-8'))
        
        # Update metadata
        clip_info = {
            "filename": filename,
            "filepath": filename,  # Relative path for portable storage
            "timestamp": datetime.now().isoformat(),
            "type": content_type,
            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        }
        
        # Add to metadata and save
        self.metadata["clipboard"].append(clip_info)
        self._save_metadata()
        
        return filepath
    
    def get_last_screenshot(self):
        """
        Get the path to the most recent screenshot.
        
        Returns:
            str: Path to the most recent screenshot or None if not available
        """
        if not self.metadata["screenshots"]:
            return None
        
        # Sort by timestamp and get the most recent one
        sorted_screenshots = sorted(
            self.metadata["screenshots"], 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        if sorted_screenshots:
            return os.path.join(self.screenshots_dir, sorted_screenshots[0]["filepath"])
        
        return None
    
    def get_last_clipboard_content(self):
        """
        Get the most recent clipboard content.
        
        Returns:
            tuple: (filepath, content) or (None, None) if not available
        """
        if not self.metadata["clipboard"]:
            return None, None
        
        # Sort by timestamp and get the most recent one
        sorted_clipboard = sorted(
            self.metadata["clipboard"], 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        if sorted_clipboard:
            filepath = os.path.join(self.clipboard_dir, sorted_clipboard[0]["filepath"])
            
            # Read the content based on type
            content_type = sorted_clipboard[0].get("type", "text")
            
            if not os.path.exists(filepath):
                return None, None
                
            # Handle different content types
            if content_type == "text":
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return filepath, content
                except IOError:
                    pass
            elif content_type == "image":
                # For images, just return the path - we don't load the binary content
                # The web app will serve the image file directly
                return filepath, f"[Image: {os.path.basename(filepath)}]"
            else:
                # For other binary types, return the path and a description
                return filepath, f"[Binary content: {os.path.basename(filepath)}]"
        
        return None, None
    
    def get_screenshots(self, limit=10):
        """
        Get recent screenshots.
        
        Args:
            limit (int): Maximum number of screenshots to return
            
        Returns:
            list: List of screenshot metadata
        """
        # Sort by timestamp (newest first) and limit the result
        return sorted(
            self.metadata.get("screenshots", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
    
    def get_clipboard_items(self, limit=10):
        """
        Get recent clipboard items.
        
        Args:
            limit (int): Maximum number of items to return
            
        Returns:
            list: List of clipboard metadata
        """
        # Sort by timestamp (newest first) and limit the result
        return sorted(
            self.metadata.get("clipboard", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]