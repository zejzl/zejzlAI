/**
 * UI Module for ZEJZL.NET Dashboard
 * Handles DOM manipulation, user interactions, and UI state management
 */

class UIManager {
    constructor() {
        this.currentTab = 'overview';
        this.theme = 'dark';
        this.animations = new Map();
        this.tooltips = new Map();
        this.modals = new Map();

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTheme();
        this.setupTooltips();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.closest('.nav-tab').dataset.tab);
            });
        });

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Global search
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleGlobalSearch(e.target.value);
            });
        }

        // Notification close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('notification-close')) {
                this.closeNotification(e.target.closest('.notification'));
            }
        });

        // Modal close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || e.target.classList.contains('modal-backdrop')) {
                this.closeModal(e.target.closest('.modal')?.id);
            }
        });

        // ESC key handler
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    setupTheme() {
        const savedTheme = localStorage.getItem('zejzl-theme') || 'dark';
        this.setTheme(savedTheme);
    }

    setupTooltips() {
        // Initialize tooltips for elements with data-tooltip
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }

            // Ctrl/Cmd + 1-9: Switch to tab
            if (e.ctrlKey || e.metaKey) {
                const tabs = ['overview', 'analytics', 'multimodal', 'chat', 'monitoring', 'security', 'mcp'];
                const num = parseInt(e.key) - 1;
                if (num >= 0 && num < tabs.length) {
                    e.preventDefault();
                    this.switchTab(tabs[num]);
                }
            }

            // Ctrl/Cmd + Shift + R: Refresh data
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
                e.preventDefault();
                this.refreshAllData();
            }
        });
    }

    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });

        // Remove active class from all tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active', 'bg-blue-600', 'text-white');
            tab.classList.add('bg-gray-700', 'hover:bg-gray-600');
        });

        // Show selected tab
        const tabElement = document.getElementById(`${tabName}-tab`);
        if (tabElement) {
            tabElement.classList.remove('hidden');
        }

        // Set active tab
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active', 'bg-blue-600', 'text-white');
            activeTab.classList.remove('bg-gray-700', 'hover:bg-gray-600');
        }

        this.currentTab = tabName;

        // Trigger tab change event
        this.emit('tabChanged', { tabName });

        // Load tab-specific data if handler exists
        if (window.dashboard && typeof window.dashboard.loadTabData === 'function') {
            window.dashboard.loadTabData(tabName);
        }
    }

    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('zejzl-theme', theme);

        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.setAttribute('data-lucide',
                theme === 'dark' ? 'sun' : 'moon'
            );
            // Re-initialize Lucide icons
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }

        this.emit('themeChanged', { theme });
    }

    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    showTooltip(element, content) {
        this.hideTooltip(); // Hide any existing tooltip

        const tooltip = document.createElement('div');
        tooltip.className = 'fixed z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
        tooltip.textContent = content;
        tooltip.id = 'active-tooltip';

        document.body.appendChild(tooltip);

        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - 30}px`;
        tooltip.style.transform = 'translateX(-50%)';
    }

    hideTooltip() {
        const tooltip = document.getElementById('active-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    handleGlobalSearch(query) {
        // Emit search event for other modules to handle
        this.emit('globalSearch', { query });

        // Basic client-side search in current tab
        const tabContent = document.getElementById(`${this.currentTab}-tab`);
        if (!tabContent) return;

        const elements = tabContent.querySelectorAll('*');
        elements.forEach(element => {
            if (element.children.length === 0 && element.textContent) {
                const text = element.textContent.toLowerCase();
                const parent = element.closest('.searchable-item') || element.parentElement;

                if (query && text.includes(query.toLowerCase())) {
                    parent?.classList.remove('hidden');
                    element.innerHTML = element.textContent.replace(
                        new RegExp(query, 'gi'),
                        match => `<mark class="bg-yellow-200 text-black">${match}</mark>`
                    );
                } else {
                    parent?.classList.add('hidden');
                    element.innerHTML = element.textContent;
                }
            }
        });
    }

    showNotification(title, message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 notification ${
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' :
            type === 'success' ? 'bg-green-500' : 'bg-blue-500'
        } text-white max-w-sm transform translate-x-full transition-transform`;

        notification.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <h4 class="font-bold">${title}</h4>
                    <p class="text-sm mt-1">${message}</p>
                </div>
                <button class="ml-4 text-white hover:text-gray-200 notification-close text-xl leading-none">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.closeNotification(notification);
            }, duration);
        }

        return notification;
    }

    closeNotification(notification) {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }

    showModal(id, content, options = {}) {
        // Remove existing modal with same id
        this.closeModal(id);

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 modal';
        modal.id = id;

        modal.innerHTML = `
            <div class="absolute inset-0 bg-black bg-opacity-50 modal-backdrop"></div>
            <div class="relative mx-auto mt-20 max-w-lg bg-gray-800 rounded-lg shadow-xl">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold">${options.title || 'Modal'}</h3>
                        <button class="text-gray-400 hover:text-white modal-close">×</button>
                    </div>
                    <div class="modal-content">
                        ${content}
                    </div>
                    ${options.footer ? `<div class="mt-6 flex justify-end space-x-2">${options.footer}</div>` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.modals.set(id, modal);

        // Focus management
        const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }

        return modal;
    }

    closeModal(id) {
        const modal = this.modals.get(id);
        if (modal) {
            modal.remove();
            this.modals.delete(id);
        }
    }

    closeAllModals() {
        this.modals.forEach((modal, id) => {
            this.closeModal(id);
        });
    }

    showLoading(element, message = 'Loading...') {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'absolute inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center rounded-lg';
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p class="mt-2 text-sm text-gray-300">${message}</p>
            </div>
        `;

        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (element) {
            element.style.position = 'relative';
            element.appendChild(loadingOverlay);
            return loadingOverlay;
        }
    }

    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (element) {
            const overlay = element.querySelector('.bg-opacity-75');
            if (overlay) {
                overlay.remove();
            }
        }
    }

    animateValue(element, startValue, endValue, duration = 1000, formatter = (v) => v) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        const startTime = performance.now();
        const difference = endValue - startValue;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const easedProgress = 1 - Math.pow(1 - progress, 3);

            const currentValue = startValue + (difference * easedProgress);
            element.textContent = formatter(currentValue);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    refreshAllData() {
        this.showNotification('Refreshing', 'Updating all data...', 'info');

        // Trigger refresh in main dashboard
        if (window.dashboard && typeof window.dashboard.refreshAllData === 'function') {
            window.dashboard.refreshAllData();
        }

        // Emit refresh event
        this.emit('dataRefresh');
    }

    // Event system
    on(event, callback) {
        if (!this.eventListeners) {
            this.eventListeners = new Map();
        }

        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (!this.eventListeners) return;

        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (!this.eventListeners) return;

        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in UI event listener for ${event}:`, error);
                }
            });
        }
    }

    // Utility methods
    debounce(func, wait) {
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

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }

    formatNumber(num, decimals = 0) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    }
}

// Create and export singleton instance
const uiManager = new UIManager();

// Export for use in other modules
window.UIManager = UIManager;
window.uiManager = uiManager;