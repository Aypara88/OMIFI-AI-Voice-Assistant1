"""
Command processor module for the OMIFI assistant.
"""

import os
import logging
import subprocess
from .text_to_speech import TextToSpeech
from .screenshot import ScreenshotManager
from .clipboard import ClipboardManager

logger = logging.getLogger(__name__)

class CommandProcessor:
    """
    Processes voice commands and dispatches them to the appropriate handlers.
    """
    
    def __init__(self, storage):
        """
        Initialize the command processor.
        
        Args:
            storage: Storage instance for accessing stored data
        """
        self.storage = storage
        
        # Initialize text-to-speech
        self.text_to_speech = TextToSpeech()
        
        # Initialize screenshot manager
        self.screenshot_manager = ScreenshotManager(storage)
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(storage)
        
        # Command handlers
        self.command_handlers = {
            "screenshot": self._handle_screenshot,
            "take a screenshot": self._handle_screenshot,
            "capture screen": self._handle_screenshot,
            
            "clipboard": self._handle_sense_clipboard,
            "sense clipboard": self._handle_sense_clipboard,
            "check clipboard": self._handle_sense_clipboard,
            
            "read clipboard": self._handle_read_clipboard,
            "read the clipboard": self._handle_read_clipboard,
            "what's in the clipboard": self._handle_read_clipboard,
            
            "open screenshot": self._handle_open_last_screenshot,
            "open last screenshot": self._handle_open_last_screenshot,
            "show last screenshot": self._handle_open_last_screenshot,
            
            "help": self._handle_help,
            "what can you do": self._handle_help,
            "commands": self._handle_help
        }
        
        logger.info("Command processor initialized")
    
    def process_command(self, text):
        """
        Process a voice command.
        
        Args:
            text (str): The command text
        
        Returns:
            bool: True if a command was processed, False otherwise
        """
        if not text:
            return False
            
        text = text.lower().strip()
        logger.debug(f"Processing command: {text}")
        
        # Check for exact matches
        if text in self.command_handlers:
            return self.command_handlers[text](text)
        
        # Check for partial matches
        for command, handler in self.command_handlers.items():
            if command in text:
                return handler(text)
        
        logger.debug(f"No handler found for command: {text}")
        return False
    
    def _handle_screenshot(self, text):
        """Handle screenshot command."""
        self.text_to_speech.speak("Taking a screenshot", block=False)
        
        filepath = self.screenshot_manager.take_screenshot()
        
        if filepath:
            self.text_to_speech.speak("Screenshot saved", block=False)
            return True
        else:
            self.text_to_speech.speak("Failed to take screenshot", block=False)
            return False
    
    def _handle_sense_clipboard(self, text):
        """Handle clipboard sensing command."""
        self.text_to_speech.speak("Checking clipboard", block=False)
        
        content_type, content = self.clipboard_manager.sense_clipboard()
        
        if content:
            self.text_to_speech.speak("Clipboard content saved", block=False)
            return True
        else:
            self.text_to_speech.speak("No clipboard content found", block=False)
            return False
    
    def _handle_read_clipboard(self, text):
        """Handle reading clipboard command."""
        filepath, content = self.storage.get_last_clipboard_content()
        
        if content:
            if len(content) > 200:
                # If content is too long, just read the first part
                content = content[:200] + "... and more"
                
            self.text_to_speech.speak(f"Clipboard contains: {content}", block=False)
            return True
        else:
            self.text_to_speech.speak("No clipboard content available", block=False)
            return False
    
    def _handle_open_last_screenshot(self, text):
        """Handle opening the last screenshot."""
        self.text_to_speech.speak("Opening the last screenshot", block=False)
        
        if self.screenshot_manager.open_last_screenshot():
            return True
        else:
            self.text_to_speech.speak("No screenshot available", block=False)
            return False
    
    def _handle_help(self, text):
        """Handle help command."""
        help_text = """
        I can help you with the following commands:
        - Take a screenshot: Captures your screen
        - Sense clipboard: Saves the current clipboard content
        - Read clipboard: Reads aloud the saved clipboard content
        - Open last screenshot: Opens the most recent screenshot
        """
        
        self.text_to_speech.speak(help_text, block=False)
        return True