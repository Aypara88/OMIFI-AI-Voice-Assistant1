/**
 * OMIFI Dashboard JavaScript
 */

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize elements
    const toggleButton = document.getElementById('toggle-omifi');
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.querySelector('.status-indicator');
    const screenshotModal = document.getElementById('screenshotModal');
    const clipboardItems = document.querySelectorAll('.clipboard-item');
    
    // Set up event listeners
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleOmifiStatus);
    }
    
    // Set up screenshot modal
    if (screenshotModal) {
        screenshotModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const src = button.getAttribute('data-src');
            const modalImage = document.getElementById('modal-screenshot');
            if (modalImage) {
                modalImage.src = src;
            }
        });
    }
    
    // Set up clipboard items
    clipboardItems.forEach(item => {
        item.addEventListener('click', fetchClipboardContent);
    });
    
    // Start auto-refresh
    setInterval(refreshStatus, 5000);
});

/**
 * Toggle OMIFI running status
 */
function toggleOmifiStatus() {
    const toggleButton = document.getElementById('toggle-omifi');
    const isRunning = toggleButton.classList.contains('btn-danger');
    const endpoint = isRunning ? '/stop' : '/start';
    
    fetch(endpoint, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            refreshStatus();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

/**
 * Fetch and display clipboard content
 * @param {Event} event - Click event
 */
function fetchClipboardContent(event) {
    const clipboardItems = document.querySelectorAll('.clipboard-item');
    const filepath = this.getAttribute('data-filepath');
    
    // Remove active class from all items
    clipboardItems.forEach(i => i.classList.remove('active'));
    
    // Add active class to clicked item
    this.classList.add('active');
    
    // Fetch clipboard content
    fetch('/clipboard/' + filepath)
        .then(response => response.text())
        .then(content => {
            document.getElementById('clipboard-content').textContent = content;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('clipboard-content').textContent = 'Error loading content';
        });
}

/**
 * Refresh OMIFI status without reloading the page
 */
function refreshStatus() {
    const toggleButton = document.getElementById('toggle-omifi');
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.querySelector('.status-indicator');
    
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                statusText.textContent = 'OMIFI is running';
                statusIndicator.classList.remove('status-stopped');
                statusIndicator.classList.add('status-running');
                toggleButton.textContent = 'Stop OMIFI';
                toggleButton.classList.remove('btn-success');
                toggleButton.classList.add('btn-danger');
            } else {
                statusText.textContent = 'OMIFI is stopped';
                statusIndicator.classList.remove('status-running');
                statusIndicator.classList.add('status-stopped');
                toggleButton.textContent = 'Start OMIFI';
                toggleButton.classList.remove('btn-danger');
                toggleButton.classList.add('btn-success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}