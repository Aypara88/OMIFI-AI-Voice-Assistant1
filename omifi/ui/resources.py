import os
import logging

logger = logging.getLogger(__name__)

def get_asset_dir():
    """
    Get the assets directory path.
    
    Returns:
        str: Path to the assets directory
    """
    # Find the assets directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "assets")
    
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
    icon_path = os.path.join(assets_dir, icon_name)
    
    if not os.path.exists(icon_path):
        logger.warning(f"Icon file not found: {icon_path}")
        
        # Return a default icon if the requested one doesn't exist
        if icon_name != "omifi_icon.svg":
            return get_icon_path("omifi_icon.svg")
    
    return icon_path
