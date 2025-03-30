"""
Dashboard interface for the OMIFI assistant.
"""

import os
import sys
import logging
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QListWidget, QListWidgetItem, QTextEdit,
    QSplitter, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

from omifi.ui.resources import get_icon_path

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
        self.logger = logging.getLogger(__name__)
        self.storage = storage
        self.clipboard_manager = clipboard_manager
        self.screenshot_manager = screenshot_manager
        self.text_to_speech = text_to_speech
        
        # Set window properties
        self.setWindowTitle("OMIFI Assistant Dashboard")
        self.setMinimumSize(800, 600)
        
        # Load icon
        icon_path = get_icon_path("omifi_icon.png")
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize UI
        self.init_ui()
        
        # Refresh data
        self.refresh_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        header_label = QLabel("OMIFI Assistant Dashboard")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)
        
        # Add refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Add tab widget
        self.tabs = QTabWidget()
        
        # Setup screenshots tab
        self.screenshots_tab = QWidget()
        self.setup_screenshots_tab()
        self.tabs.addTab(self.screenshots_tab, "Screenshots")
        
        # Setup clipboard tab
        self.clipboard_tab = QWidget()
        self.setup_clipboard_tab()
        self.tabs.addTab(self.clipboard_tab, "Clipboard")
        
        main_layout.addWidget(self.tabs)
    
    def setup_screenshots_tab(self):
        """Set up the screenshots tab UI."""
        # Create layout
        screenshots_layout = QVBoxLayout(self.screenshots_tab)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Add screenshot button
        screenshot_button = QPushButton("Take Screenshot")
        screenshot_button.clicked.connect(self.take_screenshot)
        controls_layout.addWidget(screenshot_button)
        
        # Add spacer
        controls_layout.addStretch(1)
        
        screenshots_layout.addLayout(controls_layout)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        
        # Add list of screenshots
        self.screenshots_list = QListWidget()
        self.screenshots_list.setMinimumWidth(250)
        self.screenshots_list.itemDoubleClicked.connect(
            lambda item: self.open_screenshot(item.data(Qt.UserRole))
        )
        splitter.addWidget(self.screenshots_list)
        
        # Add preview area
        self.screenshot_preview = QLabel("Select a screenshot to preview")
        self.screenshot_preview.setAlignment(Qt.AlignCenter)
        self.screenshot_preview.setStyleSheet("background-color: #f0f0f0;")
        splitter.addWidget(self.screenshot_preview)
        
        # Set initial splitter sizes
        splitter.setSizes([250, 550])
        
        screenshots_layout.addWidget(splitter)
    
    def setup_clipboard_tab(self):
        """Set up the clipboard tab UI."""
        # Create layout
        clipboard_layout = QVBoxLayout(self.clipboard_tab)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Add sense clipboard button
        sense_button = QPushButton("Sense Clipboard")
        sense_button.clicked.connect(self.sense_clipboard)
        controls_layout.addWidget(sense_button)
        
        # Add read clipboard button
        read_button = QPushButton("Read Aloud")
        read_button.clicked.connect(self.read_clipboard_aloud)
        controls_layout.addWidget(read_button)
        
        # Add spacer
        controls_layout.addStretch(1)
        
        clipboard_layout.addLayout(controls_layout)
        
        # Create splitter for list and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Add list of clipboard items
        self.clipboard_list = QListWidget()
        self.clipboard_list.setMinimumWidth(250)
        self.clipboard_list.currentItemChanged.connect(self.show_clipboard_content)
        splitter.addWidget(self.clipboard_list)
        
        # Add content area
        self.clipboard_content = QTextEdit()
        self.clipboard_content.setReadOnly(True)
        splitter.addWidget(self.clipboard_content)
        
        # Set initial splitter sizes
        splitter.setSizes([250, 550])
        
        clipboard_layout.addWidget(splitter)
    
    def refresh_data(self):
        """Refresh the displayed data."""
        self.refresh_screenshots()
        self.refresh_clipboard()
    
    def refresh_screenshots(self):
        """Refresh the screenshots list."""
        # Clear the list
        self.screenshots_list.clear()
        
        # Get screenshots from storage
        screenshots = self.storage.get_screenshots()
        
        # Add items to list
        for screenshot in screenshots:
            item = QListWidgetItem()
            filepath = os.path.join(self.storage.screenshots_dir, screenshot.get("filepath", ""))
            timestamp = screenshot.get("timestamp", "").replace("T", " ").split(".")[0]
            
            item.setText(f"{os.path.basename(filepath)} ({timestamp})")
            item.setData(Qt.UserRole, filepath)
            
            self.screenshots_list.addItem(item)
    
    def refresh_clipboard(self):
        """Refresh the clipboard list."""
        # Clear the list
        self.clipboard_list.clear()
        
        # Get clipboard items from storage
        clipboard_items = self.storage.get_clipboard_items()
        
        # Add items to list
        for clip in clipboard_items:
            item = QListWidgetItem()
            filepath = os.path.join(self.storage.clipboard_dir, clip.get("filepath", ""))
            timestamp = clip.get("timestamp", "").replace("T", " ").split(".")[0]
            content_type = clip.get("type", "text")
            
            item.setText(f"{content_type.capitalize()} ({timestamp})")
            item.setData(Qt.UserRole, filepath)
            
            self.clipboard_list.addItem(item)
    
    def show_clipboard_content(self, current, previous):
        """Show the content of the selected clipboard item."""
        if not current:
            self.clipboard_content.clear()
            return
        
        filepath = current.data(Qt.UserRole)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.clipboard_content.setText(content)
        except Exception as e:
            self.logger.error(f"Error loading clipboard content: {e}")
            self.clipboard_content.setText(f"Error loading content: {str(e)}")
    
    def take_screenshot(self):
        """Take a screenshot from the UI."""
        try:
            filepath = self.screenshot_manager.take_screenshot()
            
            if filepath:
                self.refresh_screenshots()
                QMessageBox.information(
                    self,
                    "Screenshot Taken",
                    f"Screenshot saved to {os.path.basename(filepath)}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Screenshot Failed",
                    "Failed to take screenshot"
                )
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            QMessageBox.critical(
                self,
                "Screenshot Error",
                f"Error taking screenshot: {str(e)}"
            )
    
    def sense_clipboard(self):
        """Sense clipboard from the UI."""
        try:
            content_type, content = self.clipboard_manager.sense_clipboard()
            
            if content and content.strip():
                self.refresh_clipboard()
                QMessageBox.information(
                    self,
                    "Clipboard Sensed",
                    "Clipboard content saved"
                )
            else:
                QMessageBox.information(
                    self,
                    "Clipboard Empty",
                    "Clipboard is empty or contains non-text content"
                )
        except Exception as e:
            self.logger.error(f"Error sensing clipboard: {e}")
            QMessageBox.critical(
                self,
                "Clipboard Error",
                f"Error sensing clipboard: {str(e)}"
            )
    
    def read_clipboard_aloud(self):
        """Read the selected clipboard content aloud."""
        if not self.text_to_speech:
            QMessageBox.warning(
                self,
                "Text-to-Speech Unavailable",
                "Text-to-speech functionality is not available"
            )
            return
        
        current_item = self.clipboard_list.currentItem()
        
        if not current_item:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a clipboard item to read"
            )
            return
        
        filepath = current_item.data(Qt.UserRole)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content and content.strip():
                # Show notification
                QMessageBox.information(
                    self,
                    "Reading Clipboard",
                    "Reading clipboard content aloud"
                )
                
                # Speak in non-blocking mode
                self.text_to_speech.speak(content)
            else:
                QMessageBox.warning(
                    self,
                    "Empty Content",
                    "The selected clipboard item is empty"
                )
        except Exception as e:
            self.logger.error(f"Error reading clipboard content: {e}")
            QMessageBox.critical(
                self,
                "Read Error",
                f"Error reading clipboard content: {str(e)}"
            )
    
    def open_screenshot(self, filepath):
        """Open the selected screenshot."""
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(
                self,
                "File Not Found",
                "The screenshot file could not be found"
            )
            return
        
        try:
            # Try to load and display the screenshot
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                # Scale pixmap to fit the preview area while maintaining aspect ratio
                self.screenshot_preview.setPixmap(
                    pixmap.scaled(
                        self.screenshot_preview.width(),
                        self.screenshot_preview.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                
                # Also try to open it with the default viewer
                self.screenshot_manager.open_last_screenshot()
            else:
                self.screenshot_preview.setText("Failed to load screenshot")
        except Exception as e:
            self.logger.error(f"Error opening screenshot: {e}")
            self.screenshot_preview.setText(f"Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Screenshot Error",
                f"Error opening screenshot: {str(e)}"
            )