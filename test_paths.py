#!/usr/bin/env python3
"""
Quick test script for OMIFI storage paths.
This validates that storage directories are created and accessible.
"""

import os
import json
import time
from datetime import datetime
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omifi-test")

def initialize_storage():
    """Initialize test storage directories and sample files."""
    # Create multiple base directories for better compatibility
    base_dirs = [
        os.path.expanduser("~/.omifi"),  # User home directory (standard)
        os.path.join(os.getcwd(), ".omifi"),  # Current working directory
        os.path.join(os.getcwd(), "omifi-data"),  # Alternative in current directory
        "/tmp/omifi"  # Temporary directory (fallback)
    ]
    
    timestamp = datetime.now().isoformat().replace(':', '-')
    
    for base_dir in base_dirs:
        try:
            logger.info(f"Testing directory: {base_dir}")
            
            # Create base dir and subdirectories
            os.makedirs(base_dir, exist_ok=True)
            screenshots_dir = os.path.join(base_dir, "screenshots")
            clipboard_dir = os.path.join(base_dir, "clipboard")
            os.makedirs(screenshots_dir, exist_ok=True)
            os.makedirs(clipboard_dir, exist_ok=True)
            
            # Create a test file to verify write permissions
            test_file = os.path.join(base_dir, "test_file.txt")
            with open(test_file, 'w') as f:
                f.write(f"Test file created at {timestamp}")
            logger.info(f"  Created test file: {test_file}")
            
            # Create a test screenshot
            screenshot_file = os.path.join(screenshots_dir, f"test_screenshot_{timestamp}.png")
            img = Image.new('RGB', (400, 300), color=(30, 60, 90))
            img.save(screenshot_file)
            logger.info(f"  Created test screenshot: {screenshot_file}")
            
            # Create a test clipboard text file
            clipboard_text_file = os.path.join(clipboard_dir, f"test_clipboard_text_{timestamp}.txt")
            with open(clipboard_text_file, 'w') as f:
                f.write(f"This is a test clipboard text entry created at {timestamp}")
            logger.info(f"  Created test clipboard text: {clipboard_text_file}")
            
            # Create a test JSON file
            clipboard_json_file = os.path.join(clipboard_dir, f"test_clipboard_json_{timestamp}.json")
            test_data = {
                "test": True,
                "timestamp": timestamp,
                "data": {
                    "name": "OMIFI Test Data",
                    "value": 42,
                    "tags": ["test", "json", "clipboard"]
                }
            }
            with open(clipboard_json_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            logger.info(f"  Created test clipboard JSON: {clipboard_json_file}")
            
            # Create a test clipboard image 
            clipboard_image_file = os.path.join(clipboard_dir, f"test_clipboard_image_{timestamp}.png")
            img = Image.new('RGB', (200, 150), color=(120, 40, 80))
            img.save(clipboard_image_file)
            logger.info(f"  Created test clipboard image: {clipboard_image_file}")
            
            # Create/update metadata file
            metadata_file = os.path.join(base_dir, "metadata.json")
            metadata = {}
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, IOError):
                    metadata = {"screenshots": [], "clipboard": []}
            else:
                metadata = {"screenshots": [], "clipboard": []}
            
            # Add test entries to metadata
            screenshot_filename = os.path.basename(screenshot_file)
            metadata["screenshots"].append({
                "timestamp": timestamp,
                "filename": screenshot_filename,
                "filepath": screenshot_filename
            })
            
            for file_path in [clipboard_text_file, clipboard_json_file, clipboard_image_file]:
                filename = os.path.basename(file_path)
                file_type = "text"
                if file_path.endswith(".json"):
                    file_type = "json"
                elif file_path.endswith((".png", ".jpg", ".jpeg", ".gif")):
                    file_type = "image"
                
                metadata["clipboard"].append({
                    "timestamp": timestamp,
                    "filename": filename,
                    "filepath": filename,
                    "type": file_type
                })
            
            # Save updated metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"  Updated metadata: {metadata_file}")
            
            logger.info(f"✅ Successfully initialized {base_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing {base_dir}: {e}")

def check_files():
    """Check that files exist in the expected locations."""
    base_dirs = [
        os.path.expanduser("~/.omifi"),
        os.path.join(os.getcwd(), ".omifi"),
        os.path.join(os.getcwd(), "omifi-data"),
        "/tmp/omifi"
    ]
    
    success = False
    
    for base_dir in base_dirs:
        screenshots_dir = os.path.join(base_dir, "screenshots")
        clipboard_dir = os.path.join(base_dir, "clipboard")
        metadata_file = os.path.join(base_dir, "metadata.json")
        
        if not os.path.exists(base_dir):
            logger.warning(f"Directory doesn't exist: {base_dir}")
            continue
            
        logger.info(f"Checking directory: {base_dir}")
        
        # Check metadata file
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"  Metadata available: {len(metadata.get('screenshots', []))} screenshots, {len(metadata.get('clipboard', []))} clipboard items")
                success = True
                
                # Check screenshots
                if os.path.exists(screenshots_dir):
                    screenshots = os.listdir(screenshots_dir)
                    logger.info(f"  Screenshots directory contains {len(screenshots)} files")
                else:
                    logger.warning(f"  Screenshots directory missing: {screenshots_dir}")
                
                # Check clipboard
                if os.path.exists(clipboard_dir):
                    clipboard_files = os.listdir(clipboard_dir)
                    logger.info(f"  Clipboard directory contains {len(clipboard_files)} files")
                else:
                    logger.warning(f"  Clipboard directory missing: {clipboard_dir}")
                
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"  Error reading metadata: {e}")
        else:
            logger.warning(f"  Metadata file missing: {metadata_file}")
    
    return success

if __name__ == "__main__":
    logger.info("OMIFI Path Test Script")
    logger.info("=====================")
    logger.info("Current working directory: " + os.getcwd())
    
    initialize_storage()
    time.sleep(1)  # Wait for file operations to complete
    
    logger.info("\nChecking files:")
    success = check_files()
    
    if success:
        logger.info("\n✅ Test completed successfully - storage directories are working")
    else:
        logger.error("\n❌ Test failed - storage directories not fully working")
    
    logger.info("\nTesting script complete")