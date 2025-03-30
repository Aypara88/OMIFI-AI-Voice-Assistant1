"""
System tray interface for the OMIFI assistant.
"""

import os
import logging
import threading
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .resources import get_icon_path
from .dashboard import OmifiDashboard

logger = logging.getLogger(__name__)

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
        # Get tray icon
        icon_path = get_icon_path("omifi_icon.svg")
        icon = QIcon(icon_path)
        
        super().__init__(icon, app)
        
        self.app = app
        self.voice_recognizer = voice_recognizer
        self.storage = storage
        
        # Create command processor and managers
        self.command_processor = voice_recognizer.command_processor
        self.clipboard_manager = self.command_processor.clipboard_manager
        self.screenshot_manager = self.command_processor.screenshot_manager
        self.text_to_speech = self.command_processor.text_to_speech
        
        # Dashboard window
        self.dashboard = None
        
        # Initialize UI
        self.init_ui()
        
        # Show the tray icon
        self.show()
        
        logger.info("System tray initialized")
    
    def init_ui(self):
        """Initialize the system tray UI."""
        # Create menu
        menu = QMenu()
        
        # Status action (non-clickable)
        status_action = QAction("OMIFI Voice Assistant", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        menu.addSeparator()
        
        # Dashboard action
        dashboard_action = QAction("Open Dashboard", self)
        dashboard_action.triggered.connect(self.open_dashboard)
        menu.addAction(dashboard_action)
        
        menu.addSeparator()
        
        # Toggle voice recognition
        self.voice_toggle_action = QAction("Pause Voice Recognition", self)
        self.voice_toggle_action.triggered.connect(self.toggle_voice_recognition)
        menu.addAction(self.voice_toggle_action)
        
        menu.addSeparator()
        
        # Screenshot action
        screenshot_action = QAction("Take Screenshot", self)
        screenshot_action.triggered.connect(self.take_screenshot)
        menu.addAction(screenshot_action)
        
        # Clipboard action
        clipboard_action = QAction("Sense Clipboard", self)
        clipboard_action.triggered.connect(self.sense_clipboard)
        menu.addAction(clipboard_action)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)
        
        # Set the menu
        self.setContextMenu(menu)
        
        # Connect the activated signal
        self.activated.connect(self.on_tray_icon_activated)
    
    def on_tray_icon_activated(self, reason):
        """
        Handle tray icon activation.
        
        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.DoubleClick:
            # Open dashboard on double-click
            self.open_dashboard()
    
    def open_dashboard(self):
        """Open the dashboard window."""
        if self.dashboard is None:
            # Create dashboard if it doesn't exist
            self.dashboard = OmifiDashboard(
                self.storage,
                self.clipboard_manager,
                self.screenshot_manager,
                self.text_to_speech
            )
            
            # Connect close event to handler
            self.dashboard.closeEvent = self.on_dashboard_closed
        
        # Show dashboard
        self.dashboard.show()
        self.dashboard.activateWindow()
    
    def on_dashboard_closed(self, event):
        """Handle dashboard close event."""
        # Set dashboard to None when closed
        self.dashboard = None
        event.accept()
    
    def toggle_voice_recognition(self):
        """Toggle voice recognition on/off."""
        if self.voice_recognizer.paused:
            # Resume voice recognition
            self.voice_recognizer.resume()
            self.voice_toggle_action.setText("Pause Voice Recognition")
            self.text_to_speech.speak("Voice recognition resumed", block=False)
        else:
            # Pause voice recognition
            self.voice_recognizer.pause()
            self.voice_toggle_action.setText("Resume Voice Recognition")
            self.text_to_speech.speak("Voice recognition paused", block=False)
    
    def take_screenshot(self):
        """Take a screenshot from the tray menu."""
        # Take screenshot in a thread to avoid blocking the UI
        def take_screenshot_thread():
            filepath = self.screenshot_manager.take_screenshot()
            
            if filepath:
                self.text_to_speech.speak("Screenshot saved", block=False)
            else:
                self.text_to_speech.speak("Failed to take screenshot", block=False)
        
        threading.Thread(target=take_screenshot_thread).start()
    
    def sense_clipboard(self):
        """Sense clipboard from the tray menu."""
        # Sense clipboard in a thread to avoid blocking the UI
        def sense_clipboard_thread():
            content_type, content = self.clipboard_manager.sense_clipboard()
            
            if content:
                self.text_to_speech.speak("Clipboard content saved", block=False)
            else:
                self.text_to_speech.speak("No clipboard content found or unchanged", block=False)
        
        threading.Thread(target=sense_clipboard_thread).start()
    
    def quit_application(self):
        """Quit the application."""
        # Stop voice recognition
        self.voice_recognizer.stop()
        
        # Hide the tray icon
        self.hide()
        
        # Exit application after a short delay
        QApplication.quit()