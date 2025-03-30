# OMIFI Voice Assistant

A desktop AI voice assistant that operates in the background and activates when you say "Hey OMIFI". It provides voice-activated utilities for taking screenshots, managing clipboard content, and more.

## Features

- **Voice Recognition**: Activates with "Hey OMIFI" wake word
- **Screenshot Capture**: Take and manage screenshots via voice commands
- **Clipboard Management**: Save and read clipboard content
- **Text-to-Speech**: Audible responses and clipboard content reading
- **System Tray Integration**: Quick access to features via system tray
- **Web Dashboard**: Browser-based control and history viewing

## Voice Commands

After saying "Hey OMIFI", you can use these commands:

- **"Take a screenshot"** - Captures your screen
- **"Sense clipboard"** - Saves current clipboard content
- **"Read clipboard"** - Reads the most recent clipboard content aloud
- **"Show last screenshot"** - Opens the most recent screenshot
- **"What can you do?"** - Lists available commands

## Getting Started

### Prerequisites

- Python 3.6+
- PyQt5
- SpeechRecognition
- PyAudio
- pyttsx3
- Flask (for web dashboard)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/omifi.git
   cd omifi
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start OMIFI:
   ```
   python main.py
   ```

### Web Dashboard

OMIFI includes a web dashboard for viewing screenshots and clipboard history:

1. Start the web server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

- `main.py` - Desktop application entry point
- `app.py` - Web dashboard server
- `omifi/` - Core modules
  - `clipboard.py` - Clipboard management
  - `command_processor.py` - Voice command handling
  - `screenshot.py` - Screenshot utilities
  - `storage.py` - Data persistence
  - `text_to_speech.py` - Voice output
  - `voice_recognition.py` - Voice input
  - `ui/` - User interface components
    - `dashboard.py` - Desktop dashboard window
    - `system_tray.py` - System tray integration

## Future Enhancements

- Cross-device synchronization
- AI-powered text summarization
- End-to-end encryption
- Third-party service integration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Icons: [Feather Icons](https://feathericons.com/)
- Speech Recognition: [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- Text-to-Speech: [pyttsx3](https://pypi.org/project/pyttsx3/)