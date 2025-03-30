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
    
    // Try to request microphone access
    navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
        .then(stream => {
            // Microphone is available
            stream.getTracks().forEach(track => track.stop()); // Stop the stream
            updateMicrophoneStatus(true);
            reconnectAttempts = 0;
            
            if (recognitionActive) {
                // Restart voice recognition
                try {
                    if (recognition) {
                        recognition.stop();
                    }
                } catch (e) {
                    console.log('Error stopping recognition before restart:', e);
                }
                
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
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                showNotification('warning', 'No microphone detected. Please connect a microphone and try again.');
            } else {
                showNotification('warning', `Failed to reconnect microphone (attempt ${reconnectAttempts}/${maxReconnectAttempts}). Will try simulated mode.`);
                
                // Enable simulated mode for training
                if (voiceTrainingActive) {
                    showNotification('info', 'Switching to simulation mode for training.');
                }
            }
            
            // In web-only mode, we can use server-side fall backs and simulation
            document.getElementById('voiceStatus').textContent = 'Using simulation mode for voice functions.';
        });
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
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        // Simulate training if no microphone is available
        simulateWakeWordTraining();
        return;
    }
    
    const wakeWordProgress = document.getElementById('wakeWordProgress');
    const startButton = document.getElementById('startWakeWordTraining');
    
    // Disable the button during recording
    startButton.disabled = true;
    startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Recording...';
    
    // Get wake word from element
    const wakeWord = document.getElementById('wakeWordPhrase').textContent;
    currentTrainingPhrase = wakeWord.toLowerCase();
    
    // Record the user saying the wake word
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Update microphone status to available since we successfully got access
            updateMicrophoneStatus(true);
            
            const mediaRecorder = new MediaRecorder(stream);
            const chunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                chunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', () => {
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
                
                // Create blob from chunks
                const audioBlob = new Blob(chunks, { 'type' : 'audio/webm' });
                
                // Save wake word sample
                saveWakeWordSample(audioBlob);
                
                // Update progress
                completeWakeWordTrainingStep();
            });
            
            // Record for 2 seconds
            mediaRecorder.start();
            setTimeout(() => {
                mediaRecorder.stop();
            }, 2000);
        })
        .catch(error => {
            console.error('Microphone access error:', error);
            showNotification('warning', 'Using simulation mode for training due to microphone access issues.');
            simulateWakeWordTraining();
        });
}

/**
 * Simulate wake word training when microphone is not available
 */
function simulateWakeWordTraining() {
    showNotification('info', 'Simulating training (microphone not available)');
    
    // Get wake word from element
    const wakeWord = document.getElementById('wakeWordPhrase').textContent;
    currentTrainingPhrase = wakeWord.toLowerCase();
    
    // Create a simulated audio sample
    const dummyAudio = new Uint8Array(1000).fill(128);
    const audioBlob = new Blob([dummyAudio], { type: 'audio/webm' });
    
    // Save simulated wake word sample
    saveWakeWordSample(audioBlob);
    
    // Update UI to show progress
    setTimeout(() => {
        completeWakeWordTrainingStep();
    }, 1000);
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
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        // Simulate training if no microphone is available
        simulateCommandTraining();
        return;
    }
    
    const commandProgress = document.getElementById('commandProgress');
    const startButton = document.getElementById('startCommandTraining');
    
    // Disable the button during recording
    startButton.disabled = true;
    startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Recording...';
    
    // Get the command phrase
    const command = document.getElementById('commandPhrase').textContent;
    currentTrainingPhrase = command.toLowerCase();
    
    // Record the user saying the command
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Update microphone status to available since we successfully got access
            updateMicrophoneStatus(true);
            
            const mediaRecorder = new MediaRecorder(stream);
            const chunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                chunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', () => {
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
            });
            
            // Record for 3 seconds
            mediaRecorder.start();
            setTimeout(() => {
                mediaRecorder.stop();
            }, 3000);
        })
        .catch(error => {
            console.error('Microphone access error:', error);
            showNotification('warning', 'Using simulation mode for training due to microphone access issues.');
            simulateCommandTraining();
        });
}

/**
 * Simulate command training when microphone is not available
 */
function simulateCommandTraining() {
    showNotification('info', 'Simulating command training (microphone not available)');
    
    // Get command from element
    const command = document.getElementById('commandPhrase').textContent;
    currentTrainingPhrase = command.toLowerCase();
    
    // Create a simulated audio sample
    const dummyAudio = new Uint8Array(1000).fill(128);
    const audioBlob = new Blob([dummyAudio], { type: 'audio/webm' });
    
    // Create a loading effect
    const startButton = document.getElementById('startCommandTraining');
    startButton.disabled = true;
    startButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Simulating...';
    
    // Save simulated command sample
    saveCommandSample(audioBlob);
    
    // Update UI to show progress after a delay
    setTimeout(() => {
        updateCommandTrainingProgress();
        startButton.disabled = false;
        startButton.textContent = 'Start Recording';
    }, 1500);
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