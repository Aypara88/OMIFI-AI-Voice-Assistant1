"""
Voice recognition module for the OMIFI assistant.
"""

import os
import time
import queue
import logging
import threading
import speech_recognition as sr

logger = logging.getLogger(__name__)

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
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.command_processor = command_processor
        self.wake_word = wake_word.lower()
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Adjust for ambient noise level
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000
        
        # Queue for handling commands
        self.command_queue = queue.Queue()
        
        # Start a separate thread for processing commands
        self.command_thread = threading.Thread(target=self._process_command_queue)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        # Control flags
        self.running = True
        self.paused = False
        
        logger.info("Voice recognizer initialized")
    
    def run(self):
        """Main loop that continually listens for the wake word followed by commands."""
        logger.info("Voice recognition started")
        
        # Give the text-to-speech engine a moment to speak the welcome message
        time.sleep(2)
        
        while self.running:
            if self.paused:
                time.sleep(0.5)
                continue
                
            try:
                # Use the microphone as source
                with sr.Microphone() as source:
                    logger.debug("Listening for wake word...")
                    
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    try:
                        # Convert speech to text
                        text = self.recognizer.recognize_google(audio).lower()
                        logger.debug(f"Heard: {text}")
                        
                        # Check for wake word
                        if self.wake_word in text:
                            logger.info("Wake word detected")
                            
                            # Play acknowledgment
                            self.command_processor.text_to_speech.speak("Yes?", block=False)
                            
                            # Listen for command
                            self._listen_for_command()
                    
                    except sr.UnknownValueError:
                        # Speech was unintelligible
                        pass
                        
                    except sr.RequestError as e:
                        logger.error(f"Could not request results from Google Speech Recognition service: {e}")
                        time.sleep(1)  # Wait before trying again
            
            except Exception as e:
                logger.error(f"Error in voice recognition: {e}")
                time.sleep(1)  # Wait before trying again
    
    def _listen_for_command(self):
        """Listen for a command after the wake word is detected."""
        try:
            with sr.Microphone() as source:
                # Reduce the listening time for commands
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    # Convert speech to text
                    command = self.recognizer.recognize_google(audio).lower()
                    logger.info(f"Command detected: {command}")
                    
                    # Add command to queue
                    self.command_queue.put(command)
                    
                except sr.UnknownValueError:
                    # Command was unintelligible
                    self.command_processor.text_to_speech.speak("Sorry, I didn't catch that", block=False)
                    
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service: {e}")
                    self.command_processor.text_to_speech.speak("Sorry, I'm having trouble understanding you", block=False)
        
        except Exception as e:
            logger.error(f"Error listening for command: {e}")
    
    def _process_command_queue(self):
        """Process commands in the queue to avoid blocking the listening thread."""
        while True:
            try:
                # Get command from queue
                command = self.command_queue.get(block=True)
                
                # Process the command
                if not self.command_processor.process_command(command):
                    # If no command was recognized, say so
                    self.command_processor.text_to_speech.speak("I'm not sure what you want me to do", block=False)
                
                # Mark task as done
                self.command_queue.task_done()
                
                # Small delay between commands
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                time.sleep(0.1)  # Avoid CPU spinning if there's an error
    
    def pause(self):
        """Pause voice recognition."""
        if not self.paused:
            self.paused = True
            logger.info("Voice recognition paused")
    
    def resume(self):
        """Resume voice recognition."""
        if self.paused:
            self.paused = False
            logger.info("Voice recognition resumed")
    
    def stop(self):
        """Stop voice recognition thread."""
        self.running = False
        logger.info("Voice recognition stopped")