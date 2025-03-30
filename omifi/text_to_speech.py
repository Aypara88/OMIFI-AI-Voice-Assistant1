"""
Text-to-speech module for the OMIFI assistant.
"""

import logging
import threading
import queue
import time
import pyttsx3

logger = logging.getLogger(__name__)

class TextToSpeech:
    """
    Handles text-to-speech conversion for OMIFI.
    """
    
    def __init__(self):
        """Initialize the text-to-speech engine."""
        try:
            # Initialize the TTS engine
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Try to use a more natural voice if available
            if voices:
                # Use the first female voice if available, otherwise use default
                female_voices = [v for v in voices if 'female' in v.name.lower()]
                if female_voices:
                    self.engine.setProperty('voice', female_voices[0].id)
                else:
                    self.engine.setProperty('voice', voices[0].id)
            
            # Create a queue for non-blocking speech
            self.speech_queue = queue.Queue()
            
            # Start the speech processing thread
            self.speech_thread = threading.Thread(target=self._process_speech_queue)
            self.speech_thread.daemon = True
            self.speech_thread.start()
            
            self.is_speaking = False
            logger.info("Text-to-speech engine initialized")
            
        except Exception as e:
            logger.error(f"Error initializing text-to-speech: {e}")
            self.engine = None
    
    def speak(self, text, block=False):
        """
        Convert text to speech.
        
        Args:
            text (str): The text to convert to speech
            block (bool): Whether to block until speech is complete
        """
        if not text or self.engine is None:
            return
        
        try:
            if block:
                # Blocking mode - speak immediately
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Non-blocking mode - add to queue
                self.speech_queue.put(text)
                
            logger.debug(f"Speaking: {text}")
                
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
    
    def _process_speech_queue(self):
        """Helper method to process speech queue in a background thread."""
        while True:
            try:
                # Get next text from queue
                text = self.speech_queue.get(block=True)
                
                # Mark as speaking
                self.is_speaking = True
                
                # Speak the text
                self._speak_thread(text)
                
                # Mark as not speaking
                self.is_speaking = False
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in speech queue processing: {e}")
                time.sleep(0.1)  # Avoid CPU spinning if there's an error
    
    def _speak_thread(self, text):
        """Helper method to speak in a separate thread."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in speech thread: {e}")