/* Main JavaScript - Healthcare Risk Prediction Web App */

// Utility Functions
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.body.insertAdjacentHTML('afterbegin', alertHtml);
}

function showSpinner(element) {
    element.innerHTML = '<div class="spinner"></div>';
    element.disabled = true;
}

function hideSpinner(element, text) {
    element.innerHTML = text;
    element.disabled = false;
}

// Format Number
function formatNumber(num, decimals = 2) {
    return Number(num).toFixed(decimals);
}

// Format Date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// API Request Helper
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Range Slider Value Update
function updateValue(element) {
    const displayId = element.id + '_Display';
    const displayElement = document.getElementById(displayId);
    if (displayElement) {
        displayElement.textContent = element.value;
    }
}

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const formData = new FormData(form);
    let isValid = true;

    for (let [key, value] of formData.entries()) {
        if (!value || value.trim() === '') {
            console.warn(`Field ${key} is empty`);
            isValid = false;
        }
    }

    return isValid;
}

// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Initialize Dark Mode from localStorage
function initializeDarkMode() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}

// Dropdown Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Initialize dark mode
    initializeDarkMode();
});

// Mobile Menu Handler
function handleMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse) {
                navbarCollapse.classList.toggle('show');
            }
        });
    }
}

// Load More Function
async function loadMore(url, containerId, pageParam = 'page') {
    try {
        const container = document.getElementById(containerId);
        const currentPage = parseInt(container.dataset.page || 1);
        const nextPage = currentPage + 1;

        const response = await fetch(`${url}?${pageParam}=${nextPage}`);
        const html = await response.text();

        container.innerHTML += html;
        container.dataset.page = nextPage;
    } catch (error) {
        showAlert('Error loading more items', 'danger');
    }
}

// Export Functions
function exportAsCSV(data, filename = 'export.csv') {
    const csv = convertToCSV(data);
    downloadFile(csv, filename, 'text/csv');
}

function exportAsPDF(url) {
    window.open(url, '_blank');
}

function convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const rows = data.map(obj => 
        headers.map(header => {
            const value = obj[header];
            return typeof value === 'string' && value.includes(',') 
                ? `"${value}"` 
                : value;
        }).join(',')
    );

    return [headers.join(','), ...rows].join('\n');
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Chart Helper
function createRiskChart(elementId, data) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Health Risk Score',
                data: data.values,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Fetch and Display Statistics
async function loadStatistics(containerId) {
    try {
        const response = await apiRequest('/api/statistics');
        const container = document.getElementById(containerId);
        
        if (container) {
            container.innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-box">
                            <strong>${response.total_predictions}</strong>
                            <span>Total Predictions</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box">
                            <strong>${formatNumber(response.average_risk_score)}</strong>
                            <span>Avg Risk Score</span>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle Function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize on Page Load
document.addEventListener('DOMContentLoaded', function() {
    handleMobileMenu();
    initializeDarkMode();
});

console.log('Healthcare Risk Prediction App Loaded');
