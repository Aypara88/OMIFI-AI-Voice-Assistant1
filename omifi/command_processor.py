import logging
import re

from omifi.screenshot import ScreenshotManager
from omifi.clipboard import ClipboardManager
from omifi.text_to_speech import TextToSpeech

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
        self.tts = TextToSpeech()
        self.screenshot_manager = ScreenshotManager(storage)
        self.clipboard_manager = ClipboardManager(storage)
        
        # Define command patterns and their handlers
        self.commands = [
            {
                'patterns': [
                    r'take a screenshot',
                    r'capture( the)? screen',
                    r'screenshot'
                ],
                'handler': self._handle_screenshot
            },
            {
                'patterns': [
                    r'sense( my)? clipboard',
                    r'get clipboard',
                    r'copy clipboard',
                    r'check clipboard'
                ],
                'handler': self._handle_sense_clipboard
            },
            {
                'patterns': [
                    r'read( this)? clipboard',
                    r'read clipboard( content)?',
                    r'read( the)? clipboard aloud'
                ],
                'handler': self._handle_read_clipboard
            },
            {
                'patterns': [
                    r'open( my)? last screenshot',
                    r'show( my)? last screenshot',
                    r'display( the)? last screenshot'
                ],
                'handler': self._handle_open_last_screenshot
            },
            {
                'patterns': [
                    r'help',
                    r'what can you do',
                    r'commands',
                    r'list( of)? commands'
                ],
                'handler': self._handle_help
            }
        ]
    
    def process_command(self, text):
        """
        Process a voice command.
        
        Args:
            text (str): The command text
        
        Returns:
            bool: True if a command was processed, False otherwise
        """
        text = text.lower().strip()
        logger.info(f"Processing command: {text}")
        
        # Check each command pattern
        for command in self.commands:
            for pattern in command['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    # Found a matching command
                    logger.debug(f"Command matched pattern: {pattern}")
                    return command['handler'](text)
        
        # No matching command found
        logger.info("No matching command found")
        self.tts.speak("I'm sorry, I didn't understand that command.")
        return False
    
    def _handle_screenshot(self, text):
        """Handle screenshot command."""
        self.tts.speak("Taking a screenshot")
        filepath = self.screenshot_manager.take_screenshot()
        
        if filepath:
            self.tts.speak("Screenshot taken and saved")
            return True
        else:
            self.tts.speak("Sorry, I couldn't take a screenshot")
            return False
    
    def _handle_sense_clipboard(self, text):
        """Handle clipboard sensing command."""
        self.tts.speak("Sensing clipboard content")
        content_type, content = self.clipboard_manager.sense_clipboard()
        
        if content:
            self.tts.speak("Clipboard content saved")
            return True
        else:
            self.tts.speak("The clipboard is empty or I couldn't access it")
            return False
    
    def _handle_read_clipboard(self, text):
        """Handle reading clipboard command."""
        # Try to get the current clipboard content first
        content = self.clipboard_manager.get_current_clipboard()
        
        # If no current content, try to get the last saved content
        if not content:
            _, content = self.clipboard_manager.get_last_clipboard_content()
        
        if content:
            # For very long content, summarize or truncate
            if len(content) > 500:
                truncated = content[:500] + "... (content truncated)"
                self.tts.speak("Reading clipboard content: " + truncated)
            else:
                self.tts.speak("Reading clipboard content: " + content)
            return True
        else:
            self.tts.speak("There's no clipboard content to read")
            return False
    
    def _handle_open_last_screenshot(self, text):
        """Handle opening the last screenshot."""
        success = self.screenshot_manager.open_last_screenshot()
        
        if success:
            self.tts.speak("Opening your last screenshot")
            return True
        else:
            self.tts.speak("Sorry, I couldn't find any screenshots")
            return False
    
    def _handle_help(self, text):
        """Handle help command."""
        help_text = (
            "I can help you with several tasks. Try saying: "
            "Take a screenshot, "
            "Sense my clipboard, "
            "Read clipboard aloud, or "
            "Open my last screenshot."
        )
        self.tts.speak(help_text)
        return True
