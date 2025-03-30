"""
Text-to-speech module for the OMIFI assistant.
"""

import os
import sys
import logging
import queue
import threading
from datetime import datetime
import pyttsx3

class TextToSpeech:
    """
    Handles text-to-speech conversion for OMIFI.
    """
    
    def __init__(self):
        """Initialize the text-to-speech engine."""
        self.logger = logging.getLogger(__name__)
        self.speech_queue = queue.Queue()
        self.speaking = False
        self.speech_thread = None
        
        try:
            # Initialize pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', 175)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Get available voices and set a preferably female voice
            voices = self.engine.getProperty('voices')
            female_voice = None
            
            # Try to find a female voice
            for voice in voices:
                if 'female' in voice.name.lower():
                    female_voice = voice.id
                    break
            
            # Set the voice (female if found, otherwise default)
            if female_voice:
                self.engine.setProperty('voice', female_voice)
                self.logger.info(f"Set TTS voice to {female_voice}")
            else:
                self.logger.info("Using default TTS voice")
            
            # Initialize background thread for non-blocking speech
            self.speech_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
            self.speech_thread.start()
            
            self.logger.info("Text-to-speech engine initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Error initializing text-to-speech engine: {e}")
            self.engine = None
    
    def speak(self, text, block=False):
        """
        Convert text to speech.
        
        Args:
            text (str): The text to convert to speech
            block (bool): Whether to block until speech is complete
        """
        if not text:
            return
        
        if not self.engine:
            self.logger.error("Text-to-speech engine not available")
            return
        
        try:
            self.logger.info(f"Speaking: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            if block:
                # Speak immediately and block until complete
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Add to queue for background processing
                self.speech_queue.put(text)
        
        except Exception as e:
            self.logger.error(f"Error during text-to-speech: {e}")
    
    def _process_speech_queue(self):
        """Helper method to process speech queue in a background thread."""
        while True:
            try:
                # Get the next text to speak (blocks until an item is available)
                text = self.speech_queue.get()
                
                # Mark as speaking
                self.speaking = True
                
                # Process the speech in a separate thread to avoid blocking
                speech_thread = threading.Thread(target=self._speak_thread, args=(text,))
                speech_thread.daemon = True
                speech_thread.start()
                speech_thread.join()  # Wait for speech to complete
                
                # Mark queue item as processed
                self.speech_queue.task_done()
                
                # Mark as not speaking
                self.speaking = False
            
            except Exception as e:
                self.logger.error(f"Error processing speech queue: {e}")
                self.speaking = False
    
    def _speak_thread(self, text):
        """Helper method to speak in a separate thread."""
        try:
            if self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Error in speech thread: {e}")