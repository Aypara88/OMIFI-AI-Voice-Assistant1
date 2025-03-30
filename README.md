# OMIFI Voice Assistant

A desktop AI voice assistant that operates in the background and activates when called with the wake word "Hey OMIFI".

## Features

- Voice recognition with wake word detection
- Screenshot capture
- Clipboard sensing and management
- Text-to-speech capabilities
- Desktop application with system tray interface
- Web dashboard for viewing captured content

## Usage

### Desktop Application

To run the desktop application:

```bash
python main.py
```

This will start the OMIFI voice assistant in the background with a system tray icon.

### Web Dashboard

To run the web dashboard:

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

This will start the web server on port 5000. You can access the dashboard at `http://localhost:5000`.

## Voice Commands

OMIFI responds to the following voice commands:

- "Hey OMIFI, take a screenshot" - Captures your screen
- "Hey OMIFI, sense clipboard" - Saves the current clipboard content
- "Hey OMIFI, read clipboard" - Reads aloud the saved clipboard content
- "Hey OMIFI, open last screenshot" - Opens the most recent screenshot
- "Hey OMIFI, help" - Lists available commands

## Requirements

- Python 3.6+
- PyQt5
- Flask
- SpeechRecognition
- pyttsx3
- pyperclip
- Pillow

## License

MIT License

## Author

OMIFI Development Team