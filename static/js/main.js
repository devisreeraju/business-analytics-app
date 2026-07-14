/**
 * AI Business Analytics Copilot Global JS
 */

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show/Hide Fullscreen Loading Spinner
function showLoading(message = "Processing...") {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const textEl = overlay.querySelector('h5');
        if (textEl) textEl.textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Show Premium Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast-custom`;
    
    // Determine color border and icon
    let borderCol = '#1E3A8A';
    let icon = '<i class="bi bi-info-circle-fill text-primary"></i>';
    
    if (type === 'success') {
        borderCol = '#22C55E';
        icon = '<i class="bi bi-check-circle-fill text-success"></i>';
    } else if (type === 'warning') {
        borderCol = '#F59E0B';
        icon = '<i class="bi bi-exclamation-triangle-fill text-warning"></i>';
    } else if (type === 'danger' || type === 'error') {
        borderCol = '#EF4444';
        icon = '<i class="bi bi-x-circle-fill text-danger"></i>';
    }
    
    toast.style.setProperty('--accent-color', borderCol);
    
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-3">
            ${icon}
            <span style="font-size: 0.875rem; font-weight: 500;">${message}</span>
        </div>
        <button type="button" class="btn-close" style="font-size: 0.75rem;" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 4.5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Update Theme Toggle Button Icons
function updateThemeToggleIcons(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    
    if (theme === 'dark') {
        btn.innerHTML = '<i class="bi bi-sun-fill text-warning"></i>';
        btn.setAttribute('title', 'Switch to Light Theme');
    } else {
        btn.innerHTML = '<i class="bi bi-moon-fill text-primary"></i>';
        btn.setAttribute('title', 'Switch to Dark Theme');
    }
}

// Toggle Theme on client & server
function toggleThemePreference() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update DOM
    document.documentElement.setAttribute('data-theme', newTheme);
    updateThemeToggleIcons(newTheme);
    
    // Save to user settings endpoint
    fetch('/settings/toggle-theme/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ theme: newTheme })
    })
    .then(response => {
        if (!response.ok) throw new Error("Theme save failed");
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast(`Switched to ${newTheme} theme`, 'success');
        }
    })
    .catch(err => {
        console.error("Theme toggle error:", err);
    });
}

// Handle Sidebar Toggling
document.addEventListener('DOMContentLoaded', () => {
    // Desktop Sidebar collapse
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
            
            // Save state in local storage to remember collapsed preference
            const isCollapsed = document.body.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed ? 'true' : 'false');
        });
        
        // Restore collapse state
        const savedCollapseState = localStorage.getItem('sidebar-collapsed');
        if (savedCollapseState === 'true') {
            document.body.classList.add('sidebar-collapsed');
        }
    }
    
    // Mobile Sidebar controls
    const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', () => {
            document.body.classList.add('sidebar-open');
        });
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            document.body.classList.remove('sidebar-open');
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // Set initial theme toggle button icon
    const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeToggleIcons(activeTheme);
});
