// ZEJZL.NET Dashboard JavaScript

class DashboardManager {
    constructor() {
        this.currentTab = 'overview';
        this.charts = {};
        this.websocket = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupWebSocket();
        this.updateTimestamp();
        setInterval(() => this.updateTimestamp(), 1000);
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.closest('.nav-tab').dataset.tab);
            });
        });

        // Theme toggle
        document.getElementById('theme-toggle')?.addEventListener('click', () => {
            this.toggleTheme();
        });

        // File upload
        this.setupFileUpload();

        // Chat functionality
        this.setupChat();

        // Analysis
        document.getElementById('analyze-btn')?.addEventListener('click', () => {
            this.analyzeFile();
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
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');

        // Set active tab
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active', 'bg-blue-600', 'text-white');
        document.querySelector(`[data-tab="${tabName}"]`).classList.remove('bg-gray-700', 'hover:bg-gray-600');

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadInitialData() {
        await Promise.all([
            this.loadOverviewData(),
            this.loadAnalyticsData()
        ]);
    }

    async loadTabData(tabName) {
        switch(tabName) {
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'multimodal':
                await this.loadMultimodalData();
                break;
            case 'monitoring':
                await this.loadMonitoringData();
                break;
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch('/api/analytics/usage?days=7');
            const data = await response.json();

            if (data.success) {
                document.getElementById('total-requests').textContent = data.data.total_requests || 0;
                document.getElementById('total-tokens').textContent = (data.data.total_tokens || 0).toLocaleString();
                document.getElementById('total-cost').textContent = `$${data.data.total_cost_usd?.toFixed(4) || '0.0000'}`;
                document.getElementById('success-rate').textContent = `${(data.data.success_rate * 100)?.toFixed(1) || 0}%`;
            }
        } catch (error) {
            console.error('Failed to load overview data:', error);
        }
    }

    async loadAnalyticsData() {
        try {
            // Load usage analytics
            const usageResponse = await fetch('/api/analytics/usage?days=7');
            const usageData = await usageResponse.json();

            // Load cost analytics
            const costResponse = await fetch('/api/analytics/costs?days=30');
            const costData = await costResponse.json();

            if (usageData.success && costData.success) {
                this.renderUsageChart(usageData.data);
                this.renderCostChart(costData.data);
                this.renderProviderPerformance(usageData.data.provider_breakdown);
            }
        } catch (error) {
            console.error('Failed to load analytics data:', error);
        }
    }

    renderUsageChart(data) {
        const ctx = document.getElementById('usageChart');
        if (!ctx) return;

        const chartData = {
            labels: data.hourly_usage?.map(h => h.hour?.split(' ')[1] || h.hour) || [],
            datasets: [{
                label: 'Requests',
                data: data.hourly_usage?.map(h => h.requests) || [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4
            }, {
                label: 'Tokens',
                data: data.hourly_usage?.map(h => h.tokens) || [],
                borderColor: 'rgb(16, 185, 129)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        };

        if (this.charts.usageChart) {
            this.charts.usageChart.destroy();
        }

        this.charts.usageChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(156, 163, 175, 0.8)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(156, 163, 175, 0.8)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(156, 163, 175, 0.8)'
                        }
                    }
                }
            }
        });
    }

    renderCostChart(data) {
        const ctx = document.getElementById('costChart');
        if (!ctx) return;

        const chartData = {
            labels: ['Current Period', 'Projected Monthly', 'Avg Daily'],
            datasets: [{
                label: 'Cost (USD)',
                data: [
                    data.total_cost || 0,
                    data.projected_monthly_cost || 0,
                    data.avg_daily_cost || 0
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(16, 185, 129, 0.8)'
                ],
                borderColor: [
                    'rgb(239, 68, 68)',
                    'rgb(245, 158, 11)',
                    'rgb(16, 185, 129)'
                ],
                borderWidth: 1
            }]
        };

        if (this.charts.costChart) {
            this.charts.costChart.destroy();
        }

        this.charts.costChart = new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(156, 163, 175, 0.8)',
                            callback: function(value) {
                                return '$' + value.toFixed(4);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(156, 163, 175, 0.8)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(156, 163, 175, 0.8)'
                        }
                    }
                }
            }
        });
    }

    renderProviderPerformance(providerBreakdown) {
        const container = document.getElementById('provider-performance');
        if (!container || !providerBreakdown) return;

        container.innerHTML = '';

        Object.entries(providerBreakdown).forEach(([provider, data]) => {
            const card = document.createElement('div');
            card.className = 'bg-gray-700 rounded-lg p-4';
            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-white">${provider}</h4>
                    <span class="text-sm px-2 py-1 rounded ${data.success_rate > 0.8 ? 'bg-green-600' : data.success_rate > 0.6 ? 'bg-yellow-600' : 'bg-red-600'}">
                        ${(data.success_rate * 100).toFixed(1)}%
                    </span>
                </div>
                <div class="space-y-1 text-sm text-gray-400">
                    <div class="flex justify-between">
                        <span>Requests:</span>
                        <span>${data.requests}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Tokens:</span>
                        <span>${data.tokens?.toLocaleString()}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Cost:</span>
                        <span>$${data.cost_usd?.toFixed(4)}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Avg Response:</span>
                        <span>${data.avg_response_time?.toFixed(2)}s</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }

    async loadMultimodalData() {
        try {
            const response = await fetch('/api/multimodal/providers');
            const data = await response.json();

            if (data.success) {
                console.log('Multi-modal providers loaded:', data.providers);
                // Update provider dropdowns
                this.updateProviderDropdowns(data.providers);
            }
        } catch (error) {
            console.error('Failed to load multi-modal data:', error);
        }
    }

    updateProviderDropdowns(providers) {
        const providerSelects = ['analysis-provider-select', 'chat-provider'];
        providerSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                // Clear existing options except first
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }

                // Add provider options
                providers.forEach(provider => {
                    const option = document.createElement('option');
                    option.value = provider;
                    option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
                    select.appendChild(option);
                });
            }
        });
    }

    setupFileUpload() {
        const fileInput = document.getElementById('file-input');
        const filePreview = document.getElementById('file-preview');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');
        const removeFile = document.getElementById('remove-file');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.handleFileSelect(file);
                }
            });
        }

        if (removeFile) {
            removeFile.addEventListener('click', () => {
                fileInput.value = '';
                filePreview.classList.add('hidden');
            });
        }

        // Drag and drop
        const uploadArea = document.querySelector('.file-upload-area');
        if (uploadArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.add('dragover');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.remove('dragover');
                });
            });

            uploadArea.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    this.handleFileSelect(files[0]);
                }
            });
        }
    }

    handleFileSelect(file) {
        const filePreview = document.getElementById('file-preview');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');

        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = this.formatFileSize(file.size);

        if (filePreview) {
            filePreview.classList.remove('hidden');
        }

        // Store file for analysis
        this.selectedFile = file;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async analyzeFile() {
        if (!this.selectedFile) {
            alert('Please select a file first');
            return;
        }

        const analyzeBtn = document.getElementById('analyze-btn');
        const analyzeText = document.getElementById('analyze-text');

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeText.textContent = 'Analyzing...';

        try {
            const formData = new FormData();
            formData.append('file', this.selectedFile);

            const analysisType = document.getElementById('analysis-type').value;
            const provider = document.getElementById('ai-provider').value;
            const customQuery = document.getElementById('custom-query').value;

            // For now, use the API endpoints we created
            let endpoint = '';
            let requestData = {};

            if (this.selectedFile.type === 'application/pdf' || this.selectedFile.name.toLowerCase().endsWith('.pdf')) {
                // PDF analysis
                endpoint = '/api/multimodal/analyze-pdf';

                // Convert file to base64
                const base64 = await this.fileToBase64(this.selectedFile);
                requestData = {
                    pdf_data: base64,
                    query: customQuery || 'Analyze this PDF document',
                    provider: provider
                };
            } else if (this.selectedFile.type.startsWith('image/')) {
                // Image analysis
                endpoint = '/api/multimodal/analyze-image';

                // Convert file to base64
                const base64 = await this.fileToBase64(this.selectedFile);
                requestData = {
                    image_data: base64,
                    query: customQuery || 'Describe this image',
                    provider: provider
                };
            } else {
                // Generic document analysis
                endpoint = '/api/multimodal/analyze-document';
                const base64 = await this.fileToBase64(this.selectedFile);
                requestData = {
                    document_data: base64,
                    document_type: this.selectedFile.type,
                    query: customQuery || 'Analyze this document',
                    provider: provider
                };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                this.displayAnalysisResults(result);
            } else {
                throw new Error(result.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('Analysis error:', error);
            alert('Analysis failed: ' + error.message);
        } finally {
            // Reset button state
            analyzeBtn.disabled = false;
            analyzeText.textContent = 'Analyze File';
        }
    }

    async fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const result = reader.result;
                // Remove data URL prefix if present
                const base64 = result.split(',')[1] || result;
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    displayAnalysisResults(result) {
        const resultsContainer = document.getElementById('analysis-results');
        const resultsContent = document.getElementById('results-content');

        if (resultsContent) {
            resultsContent.innerHTML = `
                <div class="bg-gray-700 rounded-lg p-4 mb-4">
                    <h4 class="text-lg font-semibold mb-2 text-green-400">Analysis Complete</h4>
                    <div class="prose prose-invert max-w-none">
                        <p class="text-gray-300 leading-relaxed">${result.analysis || result.description || 'Analysis completed successfully'}</p>
                    </div>
                    ${result.page_count ? `<p class="text-sm text-gray-400 mt-2">Pages: ${result.page_count}</p>` : ''}
                    ${result.text_length ? `<p class="text-sm text-gray-400">Text length: ${result.text_length} characters</p>` : ''}
                </div>
            `;
        }

        if (resultsContainer) {
            resultsContainer.classList.remove('hidden');
        }
    }

    setupChat() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const clearBtn = document.getElementById('clear-chat');

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendChatMessage());
        }

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearChat());
        }
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addChatMessage(message, 'user');

        // Clear input
        chatInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const provider = document.getElementById('chat-provider').value;
            const mode = document.getElementById('chat-mode').value;
            const streaming = document.getElementById('streaming').checked;

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    provider: provider,
                    stream: streaming
                })
            });

            const result = await response.json();

            // Remove typing indicator
            this.hideTypingIndicator();

            if (result.success) {
                this.addChatMessage(result.response, 'assistant');
            } else {
                this.addChatMessage('Sorry, I encountered an error: ' + result.error, 'assistant', true);
            }

        } catch (error) {
            this.hideTypingIndicator();
            this.addChatMessage('Network error: ' + error.message, 'assistant', true);
        }
    }

    addChatMessage(content, sender, isError = false) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start space-x-3 chat-message ${isError ? 'error' : ''}`;

        const avatarColor = sender === 'user' ? 'bg-blue-600' : 'bg-green-600';
        const avatarIcon = sender === 'user' ? 'user' : 'bot';

        messageDiv.innerHTML = `
            <div class="w-8 h-8 ${avatarColor} rounded-full flex items-center justify-center flex-shrink-0">
                <i data-lucide="${avatarIcon}" class="w-4 h-4"></i>
            </div>
            <div class="bg-gray-700 rounded-lg p-3 max-w-xs lg:max-w-md">
                <p class="text-sm ${isError ? 'text-red-400' : 'text-white'}">${content}</p>
                <p class="text-xs text-gray-400 mt-1">${new Date().toLocaleTimeString()}</p>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Re-initialize Lucide icons for new elements
        lucide.createIcons();
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'flex items-start space-x-3 chat-message';
        indicator.innerHTML = `
            <div class="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i data-lucide="bot" class="w-4 h-4"></i>
            </div>
            <div class="bg-gray-700 rounded-lg p-3">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        `;

        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            // Keep only the initial greeting message
            const greeting = chatMessages.querySelector('.flex.items-start.space-x-3');
            chatMessages.innerHTML = '';
            if (greeting) {
                chatMessages.appendChild(greeting);
            }
        }
    }

    async loadMonitoringData() {
        try {
            // Load system health
            const healthResponse = await fetch('/api/health/detailed');
            const healthData = await healthResponse.json();

            if (healthData.success) {
                this.renderSystemHealth(healthData.data);
            }

            // Load recent logs (if available)
            this.loadSystemLogs();

        } catch (error) {
            console.error('Failed to load monitoring data:', error);
        }
    }

    renderSystemHealth(healthData) {
        const container = document.getElementById('system-health');
        if (!container) return;

        const healthItems = [
            { label: 'CPU Usage', value: healthData.cpu_percent || 0, unit: '%', status: 'healthy' },
            { label: 'Memory Usage', value: healthData.memory_percent || 0, unit: '%', status: 'healthy' },
            { label: 'Disk Usage', value: healthData.disk_percent || 0, unit: '%', status: 'warning' },
            { label: 'Active Connections', value: healthData.active_connections || 0, unit: '', status: 'healthy' },
            { label: 'Uptime', value: healthData.uptime_seconds || 0, unit: 's', status: 'healthy' },
            { label: 'Request Rate', value: healthData.requests_per_second || 0, unit: '/s', status: 'healthy' }
        ];

        container.innerHTML = healthItems.map(item => `
            <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <div class="flex items-center space-x-3">
                    <div class="w-3 h-3 rounded-full status-${item.status}"></div>
                    <span class="text-white font-medium">${item.label}</span>
                </div>
                <span class="text-gray-300">${item.value}${item.unit}</span>
            </div>
        `).join('');
    }

    async loadSystemLogs() {
        // This would connect to a logging endpoint
        const logsContainer = document.getElementById('system-logs');
        if (!logsContainer) return;

        // Mock logs for demonstration
        const mockLogs = [
            '[INFO] AI Framework initialized successfully',
            '[INFO] Multi-modal providers loaded: GPT-4 Vision, Gemini Vision',
            '[INFO] Cost tracking system active',
            '[INFO] Pantheon orchestration ready',
            '[DEBUG] Health check passed',
            '[INFO] Dashboard serving on http://localhost:8000'
        ];

        logsContainer.innerHTML = mockLogs.map(log =>
            `<div class="text-gray-300 font-mono text-sm py-1">${log}</div>`
        ).join('');
    }

    setupWebSocket() {
        // WebSocket connection for real-time updates
        try {
            this.websocket = new WebSocket('ws://localhost:8000/ws/live');

            this.websocket.onopen = () => {
                console.log('WebSocket connected');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after delay
                setTimeout(() => this.setupWebSocket(), 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.warn('WebSocket not available:', error);
        }
    }

    handleWebSocketMessage(data) {
        // Handle real-time updates from the server
        switch (data.type) {
            case 'health_update':
                this.updateHealthData(data.data);
                break;
            case 'new_request':
                this.updateRequestCount(data.data);
                break;
            case 'cost_update':
                this.updateCostData(data.data);
                break;
            case 'log_entry':
                this.addLogEntry(data.data);
                break;
        }
    }

    updateTimestamp() {
        const timestampElement = document.getElementById('timestamp');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleString();
        }
    }

    toggleTheme() {
        // Theme toggle functionality (expandable)
        document.body.classList.toggle('light-theme');
        const icon = document.querySelector('#theme-toggle i');
        if (icon) {
            icon.setAttribute('data-lucide', document.body.classList.contains('light-theme') ? 'sun' : 'moon');
            lucide.createIcons();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});