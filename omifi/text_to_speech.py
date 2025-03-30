import logging
import pyttsx3
import threading

logger = logging.getLogger(__name__)

class TextToSpeech:
    """
    Handles text-to-speech conversion for OMIFI.
    """
    
    def __init__(self):
        """Initialize the text-to-speech engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Get available voices and set a suitable one
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find a female voice as it sounds better for assistants
                female_voices = [v for v in voices if 'female' in v.name.lower()]
                if female_voices:
                    self.engine.setProperty('voice', female_voices[0].id)
                else:
                    # Otherwise just use the first available voice
                    self.engine.setProperty('voice', voices[0].id)
                    
            logger.info("Text-to-speech engine initialized")
            
        except Exception as e:
            logger.error(f"Error initializing text-to-speech engine: {e}")
            self.engine = None
    
    def speak(self, text, block=False):
        """
        Convert text to speech.
        
        Args:
            text (str): The text to convert to speech
            block (bool): Whether to block until speech is complete
        """
        if not self.engine:
            logger.error("Text-to-speech engine not available")
            return
            
        try:
            logger.info(f"Speaking: {text}")
            
            if block:
                # Speak in the current thread (blocking)
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Speak in a separate thread (non-blocking)
                thread = threading.Thread(target=self._speak_thread, args=(text,))
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def _speak_thread(self, text):
        """Helper method to speak in a separate thread."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in speech thread: {e}")
