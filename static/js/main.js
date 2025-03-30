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
    
    const url = event.currentTarget.href;
    
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
            alert('Error loading clipboard content. Please try again.');
        });
}

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