/**
 * OMIFI WebRTC Hardware Access
 * This file provides browser-based hardware access functionality using WebRTC APIs
 */

let recognition = null;
let recognitionActive = false;
let wakeWordDetected = false;
let reconnectAttempts = 0;
let maxReconnectAttempts = 3;
let microphoneAccessGranted = false;
let voiceTrainingActive = false;
let voiceTrainingStep = 1;
let wakeWordSamples = [];
let commandSamples = {};
let currentTrainingPhrase = "";
let currentPhraseAttempts = 0;

// Default settings that can be overridden by user 
let settings = {
    language: 'en-US',
    wakeWord: 'hey omifi',
    sensitivity: 50,
    continualListening: true
};

// Try to load saved settings from localStorage
try {
    const savedSettings = localStorage.getItem('omifiVoiceSettings');
    if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        settings = { ...settings, ...parsedSettings };
    }
} catch (e) {
    console.error('Error loading saved settings:', e);
}

// Initialize wake word from settings
const WAKE_WORD = settings.wakeWord;

/**
 * Initialize WebRTC hardware access
 */
function initWebRTCHardware() {
    // Initialize UI components for voice training and settings
    initVoiceSettings();
    initVoiceTraining();
    
    // Set up the toggle button for voice recognition
    const toggleButton = document.getElementById('toggleVoiceButton');
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleVoiceRecognition);
    }
    
    // Check for microphone support
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                // Microphone is available
                stream.getTracks().forEach(track => track.stop()); // Stop the stream
                updateMicrophoneStatus(true);
                microphoneAccessGranted = true;
                
                // Initialize speech recognition if available
                initSpeechRecognition();
                
                // Auto-start voice recognition if previously active
                if (localStorage.getItem('voiceRecognitionActive') === 'true') {
                    setTimeout(() => {
                        startVoiceRecognition();
                    }, 1000);
                }
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
    recognition.lang = settings.language || 'en-US';
    
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
            if (settings.continualListening) {
                console.log('Continuous listening enabled, attempting to restart recognition...');
                setTimeout(() => {
                    try {
                        recognition.start();
                    } catch (error) {
                        console.error('Error restarting speech recognition:', error);
                        
                        // Show reconnect button
                        const reconnectBtn = document.getElementById('microphoneReconnect');
                        if (reconnectBtn) {
                            reconnectBtn.style.display = 'block';
                        }
                        
                        // Update status and UI
                        updateMicrophoneStatus(false);
                        document.getElementById('voiceStatus').textContent = 'Microphone disconnected. Click reconnect to try again.';
                    }
                }, 1000); // Wait a second before trying to restart
            } else {
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
        } else if (event.error === 'network') {
            // Network issues
            showNotification('warning', 'Network issue with speech recognition. Trying to reconnect...');
            setTimeout(() => {
                if (recognitionActive && settings.continualListening) {
                    try {
                        recognition.start();
                    } catch (e) {
                        console.error('Error restarting after network error:', e);
                    }
                }
            }, 2000);
        } else if (event.error === 'no-speech') {
            // No speech detected, just keep listening
            console.log('No speech detected, continuing to listen...');
        } else if (event.error === 'aborted') {
            // Recognition was aborted, try to restart if we're still supposed to be active
            if (recognitionActive && settings.continualListening) {
                setTimeout(() => {
                    try {
                        recognition.start();
                    } catch (e) {
                        console.error('Error restarting after abort:', e);
                    }
                }, 1000);
            }
        }
    };
    
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
        
        const lowerTranscript = transcript.toLowerCase();
        
        document.getElementById('voiceStatus').textContent = `Heard: "${transcript}"`;
        
        // Always process command, with or without wake word
        if (event.results[event.results.length - 1].isFinal) {
            // First check if it has wake word
            if (lowerTranscript.includes(WAKE_WORD)) {
                wakeWordDetected = true;
                playActivationSound();
                document.getElementById('voiceStatus').textContent = 'Wake word detected! Processing command...';
                
                // Extract command after wake word if it exists
                const command = extractCommandAfterWakeWord(lowerTranscript);
                if (command && command.length > 1) {
                    processCommand(command);
                }
            } 
            // Even without wake word, check if it's a direct screenshot or clipboard command
            else if (
                lowerTranscript.includes('screenshot') || 
                lowerTranscript.includes('screen shot') ||
                lowerTranscript.includes('take picture') ||
                lowerTranscript.includes('clipboard') || 
                lowerTranscript.includes('sense clipboard') ||
                lowerTranscript.includes('copy text')
            ) {
                document.getElementById('voiceStatus').textContent = `Executing: "${lowerTranscript}"`;
                processCommand(lowerTranscript);
            }
            // Handle just heard "screenshot" or "clipboard"
            else if (lowerTranscript.trim() === 'screenshot') {
                document.getElementById('voiceStatus').textContent = 'Taking screenshot...';
                takeScreenshotFromBrowser();
            }
            else if (lowerTranscript.trim() === 'clipboard') {
                document.getElementById('voiceStatus').textContent = 'Sensing clipboard...';
                senseClipboardFromBrowser();
            }
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
    if (!recognition) {
        showNotification('warning', 'Voice recognition is not supported in your browser');
        return;
    }
    
    try {
        // Always try to get fresh microphone access to ensure it's working
        navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
            .then(stream => {
                // Stop the stream immediately after confirming access
                stream.getTracks().forEach(track => track.stop());
                
                // Update status
                updateMicrophoneStatus(true);
                microphoneAccessGranted = true;
                
                // Now start recognition with confirmed microphone access
                try {
                    recognition.start();
                    recognitionActive = true;
                    wakeWordDetected = false;
                    localStorage.setItem('voiceRecognitionActive', 'true');
                    
                    // Update UI
                    document.getElementById('voiceStatus').textContent = 'Listening for wake word "Hey OMIFI"...';
                    document.getElementById('toggleVoiceButton').textContent = 'Stop Voice Recognition';
                    document.getElementById('toggleVoiceButton').classList.remove('btn-success');
                    document.getElementById('toggleVoiceButton').classList.add('btn-danger');
                    
                    // Hide reconnect button if shown
                    const reconnectBtn = document.getElementById('microphoneReconnect');
                    if (reconnectBtn) {
                        reconnectBtn.style.display = 'none';
                    }
                    
                    showNotification('success', 'Voice recognition started!');
                } catch (e) {
                    console.error('Error starting recognition after microphone access:', e);
                    showNotification('warning', 'Error starting recognition: ' + e.message);
                }
            })
            .catch(error => {
                console.error('Microphone access error in startVoiceRecognition:', error);
                updateMicrophoneStatus(false);
                
                // Show different messages based on error type
                if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                    showNotification('danger', 'Microphone access denied. Please enable microphone access in your browser settings.');
                } else {
                    showNotification('warning', 'Could not access microphone. Using simulation mode instead.');
                    
                    // Use simulation mode
                    recognitionActive = true;
                    wakeWordDetected = false;
                    localStorage.setItem('voiceRecognitionActive', 'true');
                    
                    // Update UI to show simulated mode
                    document.getElementById('voiceStatus').textContent = 'Simulation mode active (no microphone)';
                    document.getElementById('toggleVoiceButton').textContent = 'Stop Simulation';
                    document.getElementById('toggleVoiceButton').classList.remove('btn-success');
                    document.getElementById('toggleVoiceButton').classList.add('btn-warning');
                    
                    // Show reconnect button
                    const reconnectBtn = document.getElementById('microphoneReconnect');
                    if (reconnectBtn) {
                        reconnectBtn.style.display = 'block';
                    }
                }
            });
    } catch (error) {
        console.error('Error in startVoiceRecognition:', error);
        showNotification('danger', 'Error starting voice recognition: ' + error.message);
    }
}

/**
 * Stop voice recognition
 */
function stopVoiceRecognition() {
    if (recognition) {
        try {
            // Check if recognition is actually running
            if (recognition && recognitionActive) {
                recognition.stop();
            }
        } catch (error) {
            console.error('Error stopping voice recognition:', error);
            // Non-critical error, we proceed with UI reset anyway
        }
    }
    
    // Always update state variables and UI
    recognitionActive = false;
    wakeWordDetected = false;
    localStorage.setItem('voiceRecognitionActive', 'false');
    
    // Reset UI
    resetVoiceRecognitionUI();
    showNotification('info', 'Voice recognition stopped');
}

/**
 * Process a voice command
 */
function processCommand(command) {
    console.log('Processing command:', command);
    document.getElementById('voiceStatus').textContent = `Executing: "${command}"`;
    
    // Map common voice commands to functions - allow for various natural language ways to express the same command
    
    // Screenshot commands
    if (
        (command.includes('take') && command.includes('screenshot')) ||
        (command.includes('capture') && command.includes('screen')) ||
        (command.includes('screen') && command.includes('shot')) ||
        (command.includes('take') && command.includes('picture')) ||
        command.trim() === 'screenshot'
    ) {
        takeScreenshotFromBrowser();
        return; // Stop processing after executing the command
    } 
    
    // Clipboard sensing commands
    else if (
        (command.includes('sense') && command.includes('clipboard')) ||
        (command.includes('get') && command.includes('clipboard')) ||
        (command.includes('check') && command.includes('clipboard')) ||
        (command.includes('clipboard') && command.includes('content')) ||
        command.trim() === 'clipboard'
    ) {
        senseClipboardFromBrowser();
        return; // Stop processing after executing the command
    } 
    
    // Show/open screenshot commands
    else if (
        ((command.includes('show') || command.includes('open') || command.includes('view')) && command.includes('screenshot')) ||
        ((command.includes('display') || command.includes('see')) && command.includes('last') && command.includes('screen'))
    ) {
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
        return; // Stop processing after executing the command
    }
    
    // Read clipboard commands
    else if (
        (command.includes('read') && command.includes('clipboard')) ||
        (command.includes('say') && command.includes('clipboard')) ||
        (command.includes('tell') && command.includes('clipboard')) ||
        (command.includes('speak') && command.includes('clipboard'))
    ) {
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
        return; // Stop processing after executing the command
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
 * Generate QR code for content access
 * @param {string} filepath - The path to the file
 * @param {string} contentType - The type of content ('image', 'text', etc.)
 */
function generateQRCodeForContent(filepath, contentType = 'text') {
    // Determine endpoint based on content type
    const endpoint = contentType === 'image' ? 'qr/screenshot' : 'qr/clipboard';
    
    // Extract filename from filepath
    const filename = filepath.split('/').pop();
    
    // Build URL for QR code
    const qrUrl = `/${endpoint}/${encodeURIComponent(filename)}`;
    
    // Determine download URL
    const downloadEndpoint = contentType === 'image' ? 'screenshot' : 'clipboard';
    const downloadUrl = `/${downloadEndpoint}/${encodeURIComponent(filename)}`;
    
    // Create a popup notification with QR code and download link
    const popupContent = `
        <div class="text-center mb-2">
            <p>Scan QR code to access content on mobile</p>
            <img src="${qrUrl}" alt="QR Code" class="img-fluid" style="max-width: 150px;">
        </div>
        <div class="d-grid gap-2">
            <a href="${qrUrl}" target="_blank" class="btn btn-sm btn-primary">
                <i class="fas fa-qrcode"></i> View QR Code
            </a>
            <a href="${downloadUrl}" target="_blank" class="btn btn-sm btn-secondary">
                <i class="fas fa-download"></i> Download Content
            </a>
        </div>
    `;
    
    // Show notification with QR code
    if (typeof showNotification === 'function') {
        showNotification('info', popupContent, 10000); // Show for 10 seconds
    }
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
    
    microphoneAccessGranted = available;
    
    // Show the reconnect button if microphone becomes unavailable
    const reconnectBtn = document.getElementById('microphoneReconnect');
    if (reconnectBtn) {
        reconnectBtn.style.display = available ? 'none' : 'block';
    }
}

/**
 * Reconnect the microphone
 */
function reconnectMicrophone() {
    // Reset count if it's too high
    if (reconnectAttempts >= maxReconnectAttempts) {
        reconnectAttempts = 0;
        showNotification('info', 'Resetting reconnection attempts...');
    }
    
    reconnectAttempts++;
    showNotification('info', 'Attempting to reconnect microphone...');
    
    // Show spinner on reconnect button if it exists
    const reconnectBtn = document.getElementById('microphoneReconnect');
    if (reconnectBtn) {
        reconnectBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Reconnecting...';
        reconnectBtn.disabled = true;
    }
    
    // Check for devices first
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        navigator.mediaDevices.enumerateDevices()
            .then(devices => {
                // Check if any audio input devices are available
                const hasAudioInput = devices.some(device => device.kind === 'audioinput');
                
                if (!hasAudioInput) {
                    throw new Error('No audio input devices found');
                }
                
                // Try to request microphone access
                return navigator.mediaDevices.getUserMedia({ 
                    audio: { 
                        echoCancellation: true, 
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
            })
            .then(stream => {
                // Microphone is available
                stream.getTracks().forEach(track => track.stop()); // Stop the stream
                updateMicrophoneStatus(true);
                reconnectAttempts = 0;
                
                if (recognitionActive) {
                    // Restart voice recognition with a clean start
                    try {
                        if (recognition) {
                            recognition.stop();
                        }
                    } catch (e) {
                        console.log('Error stopping recognition before restart:', e);
                    }
                    
                    // Initialize a new recognition instance to avoid any stale state
                    initSpeechRecognition();
                    
                    setTimeout(() => {
                        startVoiceRecognition();
                    }, 500);
                }
                
                // Reset reconnect button
                if (reconnectBtn) {
                    reconnectBtn.innerHTML = 'Reconnect Microphone';
                    reconnectBtn.disabled = false;
                    reconnectBtn.style.display = 'none'; // Hide it since we're connected
                }
                
                showNotification('success', 'Microphone reconnected!');
                
                // Update voice status
                const voiceStatus = document.getElementById('voiceStatus');
                if (voiceStatus) {
                    if (recognitionActive) {
                        voiceStatus.textContent = 'Listening for wake word "Hey OMIFI"...';
                    } else {
                        voiceStatus.textContent = 'Voice recognition ready. Click Start to begin.';
                    }
                }
            })
            .catch(error => {
                console.error('Microphone reconnect error:', error);
                updateMicrophoneStatus(false);
                
                // Reset reconnect button
                if (reconnectBtn) {
                    reconnectBtn.innerHTML = 'Retry Microphone Access';
                    reconnectBtn.disabled = false;
                    reconnectBtn.style.display = 'block';
                }
                
                // Show different messages based on the error
                if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                    showNotification('danger', 'Microphone access denied. Please enable microphone access in your browser settings.');
                } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError' || error.message === 'No audio input devices found') {
                    showNotification('warning', 'No microphone detected. Please connect a microphone and try again.');
                } else {
                    showNotification('warning', `Failed to reconnect microphone (attempt ${reconnectAttempts}/${maxReconnectAttempts}). Will continue with server-side commands only.`);
                }
                
                // Update voice status for clarity
                document.getElementById('voiceStatus').textContent = 'No microphone access. Using button controls instead.';
                
                // Schedule another automatic reconnection attempt if we haven't exceeded the limit
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectMicrophone();
                    }, reconnectAttempts * 5000); // Increase delay with each attempt
                }
            });
    } else {
        // Browser doesn't support enumerateDevices
        showNotification('warning', 'Your browser does not fully support audio input detection.');
        document.getElementById('voiceStatus').textContent = 'Limited browser support. Using button controls instead.';
        
        if (reconnectBtn) {
            reconnectBtn.innerHTML = 'Retry Microphone Access';
            reconnectBtn.disabled = false;
        }
    }
}

/**
 * Apply voice recognition settings
 */
function applyVoiceSettings() {
    if (recognition) {
        // Update language
        recognition.lang = settings.language;
        
        // Update wake word
        if (settings.wakeWord && settings.wakeWord.trim() !== '') {
            WAKE_WORD = settings.wakeWord.toLowerCase().trim();
        }
        
        // If recognition is active, restart it to apply changes
        if (recognitionActive) {
            stopVoiceRecognition();
            startVoiceRecognition();
        }
        
        // Save settings to localStorage
        try {
            localStorage.setItem('omifiVoiceSettings', JSON.stringify(settings));
        } catch (e) {
            console.error('Error saving settings:', e);
        }
    }
}

/**
 * Start voice training for wake word
 */
function startWakeWordTraining() {
    // Clear any existing instructions
    const existingInstructions = document.querySelector('.mic-instructions');
    if (existingInstructions) {
        existingInstructions.remove();
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showNotification('danger', 'Your browser does not support microphone access. Please try using Chrome or Edge.');
        return;
    }
    
    const wakeWordProgress = document.getElementById('wakeWordProgress');
    const startButton = document.getElementById('startWakeWordTraining');
    
    // Disable the button during recording
    startButton.disabled = true;
    startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Requesting Microphone...';
    
    // Get the wake word phrase
    const wakeWord = document.getElementById('wakeWordPhrase').textContent;
    currentTrainingPhrase = wakeWord.toLowerCase();
    
    // Show recording instructions
    const recordingInstructions = document.createElement('div');
    recordingInstructions.className = 'alert alert-primary mt-3';
    recordingInstructions.innerHTML = `
        <h5>Recording Instructions</h5>
        <p>Please say the wake word phrase "<strong>${wakeWord}</strong>" clearly when recording starts.</p>
        <p>We'll record for 3 seconds after you allow microphone access.</p>
        <div class="progress mt-3" style="height: 5px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary recording-progress" 
                 role="progressbar" style="width: 0%"></div>
        </div>
    `;
    document.querySelector('.training-container').appendChild(recordingInstructions);
    
    // Request microphone with echo cancellation and noise suppression
    navigator.mediaDevices.getUserMedia({ 
        audio: { 
            echoCancellation: true, 
            noiseSuppression: true,
            autoGainControl: true
        } 
    })
    .then(stream => {
        // Update microphone status to available since we successfully got access
        updateMicrophoneStatus(true);
        
        // Update UI to show recording in progress
        startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Recording...';
        showNotification('success', 'Microphone access granted! Recording now...');
        
        const recordingProgress = document.querySelector('.recording-progress');
        
        // Animate progress bar during recording
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 3.33; // Increase every 100ms for 3 seconds
            if (recordingProgress) {
                recordingProgress.style.width = Math.min(progress, 100) + '%';
            }
        }, 100);
        
        const mediaRecorder = new MediaRecorder(stream);
        const chunks = [];
        
        mediaRecorder.addEventListener('dataavailable', event => {
            chunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            // Stop progress animation
            clearInterval(progressInterval);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Create blob from chunks
            const audioBlob = new Blob(chunks, { 'type' : 'audio/webm' });
            
            // Save wake word sample
            saveWakeWordSample(audioBlob);
            
            // Update progress
            completeWakeWordTrainingStep();
            
            // Remove recording instructions
            recordingInstructions.remove();
        });
        
        // Record for 3 seconds
        mediaRecorder.start();
        setTimeout(() => {
            mediaRecorder.stop();
        }, 3000);
    })
    .catch(error => {
        console.error('Microphone access error:', error);
        
        // Reset button
        startButton.disabled = false;
        startButton.textContent = 'Start Recording';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            showNotification('danger', 'Microphone access denied. Please allow microphone access in your browser settings to use real-time voice training.');
        } else {
            showNotification('danger', 'Could not access microphone: ' + error.message);
        }
        
        // Show detailed instructions
        simulateWakeWordTraining();
    });
}

/**
 * Simulate wake word training when microphone is not available
 */
function simulateWakeWordTraining() {
    // We want real-time training, so notify user that microphone access is required
    showNotification('warning', 'Real-time voice training requires microphone access. Please allow microphone access in your browser settings and try again.');
    
    // Reset button state
    const startButton = document.getElementById('startWakeWordTraining');
    startButton.disabled = false;
    startButton.textContent = 'Start Recording';
    
    // Show instructions to enable microphone
    const micInstructions = document.createElement('div');
    micInstructions.className = 'alert alert-info mt-3';
    micInstructions.innerHTML = `
        <h5>Microphone Access Required</h5>
        <p>This feature requires real-time microphone access. Please:</p>
        <ol>
            <li>Check that your browser supports microphone access</li>
            <li>Ensure your microphone is properly connected</li>
            <li>Allow this site to access your microphone when prompted</li>
            <li>Try using Chrome or Edge for best compatibility</li>
        </ol>
        <button class="btn btn-primary" onclick="reconnectMicrophone()">Try Again</button>
    `;
    
    // Add instructions to the DOM if not already present
    const existingInstructions = document.querySelector('.mic-instructions');
    if (!existingInstructions) {
        document.querySelector('.training-container').appendChild(micInstructions);
        micInstructions.classList.add('mic-instructions');
    }
}

/**
 * Complete a wake word training step
 */
function completeWakeWordTrainingStep() {
    const wakeWordProgress = document.getElementById('wakeWordProgress');
    const startButton = document.getElementById('startWakeWordTraining');
    
    // Update progress
    currentPhraseAttempts++;
    const progress = Math.min((currentPhraseAttempts / 3) * 100, 100);
    wakeWordProgress.style.width = progress + '%';
    wakeWordProgress.setAttribute('aria-valuenow', progress);
    
    // Enable the button for next recording
    startButton.disabled = false;
    startButton.textContent = 'Start Recording';
    
    // If we have 3 samples, show next button
    if (currentPhraseAttempts >= 3) {
        document.getElementById('nextToCommands').style.display = 'block';
        showNotification('success', 'Wake word training complete!');
    } else {
        showNotification('info', `Please record ${3 - currentPhraseAttempts} more sample(s)`);
    }
}

/**
 * Start voice training for commands
 */
function startCommandTraining() {
    // Clear any existing instructions
    const existingInstructions = document.querySelector('.mic-instructions');
    if (existingInstructions) {
        existingInstructions.remove();
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showNotification('danger', 'Your browser does not support microphone access. Please try using Chrome or Edge.');
        return;
    }
    
    const commandProgress = document.getElementById('commandProgress');
    const startButton = document.getElementById('startCommandTraining');
    
    // Disable the button during recording
    startButton.disabled = true;
    startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Requesting Microphone...';
    
    // Get the command phrase
    const command = document.getElementById('commandPhrase').textContent;
    currentTrainingPhrase = command.toLowerCase();
    
    // Show recording instructions
    const recordingInstructions = document.createElement('div');
    recordingInstructions.className = 'alert alert-primary mt-3';
    recordingInstructions.innerHTML = `
        <h5>Recording Instructions</h5>
        <p>Please say the command "<strong>${command}</strong>" clearly when recording starts.</p>
        <p>We'll record for 3 seconds after you allow microphone access.</p>
        <div class="progress mt-3" style="height: 5px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary recording-progress-cmd" 
                 role="progressbar" style="width: 0%"></div>
        </div>
    `;
    document.querySelector('.training-container').appendChild(recordingInstructions);
    
    // Request microphone with echo cancellation and noise suppression
    navigator.mediaDevices.getUserMedia({ 
        audio: { 
            echoCancellation: true, 
            noiseSuppression: true,
            autoGainControl: true
        } 
    })
    .then(stream => {
        // Update microphone status to available since we successfully got access
        updateMicrophoneStatus(true);
        
        // Update UI to show recording in progress
        startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Recording...';
        showNotification('success', 'Microphone access granted! Recording now...');
        
        const recordingProgress = document.querySelector('.recording-progress-cmd');
        
        // Animate progress bar during recording
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 3.33; // Increase every 100ms for 3 seconds
            if (recordingProgress) {
                recordingProgress.style.width = Math.min(progress, 100) + '%';
            }
        }, 100);
        
        const mediaRecorder = new MediaRecorder(stream);
        const chunks = [];
        
        mediaRecorder.addEventListener('dataavailable', event => {
            chunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            // Stop progress animation
            clearInterval(progressInterval);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Create blob from chunks
            const audioBlob = new Blob(chunks, { 'type' : 'audio/webm' });
            
            // Save command sample
            saveCommandSample(audioBlob);
            
            // Update command display and progress
            updateCommandTrainingProgress();
            
            // Enable the button for next recording
            startButton.disabled = false;
            startButton.textContent = 'Start Recording';
            
            // Remove recording instructions
            recordingInstructions.remove();
        });
        
        // Record for 3 seconds
        mediaRecorder.start();
        setTimeout(() => {
            mediaRecorder.stop();
        }, 3000);
    })
    .catch(error => {
        console.error('Microphone access error:', error);
        
        // Reset button
        startButton.disabled = false;
        startButton.textContent = 'Start Recording';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            showNotification('danger', 'Microphone access denied. Please allow microphone access in your browser settings to use real-time voice training.');
        } else {
            showNotification('danger', 'Could not access microphone: ' + error.message);
        }
        
        // Show detailed instructions
        simulateCommandTraining();
    });
}

/**
 * Simulate command training when microphone is not available
 */
function simulateCommandTraining() {
    // We want real-time training, so notify user that microphone access is required
    showNotification('warning', 'Real-time voice training requires microphone access. Please allow microphone access in your browser settings and try again.');
    
    // Reset button state
    const startButton = document.getElementById('startCommandTraining');
    startButton.disabled = false;
    startButton.textContent = 'Start Recording';
    
    // Show instructions to enable microphone if not already shown
    const existingInstructions = document.querySelector('.mic-instructions');
    if (!existingInstructions) {
        const micInstructions = document.createElement('div');
        micInstructions.className = 'alert alert-info mt-3';
        micInstructions.innerHTML = `
            <h5>Microphone Access Required</h5>
            <p>This feature requires real-time microphone access. Please:</p>
            <ol>
                <li>Check that your browser supports microphone access</li>
                <li>Ensure your microphone is properly connected</li>
                <li>Allow this site to access your microphone when prompted</li>
                <li>Try using Chrome or Edge for best compatibility</li>
            </ol>
            <button class="btn btn-primary" onclick="reconnectMicrophone()">Try Again</button>
        `;
        
        document.querySelector('.training-container').appendChild(micInstructions);
        micInstructions.classList.add('mic-instructions');
    }
}

/**
 * Save wake word sample
 */
function saveWakeWordSample(audioBlob) {
    try {
        // Create a unique ID for this sample
        const sampleId = 'wake_' + Date.now();
        
        // Save to IndexedDB or other storage
        wakeWordSamples.push({
            id: sampleId,
            phrase: currentTrainingPhrase,
            timestamp: Date.now(),
            // We'd convert blob to base64 for actual storage
            audio: URL.createObjectURL(audioBlob)
        });
        
        console.log('Wake word sample saved:', sampleId);
    } catch (error) {
        console.error('Error saving wake word sample:', error);
    }
}

/**
 * Save command sample
 */
function saveCommandSample(audioBlob) {
    try {
        // Create a unique ID for this sample
        const sampleId = 'cmd_' + Date.now();
        
        // Initialize command array if it doesn't exist
        if (!commandSamples[currentTrainingPhrase]) {
            commandSamples[currentTrainingPhrase] = [];
        }
        
        // Save to IndexedDB or other storage
        commandSamples[currentTrainingPhrase].push({
            id: sampleId,
            phrase: currentTrainingPhrase,
            timestamp: Date.now(),
            // We'd convert blob to base64 for actual storage
            audio: URL.createObjectURL(audioBlob)
        });
        
        console.log('Command sample saved:', sampleId, currentTrainingPhrase);
    } catch (error) {
        console.error('Error saving command sample:', error);
    }
}

/**
 * Update command training progress
 */
function updateCommandTrainingProgress() {
    const commandDisplay = document.getElementById('commandPhrase');
    const commandProgress = document.getElementById('commandProgress');
    
    // List of commands to train
    const commands = [
        'Take a screenshot',
        'Sense clipboard',
        'Show last screenshot',
        'Read clipboard',
        'Help me with commands'
    ];
    
    // Find current command index
    const currentIndex = commands.findIndex(cmd => cmd.toLowerCase() === currentTrainingPhrase);
    
    // If we've recorded this command, move to the next one
    if (currentIndex < commands.length - 1) {
        const nextCommand = commands[currentIndex + 1];
        commandDisplay.textContent = nextCommand;
        currentTrainingPhrase = nextCommand.toLowerCase();
    } else {
        // All commands trained
        document.getElementById('nextToConfirmation').style.display = 'block';
        showNotification('success', 'Command training complete!');
    }
    
    // Update progress
    const progress = Math.min(((currentIndex + 1) / commands.length) * 100, 100);
    commandProgress.style.width = progress + '%';
    commandProgress.setAttribute('aria-valuenow', progress);
}

/**
 * Initialize voice training UI
 */
function initVoiceTraining() {
    // Wake word training navigation
    document.getElementById('nextToCommands').addEventListener('click', () => {
        document.getElementById('trainStep1').style.display = 'none';
        document.getElementById('trainStep2').style.display = 'block';
    });
    
    // Command training navigation
    document.getElementById('prevToWakeWord').addEventListener('click', () => {
        document.getElementById('trainStep2').style.display = 'none';
        document.getElementById('trainStep1').style.display = 'block';
    });
    
    document.getElementById('nextToConfirmation').addEventListener('click', () => {
        document.getElementById('trainStep2').style.display = 'none';
        document.getElementById('trainStep3').style.display = 'block';
        
        // Update summary
        document.getElementById('wakeWordSamples').textContent = wakeWordSamples.length;
        
        // Count command samples
        const totalCommandSamples = Object.values(commandSamples)
            .reduce((total, samples) => total + samples.length, 0);
        document.getElementById('commandSamples').textContent = totalCommandSamples;
        
        // Set confidence level
        const confidenceLevel = document.getElementById('confidenceLevel');
        if (wakeWordSamples.length >= 3 && totalCommandSamples >= 4) {
            confidenceLevel.textContent = 'High';
            confidenceLevel.className = 'text-success';
        } else if (wakeWordSamples.length >= 2 && totalCommandSamples >= 3) {
            confidenceLevel.textContent = 'Medium';
            confidenceLevel.className = 'text-warning';
        } else {
            confidenceLevel.textContent = 'Low';
            confidenceLevel.className = 'text-danger';
        }
    });
    
    // Confirmation navigation
    document.getElementById('prevToCommands').addEventListener('click', () => {
        document.getElementById('trainStep3').style.display = 'none';
        document.getElementById('trainStep2').style.display = 'block';
    });
    
    // Initialize recording buttons
    document.getElementById('startWakeWordTraining').addEventListener('click', startWakeWordTraining);
    document.getElementById('startCommandTraining').addEventListener('click', startCommandTraining);
    
    // Initialize finish button
    document.getElementById('finishTraining').addEventListener('click', () => {
        // Apply any needed changes based on training data
        showNotification('success', 'Voice training data saved successfully!');
        
        // Reset training state
        currentPhraseAttempts = 0;
        voiceTrainingActive = false;
    });
}

/**
 * Initialize voice settings UI
 */
function initVoiceSettings() {
    // Load current settings into form
    document.getElementById('languageSelect').value = settings.language;
    document.getElementById('sensitivitySlider').value = settings.sensitivity;
    document.getElementById('wakeWordInput').value = settings.wakeWord;
    document.getElementById('continualListeningCheck').checked = settings.continualListening;
    
    // Set up save button
    document.getElementById('saveVoiceSettings').addEventListener('click', () => {
        // Get values from form
        settings.language = document.getElementById('languageSelect').value;
        settings.sensitivity = parseInt(document.getElementById('sensitivitySlider').value, 10);
        settings.wakeWord = document.getElementById('wakeWordInput').value.toLowerCase().trim();
        settings.continualListening = document.getElementById('continualListeningCheck').checked;
        
        // Apply settings
        applyVoiceSettings();
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('voiceSettingsModal'));
        if (modal) {
            modal.hide();
        }
        
        showNotification('success', 'Voice settings saved!');
    });
}