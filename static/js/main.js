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
            
            // Show success notification and a button to view the screenshot
            if (data.filepath) {
                const notifContainer = document.createElement('div');
                notifContainer.className = 'alert alert-success alert-dismissible fade show mt-3';
                notifContainer.innerHTML = `
                    <strong>Success!</strong> Screenshot captured successfully.
                    <div class="mt-2">
                        <button class="btn btn-sm btn-primary view-screenshot-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye me-1" viewBox="0 0 16 16">
                                <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/>
                                <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
                            </svg>
                            View Screenshot
                        </button>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Insert notification at the top of the content area
                const contentArea = document.querySelector('.container main');
                if (contentArea) {
                    contentArea.insertBefore(notifContainer, contentArea.firstChild);
                    
                    // Add click event for the view button
                    const viewBtn = notifContainer.querySelector('.view-screenshot-btn');
                    if (viewBtn) {
                        viewBtn.addEventListener('click', function() {
                            showNewContentModal('screenshot', data.filepath);
                        });
                    }
                }
                
                // Auto-dismiss after 10 seconds
                setTimeout(() => {
                    if (document.body.contains(notifContainer)) {
                        notifContainer.remove();
                    }
                }, 10000);
                
                // No automatic page reload - we'll let the user view when ready
            } else {
                // If no filepath was provided, refresh the screenshots list via AJAX instead of reloading
                refreshScreenshotsList();
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
 * Refresh the screenshots list without reloading the page
 */
function refreshScreenshotsList() {
    const screenshotsList = document.querySelector('#screenshots-list');
    if (screenshotsList) {
        fetch('/status', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.screenshots && data.screenshots.length > 0) {
                // Clear and rebuild the screenshots list
                screenshotsList.innerHTML = '';
                data.screenshots.forEach(screenshot => {
                    const listItem = document.createElement('div');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    listItem.innerHTML = `
                        <div>
                            <strong>${screenshot.filename}</strong>
                            <div class="text-muted small">${screenshot.timestamp}</div>
                        </div>
                        <div>
                            <a href="/screenshot/${encodeURIComponent(screenshot.filepath)}" target="_blank" class="btn btn-sm btn-outline-primary me-1">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/>
                                    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
                                </svg>
                            </a>
                            <a href="/screenshot/${encodeURIComponent(screenshot.filepath)}" download class="btn btn-sm btn-outline-success">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                                    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                                    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                                </svg>
                            </a>
                        </div>
                    `;
                    screenshotsList.appendChild(listItem);
                });
            }
        })
        .catch(error => {
            console.error('Error refreshing screenshots list:', error);
        });
    }
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
        // No page reload - we'll update content lists via AJAX
        if (contentType === 'screenshot') {
            refreshScreenshotsList();
        } else if (contentType === 'clipboard') {
            refreshClipboardList();
        }
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
            
            // Only show clipboard info and options without automatic QR code
            if (data.filepath) {
                const notifContainer = document.createElement('div');
                notifContainer.className = 'alert alert-success alert-dismissible fade show mt-3';
                notifContainer.innerHTML = `
                    <strong>Success!</strong> Clipboard content captured successfully.
                    <div class="mt-2 d-flex gap-2">
                        <button class="btn btn-sm btn-primary view-clipboard-qr-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-qr-code me-1" viewBox="0 0 16 16">
                                <path d="M2 2h2v2H2V2Z"/>
                                <path d="M6 0v6H0V0h6ZM5 1H1v4h4V1ZM4 12H2v2h2v-2Z"/>
                                <path d="M6 10v6H0v-6h6Zm-5 1v4h4v-4H1Zm11-9h2v2h-2V2Z"/>
                                <path d="M10 0v6h6V0h-6Zm5 1v4h-4V1h4ZM8 1V0h1v2H8v2H7V1h1Zm0 5V4h1v2H8ZM6 8V7h1V6h1v2h1V7h5v1h-4v1H7V8H6Zm0 0v1H2V8H1v1H0V7h3v1h3Zm10 1h-1V7h1v2Zm-1 0h-1v2h2v-1h-1V9Zm-4 0h2v1h-1v1h-1V9Zm2 3v-1h-1v1h-1v1h1v-1h1Zm0 0h3v1h-2v1h-1v-1Zm-4-1v1h1v-2h-1v1Zm0 0H7v1H6v-1h2Z"/>
                            </svg>
                            Show QR Code
                        </button>
                        <a href="/clipboard/${encodeURIComponent(data.filepath)}" download class="btn btn-sm btn-success">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download me-1" viewBox="0 0 16 16">
                                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                            </svg>
                            Download
                        </a>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Insert notification at the top of the content area
                const contentArea = document.querySelector('.container main');
                if (contentArea) {
                    contentArea.insertBefore(notifContainer, contentArea.firstChild);
                    
                    // Add click event for the QR code button
                    const qrBtn = notifContainer.querySelector('.view-clipboard-qr-btn');
                    if (qrBtn) {
                        qrBtn.addEventListener('click', function() {
                            showNewContentModal('clipboard', data.filepath);
                        });
                    }
                }
                
                // Auto-dismiss after 10 seconds
                setTimeout(() => {
                    if (document.body.contains(notifContainer)) {
                        notifContainer.remove();
                    }
                }, 20000);
                
                // Refresh clipboard list without page reload
                refreshClipboardList();
            } else {
                // If no filepath was provided, refresh the clipboard list via AJAX
                refreshClipboardList();
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
 * Refresh the clipboard items list without reloading the page
 */
function refreshClipboardList() {
    const clipboardList = document.querySelector('#clipboard-list');
    if (clipboardList) {
        fetch('/status', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.clipboard_items && data.clipboard_items.length > 0) {
                // Clear and rebuild the clipboard list
                clipboardList.innerHTML = '';
                data.clipboard_items.forEach(item => {
                    const listItem = document.createElement('div');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    listItem.innerHTML = `
                        <div>
                            <strong>${item.filename || 'Clipboard Item'}</strong>
                            <div class="text-muted small">${item.timestamp}</div>
                            <div class="text-muted small">${item.content_preview || ''}</div>
                        </div>
                        <div>
                            <a href="/clipboard/${encodeURIComponent(item.filepath)}" target="_blank" class="btn btn-sm btn-outline-primary me-1">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/>
                                    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
                                </svg>
                            </a>
                            <a href="/clipboard/${encodeURIComponent(item.filepath)}" download class="btn btn-sm btn-outline-success">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                                    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                                    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                                </svg>
                            </a>
                            <button class="btn btn-sm btn-outline-secondary show-qr-btn" data-filepath="${item.filepath}">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-qr-code" viewBox="0 0 16 16">
                                    <path d="M2 2h2v2H2V2Z"/>
                                    <path d="M6 0v6H0V0h6ZM5 1H1v4h4V1ZM4 12H2v2h2v-2Z"/>
                                    <path d="M6 10v6H0v-6h6Zm-5 1v4h4v-4H1Zm11-9h2v2h-2V2Z"/>
                                    <path d="M10 0v6h6V0h-6Zm5 1v4h-4V1h4ZM8 1V0h1v2H8v2H7V1h1Zm0 5V4h1v2H8ZM6 8V7h1V6h1v2h1V7h5v1h-4v1H7V8H6Zm0 0v1H2V8H1v1H0V7h3v1h3Zm10 1h-1V7h1v2Zm-1 0h-1v2h2v-1h-1V9Zm-4 0h2v1h-1v1h-1V9Zm2 3v-1h-1v1h-1v1h1v-1h1Zm0 0h3v1h-2v1h-1v-1Zm-4-1v1h1v-2h-1v1Zm0 0H7v1H6v-1h2Z"/>
                                </svg>
                            </button>
                        </div>
                    `;
                    clipboardList.appendChild(listItem);
                });
                
                // Add event listeners for QR code buttons
                document.querySelectorAll('.show-qr-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const filepath = this.getAttribute('data-filepath');
                        if (filepath) {
                            showNewContentModal('clipboard', filepath);
                        }
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error refreshing clipboard list:', error);
        });
    }
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
                    // Refresh data without reloading the page
                    setTimeout(() => {
                        refreshScreenshotsList();
                        refreshClipboardList();
                    }, 1000);
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