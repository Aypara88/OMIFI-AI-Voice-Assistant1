"""
Resource management for the OMIFI assistant UI.
"""

import os
import sys

def get_asset_dir():
    """
    Get the assets directory path.
    
    Returns:
        str: Path to the assets directory
    """
    # First try the assets directory next to the script
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(script_dir, "assets")
    
    if os.path.exists(assets_dir):
        return assets_dir
    
    # If not found, try to create it
    try:
        os.makedirs(assets_dir, exist_ok=True)
        return assets_dir
    except Exception:
        pass
    
    # Fallback to a directory in the user's home
    home_assets = os.path.expanduser("~/.omifi/assets")
    os.makedirs(home_assets, exist_ok=True)
    return home_assets

def get_icon_path(icon_name):
    """
    Get the path to an icon file.
    
    Args:
        icon_name (str): Name of the icon file
        
    Returns:
        str: Path to the icon file
    """
    # Check asset directory
    assets_dir = get_asset_dir()
    icon_path = os.path.join(assets_dir, icon_name)
    
    if os.path.exists(icon_path):
        return icon_path
    
    # If icon doesn't exist, return default icon
    default_icon = os.path.join(assets_dir, "omifi_icon.svg")
    
    if os.path.exists(default_icon):
        return default_icon
    
    # If default icon doesn't exist, create a simple SVG icon
    try:
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="#3498db" />
            <circle cx="30" cy="40" r="5" fill="white" />
            <circle cx="70" cy="40" r="5" fill="white" />
            <path d="M30,65 Q50,80 70,65" stroke="white" stroke-width="3" fill="none" />
        </svg>"""
        
        with open(default_icon, 'w') as f:
            f.write(svg_content)
        
        return default_icon
        
    except Exception:
        # Last resort, return None
        return None