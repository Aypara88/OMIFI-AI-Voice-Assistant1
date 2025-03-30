import logging
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

from omifi.ui.dashboard import OmifiDashboard
from omifi.screenshot import ScreenshotManager
from omifi.clipboard import ClipboardManager
from omifi.text_to_speech import TextToSpeech
from omifi.ui.resources import get_icon_path

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
        super().__init__()
        
        self.app = app
        self.voice_recognizer = voice_recognizer
        self.storage = storage
        
        # Initialize managers
        self.screenshot_manager = ScreenshotManager(storage)
        self.clipboard_manager = ClipboardManager(storage)
        self.tts = TextToSpeech()
        
        # Track if dashboard is open
        self.dashboard = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the system tray UI."""
        # Set the tray icon
        self.setIcon(QIcon(get_icon_path("omifi_icon.svg")))
        self.setToolTip("OMIFI Voice Assistant")
        
        # Create the tray menu
        tray_menu = QMenu()
        
        # Add actions to the menu
        dashboard_action = QAction("Open Dashboard", self)
        dashboard_action.triggered.connect(self.open_dashboard)
        tray_menu.addAction(dashboard_action)
        
        tray_menu.addSeparator()
        
        # Voice recognition toggle
        self.toggle_voice_action = QAction("Pause Voice Recognition", self)
        self.toggle_voice_action.triggered.connect(self.toggle_voice_recognition)
        tray_menu.addAction(self.toggle_voice_action)
        
        tray_menu.addSeparator()
        
        # Quick actions
        screenshot_action = QAction("Take Screenshot", self)
        screenshot_action.triggered.connect(self.take_screenshot)
        tray_menu.addAction(screenshot_action)
        
        clipboard_action = QAction("Sense Clipboard", self)
        clipboard_action.triggered.connect(self.sense_clipboard)
        tray_menu.addAction(clipboard_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit OMIFI", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # Set the menu
        self.setContextMenu(tray_menu)
        
        # Connect signal for click on the tray icon
        self.activated.connect(self.on_tray_icon_activated)
        
        # Show the tray icon
        self.show()
        
        # Startup notification
        self.showMessage(
            "OMIFI Voice Assistant",
            "OMIFI is running in the background.\nSay 'Hey OMIFI' to start using voice commands.",
            QSystemTrayIcon.Information,
            5000
        )
    
    @pyqtSlot(QSystemTrayIcon.ActivationReason)
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
        if self.dashboard is None:
            self.dashboard = OmifiDashboard(
                self.storage, 
                self.clipboard_manager, 
                self.screenshot_manager,
                self.tts
            )
            self.dashboard.setWindowIcon(QIcon(get_icon_path("omifi_icon.svg")))
            self.dashboard.show()
            
            # Connect the close event
            self.dashboard.closeEvent = self.on_dashboard_closed
        else:
            self.dashboard.activateWindow()
            self.dashboard.raise_()
    
    def on_dashboard_closed(self, event):
        """Handle dashboard close event."""
        self.dashboard = None
        event.accept()
    
    def toggle_voice_recognition(self):
        """Toggle voice recognition on/off."""
        if self.voice_recognizer.paused:
            self.voice_recognizer.resume()
            self.toggle_voice_action.setText("Pause Voice Recognition")
            self.showMessage(
                "OMIFI Voice Assistant", 
                "Voice recognition resumed", 
                QSystemTrayIcon.Information, 
                2000
            )
        else:
            self.voice_recognizer.pause()
            self.toggle_voice_action.setText("Resume Voice Recognition")
            self.showMessage(
                "OMIFI Voice Assistant", 
                "Voice recognition paused", 
                QSystemTrayIcon.Information, 
                2000
            )
    
    def take_screenshot(self):
        """Take a screenshot from the tray menu."""
        filepath = self.screenshot_manager.take_screenshot()
        
        if filepath:
            self.showMessage(
                "OMIFI Voice Assistant", 
                "Screenshot taken and saved", 
                QSystemTrayIcon.Information, 
                2000
            )
            
            # Update dashboard if open
            if self.dashboard:
                self.dashboard.refresh_screenshots()
        else:
            self.showMessage(
                "OMIFI Voice Assistant", 
                "Failed to take screenshot", 
                QSystemTrayIcon.Warning, 
                2000
            )
    
    def sense_clipboard(self):
        """Sense clipboard from the tray menu."""
        content_type, content = self.clipboard_manager.sense_clipboard()
        
        if content:
            self.showMessage(
                "OMIFI Voice Assistant", 
                "Clipboard content saved", 
                QSystemTrayIcon.Information, 
                2000
            )
            
            # Update dashboard if open
            if self.dashboard:
                self.dashboard.refresh_clipboard()
        else:
            self.showMessage(
                "OMIFI Voice Assistant", 
                "No clipboard content detected", 
                QSystemTrayIcon.Information, 
                2000
            )
    
    def quit_application(self):
        """Quit the application."""
        # Stop the voice recognition thread
        self.voice_recognizer.stop()
        
        # Quit the application
        self.app.quit()
