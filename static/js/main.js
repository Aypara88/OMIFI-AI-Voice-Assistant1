/**
 * OMIFI Dashboard JavaScript
 */

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('OMIFI Dashboard initialized');
    
    // Initial status check
    refreshStatus();
    
    // Set up periodic status refresh
    setInterval(refreshStatus, 10000); // Check status every 10 seconds
    
    // Set up QR code modal handler
    const qrModal = document.getElementById('qrModal');
    if (qrModal) {
        qrModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const qrUrl = button.getAttribute('data-qr-url');
            const title = button.getAttribute('data-title');
            
            // Update the modal's content
            const modalTitle = qrModal.querySelector('#qrModalLabel');
            const modalDescription = qrModal.querySelector('.qr-modal-description');
            const qrImage = qrModal.querySelector('#qrCodeImage');
            
            if (title) {
                modalTitle.textContent = title;
            } else {
                modalTitle.textContent = 'Scan QR Code';
            }
            
            if (qrUrl) {
                qrImage.src = qrUrl;
                qrImage.style.display = 'block';
                modalDescription.textContent = 'Scan this QR code with your phone to download the content';
            } else {
                qrImage.style.display = 'none';
                modalDescription.textContent = 'QR code not available';
            }
        });
    }
    
    // Set up voice recognition toggle
    const toggleVoiceButton = document.getElementById('toggleVoiceButton');
    if (toggleVoiceButton) {
        toggleVoiceButton.addEventListener('click', function() {
            toggleVoiceRecognition();
        });
    }
    
    // Initialize WebRTC hardware if available
    if (typeof initWebRTCHardware === 'function') {
        try {
            initWebRTCHardware();
        } catch (error) {
            console.error('Error initializing WebRTC hardware:', error);
            showNotification('warning', 'Browser hardware access is limited. Use the desktop app for full functionality.');
        }
    }
    
    // Display a welcome notification
    setTimeout(() => {
        showNotification('info', 'Welcome to the OMIFI Dashboard! Use the buttons to manage your voice assistant.');
    }, 500);
});

/**
 * Toggle OMIFI running status
 * @param {string} action - Either 'start' or 'stop'
 */
function toggleOmifiStatus(action) {
    // Disable buttons during processing
    document.querySelectorAll('.status-indicator .btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // Show loading indicator
    const statusText = document.querySelector('.status-text');
    const originalText = statusText.textContent;
    statusText.textContent = action === 'start' ? 'Starting...' : 'Stopping...';
    
    // Send AJAX request
    fetch(`/${action}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(`${action} response:`, data);
        
        // Update UI based on response
        const statusDot = document.querySelector('.status-dot');
        
        if (data.running) {
            statusDot.classList.remove('inactive');
            statusDot.classList.add('active');
            statusText.textContent = 'Running';
            updateActionButton('stop');
            
            // Show success notification
            showNotification('success', data.message || 'OMIFI started successfully');
        } else {
            statusDot.classList.remove('active');
            statusDot.classList.add('inactive');
            statusText.textContent = 'Stopped';
            updateActionButton('start');
            
            if (action === 'stop') {
                // Show success notification
                showNotification('success', data.message || 'OMIFI stopped successfully');
            } else {
                // Show error notification
                showNotification('danger', data.message || 'Failed to start OMIFI');
            }
        }
    })
    .catch(error => {
        console.error(`Error ${action}ing OMIFI:`, error);
        statusText.textContent = originalText;
        
        // Show error notification
        showNotification('danger', `Error ${action}ing OMIFI: ${error.message}`);
    })
    .finally(() => {
        // Re-enable buttons
        document.querySelectorAll('.status-indicator .btn').forEach(btn => {
            btn.disabled = false;
        });
    });
}

/**
 * Update the action button based on current status
 * @param {string} action - The current action ('start' or 'stop')
 */
function updateActionButton(action) {
    const statusContainer = document.querySelector('.status-indicator');
    const btnContainer = statusContainer.querySelector('.d-flex');
    
    if (action === 'start') {
        btnContainer.innerHTML = `
            <span class="status-dot inactive me-2"></span>
            <span class="status-text">Stopped</span>
            <button onclick="toggleOmifiStatus('start')" class="btn btn-sm btn-outline-success ms-3">Start</button>
        `;
    } else {
        btnContainer.innerHTML = `
            <span class="status-dot active me-2"></span>
            <span class="status-text">Running</span>
            <button onclick="toggleOmifiStatus('stop')" class="btn btn-sm btn-outline-danger ms-3">Stop</button>
        `;
    }
}

/**
 * Show a notification message
 * @param {string} type - The type of notification ('success', 'danger', etc.)
 * @param {string} message - The message to display
 * @param {number} [duration=5000] - Duration in milliseconds before auto-hiding
 */
function showNotification(type, message, duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to DOM
    document.querySelector('.notifications-container').appendChild(notification);
    
    // Auto-remove after specified duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, duration);
}

/**
 * Fetch and display clipboard content
 * @param {Event} event - Click event
 */
function fetchClipboardContent(event) {
    event.preventDefault();
    
    // Get the URL from the data attribute or href
    const url = event.currentTarget.dataset.clipboardUrl || event.currentTarget.href;
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(content => {
            // Create modal to display content
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Clipboard Content</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <pre class="mb-0">${escapeHtml(content)}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Show the modal
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
            
            // Remove from DOM when hidden
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        })
        .catch(error => {
            console.error('Error fetching clipboard content:', error);
            showNotification('danger', 'Error loading clipboard content. Please try again.');
        });
}

/**
 * Take a screenshot via web interface
 */
function takeScreenshot() {
    const button = document.getElementById('takeScreenshotBtn');
    button.disabled = true;
    button.textContent = 'Taking Screenshot...';
    
    // Use WebRTC to capture screen if available
    if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        try {
            // Use the WebRTC function to take screenshot
            takeScreenshotFromBrowser();
        } catch (error) {
            console.error('Error with WebRTC screenshot:', error);
            // Fall back to server-side screenshot
            fallbackServerScreenshot();
        }
    } else {
        // WebRTC not supported, use server-side method
        fallbackServerScreenshot();
    }
    
    // Re-enable button (the WebRTC function handles re-enabling separately)
    setTimeout(() => {
        button.disabled = false;
        button.textContent = 'Take Screenshot';
    }, 3000);
}

/**
 * Fallback to server-side screenshot when WebRTC is not available
 */
function fallbackServerScreenshot() {
    fetch('/take-screenshot', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('success', data.message);
            
            // Show QR code popup modal for the new screenshot
            if (data.filepath) {
                setTimeout(() => {
                    // Generate QR code if available in the WebRTC library
                    if (typeof generateQRCodeForContent === 'function') {
                        generateQRCodeForContent(data.filepath, 'image');
                    } else {
                        // Fall back to modal
                        showNewContentModal('screenshot', data.filepath);
                    }
                }, 500);
            } else {
                // Reload the page to show the new screenshot if no filepath provided
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        } else {
            showNotification('danger', data.message);
        }
    })
    .catch(error => {
        console.error('Error taking screenshot:', error);
        showNotification('danger', 'Error taking screenshot. Please try again.');
    });
}

/**
 * Show a popup modal with download and QR code for a new screenshot or clipboard item
 * @param {string} contentType - Either 'screenshot' or 'clipboard'
 * @param {string} filepath - Path to the file
 */
function showNewContentModal(contentType, filepath) {
    // Get content label for display
    const contentLabel = contentType === 'screenshot' ? 'Screenshot' : 'Clipboard Content';
    const qrEndpoint = contentType === 'screenshot' ? 'qr/screenshot' : 'qr/clipboard';
    const downloadEndpoint = contentType === 'screenshot' ? 'screenshot' : 'clipboard';
    
    // Create modal HTML
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'newContentModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'newContentModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="newContentModalLabel">New ${contentLabel} Captured</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center">
                    <p>Your ${contentLabel.toLowerCase()} has been successfully captured!</p>
                    <div class="text-center my-3">
                        <img src="/${qrEndpoint}/${encodeURIComponent(filepath)}" alt="QR Code" class="img-fluid" style="max-width: 200px;">
                        <p class="mt-2">Scan QR code to view on mobile device</p>
                    </div>
                </div>
                <div class="modal-footer d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <a href="/${downloadEndpoint}/${encodeURIComponent(filepath)}" download class="btn btn-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download me-1" viewBox="0 0 16 16">
                            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                            <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                        </svg>
                        Download
                    </a>
                </div>
            </div>
        </div>
    `;
    
    // Add to DOM
    document.body.appendChild(modal);
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Remove from DOM when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        if (document.body.contains(modal)) {
            document.body.removeChild(modal);
        }
        // Reload the page to show the updated content list
        window.location.reload();
    });
}

/**
 * Sense clipboard via web interface
 */
function senseClipboard() {
    const button = document.getElementById('senseClipboardBtn');
    button.disabled = true;
    button.textContent = 'Sensing Clipboard...';
    
    // Try to use browser clipboard API (WebRTC alternative)
    if (navigator.clipboard && navigator.clipboard.readText) {
        try {
            // Use the WebRTC function
            senseClipboardFromBrowser();
        } catch (error) {
            console.error('Error with WebRTC clipboard:', error);
            // Fall back to server-side method
            fallbackServerClipboard();
        }
    } else {
        // Clipboard API not supported, use server-side method
        fallbackServerClipboard();
    }
    
    // Re-enable button (the WebRTC function handles re-enabling separately)
    setTimeout(() => {
        button.disabled = false;
        button.textContent = 'Sense Clipboard';
    }, 3000);
}

/**
 * Fallback to server-side clipboard sensing when browser API is not available
 */
function fallbackServerClipboard() {
    fetch('/sense-clipboard', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('success', data.message);
            
            // Show preview if available
            if (data.content_preview) {
                showNotification('info', `Clipboard content: ${data.content_preview}`);
            }
            
            // Show QR code popup modal for the new clipboard content
            if (data.filepath) {
                // Generate QR code
                if (typeof generateQRCodeForContent === 'function') {
                    generateQRCodeForContent(data.filepath, 'text');
                } else {
                    // Fall back to modal
                    showNewContentModal('clipboard', data.filepath);
                }
                
                // Add a reload button that user can click when ready
                setTimeout(() => {
                    showNotification('info', `
                        <div class="d-flex align-items-center justify-content-between">
                            <div>Clipboard content saved! QR code shown above.</div>
                            <button class="btn btn-sm btn-primary ms-3" 
                                onclick="window.location.reload()">Refresh Page</button>
                        </div>
                    `, 15000);
                }, 800);
            } else {
                // Reload the page to show the new clipboard content if no filepath provided
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        } else {
            showNotification('danger', data.message);
        }
    })
    .catch(error => {
        console.error('Error sensing clipboard:', error);
        showNotification('danger', 'Error sensing clipboard. Please try again.');
    });
}

/**
 * Execute command via web interface
 */
document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('commandForm');
    if (commandForm) {
        commandForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const formData = new FormData(commandForm);
            const submitButton = commandForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Executing...';
            
            fetch('/command', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('success', data.message);
                    // Close the modal
                    bootstrap.Modal.getInstance(document.getElementById('commandModal')).hide();
                    // Reset the form
                    commandForm.reset();
                    // Reload the page to show any new data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification('danger', data.message);
                }
            })
            .catch(error => {
                console.error('Error executing command:', error);
                showNotification('danger', 'Error executing command. Please try again.');
            })
            .finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = 'Execute';
            });
        });
    }
});

/**
 * Refresh OMIFI status without reloading the page
 */
function refreshStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            // Update UI based on status
            if (data.running) {
                updateActionButton('stop');
            } else {
                updateActionButton('start');
            }
            
            // Update microphone status if available
            const microphoneStatus = document.getElementById('microphoneStatus');
            if (microphoneStatus) {
                if (data.microphone_available) {
                    microphoneStatus.textContent = 'Available';
                    microphoneStatus.classList.remove('bg-warning', 'bg-danger');
                    microphoneStatus.classList.add('bg-success');
                } else {
                    microphoneStatus.textContent = 'Not Available';
                    microphoneStatus.classList.remove('bg-warning', 'bg-success');
                    microphoneStatus.classList.add('bg-danger');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

/**
 * Helper function to escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Attempt to reconnect to the microphone
 */
function reconnectMicrophone() {
    // Show attempting reconnection status
    const voiceStatus = document.getElementById('voiceStatus');
    if (voiceStatus) {
        voiceStatus.textContent = "Attempting to reconnect microphone...";
        voiceStatus.style.backgroundColor = "rgba(255, 193, 7, 0.2)"; // warning color
    }
    
    // Hide reconnect button while attempting
    const reconnectBtn = document.getElementById('microphoneReconnect');
    if (reconnectBtn) {
        reconnectBtn.style.display = 'none';
    }
    
    // Try to request microphone access again
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                // Success - microphone reconnected
                if (voiceStatus) {
                    voiceStatus.textContent = "Microphone reconnected successfully!";
                    voiceStatus.style.backgroundColor = "rgba(25, 135, 84, 0.2)"; // success color
                    
                    // After 3 seconds, update status to ready
                    setTimeout(function() {
                        voiceStatus.textContent = "Browser microphone ready. For continuous 'Hey OMIFI' wake word detection, download the desktop version.";
                    }, 3000);
                }
                
                // Show a success notification
                showNotification('success', 'Microphone reconnected successfully!');
                
                // Update microphone status badge in the UI
                const micStatus = document.getElementById('microphoneStatus');
                if (micStatus) {
                    micStatus.textContent = "Available";
                    micStatus.classList.remove('bg-warning', 'bg-danger');
                    micStatus.classList.add('bg-success');
                }
            })
            .catch(function(err) {
                console.error('Error reconnecting microphone:', err);
                
                if (voiceStatus) {
                    voiceStatus.textContent = "Failed to reconnect microphone. Please check permissions and try again.";
                    voiceStatus.style.backgroundColor = "rgba(220, 53, 69, 0.2)"; // danger color
                }
                
                // Show reconnect button again
                if (reconnectBtn) {
                    reconnectBtn.style.display = 'block';
                }
                
                // Show an error notification
                showNotification('danger', 'Failed to reconnect to microphone. Please check your browser permissions.');
            });
    } else {
        if (voiceStatus) {
            voiceStatus.textContent = "Your browser doesn't support microphone access. Please download the desktop app.";
            voiceStatus.style.backgroundColor = "rgba(220, 53, 69, 0.2)"; // danger color
        }
        
        // Show an error notification
        showNotification('danger', 'Your browser doesn\'t support microphone access. Please download the desktop app.');
    }
}