/**
 * Main JavaScript file for URL Indexing Checker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle URL input validation
    var urlTextarea = document.getElementById('urls');
    if (urlTextarea) {
        urlTextarea.addEventListener('input', function() {
            var lines = this.value.split('\n');
            if (lines.length > 100000) {
                this.setCustomValidity('Please enter no more than 100000 URLs at a time.');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // Handle form submission with loading state
    var checkForm = document.querySelector('form[action*="check"]');
    if (checkForm) {
        checkForm.addEventListener('submit', function(e) {
            var submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
                submitBtn.disabled = true;
            }
        });
    }
    
    // Initialize any charts that might be present on the page
    initializeCharts();
});

/**
 * Initializes any Chart.js charts that might be on the page
 */
function initializeCharts() {
    // This function is a placeholder for any chart initialization
    // Specific chart initialization is done in the respective template files
    // using page-specific <script> blocks
}

/**
 * Formats a date string to a more readable format
 * @param {string} dateStr - The date string to format
 * @return {string} Formatted date string
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Validates a URL string
 * @param {string} url - The URL to validate
 * @return {boolean} True if valid, false otherwise
 */
function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch (e) {
        return false;
    }
}
