/**
 * Main JavaScript file for URL Indexing Checker
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize any charts if they exist
    initializeCharts();
    
    // File upload handling
    const fileInput = document.getElementById('url-file');
    const fileLabel = document.querySelector('.custom-file-upload');
    
    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                fileLabel.querySelector('p').textContent = `Selected file: ${fileName}`;
                fileLabel.querySelector('i').classList.remove('fa-upload');
                fileLabel.querySelector('i').classList.add('fa-check');
            } else {
                fileLabel.querySelector('p').textContent = 'Drag & drop a file or click to select';
                fileLabel.querySelector('i').classList.remove('fa-check');
                fileLabel.querySelector('i').classList.add('fa-upload');
            }
        });
    }
});

/**
 * Initializes any Chart.js charts that might be on the page
 */
function initializeCharts() {
    const indexingChart = document.getElementById('indexingChart');
    if (indexingChart) {
        const indexedCount = parseInt(indexingChart.getAttribute('data-indexed'));
        const notIndexedCount = parseInt(indexingChart.getAttribute('data-not-indexed'));
        
        new Chart(indexingChart, {
            type: 'doughnut',
            data: {
                labels: ['Indexed', 'Not Indexed'],
                datasets: [{
                    data: [indexedCount, notIndexedCount],
                    backgroundColor: ['#198754', '#dc3545'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
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
