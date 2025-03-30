# OMIFI Voice Assistant

A desktop AI voice assistant that responds to "Hey OMIFI" for taking screenshots and managing clipboard content.

## Features
- Voice recognition with "Hey OMIFI" wake word
- Screenshot capture and management
- Clipboard content sensing and monitoring
- Text-to-speech responses
- Web dashboard for management

## Installation Instructions

### Prerequisites
- Python 3.8 or higher
- PyQt5
- SpeechRecognition
- PyAudio (for microphone access)
- PyTTSx3 (for text-to-speech)

### Installation Steps

1. Clone or download this repository to your local machine

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the assistant:
```bash
python main.py
```

## Using OMIFI

After starting OMIFI, you'll see a system tray icon. The assistant will listen for the wake word "Hey OMIFI" followed by a command:

- "Hey OMIFI, take a screenshot"
- "Hey OMIFI, sense clipboard"
- "Hey OMIFI, read clipboard"
- "Hey OMIFI, show last screenshot"

## Web Dashboard

OMIFI also provides a web dashboard accessible at http://localhost:5000 when the assistant is running.

## Troubleshooting

### Microphone Issues
If you experience issues with microphone access:
- Make sure your microphone is connected and working
- Check that you've granted microphone permissions to the application
- Try running the application as administrator

### PyAudio Installation Issues
On some systems, PyAudio installation can be challenging:
- Windows: Try `pip install pipwin` followed by `pipwin install pyaudio`
- macOS: Use `brew install portaudio` before installing PyAudio
- Linux: Install portaudio development package with your package manager

## License
MIT