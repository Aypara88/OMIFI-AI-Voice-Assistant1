/**
 * OMIFI Dashboard JavaScript
 */

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set up periodic status refresh
    setInterval(refreshStatus, 10000); // Check status every 10 seconds
});

/**
 * Toggle OMIFI running status
 */
function toggleOmifiStatus() {
    const statusIndicator = document.querySelector('.status-indicator');
    const isRunning = statusIndicator.querySelector('.status-dot').classList.contains('active');
    
    // Get the appropriate URL based on current status
    const url = isRunning ? '/stop' : '/start';
    
    // Navigate to the URL
    window.location.href = url;
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
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-text');
            const statusButton = document.querySelector('.status-indicator a.btn');
            
            if (data.running) {
                statusDot.classList.remove('inactive');
                statusDot.classList.add('active');
                statusText.textContent = 'Running';
                
                if (statusButton) {
                    statusButton.textContent = 'Stop';
                    statusButton.classList.remove('btn-outline-success');
                    statusButton.classList.add('btn-outline-danger');
                    statusButton.href = '/stop';
                }
            } else {
                statusDot.classList.remove('active');
                statusDot.classList.add('inactive');
                statusText.textContent = 'Stopped';
                
                if (statusButton) {
                    statusButton.textContent = 'Start';
                    statusButton.classList.remove('btn-outline-danger');
                    statusButton.classList.add('btn-outline-success');
                    statusButton.href = '/start';
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