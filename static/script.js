// Professional Floorplan Genie JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    initializeFormValidation();
    initializeTooltips();
    initializeProgressTracking();
});

// File Upload Enhancement
function initializeFileUpload() {
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('file');
    
    if (!fileUploadArea || !fileInput) return;
    
    // Drag and drop functionality
    fileUploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        fileUploadArea.classList.add('dragover');
    });
    
    fileUploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');
    });
    
    fileUploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileDisplay(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            updateFileDisplay(e.target.files[0]);
        }
    });
}

function updateFileDisplay(file) {
    const placeholder = document.querySelector('.upload-placeholder');
    if (!placeholder) return;
    
    const fileSize = (file.size / (1024 * 1024)).toFixed(2);
    const fileType = file.name.split('.').pop().toUpperCase();
    
    placeholder.innerHTML = `
        <i class="fas fa-file-check" style="color: var(--success-color);"></i>
        <p><strong>${file.name}</strong></p>
        <small>${fileType} file • ${fileSize} MB</small>
        <div style="margin-top: 1rem;">
            <button type="button" class="btn btn-secondary" onclick="clearFile()">
                <i class="fas fa-times"></i> Change File
            </button>
        </div>
    `;
}

function clearFile() {
    const fileInput = document.getElementById('file');
    const placeholder = document.querySelector('.upload-placeholder');
    
    if (fileInput) fileInput.value = '';
    if (placeholder) {
        placeholder.innerHTML = `
            <i class="fas fa-file-upload"></i>
            <p>Drag & drop your CAD file here or click to browse</p>
            <small>Supports DXF, DWG, PDF files up to 64MB</small>
        `;
    }
}

// Form Validation
function initializeFormValidation() {
    const form = document.querySelector('.upload-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        
        showProcessingState();
    });
}

function validateForm() {
    const fileInput = document.getElementById('file');
    const islandsInput = document.getElementById('islands');
    const corridorWidthInput = document.getElementById('corridor_width');
    
    let isValid = true;
    
    // File validation
    if (!fileInput.files.length) {
        showError('Please select a CAD file to upload.');
        isValid = false;
    } else {
        const file = fileInput.files[0];
        const maxSize = 64 * 1024 * 1024; // 64MB
        const allowedTypes = ['dxf', 'dwg', 'pdf'];
        const fileType = file.name.split('.').pop().toLowerCase();
        
        if (file.size > maxSize) {
            showError('File size must be less than 64MB.');
            isValid = false;
        }
        
        if (!allowedTypes.includes(fileType)) {
            showError('Please upload a DXF, DWG, or PDF file.');
            isValid = false;
        }
    }
    
    // Islands validation
    if (islandsInput.value.trim()) {
        const islandsPattern = /^(\d+(\.\d+)?x\d+(\.\d+)?,?\s*)+$/;
        if (!islandsPattern.test(islandsInput.value.replace(/\s/g, ''))) {
            showError('Invalid îlot dimensions format. Use: width×height,width×height (e.g., 3x2,4x3)');
            isValid = false;
        }
    }
    
    // Corridor width validation
    const corridorWidth = parseFloat(corridorWidthInput.value);
    if (corridorWidth < 0.8 || corridorWidth > 3.0) {
        showError('Corridor width must be between 0.8m and 3.0m.');
        isValid = false;
    }
    
    return isValid;
}

function showError(message) {
    // Remove existing alerts
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    
    // Insert at top of main content
    const mainContent = document.querySelector('.main-content .container');
    if (mainContent) {
        mainContent.insertBefore(alert, mainContent.firstChild);
        alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function showProcessingState() {
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            Processing Floor Plan...
        `;
        submitButton.classList.add('loading');
    }
    
    // Show processing overlay
    showProcessingOverlay();
}

function showProcessingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'processingOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        color: white;
        font-family: 'Inter', sans-serif;
    `;
    
    overlay.innerHTML = `
        <div style="text-align: center; max-width: 500px; padding: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">
                <i class="fas fa-cogs fa-spin"></i>
            </div>
            <h2 style="margin-bottom: 1rem;">Processing Your Floor Plan</h2>
            <p style="margin-bottom: 2rem; opacity: 0.8;">
                Our advanced CAD analysis engine is working on your file...
            </p>
            <div class="processing-steps">
                <div class="step active" id="step1">
                    <i class="fas fa-file-import"></i> Parsing CAD File
                </div>
                <div class="step" id="step2">
                    <i class="fas fa-brain"></i> Processing Geometry
                </div>
                <div class="step" id="step3">
                    <i class="fas fa-chess-board"></i> Optimizing Layout
                </div>
                <div class="step" id="step4">
                    <i class="fas fa-palette"></i> Generating Visualization
                </div>
            </div>
        </div>
    `;
    
    // Add step styles
    const stepStyles = `
        <style>
            .processing-steps {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                margin-top: 2rem;
            }
            .step {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                opacity: 0.5;
                transition: all 0.3s;
            }
            .step.active {
                opacity: 1;
                background: rgba(37, 99, 235, 0.3);
            }
            .step.completed {
                opacity: 1;
                background: rgba(16, 185, 129, 0.3);
            }
            .step i {
                font-size: 1.2rem;
            }
        </style>
    `;
    
    document.head.insertAdjacentHTML('beforeend', stepStyles);
    document.body.appendChild(overlay);
    
    // Simulate processing steps
    simulateProcessingSteps();
}

function simulateProcessingSteps() {
    const steps = ['step1', 'step2', 'step3', 'step4'];
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep > 0) {
            const prevStep = document.getElementById(steps[currentStep - 1]);
            if (prevStep) {
                prevStep.classList.remove('active');
                prevStep.classList.add('completed');
            }
        }
        
        if (currentStep < steps.length) {
            const step = document.getElementById(steps[currentStep]);
            if (step) {
                step.classList.add('active');
            }
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 2000);
}

// Tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: var(--text-primary);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.875rem;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Progress Tracking
function initializeProgressTracking() {
    // Track form interactions for analytics
    const formElements = document.querySelectorAll('input, select, button');
    
    formElements.forEach(element => {
        element.addEventListener('change', function(e) {
            // Could send analytics data here
            console.log('Form interaction:', e.target.name, e.target.value);
        });
    });
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

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

// Export functions for global access
window.FloorplanGenie = {
    clearFile,
    showError,
    formatFileSize,
    debounce
};