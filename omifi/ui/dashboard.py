"""
Dashboard interface for the OMIFI assistant.
"""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QSplitter,
    QTextEdit, QGridLayout, QScrollArea
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

from .resources import get_icon_path

logger = logging.getLogger(__name__)

class OmifiDashboard(QMainWindow):
    """
    Main dashboard window for the OMIFI assistant.
    Shows recent screenshots and clipboard content.
    """
    
    def __init__(self, storage, clipboard_manager, screenshot_manager, text_to_speech):
        """
        Initialize the dashboard.
        
        Args:
            storage: Storage instance
            clipboard_manager: ClipboardManager instance
            screenshot_manager: ScreenshotManager instance
            text_to_speech: TextToSpeech instance
        """
        super().__init__()
        
        self.storage = storage
        self.clipboard_manager = clipboard_manager
        self.screenshot_manager = screenshot_manager
        self.text_to_speech = text_to_speech
        
        # Initialize UI
        self.init_ui()
        
        # Load data
        self.refresh_data()
        
        logger.info("Dashboard initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("OMIFI Voice Assistant Dashboard")
        self.setMinimumSize(800, 600)
        
        # Set window icon
        icon_path = get_icon_path("omifi_icon.svg")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create header
        header_layout = QHBoxLayout()
        logo_label = QLabel("OMIFI Voice Assistant")
        logo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        
        # Create action buttons
        screenshot_button = QPushButton("Take Screenshot")
        screenshot_button.clicked.connect(self.take_screenshot)
        
        clipboard_button = QPushButton("Sense Clipboard")
        clipboard_button.clicked.connect(self.sense_clipboard)
        
        header_layout.addWidget(screenshot_button)
        header_layout.addWidget(clipboard_button)
        
        main_layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Setup tabs
        self.setup_screenshots_tab()
        self.setup_clipboard_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_screenshots_tab(self):
        """Set up the screenshots tab UI."""
        # Create tab widget
        screenshots_tab = QWidget()
        screenshots_layout = QVBoxLayout()
        screenshots_tab.setLayout(screenshots_layout)
        
        # Create grid layout for screenshots
        self.screenshots_grid = QGridLayout()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.screenshots_grid)
        scroll_area.setWidget(scroll_widget)
        
        screenshots_layout.addWidget(scroll_area)
        
        # Add tab
        self.tab_widget.addTab(screenshots_tab, "Screenshots")
    
    def setup_clipboard_tab(self):
        """Set up the clipboard tab UI."""
        # Create tab widget
        clipboard_tab = QWidget()
        clipboard_layout = QVBoxLayout()
        clipboard_tab.setLayout(clipboard_layout)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Create list widget
        self.clipboard_list = QListWidget()
        self.clipboard_list.currentItemChanged.connect(self.show_clipboard_content)
        splitter.addWidget(self.clipboard_list)
        
        # Create content viewer
        self.clipboard_viewer = QTextEdit()
        self.clipboard_viewer.setReadOnly(True)
        splitter.addWidget(self.clipboard_viewer)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        
        clipboard_layout.addWidget(splitter)
        
        # Add read aloud button
        read_button = QPushButton("Read Aloud")
        read_button.clicked.connect(self.read_clipboard_aloud)
        clipboard_layout.addWidget(read_button)
        
        # Add tab
        self.tab_widget.addTab(clipboard_tab, "Clipboard")
    
    def refresh_data(self):
        """Refresh the displayed data."""
        self.refresh_screenshots()
        self.refresh_clipboard()
    
    def refresh_screenshots(self):
        """Refresh the screenshots list."""
        # Clear existing layout
        while self.screenshots_grid.count():
            item = self.screenshots_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Get recent screenshots
        screenshots = self.storage.get_screenshots(20)
        
        if not screenshots:
            # Show message if no screenshots
            label = QLabel("No screenshots available. Say 'Hey OMIFI, take a screenshot' to capture your screen.")
            label.setAlignment(Qt.AlignCenter)
            self.screenshots_grid.addWidget(label, 0, 0)
            return
        
        # Add screenshots to grid
        row, col = 0, 0
        max_cols = 3
        
        for i, screenshot in enumerate(screenshots):
            # Create widget for screenshot
            widget = QWidget()
            layout = QVBoxLayout()
            widget.setLayout(layout)
            
            # Create label for image
            img_label = QLabel()
            img_label.setFixedSize(250, 180)
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet("background-color: #2c2c2c; border-radius: 5px;")
            
            # Load image
            filepath = screenshot.get("filepath")
            if filepath and os.path.exists(filepath):
                pixmap = QPixmap(filepath)
                pixmap = pixmap.scaled(
                    250, 180,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                img_label.setPixmap(pixmap)
                
                # Make label clickable
                img_label.mousePressEvent = lambda event, path=filepath: self.open_screenshot(path)
                img_label.setCursor(Qt.PointingHandCursor)
            
            layout.addWidget(img_label)
            
            # Add timestamp
            timestamp = screenshot.get("timestamp", "").split("T")[0]
            label = QLabel(timestamp)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            # Add to grid
            self.screenshots_grid.addWidget(widget, row, col)
            
            # Update row, col
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def refresh_clipboard(self):
        """Refresh the clipboard list."""
        # Clear list
        self.clipboard_list.clear()
        
        # Get recent clipboard items
        clipboard_items = self.storage.get_clipboard_items(50)
        
        if not clipboard_items:
            # Add empty message
            item = QListWidgetItem("No clipboard content available")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.clipboard_list.addItem(item)
            return
        
        # Add items to list
        for clip in clipboard_items:
            # Format timestamp
            timestamp = clip.get("timestamp", "").replace("T", " ").split(".")[0]
            
            # Create list item
            item = QListWidgetItem(timestamp)
            item.setData(Qt.UserRole, clip.get("filepath"))
            
            self.clipboard_list.addItem(item)
    
    def show_clipboard_content(self, current, previous):
        """Show the content of the selected clipboard item."""
        if not current:
            self.clipboard_viewer.clear()
            return
        
        # Get filepath from item data
        filepath = current.data(Qt.UserRole)
        
        if not filepath or not os.path.exists(filepath):
            self.clipboard_viewer.setText("File not found")
            return
        
        try:
            # Read file content
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Set content
            self.clipboard_viewer.setText(content)
            
        except Exception as e:
            logger.error(f"Error reading clipboard content: {e}")
            self.clipboard_viewer.setText(f"Error reading content: {e}")
    
    def take_screenshot(self):
        """Take a screenshot from the UI."""
        filepath = self.screenshot_manager.take_screenshot()
        
        if filepath:
            self.text_to_speech.speak("Screenshot saved", block=False)
            # Refresh after a short delay
            self.refresh_screenshots()
        else:
            self.text_to_speech.speak("Failed to take screenshot", block=False)
    
    def sense_clipboard(self):
        """Sense clipboard from the UI."""
        content_type, content = self.clipboard_manager.sense_clipboard()
        
        if content:
            self.text_to_speech.speak("Clipboard content saved", block=False)
            # Refresh after a short delay
            self.refresh_clipboard()
        else:
            self.text_to_speech.speak("No clipboard content found or unchanged", block=False)
    
    def read_clipboard_aloud(self):
        """Read the selected clipboard content aloud."""
        current_item = self.clipboard_list.currentItem()
        
        if not current_item:
            self.text_to_speech.speak("No clipboard item selected", block=False)
            return
        
        # Get filepath from item data
        filepath = current_item.data(Qt.UserRole)
        
        if not filepath or not os.path.exists(filepath):
            self.text_to_speech.speak("Clipboard content not found", block=False)
            return
        
        try:
            # Read file content
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Limit content length for speech
            if len(content) > 500:
                content = content[:500] + "... (content truncated)"
            
            # Speak content
            self.text_to_speech.speak(f"Clipboard contains: {content}", block=False)
            
        except Exception as e:
            logger.error(f"Error reading clipboard content: {e}")
            self.text_to_speech.speak("Error reading clipboard content", block=False)
    
    def open_screenshot(self, filepath):
        """Open the selected screenshot."""
        if not filepath or not os.path.exists(filepath):
            self.text_to_speech.speak("Screenshot not found", block=False)
            return
        
        try:
            # Try to open with system default viewer
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # Linux, macOS
                import subprocess
                subprocess.Popen(['xdg-open', filepath])
            
            logger.info(f"Opened screenshot: {filepath}")
            
        except Exception as e:
            logger.error(f"Error opening screenshot: {e}")
            self.text_to_speech.speak("Error opening screenshot", block=False)