/**
 * OMIFI WebRTC Hardware Access
 * This file provides browser-based hardware access functionality using WebRTC APIs
 */

let recognition = null;
let recognitionActive = false;
let wakeWordDetected = false;
const WAKE_WORD = "hey omifi";

/**
 * Initialize WebRTC hardware access
 */
function initWebRTCHardware() {
    // Check for microphone support
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                // Microphone is available
                stream.getTracks().forEach(track => track.stop()); // Stop the stream
                updateMicrophoneStatus(true);
                
                // Initialize speech recognition if available
                initSpeechRecognition();
            })
            .catch(error => {
                console.error('Microphone access error:', error);
                updateMicrophoneStatus(false);
                showNotification('warning', 'Microphone access denied. Voice recognition will not work.');
            });
    } else {
        updateMicrophoneStatus(false);
        showNotification('warning', 'WebRTC not supported in this browser. Some features will be limited.');
    }
}

/**
 * Initialize speech recognition if supported by the browser
 */
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.error('Speech recognition not supported in this browser');
        document.getElementById('voiceStatus').textContent = 'Voice recognition not supported in this browser';
        return;
    }
    
    // Initialize speech recognition
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        document.getElementById('voiceStatus').textContent = 'Listening for wake word "Hey OMIFI"...';
        recognitionActive = true;
        document.getElementById('toggleVoiceButton').textContent = 'Stop Voice Recognition';
        document.getElementById('toggleVoiceButton').classList.remove('btn-success');
        document.getElementById('toggleVoiceButton').classList.add('btn-danger');
    };
    
    recognition.onend = () => {
        if (recognitionActive) {
            // If we're still supposed to be active, restart the recognition
            try {
                recognition.start();
            } catch (error) {
                console.error('Error restarting speech recognition:', error);
                resetVoiceRecognitionUI();
            }
        } else {
            resetVoiceRecognitionUI();
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            showNotification('danger', 'Microphone access denied. Please enable microphone access to use voice recognition.');
            resetVoiceRecognitionUI();
        }
    };
    
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
        
        const lowerTranscript = transcript.toLowerCase();
        
        document.getElementById('voiceStatus').textContent = `Heard: "${transcript}"`;
        
        // Check for wake word
        if (!wakeWordDetected && lowerTranscript.includes(WAKE_WORD)) {
            wakeWordDetected = true;
            playActivationSound();
            document.getElementById('voiceStatus').textContent = 'Wake word detected! Listening for command...';
            
            // Extract command after wake word if it exists in the same utterance
            const command = extractCommandAfterWakeWord(lowerTranscript);
            if (command && command.length > 1) {
                processCommand(command);
                resetWakeWordState();
            }
        } 
        // Process command if wake word was already detected
        else if (wakeWordDetected && event.results[event.results.length - 1].isFinal) {
            const command = lowerTranscript.trim();
            processCommand(command);
            resetWakeWordState();
        }
    };
}

/**
 * Extract command after wake word from transcript
 */
function extractCommandAfterWakeWord(text) {
    const wakeWordIndex = text.indexOf(WAKE_WORD);
    if (wakeWordIndex !== -1) {
        return text.substring(wakeWordIndex + WAKE_WORD.length).trim();
    }
    return '';
}

/**
 * Reset wake word detection state
 */
function resetWakeWordState() {
    wakeWordDetected = false;
    setTimeout(() => {
        if (!wakeWordDetected) {
            document.getElementById('voiceStatus').textContent = 'Listening for wake word "Hey OMIFI"...';
        }
    }, 3000);
}

/**
 * Reset the voice recognition UI elements
 */
function resetVoiceRecognitionUI() {
    document.getElementById('voiceStatus').textContent = 'Voice recognition inactive';
    document.getElementById('toggleVoiceButton').textContent = 'Start Voice Recognition';
    document.getElementById('toggleVoiceButton').classList.remove('btn-danger');
    document.getElementById('toggleVoiceButton').classList.add('btn-success');
    recognitionActive = false;
    wakeWordDetected = false;
}

/**
 * Toggle voice recognition on/off
 */
function toggleVoiceRecognition() {
    if (recognition) {
        if (recognitionActive) {
            stopVoiceRecognition();
        } else {
            startVoiceRecognition();
        }
    } else {
        showNotification('warning', 'Voice recognition not supported in your browser');
    }
}

/**
 * Start voice recognition
 */
function startVoiceRecognition() {
    if (recognition) {
        try {
            recognition.start();
            showNotification('success', 'Voice recognition started');
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            showNotification('danger', 'Error starting voice recognition');
        }
    }
}

/**
 * Stop voice recognition
 */
function stopVoiceRecognition() {
    if (recognition) {
        recognitionActive = false;
        try {
            recognition.stop();
            showNotification('info', 'Voice recognition stopped');
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
}

/**
 * Process a voice command
 */
function processCommand(command) {
    console.log('Processing command:', command);
    document.getElementById('voiceStatus').textContent = `Executing: "${command}"`;
    
    // Map common voice commands to functions
    if (command.includes('take') && command.includes('screenshot')) {
        takeScreenshotFromBrowser();
    } 
    else if (command.includes('sense') && command.includes('clipboard')) {
        senseClipboardFromBrowser();
    } 
    else if ((command.includes('show') || command.includes('open')) && command.includes('screenshot')) {
        // For open last screenshot, we'll use the server endpoint
        fetch('/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: 'command=open+last+screenshot'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('success', data.message);
            } else {
                showNotification('danger', data.message);
            }
        })
        .catch(error => {
            console.error('Error executing command:', error);
        });
    }
    else if (command.includes('read') && command.includes('clipboard')) {
        // For read clipboard, we'll use the server endpoint
        fetch('/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: 'command=read+clipboard'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('success', data.message);
            } else {
                showNotification('danger', data.message);
            }
        })
        .catch(error => {
            console.error('Error executing command:', error);
        });
    }
    else if ((command.includes('what') && command.includes('do')) || 
             (command.includes('help'))) {
        // Show help notification
        showNotification('info', `
            <strong>Available commands:</strong>
            <ul class="mb-0 ps-3">
                <li>Take a screenshot</li>
                <li>Sense clipboard</li>
                <li>Read clipboard</li>
                <li>Show last screenshot</li>
            </ul>
        `);
    }
    else {
        // Unknown command, try to execute via server
        fetch('/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `command=${encodeURIComponent(command)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('success', data.message);
            } else {
                showNotification('warning', 'Command not recognized: ' + command);
            }
        })
        .catch(error => {
            console.error('Error executing command:', error);
            showNotification('warning', 'Command not recognized: ' + command);
        });
    }
}

/**
 * Take a screenshot using the browser's screen capture API
 */
function takeScreenshotFromBrowser() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        showNotification('warning', 'Screen capture not supported in your browser');
        return;
    }
    
    navigator.mediaDevices.getDisplayMedia({ video: true })
        .then(stream => {
            // Create video element to capture the stream
            const video = document.createElement('video');
            video.srcObject = stream;
            
            // Once metadata is loaded, capture a frame
            video.onloadedmetadata = () => {
                video.play();
                
                // Wait a small amount of time to ensure the video is playing
                setTimeout(() => {
                    // Create canvas element to draw the screenshot
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    
                    // Draw the video frame to canvas
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Convert canvas to blob
                    canvas.toBlob(blob => {
                        // Create form data to send to server
                        const formData = new FormData();
                        formData.append('screenshot', blob, 'screenshot.png');
                        
                        // Send to server
                        fetch('/take-screenshot', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                showNotification('success', 'Screenshot captured from browser');
                                // Reload the page to show the new screenshot
                                setTimeout(() => {
                                    window.location.reload();
                                }, 1500);
                            } else {
                                showNotification('danger', data.message || 'Error saving screenshot');
                            }
                        })
                        .catch(error => {
                            console.error('Error saving screenshot:', error);
                            showNotification('danger', 'Error saving screenshot');
                        });
                    }, 'image/png');
                }, 100);
            };
        })
        .catch(error => {
            console.error('Error accessing screen:', error);
            showNotification('danger', 'Screen capture was denied or failed');
            
            // Fall back to server-side screenshot
            fallbackServerScreenshot();
        });
}

/**
 * Sense clipboard content using the browser's clipboard API
 */
function senseClipboardFromBrowser() {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
        showNotification('warning', 'Clipboard access not supported in your browser');
        return;
    }
    
    navigator.clipboard.readText()
        .then(text => {
            if (!text) {
                showNotification('warning', 'Clipboard is empty or contains non-text content');
                return;
            }
            
            // Create form data to send to server
            const formData = new FormData();
            formData.append('content', text);
            
            // Send to server
            fetch('/sense-clipboard', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('success', 'Clipboard content captured from browser');
                    // Show preview if content isn't too long
                    if (text.length <= 50) {
                        showNotification('info', `Clipboard content: ${text}`);
                    } else {
                        showNotification('info', `Clipboard content: ${text.substring(0, 47)}...`);
                    }
                    // Reload the page to show the new clipboard content
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification('danger', data.message || 'Error saving clipboard content');
                }
            })
            .catch(error => {
                console.error('Error saving clipboard content:', error);
                showNotification('danger', 'Error saving clipboard content');
            });
        })
        .catch(error => {
            console.error('Error reading clipboard:', error);
            showNotification('danger', 'Clipboard access was denied or failed');
            
            // Fall back to server-side clipboard
            fallbackServerClipboard();
        });
}

/**
 * Play a sound to indicate wake word activation
 */
function playActivationSound() {
    // Create audio context
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    
    const audioCtx = new AudioContext();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
    gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
    
    oscillator.start();
    
    // Fade out and stop
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
    setTimeout(() => {
        oscillator.stop();
    }, 300);
}

/**
 * Update the microphone status indicator
 */
function updateMicrophoneStatus(available) {
    const microphoneStatus = document.getElementById('microphoneStatus');
    if (microphoneStatus) {
        microphoneStatus.textContent = available ? 'Available' : 'Not Available';
        microphoneStatus.classList.remove('bg-warning');
        microphoneStatus.classList.add(available ? 'bg-success' : 'bg-danger');
    }
}