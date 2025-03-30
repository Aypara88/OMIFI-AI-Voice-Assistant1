"""
Resource management for the OMIFI assistant UI.
"""

import os
import sys
import logging
from pathlib import Path

def get_asset_dir():
    """
    Get the assets directory path.
    
    Returns:
        str: Path to the assets directory
    """
    # First check relative to current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    assets_dir = os.path.join(project_root, "static", "assets")
    
    # Create assets directory if it doesn't exist
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir, exist_ok=True)
    
    return assets_dir

def get_icon_path(icon_name):
    """
    Get the path to an icon file.
    
    Args:
        icon_name (str): Name of the icon file
        
    Returns:
        str: Path to the icon file
    """
    assets_dir = get_asset_dir()
    
    # Check if icon exists in assets directory
    icon_path = os.path.join(assets_dir, icon_name)
    if os.path.exists(icon_path):
        return icon_path
    
    # If specific icon doesn't exist, return default
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    default_icon = os.path.join(project_root, "generated-icon.png")
    
    # If no default icon exists, return None
    if not os.path.exists(default_icon):
        return None
    
    return default_icon