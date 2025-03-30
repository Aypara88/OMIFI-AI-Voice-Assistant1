"""
Voice recognition module for the OMIFI assistant.
"""

import os
import sys
import time
import queue
import logging
import threading
from datetime import datetime
import speech_recognition as sr

class VoiceRecognizer(threading.Thread):
    """
    Handles voice recognition and wake word detection.
    Runs in a background thread continuously listening for voice commands.
    """
    
    def __init__(self, command_processor, wake_word="hey omifi"):
        """
        Initialize the voice recognizer.
        
        Args:
            command_processor: CommandProcessor instance to handle detected commands
            wake_word: The wake word/phrase to listen for (default: "hey omifi")
        """
        super().__init__(daemon=True)
        self.logger = logging.getLogger(__name__)
        self.command_processor = command_processor
        self.wake_word = wake_word.lower()
        self.paused = False
        self.stopped = False
        self.command_queue = queue.Queue()
        
        # Initialize the recognizer
        try:
            self.recognizer = sr.Recognizer()
            
            # Adjust for ambient noise to improve recognition (optional)
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 4000  # Adjust based on testing
            self.recognizer.pause_threshold = 0.8    # Time of silence to consider end of phrase
            
            # Create a command processing thread
            self.command_thread = threading.Thread(target=self._process_command_queue, daemon=True)
            self.command_thread.start()
            
            self.logger.info("Voice recognizer initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Error initializing voice recognizer: {e}")
            self.recognizer = None
    
    def run(self):
        """Main loop that continually listens for the wake word followed by commands."""
        if not self.recognizer:
            self.logger.error("Voice recognizer not available. Cannot start listening.")
            return
        
        self.logger.info("Voice recognition thread started")
        
        while not self.stopped:
            if self.paused:
                time.sleep(0.5)  # Sleep briefly when paused
                continue
            
            # Use the microphone as audio source
            try:
                with sr.Microphone() as source:
                    self.logger.debug("Listening for wake word...")
                    
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for speech
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    
                    try:
                        # Convert speech to text using Google Speech Recognition
                        text = self.recognizer.recognize_google(audio).lower()
                        self.logger.debug(f"Detected: {text}")
                        
                        # Check if wake word is detected
                        if self.wake_word in text:
                            self.logger.info(f"Wake word detected: {text}")
                            
                            # Extract any command included after the wake word
                            command_text = text.split(self.wake_word, 1)[-1].strip()
                            if command_text:
                                # If command was included with wake word
                                self.logger.info(f"Command included with wake word: {command_text}")
                                self.command_queue.put(command_text)
                            else:
                                # Otherwise listen specifically for a command
                                self._listen_for_command()
                    
                    except sr.UnknownValueError:
                        # Speech was unintelligible
                        pass
                    except sr.RequestError as e:
                        self.logger.error(f"Speech recognition service error: {e}")
                    except Exception as e:
                        self.logger.error(f"Error processing speech: {e}")
            
            except Exception as e:
                self.logger.error(f"Error accessing microphone: {e}")
                time.sleep(1)  # Wait before retrying
    
    def _listen_for_command(self):
        """Listen for a command after the wake word is detected."""
        try:
            with sr.Microphone() as source:
                self.logger.info("Listening for command...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for speech with shorter timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    # Convert speech to text using Google Speech Recognition
                    text = self.recognizer.recognize_google(audio).lower()
                    self.logger.info(f"Command detected: {text}")
                    
                    # Add command to processing queue
                    self.command_queue.put(text)
                
                except sr.UnknownValueError:
                    self.logger.info("Command not understood")
                except sr.RequestError as e:
                    self.logger.error(f"Speech recognition service error: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing command: {e}")
        
        except Exception as e:
            self.logger.error(f"Error accessing microphone for command: {e}")
    
    def _process_command_queue(self):
        """Process commands in the queue to avoid blocking the listening thread."""
        while not self.stopped:
            try:
                # Get command from queue (blocks until an item is available)
                command = self.command_queue.get(timeout=1)
                
                # Process the command
                if command:
                    self.command_processor.process_command(command)
                
                # Mark queue item as processed
                self.command_queue.task_done()
            
            except queue.Empty:
                # Queue timeout, continue polling
                pass
            except Exception as e:
                self.logger.error(f"Error processing command queue: {e}")
    
    def pause(self):
        """Pause voice recognition."""
        self.paused = True
        self.logger.info("Voice recognition paused")
    
    def resume(self):
        """Resume voice recognition."""
        self.paused = False
        self.logger.info("Voice recognition resumed")
    
    def stop(self):
        """Stop voice recognition thread."""
        self.logger.info("Stopping voice recognition...")
        self.stopped = True
        self.paused = True  # Also pause to prevent any new recognitions during shutdown