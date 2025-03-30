"""
System tray interface for the OMIFI assistant.
"""

import os
import sys
import logging
import threading
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread

from omifi.ui.resources import get_icon_path
from omifi.ui.dashboard import OmifiDashboard
from omifi.clipboard import ClipboardManager
from omifi.screenshot import ScreenshotManager
from omifi.text_to_speech import TextToSpeech

class OmifiSystemTray(QSystemTrayIcon):
    """
    System tray icon and menu for the OMIFI assistant.
    """
    
    def __init__(self, app, voice_recognizer, storage):
        """
        Initialize the system tray icon.
        
        Args:
            app: QApplication instance
            voice_recognizer: VoiceRecognizer instance
            storage: Storage instance
        """
        self.logger = logging.getLogger(__name__)
        self.app = app
        self.voice_recognizer = voice_recognizer
        self.storage = storage
        
        # Load icon
        icon_path = get_icon_path("omifi_icon.png")
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # Fallback to a generic icon
            icon = QIcon.fromTheme("audio-input-microphone")
        
        # Initialize system tray with icon
        super().__init__(icon, app)
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(storage)
        
        # Initialize screenshot manager
        self.screenshot_manager = ScreenshotManager(storage)
        
        # Initialize text-to-speech
        self.text_to_speech = TextToSpeech()
        
        # Initialize dashboard
        self.dashboard = None
        
        # Set up UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the system tray UI."""
        # Create menu
        self.menu = QMenu()
        
        # Add menu items
        # Toggle voice recognition
        self.toggle_voice_action = QAction("Pause Voice Recognition", self.menu)
        self.toggle_voice_action.triggered.connect(self.toggle_voice_recognition)
        self.menu.addAction(self.toggle_voice_action)
        
        # Open dashboard
        self.dashboard_action = QAction("Open Dashboard", self.menu)
        self.dashboard_action.triggered.connect(self.open_dashboard)
        self.menu.addAction(self.dashboard_action)
        
        # Separator
        self.menu.addSeparator()
        
        # Take screenshot
        self.screenshot_action = QAction("Take Screenshot", self.menu)
        self.screenshot_action.triggered.connect(self.take_screenshot)
        self.menu.addAction(self.screenshot_action)
        
        # Sense clipboard
        self.clipboard_action = QAction("Sense Clipboard", self.menu)
        self.clipboard_action.triggered.connect(self.sense_clipboard)
        self.menu.addAction(self.clipboard_action)
        
        # Separator
        self.menu.addSeparator()
        
        # Quit
        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(self.quit_application)
        self.menu.addAction(self.quit_action)
        
        # Set menu
        self.setContextMenu(self.menu)
        
        # Connect activated signal (when user clicks on the tray icon)
        self.activated.connect(self.on_tray_icon_activated)
        
        # Show initialization message
        self.showMessage(
            "OMIFI Assistant",
            "OMIFI is running in the background. Say 'Hey OMIFI' to activate.",
            QSystemTrayIcon.Information,
            3000
        )
    
    def on_tray_icon_activated(self, reason):
        """
        Handle tray icon activation.
        
        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_dashboard()
    
    def open_dashboard(self):
        """Open the dashboard window."""
        if not self.dashboard:
            self.dashboard = OmifiDashboard(
                self.storage,
                self.clipboard_manager,
                self.screenshot_manager,
                self.text_to_speech
            )
            self.dashboard.closeEvent = self.on_dashboard_closed
        
        self.dashboard.show()
        self.dashboard.activateWindow()
    
    def on_dashboard_closed(self, event):
        """Handle dashboard close event."""
        # Just hide the dashboard instead of destroying it
        self.dashboard.hide()
        event.ignore()
    
    def toggle_voice_recognition(self):
        """Toggle voice recognition on/off."""
        if self.voice_recognizer.paused:
            self.voice_recognizer.resume()
            self.toggle_voice_action.setText("Pause Voice Recognition")
            self.showMessage(
                "OMIFI Assistant",
                "Voice recognition resumed. Say 'Hey OMIFI' to activate.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.voice_recognizer.pause()
            self.toggle_voice_action.setText("Resume Voice Recognition")
            self.showMessage(
                "OMIFI Assistant",
                "Voice recognition paused.",
                QSystemTrayIcon.Information,
                2000
            )
    
    def take_screenshot(self):
        """Take a screenshot from the tray menu."""
        # Use a thread to prevent UI freezing
        screenshot_thread = threading.Thread(target=self._take_screenshot_thread)
        screenshot_thread.daemon = True
        screenshot_thread.start()
    
    def _take_screenshot_thread(self):
        """Take screenshot in a separate thread."""
        try:
            filepath = self.screenshot_manager.take_screenshot()
            
            if filepath:
                self.showMessage(
                    "OMIFI Assistant",
                    f"Screenshot saved to {os.path.basename(filepath)}",
                    QSystemTrayIcon.Information,
                    3000
                )
                
                # Speak notification
                if self.text_to_speech:
                    self.text_to_speech.speak("Screenshot captured and saved")
            else:
                self.showMessage(
                    "OMIFI Assistant",
                    "Failed to take screenshot",
                    QSystemTrayIcon.Warning,
                    3000
                )
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            self.showMessage(
                "OMIFI Assistant",
                "Error taking screenshot",
                QSystemTrayIcon.Critical,
                3000
            )
    
    def sense_clipboard(self):
        """Sense clipboard from the tray menu."""
        # Use a thread to prevent UI freezing
        clipboard_thread = threading.Thread(target=self._sense_clipboard_thread)
        clipboard_thread.daemon = True
        clipboard_thread.start()
    
    def _sense_clipboard_thread(self):
        """Sense clipboard in a separate thread."""
        try:
            content_type, content = self.clipboard_manager.sense_clipboard()
            
            if content and content.strip():
                # Truncate content preview if too long
                preview = content[:50] + "..." if len(content) > 50 else content
                
                self.showMessage(
                    "OMIFI Assistant",
                    f"Clipboard content saved: {preview}",
                    QSystemTrayIcon.Information,
                    3000
                )
                
                # Speak notification
                if self.text_to_speech:
                    self.text_to_speech.speak(f"Clipboard content saved")
            else:
                self.showMessage(
                    "OMIFI Assistant",
                    "Clipboard is empty or contains non-text content",
                    QSystemTrayIcon.Information,
                    3000
                )
        except Exception as e:
            self.logger.error(f"Error sensing clipboard: {e}")
            self.showMessage(
                "OMIFI Assistant",
                "Error sensing clipboard",
                QSystemTrayIcon.Critical,
                3000
            )
    
    def quit_application(self):
        """Quit the application."""
        # Stop voice recognition
        if self.voice_recognizer:
            self.voice_recognizer.stop()
        
        # Quit application
        QApplication.quit()