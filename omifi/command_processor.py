"""
Command processor module for the OMIFI assistant.
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

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
        self.logger = logging.getLogger(__name__)
        self.storage = storage
        
        # References to other components (to be set by the caller)
        self.clipboard_manager = None
        self.screenshot_manager = None
        self.text_to_speech = None
        
        # Define command handlers and their keywords
        self.command_handlers = {
            "screenshot": self._handle_screenshot,
            "take a screenshot": self._handle_screenshot,
            "capture screen": self._handle_screenshot,
            "take screenshot": self._handle_screenshot,
            
            "sense clipboard": self._handle_sense_clipboard,
            "check clipboard": self._handle_sense_clipboard,
            "what's in clipboard": self._handle_sense_clipboard,
            "what is in clipboard": self._handle_sense_clipboard,
            "clipboard": self._handle_sense_clipboard,
            "clipboard content": self._handle_sense_clipboard,
            "get clipboard": self._handle_sense_clipboard,
            "copy clipboard": self._handle_sense_clipboard,
            "save clipboard": self._handle_sense_clipboard,
            "check my clipboard": self._handle_sense_clipboard,
            
            "read clipboard": self._handle_read_clipboard,
            "read back clipboard": self._handle_read_clipboard,
            "read the clipboard": self._handle_read_clipboard,
            "read my clipboard": self._handle_read_clipboard,
            "read out clipboard": self._handle_read_clipboard,
            
            "show last screenshot": self._handle_open_last_screenshot,
            "open last screenshot": self._handle_open_last_screenshot,
            "display screenshot": self._handle_open_last_screenshot,
            "view screenshot": self._handle_open_last_screenshot,
            
            "help": self._handle_help,
            "what can you do": self._handle_help
        }
    
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
        
        # Convert to lowercase for case-insensitive matching
        text = text.lower().strip()
        
        self.logger.info(f"Processing command: {text}")
        
        # Check exact matches first
        if text in self.command_handlers:
            return self.command_handlers[text](text)
        
        # Check for partial matches
        for cmd, handler in self.command_handlers.items():
            if cmd in text:
                return handler(text)
                
        # If no command was recognized
        self.logger.info("Command not recognized")
        if self.text_to_speech:
            self.text_to_speech.speak("I'm sorry, I didn't understand that command.")
        return False
    
    def _handle_screenshot(self, text):
        """Handle screenshot command."""
        self.logger.info("Taking screenshot")
        
        if self.text_to_speech:
            self.text_to_speech.speak("Taking a screenshot")
        
        if self.screenshot_manager:
            filepath = self.screenshot_manager.take_screenshot()
            if filepath:
                if self.text_to_speech:
                    self.text_to_speech.speak("Screenshot captured and saved")
                return True
            else:
                if self.text_to_speech:
                    self.text_to_speech.speak("Sorry, I couldn't take a screenshot")
        else:
            if self.text_to_speech:
                self.text_to_speech.speak("Screenshot functionality is not available")
            
        return False
    
    def _handle_sense_clipboard(self, text):
        """Handle clipboard sensing command."""
        self.logger.info("Sensing clipboard")
        
        if self.text_to_speech:
            self.text_to_speech.speak("Checking clipboard content")
        
        if not self.clipboard_manager:
            if self.text_to_speech:
                self.text_to_speech.speak("Clipboard functionality is not available")
            return False
            
        try:
            # Handle clipboard results safely
            content_type, content = "", ""
            
            try:
                
                # Get clipboard content
                result = self.clipboard_manager.sense_clipboard()
                
                # Check if result is a valid tuple with content
                if result and isinstance(result, tuple) and len(result) >= 2:
                    content_type, content = result[0], result[1]
            except TypeError:
                self.logger.warning("Clipboard manager returned unexpected result")
                
            # Check if we got content
            if content and isinstance(content, str) and content.strip():
                preview = content[:100] + "..." if len(content) > 100 else content
                if self.text_to_speech:
                    self.text_to_speech.speak(f"Clipboard contains: {preview}")
                return True
            else:
                if self.text_to_speech:
                    self.text_to_speech.speak("Clipboard is empty or contains non-text content")
                    
        except Exception as e:
            self.logger.error(f"Error in clipboard sensing: {e}")
            if self.text_to_speech:
                self.text_to_speech.speak("Error accessing clipboard")
                
        return False
    
    def _handle_read_clipboard(self, text):
        """Handle reading clipboard command."""
        self.logger.info("Reading clipboard")
        
        if not self.clipboard_manager or not self.text_to_speech:
            if self.text_to_speech:
                self.text_to_speech.speak("Sorry, clipboard reading is not available")
            return False
        
        # Get the latest clipboard content
        filepath, content = self.storage.get_last_clipboard_content()
        
        if content and content.strip():
            self.text_to_speech.speak("Here's what's in the clipboard:")
            self.text_to_speech.speak(content)
            return True
        else:
            self.text_to_speech.speak("There's no text content in the clipboard history")
            return False
    
    def _handle_open_last_screenshot(self, text):
        """Handle opening the last screenshot."""
        self.logger.info("Opening last screenshot")
        
        if self.text_to_speech:
            self.text_to_speech.speak("Opening the last screenshot")
        
        if self.screenshot_manager:
            success = self.screenshot_manager.open_last_screenshot()
            
            if success:
                if self.text_to_speech:
                    self.text_to_speech.speak("Screenshot opened")
                return True
            else:
                if self.text_to_speech:
                    self.text_to_speech.speak("Sorry, I couldn't find any screenshots")
        else:
            if self.text_to_speech:
                self.text_to_speech.speak("Screenshot functionality is not available")
            
        return False
    
    def _handle_help(self, text):
        """Handle help command."""
        if not self.text_to_speech:
            return False
        
        self.logger.info("Providing help information")
        
        help_text = (
            "Here are some things you can ask me to do: "
            "Take a screenshot. "
            "Check what's in the clipboard. "
            "Read the clipboard content aloud. "
            "Show the last screenshot."
        )
        
        self.text_to_speech.speak(help_text)
        return True