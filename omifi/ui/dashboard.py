import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QWidget, QLabel, QListWidget, QListWidgetItem, 
                           QPushButton, QScrollArea, QTextEdit, QSplitter)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from datetime import datetime

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
        self.tts = text_to_speech
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("OMIFI Assistant Dashboard")
        self.setMinimumSize(800, 600)
        
        # Create the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header_layout = QHBoxLayout()
        logo_label = QLabel("OMIFI")
        logo_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        
        # Add header to main layout
        main_layout.addLayout(header_layout)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.screenshots_tab = QWidget()
        self.clipboard_tab = QWidget()
        
        self.tab_widget.addTab(self.screenshots_tab, "Screenshots")
        self.tab_widget.addTab(self.clipboard_tab, "Clipboard")
        
        # Setup the screenshots tab
        self.setup_screenshots_tab()
        
        # Setup the clipboard tab
        self.setup_clipboard_tab()
        
        # Add tabs to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Refresh data on startup
        self.refresh_data()
    
    def setup_screenshots_tab(self):
        """Set up the screenshots tab UI."""
        layout = QVBoxLayout(self.screenshots_tab)
        
        # Screenshot controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)
        
        take_screenshot_btn = QPushButton("Take Screenshot")
        take_screenshot_btn.clicked.connect(self.take_screenshot)
        controls_layout.addWidget(take_screenshot_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Screenshots list
        self.screenshots_list = QListWidget()
        self.screenshots_list.setIconSize(QSize(120, 90))
        self.screenshots_list.itemDoubleClicked.connect(self.open_screenshot)
        layout.addWidget(self.screenshots_list)
    
    def setup_clipboard_tab(self):
        """Set up the clipboard tab UI."""
        layout = QVBoxLayout(self.clipboard_tab)
        
        # Clipboard controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)
        
        sense_clipboard_btn = QPushButton("Sense Clipboard")
        sense_clipboard_btn.clicked.connect(self.sense_clipboard)
        controls_layout.addWidget(sense_clipboard_btn)
        
        read_aloud_btn = QPushButton("Read Aloud")
        read_aloud_btn.clicked.connect(self.read_clipboard_aloud)
        controls_layout.addWidget(read_aloud_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Add a splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Clipboard content list
        self.clipboard_list = QListWidget()
        splitter.addWidget(self.clipboard_list)
        self.clipboard_list.currentItemChanged.connect(self.show_clipboard_content)
        
        # Clipboard content preview
        self.clipboard_preview = QTextEdit()
        self.clipboard_preview.setReadOnly(True)
        splitter.addWidget(self.clipboard_preview)
        
        # Set splitter sizes
        splitter.setSizes([300, 500])
    
    def refresh_data(self):
        """Refresh the displayed data."""
        logger.info("Refreshing dashboard data")
        self.refresh_screenshots()
        self.refresh_clipboard()
    
    def refresh_screenshots(self):
        """Refresh the screenshots list."""
        self.screenshots_list.clear()
        
        screenshots = self.storage.get_screenshots()
        
        if not screenshots:
            empty_item = QListWidgetItem("No screenshots found")
            self.screenshots_list.addItem(empty_item)
            return
        
        for screenshot in screenshots:
            try:
                # Format the timestamp
                timestamp = datetime.fromisoformat(screenshot["timestamp"])
                display_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                # Create a list item with the timestamp
                item = QListWidgetItem(display_time)
                item.setData(Qt.UserRole, screenshot["path"])
                
                # Try to create a small thumbnail (using path directly)
                # This is a simplified version; in a real app you might want to generate actual thumbnails
                pixmap = QPixmap(screenshot["path"])
                if not pixmap.isNull():
                    # Scale down for the list
                    pixmap = pixmap.scaled(120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(pixmap))
                
                self.screenshots_list.addItem(item)
                
            except Exception as e:
                logger.error(f"Error adding screenshot to list: {e}")
    
    def refresh_clipboard(self):
        """Refresh the clipboard list."""
        self.clipboard_list.clear()
        self.clipboard_preview.clear()
        
        clipboard_items = self.storage.get_clipboard_items()
        
        if not clipboard_items:
            empty_item = QListWidgetItem("No clipboard content found")
            self.clipboard_list.addItem(empty_item)
            return
        
        for item in clipboard_items:
            try:
                # Format the timestamp
                timestamp = datetime.fromisoformat(item["timestamp"])
                display_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                # Create a list item with the timestamp
                list_item = QListWidgetItem(display_time)
                list_item.setData(Qt.UserRole, item["path"])
                
                self.clipboard_list.addItem(list_item)
                
            except Exception as e:
                logger.error(f"Error adding clipboard item to list: {e}")
    
    def show_clipboard_content(self, current, previous):
        """Show the content of the selected clipboard item."""
        if not current:
            self.clipboard_preview.clear()
            return
        
        path = current.data(Qt.UserRole)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.clipboard_preview.setText(content)
            
        except Exception as e:
            logger.error(f"Error reading clipboard content: {e}")
            self.clipboard_preview.setText(f"Error reading content: {e}")
    
    def take_screenshot(self):
        """Take a screenshot from the UI."""
        filepath = self.screenshot_manager.take_screenshot()
        
        if filepath:
            self.refresh_screenshots()
            logger.info(f"Screenshot taken from UI: {filepath}")
        else:
            logger.error("Failed to take screenshot from UI")
    
    def sense_clipboard(self):
        """Sense clipboard from the UI."""
        content_type, content = self.clipboard_manager.sense_clipboard()
        
        if content:
            self.refresh_clipboard()
            logger.info("Clipboard sensed from UI")
        else:
            logger.info("No clipboard content detected")
    
    def read_clipboard_aloud(self):
        """Read the selected clipboard content aloud."""
        current_item = self.clipboard_list.currentItem()
        
        if not current_item:
            self.tts.speak("No clipboard content selected")
            return
        
        path = current_item.data(Qt.UserRole)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content:
                # For long content, truncate it
                if len(content) > 500:
                    truncated = content[:500] + "... (content truncated)"
                    self.tts.speak(truncated)
                else:
                    self.tts.speak(content)
            else:
                self.tts.speak("The clipboard content is empty")
                
        except Exception as e:
            logger.error(f"Error reading clipboard content aloud: {e}")
            self.tts.speak("Error reading clipboard content")
    
    def open_screenshot(self, item):
        """Open the selected screenshot."""
        path = item.data(Qt.UserRole)
        
        try:
            # Windows
            if os.name == 'nt':
                os.startfile(path)
            # macOS
            elif os.name == 'posix' and hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
                os.system(f'open "{path}"')
            # Linux
            else:
                os.system(f'xdg-open "{path}"')
                
            logger.info(f"Opened screenshot: {path}")
            
        except Exception as e:
            logger.error(f"Error opening screenshot: {e}")
