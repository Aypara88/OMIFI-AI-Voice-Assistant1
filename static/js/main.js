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
 */
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to DOM
    document.querySelector('.notifications-container').appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, 5000);
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
            // Reload the page to show the new screenshot
            setTimeout(() => {
                window.location.reload();
            }, 1500);
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
            // Reload the page to show the new clipboard content
            setTimeout(() => {
                window.location.reload();
            }, 1500);
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