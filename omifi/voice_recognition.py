import threading
import time
import logging
import speech_recognition as sr
import queue

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
        super().__init__()
        self.daemon = True  # Thread will exit when main program exits
        self.command_processor = command_processor
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.is_listening = True
        self.paused = False
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000  # Adjust based on environment
        self.command_queue = queue.Queue()
        self.command_thread = threading.Thread(target=self._process_command_queue)
        self.command_thread.daemon = True
        self.command_thread.start()
    
    def run(self):
        """Main loop that continually listens for the wake word followed by commands."""
        logger.info("Voice recognition thread started")
        
        while self.is_listening:
            if self.paused:
                time.sleep(0.5)
                continue
                
            try:
                with sr.Microphone() as source:
                    logger.debug("Listening for wake word...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                try:
                    # Attempt to recognize the wake word
                    text = self.recognizer.recognize_google(audio).lower()
                    logger.debug(f"Heard: {text}")
                    
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        self._listen_for_command()
                        
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service; {e}")
                    
            except (sr.WaitTimeoutError, Exception) as e:
                if isinstance(e, sr.WaitTimeoutError):
                    # This is normal, just continue listening
                    pass
                else:
                    logger.error(f"Error in voice recognition: {e}")
                    time.sleep(1)  # Prevent CPU overload in case of errors
    
    def _listen_for_command(self):
        """Listen for a command after the wake word is detected."""
        try:
            with sr.Microphone() as source:
                logger.info("Listening for command...")
                # Using a shorter timeout for commands to improve responsiveness
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=10)
                
            try:
                command = self.recognizer.recognize_google(audio).lower()
                logger.info(f"Command detected: {command}")
                
                # Add command to processing queue
                self.command_queue.put(command)
                
            except sr.UnknownValueError:
                logger.info("Command not understood")
            except sr.RequestError as e:
                logger.error(f"Could not request results from Google Speech Recognition service; {e}")
                
        except Exception as e:
            logger.error(f"Error listening for command: {e}")
    
    def _process_command_queue(self):
        """Process commands in the queue to avoid blocking the listening thread."""
        while self.is_listening:
            try:
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    self.command_processor.process_command(command)
                    self.command_queue.task_done()
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                time.sleep(0.1)
    
    def pause(self):
        """Pause voice recognition."""
        logger.info("Voice recognition paused")
        self.paused = True
    
    def resume(self):
        """Resume voice recognition."""
        logger.info("Voice recognition resumed")
        self.paused = False
    
    def stop(self):
        """Stop voice recognition thread."""
        logger.info("Stopping voice recognition")
        self.is_listening = False
