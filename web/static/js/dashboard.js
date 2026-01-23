// ZEJZL.NET Dashboard JavaScript

/**
 * Main Dashboard Manager - ZEJZL.NET Dashboard
 * Orchestrates all dashboard functionality using modular architecture
 */

class DashboardManager {
    constructor() {
        this.currentTab = 'overview';
        this.isLoading = false;
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;

        // Module references (will be set after initialization)
        this.api = null;
        this.ws = null;
        this.ui = null;
        this.charts = null;

        this.init();
    }

    async init() {
        // Wait for modules to be available
        await this.waitForModules();

        // Setup module references
        this.api = window.apiManager;
        this.ws = window.wsManager;
        this.ui = window.uiManager;
        this.charts = window.chartsManager;

        // Setup module integrations
        this.setupModuleIntegrations();

        // Initialize dashboard
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
        this.updateTimestamp();
        setInterval(() => this.updateTimestamp(), 1000);

        console.log('Dashboard initialized with modular architecture');
    }

    async waitForModules() {
        const requiredModules = ['apiManager', 'wsManager', 'uiManager', 'chartsManager'];
        const maxWait = 5000; // 5 seconds
        const startTime = Date.now();

        while (Date.now() - startTime < maxWait) {
            const loadedModules = requiredModules.filter(module => window[module]);
            if (loadedModules.length === requiredModules.length) {
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        console.warn('Some modules failed to load:', requiredModules.filter(module => !window[module]));
    }

    setupModuleIntegrations() {
        // WebSocket event handlers
        this.ws.on('system_status', (data) => this.handleSystemStatus(data));
        this.ws.on('agent_update', (data) => this.handleAgentUpdate(data));
        this.ws.on('metrics_update', (data) => this.handleMetricsUpdate(data));
        this.ws.on('chat_message', (data) => this.handleChatMessage(data));
        this.ws.on('multimodal_update', (data) => this.handleMultimodalUpdate(data));
        this.ws.on('learning_update', (data) => this.handleLearningUpdate(data));
        this.ws.on('security_alert', (data) => this.handleSecurityAlert(data));

        // UI event handlers
        this.ui.on('tabChanged', (data) => this.handleTabChange(data));
        this.ui.on('dataRefresh', () => this.refreshAllData());
        this.ui.on('globalSearch', (data) => this.handleGlobalSearch(data));
    }

    setupEventListeners() {
        // File upload
        this.setupFileUpload();

        // Chat functionality
        this.setupChat();

        // Analysis
        document.getElementById('analyze-btn')?.addEventListener('click', () => {
            this.analyzeFile();
        });

        // Learning cycle trigger
        document.getElementById('learning-cycle-btn')?.addEventListener('click', () => {
            this.triggerLearningCycle();
        });

        // MCP tool execution
        document.getElementById('mcp-execute-btn')?.addEventListener('click', () => {
            this.executeMCPTool();
        });

        // Security scan
        document.getElementById('security-scan-btn')?.addEventListener('click', () => {
            this.runSecurityScan();
        });

        // Export data
        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.exportData();
        });

        // Offline mode toggle
        document.getElementById('offline-toggle')?.addEventListener('click', () => {
            this.toggleOfflineMode();
        });

        // Cache management
        document.getElementById('clear-cache-btn')?.addEventListener('click', () => {
            this.clearCache();
        });

        document.getElementById('refresh-cache-btn')?.addEventListener('click', () => {
            this.refreshCacheStats();
        });
    }

    switchTab(tabName) {
        // Use UI module for tab switching
        this.ui.switchTab(tabName);
    }

    async loadInitialData() {
        try {
            this.ui.showLoading('#overview-tab', 'Loading dashboard data...');
            await Promise.all([
                this.loadOverviewData(),
                this.loadAnalyticsData(),
                this.loadRecentActivity(),
                this.loadOfflineStatus()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.ui.showNotification('Error', 'Failed to load dashboard data', 'error');
        } finally {
            this.ui.hideLoading('#overview-tab');
        }
    }

    async loadTabData(tabName) {
        try {
            const tabElement = `#${tabName}-tab`;
            this.ui.showLoading(tabElement, `Loading ${tabName} data...`);

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
                case 'security':
                    await this.loadSecurityData();
                    break;
                case 'mcp':
                    await this.loadMCPData();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${tabName} data:`, error);
            this.ui.showNotification('Error', `Failed to load ${tabName} data`, 'error');
        } finally {
            this.ui.hideLoading(`#${tabName}-tab`);
        }
    }

    async loadOverviewData() {
        try {
            const data = await this.api.getUsageAnalytics(7);

            if (data.success) {
                // Animate value changes
                this.ui.animateValue('#total-requests', 0, data.data.total_requests || 0, 1000, this.ui.formatNumber);
                this.ui.animateValue('#total-tokens', 0, data.data.total_tokens || 0, 1000, (v) => this.ui.formatNumber(v));
                this.ui.animateValue('#total-cost', 0, data.data.total_cost_usd || 0, 1000, (v) => `$${v.toFixed(4)}`);
                this.ui.animateValue('#success-rate', 0, (data.data.success_rate || 0) * 100, 1000, (v) => `${v.toFixed(1)}%`);
            }
        } catch (error) {
            console.error('Failed to load overview data:', error);
        }
    }

    async loadRecentActivity() {
        try {
            const response = await this.api.get('/activity/recent', { limit: 8 });
            if (response.success) {
                this.updateRecentActivity(response.data);
            } else {
                this.showDefaultActivity();
            }
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            this.showDefaultActivity();
        }
    }

    updateRecentActivity(activities) {
        const container = document.getElementById('recent-activity');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <i data-lucide="clock" class="w-12 h-12 mx-auto mb-4 opacity-50"></i>
                    <p>No recent activity</p>
                </div>
            `;
            return;
        }

        container.innerHTML = activities.map(activity => {
            const timeAgo = this.getTimeAgo(activity.timestamp);
            const iconClass = this.getActivityIcon(activity.icon);

            return `
                <div class="flex items-start space-x-3 p-3 rounded-lg bg-gray-700/50 hover:bg-gray-700/70 transition-colors">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                            <i data-lucide="${activity.icon}" class="w-4 h-4"></i>
                        </div>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between">
                            <p class="text-sm font-medium text-white truncate">
                                ${activity.title}
                            </p>
                            <p class="text-xs text-gray-400 ml-2">
                                ${timeAgo}
                            </p>
                        </div>
                        <p class="text-xs text-gray-300 mt-1">
                            ${activity.description}
                        </p>
                    </div>
                </div>
            `;
        }).join('');

        // Re-initialize Lucide icons for the new content
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    showDefaultActivity() {
        const container = document.getElementById('recent-activity');
        if (container) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <i data-lucide="activity" class="w-12 h-12 mx-auto mb-4 opacity-50"></i>
                    <p class="text-sm">Dashboard initialized</p>
                    <p class="text-xs text-gray-500 mt-1">Ready for activity</p>
                </div>
            `;
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const activityTime = new Date(timestamp);
        const diffMs = now - activityTime;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    getActivityIcon(iconType) {
        const iconMap = {
            'bot': 'bot',
            'zap': 'zap',
            'message-circle': 'message-circle',
            'brain': 'brain',
            'power': 'power',
            'check-circle': 'check-circle',
            'alert-triangle': 'alert-triangle',
            'user': 'user',
            'cpu': 'cpu',
            'database': 'database'
        };
        return iconMap[iconType] || 'activity';
    }

    async loadAnalyticsData() {
        try {
            const [usageData, performanceData, tokenData, costData] = await Promise.all([
                this.api.getUsageAnalytics(30),
                this.api.getPerformanceMetrics(),
                this.api.getTokenUsage(),
                this.api.getCostAnalytics()
            ]);

            // Create charts using Charts module
            if (usageData.success) {
                this.charts.createUsageChart('usage-chart', usageData.data.daily_usage || []);
            }

            if (costData.success) {
                this.charts.createCostChart('cost-chart', costData.data.daily_costs || []);
            }

            if (performanceData.success) {
                this.charts.createAgentPerformanceChart('performance-chart', performanceData.data.agent_metrics || {});
            }

            if (tokenData.success) {
                this.charts.createProviderDistributionChart('provider-chart', tokenData.data.provider_usage || {});
            }
        } catch (error) {
            console.error('Failed to load analytics data:', error);
        }
    }

    async loadMultimodalData() {
        try {
            const history = await this.api.getMultimodalHistory(20);
            if (history.success) {
                this.updateMultimodalHistory(history.data);
            }
        } catch (error) {
            console.error('Failed to load multimodal data:', error);
        }
    }

    async loadMonitoringData() {
        try {
            const [healthData, metricsData, debugData] = await Promise.all([
                this.api.getDetailedHealth(),
                this.api.getMetrics(),
                this.api.getPerformanceData()
            ]);

            if (healthData.success) {
                this.updateSystemHealth(healthData.data);
                this.charts.createSystemHealthChart('health-chart', healthData.data.system);
            }

            if (metricsData.success) {
                this.updateMetricsDisplay(metricsData.data);
            }

            if (debugData.success) {
                this.updateDebugInfo(debugData.data);
            }
        } catch (error) {
            console.error('Failed to load monitoring data:', error);
        }
    }

    async loadSecurityData() {
        try {
            const status = await this.api.getSecurityStatus();
            if (status.success) {
                this.updateSecurityStatus(status.data);
            }
        } catch (error) {
            console.error('Failed to load security data:', error);
        }
    }

    async loadMCPData() {
        try {
            const [servers, tools] = await Promise.all([
                this.api.getMCPServers(),
                this.api.getMCPTools()
            ]);

            if (servers.success) {
                this.updateMCPServers(servers.data);
            }

            if (tools.success) {
                this.updateMCPTools(tools.data);
            }
        } catch (error) {
            console.error('Failed to load MCP data:', error);
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
                <div class="text-sm ${isError ? 'text-red-400' : 'text-white'} message-content">${this.formatMessageContent(content)}</div>
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

    // Event handlers for real-time updates
    handleSystemStatus(data) {
        this.updateSystemHealth(data);
    }

    handleAgentUpdate(data) {
        // Update agent status displays
        this.ui.showNotification('Agent Update', `${data.agent}: ${data.status}`, 'info');
        this.loadOverviewData(); // Refresh overview stats
        this.loadRecentActivity(); // Refresh recent activity
    }

    handleMetricsUpdate(data) {
        this.updateMetricsDisplay(data);
    }

    handleChatMessage(data) {
        this.addChatMessage(data);
        this.loadRecentActivity(); // Refresh recent activity with new chat
    }

    handleMultimodalUpdate(data) {
        this.updateMultimodalHistory([data]);
        this.loadRecentActivity(); // Refresh recent activity with new multimodal processing
    }

    handleLearningUpdate(data) {
        this.ui.showNotification('Learning Update', data.message, data.level || 'info');
        if (data.insights) {
            this.displayLearningInsights(data.insights);
        }
        this.loadRecentActivity(); // Refresh recent activity with learning updates
    }

    handleSecurityAlert(data) {
        this.ui.showNotification('Security Alert', data.message, 'warning');
        this.loadSecurityData(); // Refresh security status
    }

    handleTabChange(data) {
        this.currentTab = data.tabName;
        // Tab-specific logic can be added here
    }

    handleGlobalSearch(data) {
        // Implement global search across current tab
        this.ui.handleGlobalSearch(data.query);
    }

    // User interaction methods
    async triggerLearningCycle() {
        try {
            this.ui.showLoading('#learning-cycle-btn', 'Running learning cycle...');
            const result = await this.api.triggerLearningCycle();

            if (result.success) {
                this.ui.showNotification('Success', 'Learning cycle completed', 'success');
                this.displayLearningInsights(result.data.insights || []);
            } else {
                this.ui.showNotification('Error', result.error || 'Learning cycle failed', 'error');
            }
        } catch (error) {
            console.error('Learning cycle error:', error);
            this.ui.showNotification('Error', 'Failed to trigger learning cycle', 'error');
        } finally {
            this.ui.hideLoading('#learning-cycle-btn');
        }
    }

    async executeMCPTool() {
        const serverId = document.getElementById('mcp-server-select')?.value;
        const toolName = document.getElementById('mcp-tool-select')?.value;
        const paramsInput = document.getElementById('mcp-params')?.value;

        if (!serverId || !toolName) {
            this.ui.showNotification('Error', 'Please select server and tool', 'error');
            return;
        }

        try {
            let params = {};
            if (paramsInput) {
                params = JSON.parse(paramsInput);
            }

            this.ui.showLoading('#mcp-execute-btn', 'Executing MCP tool...');
            const result = await this.api.callMCPTool(serverId, toolName, params);

            if (result.success) {
                this.ui.showModal('mcp-result', `
                    <h3 class="text-lg font-bold mb-4">MCP Tool Result</h3>
                    <pre class="bg-gray-100 p-4 rounded text-sm overflow-auto">${JSON.stringify(result.data, null, 2)}</pre>
                `);
            } else {
                this.ui.showNotification('Error', result.error || 'MCP tool execution failed', 'error');
            }
        } catch (error) {
            console.error('MCP tool execution error:', error);
            this.ui.showNotification('Error', 'Failed to execute MCP tool', 'error');
        } finally {
            this.ui.hideLoading('#mcp-execute-btn');
        }
    }

    async runSecurityScan() {
        try {
            this.ui.showLoading('#security-scan-btn', 'Running security scan...');
            const result = await this.api.runSecurityScan();

            if (result.success) {
                this.ui.showNotification('Success', 'Security scan completed', 'success');
                this.loadSecurityData(); // Refresh security status
            } else {
                this.ui.showNotification('Error', result.error || 'Security scan failed', 'error');
            }
        } catch (error) {
            console.error('Security scan error:', error);
            this.ui.showNotification('Error', 'Failed to run security scan', 'error');
        } finally {
            this.ui.hideLoading('#security-scan-btn');
        }
    }

    exportData() {
        const exportModal = `
            <h3 class="text-lg font-bold mb-4">Export Dashboard Data</h3>
            <div class="space-y-3">
                <label class="flex items-center">
                    <input type="checkbox" id="export-analytics" class="mr-2">
                    Analytics Data
                </label>
                <label class="flex items-center">
                    <input type="checkbox" id="export-metrics" class="mr-2">
                    System Metrics
                </label>
                <label class="flex items-center">
                    <input type="checkbox" id="export-logs" class="mr-2">
                    Debug Logs
                </label>
            </div>
            <div class="mt-6 flex justify-end space-x-2">
                <button class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500" onclick="uiManager.closeModal('export-modal')">Cancel</button>
                <button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500" onclick="dashboardManager.doExport()">Export</button>
            </div>
        `;
        this.ui.showModal('export-modal', exportModal);
    }

    async doExport() {
        const options = {
            analytics: document.getElementById('export-analytics')?.checked,
            metrics: document.getElementById('export-metrics')?.checked,
            logs: document.getElementById('export-logs')?.checked
        };

        this.ui.closeModal('export-modal');

        try {
            const exportData = {};

            if (options.analytics) {
                exportData.analytics = await this.api.getUsageAnalytics(30);
            }

            if (options.metrics) {
                exportData.metrics = await this.api.getMetrics();
            }

            if (options.logs) {
                exportData.logs = await this.api.getRecentLogs(100);
            }

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `zejzl-dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.ui.showNotification('Success', 'Data exported successfully', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.ui.showNotification('Error', 'Failed to export data', 'error');
        }
    }

    refreshAllData() {
        this.loadInitialData();
        this.loadTabData(this.currentTab);
        // Recent activity is already included in loadInitialData
    }

    startAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                this.refreshAllData();
            }, 30000); // Refresh every 30 seconds

            // Also refresh recent activity more frequently
            this.activityRefreshInterval = setInterval(() => {
                this.loadRecentActivity();
            }, 10000); // Refresh every 10 seconds
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.activityRefreshInterval) {
            clearInterval(this.activityRefreshInterval);
            this.activityRefreshInterval = null;
        }
    }

    // UI Update Methods
    updateSystemHealth(data) {
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            const status = data.status || 'unknown';
            statusElement.className = `px-2 py-1 rounded text-xs font-medium ${
                status === 'healthy' ? 'bg-green-100 text-green-800' :
                status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
            }`;
            statusElement.textContent = status.toUpperCase();
        }
    }

    updateMetricsDisplay(data) {
        // Update metrics in monitoring tab
        Object.entries(data).forEach(([key, value]) => {
            const element = document.getElementById(`metric-${key}`);
            if (element) {
                element.textContent = typeof value === 'number' ? this.ui.formatNumber(value) : value;
            }
        });
    }

    updateDebugInfo(data) {
        const logContainer = document.getElementById('debug-logs');
        if (logContainer && data.logs) {
            logContainer.innerHTML = data.logs.map(log =>
                `<div class="text-xs font-mono bg-gray-100 p-2 rounded mb-1">${log}</div>`
            ).join('');
        }
    }

    updateSecurityStatus(data) {
        const statusElement = document.getElementById('security-status');
        if (statusElement) {
            const status = data.status || 'unknown';
            statusElement.className = `px-2 py-1 rounded text-xs font-medium ${
                status === 'secure' ? 'bg-green-100 text-green-800' :
                status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
            }`;
            statusElement.textContent = status.toUpperCase();
        }
    }

    updateMCPServers(data) {
        const container = document.getElementById('mcp-servers');
        if (container) {
            container.innerHTML = data.servers?.map(server =>
                `<div class="bg-gray-50 p-3 rounded">
                    <h4 class="font-medium">${server.name}</h4>
                    <p class="text-sm text-gray-600">${server.description}</p>
                    <span class="text-xs ${server.connected ? 'text-green-600' : 'text-red-600'}">
                        ${server.connected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>`
            ).join('') || '<p class="text-gray-500">No MCP servers available</p>';
        }
    }

    updateMCPTools(data) {
        const container = document.getElementById('mcp-tools');
        if (container) {
            container.innerHTML = data.tools?.map(tool =>
                `<div class="bg-gray-50 p-3 rounded">
                    <h4 class="font-medium">${tool.name}</h4>
                    <p class="text-sm text-gray-600">${tool.description}</p>
                </div>`
            ).join('') || '<p class="text-gray-500">No MCP tools available</p>';
        }
    }

    updateMultimodalHistory(history) {
        const container = document.getElementById('multimodal-history');
        if (container) {
            container.innerHTML = history.map(item =>
                `<div class="bg-gray-50 p-3 rounded mb-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="font-medium">${item.modality}</span>
                            <span class="text-sm text-gray-500 ml-2">${new Date(item.timestamp).toLocaleString()}</span>
                        </div>
                        <span class="text-xs ${item.status === 'processed' ? 'text-green-600' : 'text-yellow-600'}">
                            ${item.status}
                        </span>
                    </div>
                    ${item.result ? `<p class="text-sm mt-1">${item.result}</p>` : ''}
                </div>`
            ).join('');
        }
    }

    addChatMessage(message) {
        const container = document.getElementById('chat-messages');
        if (container) {
            const messageElement = document.createElement('div');
            messageElement.className = `p-3 rounded mb-2 ${message.sender === 'user' ? 'bg-blue-100 ml-12' : 'bg-gray-100 mr-12'}`;
            messageElement.innerHTML = `
                <div class="flex justify-between items-start mb-1">
                    <span class="font-medium text-sm">${message.sender}</span>
                    <span class="text-xs text-gray-500">${new Date(message.timestamp).toLocaleString()}</span>
                </div>
                <div class="text-sm message-content">${this.formatMessageContent(message.content)}</div>
            `;
            container.appendChild(messageElement);
            container.scrollTop = container.scrollHeight;
        }
    }

    formatMessageContent(content) {
        if (!content) return '';

        // Handle markdown-like formatting
        let formatted = content
            // Bold text **text**
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text *text*
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Newlines to <br>
            .replace(/\n/g, '<br>')
            // Headers
            .replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold mt-2 mb-1">$1</h3>')
            .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold mt-3 mb-2">$1</h2>')
            .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-4 mb-3">$1</h1>')
            // Bullet points
            .replace(/^- (.*$)/gm, '<li class="ml-4">• $1</li>')
            // Links [text](url)
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-600 hover:underline">$1</a>')
            // Code blocks ```code```
            .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-200 p-2 rounded mt-1 mb-1 overflow-x-auto"><code>$1</code></pre>')
            // Inline code `code`
            .replace(/`([^`]+)`/g, '<code class="bg-gray-200 px-1 rounded">$1</code>');

        // Handle common emojis (basic ones)
        const emojiMap = {
            '✨': '✨',
            '🛡️': '🛡️',
            '💪': '💪',
            '⚡': '⚡',
            '🔮': '🔮',
            '❌': '❌',
            '✅': '✅',
            '🔥': '🔥',
            '🌟': '🌟',
            '💡': '💡',
            '🚀': '🚀',
            '🎉': '🎉',
            '⚠️': '⚠️',
            'ℹ️': 'ℹ️',
            '🔔': '🔔',
            '🔧': '🔧'
        };

        // Replace emoji codes with actual emojis
        Object.keys(emojiMap).forEach(code => {
            formatted = formatted.replace(new RegExp(code, 'g'), emojiMap[code]);
        });

        return formatted;
    }

    displayLearningInsights(insights) {
        const container = document.getElementById('learning-insights');
        if (container) {
            container.innerHTML = insights.map(insight =>
                `<div class="bg-blue-50 border-l-4 border-blue-400 p-3 mb-2">
                    <div class="flex items-start">
                        <div class="flex-1">
                            <h4 class="font-medium text-blue-800">${insight.type}</h4>
                            <p class="text-sm text-blue-700">${insight.description}</p>
                        </div>
                        ${insight.confidence > 0.8 ?
                            '<span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">High Confidence</span>' :
                            '<span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Medium Confidence</span>'
                        }
                    </div>
                </div>`
            ).join('');
        }
    }

    // File Upload and Chat Functionality
    setupFileUpload() {
        const fileInput = document.getElementById('file-input');
        const dropZone = document.getElementById('file-drop-zone');

        if (fileInput && dropZone) {
            // Drag and drop
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, this.preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => dropZone.classList.add('bg-blue-50', 'border-blue-300'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => dropZone.classList.remove('bg-blue-50', 'border-blue-300'), false);
            });

            dropZone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                this.handleFiles(files);
            });

            // File input change
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFiles(files) {
        [...files].forEach(file => {
            this.uploadFile(file);
        });
    }

    async uploadFile(file) {
        try {
            this.ui.showLoading('#file-drop-zone', 'Uploading file...');
            const result = await this.api.uploadFile(file);

            if (result.success) {
                this.ui.showNotification('Success', 'File uploaded successfully', 'success');
                this.loadMultimodalData(); // Refresh multimodal history
            } else {
                this.ui.showNotification('Error', result.error || 'File upload failed', 'error');
            }
        } catch (error) {
            console.error('File upload error:', error);
            this.ui.showNotification('Error', 'Failed to upload file', 'error');
        } finally {
            this.ui.hideLoading('#file-drop-zone');
        }
    }

    async analyzeFile() {
        const file = document.getElementById('file-input')?.files[0];
        if (!file) {
            this.ui.showNotification('Error', 'Please select a file first', 'error');
            return;
        }

        try {
            this.ui.showLoading('#analyze-btn', 'Analyzing file...');
            const result = await this.api.processMultimodalContent(file, 'auto');

            if (result.success) {
                this.ui.showModal('analysis-result', `
                    <h3 class="text-lg font-bold mb-4">File Analysis Result</h3>
                    <pre class="bg-gray-100 p-4 rounded text-sm overflow-auto">${JSON.stringify(result.data, null, 2)}</pre>
                `);
            } else {
                this.ui.showNotification('Error', result.error || 'Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.ui.showNotification('Error', 'Failed to analyze file', 'error');
        } finally {
            this.ui.hideLoading('#analyze-btn');
        }
    }

    setupChat() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-chat-btn');

        if (chatInput && sendBtn) {
            const sendMessage = () => {
                const message = chatInput.value.trim();
                if (message) {
                    this.sendChatMessage(message);
                    chatInput.value = '';
                }
            };

            sendBtn.addEventListener('click', sendMessage);
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }
    }

    async sendChatMessage(message) {
        try {
            const provider = document.getElementById('chat-provider-select')?.value || 'grok';

            // Add user message to chat
            this.addChatMessage({
                sender: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });

            // Send to API
            const result = await this.api.sendChatMessage(message, provider);

            if (result.success) {
                this.addChatMessage({
                    sender: 'assistant',
                    content: result.data.response,
                    timestamp: new Date().toISOString()
                });
            } else {
                this.ui.showNotification('Error', result.error || 'Failed to send message', 'error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.ui.showNotification('Error', 'Failed to send chat message', 'error');
        }
    }

    // Offline Mode Methods
    async toggleOfflineMode() {
        try {
            const toggle = document.getElementById('offline-toggle');
            const dot = document.getElementById('offline-toggle-dot');
            const status = document.getElementById('offline-status');

            if (!toggle || !dot || !status) return;

            const isCurrentlyEnabled = toggle.classList.contains('bg-green-600');
            const newState = !isCurrentlyEnabled;

            this.ui.showLoading('#offline-toggle', 'Updating offline mode...');

            const response = await this.api.post('/offline/toggle', { enabled: newState });

            if (response.success) {
                this.updateOfflineToggleUI(newState);
                this.ui.showNotification(
                    'Offline Mode',
                    `Offline mode ${newState ? 'enabled' : 'disabled'}`,
                    'success'
                );

                // Refresh data to show cache status
                await this.loadInitialData();
            } else {
                this.ui.showNotification('Error', response.error || 'Failed to toggle offline mode', 'error');
            }

        } catch (error) {
            console.error('Offline mode toggle error:', error);
            this.ui.showNotification('Error', 'Failed to toggle offline mode', 'error');
        } finally {
            this.ui.hideLoading('#offline-toggle');
        }
    }

    updateOfflineToggleUI(enabled) {
        const toggle = document.getElementById('offline-toggle');
        const dot = document.getElementById('offline-toggle-dot');
        const status = document.getElementById('offline-status');

        if (!toggle || !dot || !status) return;

        if (enabled) {
            toggle.classList.remove('bg-gray-600');
            toggle.classList.add('bg-green-600');
            dot.classList.remove('translate-x-1');
            dot.classList.add('translate-x-6');
            status.textContent = 'ON';
            status.className = 'text-sm text-green-400';
        } else {
            toggle.classList.remove('bg-green-600');
            toggle.classList.add('bg-gray-600');
            dot.classList.remove('translate-x-6');
            dot.classList.add('translate-x-1');
            status.textContent = 'OFF';
            status.className = 'text-sm text-gray-400';
        }
    }

    async loadOfflineStatus() {
        try {
            const response = await this.api.get('/offline/status');
            if (response.success) {
                const data = response.data;
                this.updateOfflineToggleUI(data.offline_mode_enabled);

                // Update cache stats if available
                if (data.cache_stats) {
                    this.updateCacheStats(data.cache_stats);
                }

                // Update connectivity status
                this.updateConnectivityStatus(data.connectivity_status, data.is_online);
            }
        } catch (error) {
            console.error('Failed to load offline status:', error);
        }
    }

    updateCacheStats(stats) {
        // Update cache statistics in the UI if elements exist
        const elements = {
            'cache-entries': stats.total_entries,
            'cache-size': `${stats.total_size_mb?.toFixed(1) || 0} MB`,
            'cache-usage': `${stats.usage_percent?.toFixed(1) || 0}%`,
            'cache-hits': stats.cache_stats?.hits || 0,
            'cache-misses': stats.cache_stats?.misses || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateConnectivityStatus(status, isOnline) {
        const indicator = document.getElementById('connectivity-indicator');
        if (indicator) {
            indicator.className = `px-2 py-1 rounded text-xs font-medium ${
                isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`;
            indicator.textContent = isOnline ? 'ONLINE' : 'OFFLINE';
        }
    }

    async clearCache() {
        if (!confirm('Are you sure you want to clear all cached responses? This action cannot be undone.')) {
            return;
        }

        try {
            this.ui.showLoading('#clear-cache-btn', 'Clearing cache...');
            const response = await fetch('/api/cache/clear', { method: 'DELETE' });

            if (response.ok) {
                this.ui.showNotification('Success', 'Cache cleared successfully', 'success');
                await this.loadOfflineStatus(); // Refresh stats
                await this.loadInitialData(); // Refresh all data
            } else {
                const error = await response.json();
                this.ui.showNotification('Error', error.error || 'Failed to clear cache', 'error');
            }

        } catch (error) {
            console.error('Clear cache error:', error);
            this.ui.showNotification('Error', 'Failed to clear cache', 'error');
        } finally {
            this.ui.hideLoading('#clear-cache-btn');
        }
    }

    async refreshCacheStats() {
        try {
            this.ui.showLoading('#refresh-cache-btn', 'Refreshing stats...');
            await this.loadOfflineStatus();
            this.ui.showNotification('Success', 'Cache statistics refreshed', 'success');

        } catch (error) {
            console.error('Refresh cache stats error:', error);
            this.ui.showNotification('Error', 'Failed to refresh cache statistics', 'error');
        } finally {
            this.ui.hideLoading('#refresh-cache-btn');
        }
    }

    updateTimestamp() {
        const now = new Date();
        const timestamp = document.getElementById('current-timestamp');
        if (timestamp) {
            timestamp.textContent = now.toLocaleString();
        }
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

// MCP Dashboard Functions
async function loadMCPData() {
    try {
        // Load MCP status
        const statusResponse = await fetch('/api/mcp/status');
        const statusData = await statusResponse.json();

        if (statusData.success) {
            updateMCPOveview(statusData);
        }

        // Load MCP servers
        const serversResponse = await fetch('/api/mcp/servers');
        const serversData = await serversResponse.json();

        if (serversData.success) {
            updateMCPServers(serversData.servers);
        }

        // Load MCP security
        const securityResponse = await fetch('/api/mcp/security');
        const securityData = await securityResponse.json();

        if (securityData.success) {
            updateMCPSecurity(securityData.security);
        }

    } catch (error) {
        console.error('Failed to load MCP data:', error);
    }
}

function updateMCPOveview(data) {
    const stats = data.stats;

    document.getElementById('mcp-active-servers').textContent = stats.connected_servers || 0;
    document.getElementById('mcp-total-tools').textContent = stats.total_tools || 0;
    document.getElementById('mcp-total-resources').textContent = stats.total_resources || 0;
    document.getElementById('mcp-total-requests').textContent = stats.total_requests || 0;
    document.getElementById('mcp-success-rate').textContent = `${(stats.success_rate * 100 || 0).toFixed(1)}%`;
    document.getElementById('mcp-avg-response').textContent = 'N/A'; // Would need to calculate from server metrics
}

function updateMCPServers(servers) {
    const container = document.getElementById('mcp-servers-list');
    if (!container) return;

    container.innerHTML = '';

    if (!servers || Object.keys(servers).length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-400 py-8">
                <i data-lucide="server-off" class="w-12 h-12 mx-auto mb-4 opacity-50"></i>
                <p>No MCP servers configured</p>
            </div>
        `;
        return;
    }

    for (const [name, server] of Object.entries(servers)) {
        const serverDiv = document.createElement('div');
        serverDiv.className = 'flex items-center justify-between p-3 bg-gray-700 rounded-lg';

        const status = server.status?.connected ? 'Connected' : 'Disconnected';
        const statusClass = server.status?.connected ? 'text-green-400' : 'text-red-400';

        serverDiv.innerHTML = `
            <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <div class="flex items-center space-x-3">
                    <i data-lucide="server" class="w-5 h-5 text-gray-400"></i>
                    <div>
                        <div class="font-medium">${name}</div>
                        <div class="text-sm text-gray-400">${server.config?.transport || 'Unknown'} • ${server.status?.tools?.length || 0} tools</div>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-sm ${statusClass}">${status}</span>
                    <button class="text-gray-400 hover:text-white" onclick="toggleMCPServer('${name}', ${!server.status?.connected})">
                        <i data-lucide="${server.status?.connected ? 'power-off' : 'power'}" class="w-4 h-4"></i>
                    </button>
                </div>
            </div>
        `;

        container.appendChild(serverDiv);
    }

    // Re-create icons for new elements
    lucide.createIcons();
}

function updateMCPSecurity(security) {
    const metrics = security.metrics || {};

    document.getElementById('mcp-auth-failures').textContent = metrics.auth_failures || 0;
    document.getElementById('mcp-rate-limited').textContent = metrics.rate_limited_requests || 0;
    document.getElementById('mcp-active-tokens').textContent = security.active_tokens || 0;
}

async function toggleMCPServer(serverName, connect) {
    try {
        const endpoint = connect ? `/api/mcp/server/connect/${serverName}` : `/api/mcp/server/disconnect/${serverName}`;
        const response = await fetch(endpoint, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showAlert(`Server ${connect ? 'connected' : 'disconnected'} successfully`, 'success');
            loadMCPData();
        } else {
            showAlert(`Failed to ${connect ? 'connect' : 'disconnect'} server: ${result.error}`, 'error');
        }
    } catch (error) {
        showAlert(`Server operation failed: ${error.message}`, 'error');
    }
}

async function showMCPTools() {
    try {
        const response = await fetch('/api/mcp/tools');
        const data = await response.json();

        if (data.success) {
            displayMCPItems(data.tools, 'tools');
        }
    } catch (error) {
        console.error('Failed to load MCP tools:', error);
    }
}

async function showMCPResources() {
    try {
        const response = await fetch('/api/mcp/resources');
        const data = await response.json();

        if (data.success) {
            displayMCPItems(data.resources, 'resources');
        }
    } catch (error) {
        console.error('Failed to load MCP resources:', error);
    }
}

function displayMCPItems(items, type) {
    const container = document.getElementById('mcp-tools-resources');
    if (!container) return;

    container.innerHTML = '';

    if (!items || items.length === 0) {
        container.innerHTML = `<p class="text-gray-400">No ${type} available</p>`;
        return;
    }

    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'p-2 bg-gray-700 rounded text-sm';

        if (type === 'tools') {
            itemDiv.innerHTML = `
                <div class="font-medium text-blue-400">${item.name}</div>
                <div class="text-gray-300 text-xs">${item.description}</div>
                <div class="text-gray-500 text-xs">Server: ${item.server}</div>
            `;
            itemDiv.onclick = () => selectMCPTool(item);
        } else {
            itemDiv.innerHTML = `
                <div class="font-medium text-purple-400">${item.name}</div>
                <div class="text-gray-300 text-xs">${item.description}</div>
                <div class="text-gray-500 text-xs">URI: ${item.uri}</div>
            `;
        }

        container.appendChild(itemDiv);
    });
}

function selectMCPTool(tool) {
    // Populate the tool execution form
    const serverSelect = document.getElementById('tool-server-select');
    const toolSelect = document.getElementById('tool-name-select');

    // Set server
    serverSelect.value = tool.server;

    // Add tool option if not exists
    let option = toolSelect.querySelector(`option[value="${tool.name}"]`);
    if (!option) {
        option = document.createElement('option');
        option.value = tool.name;
        option.textContent = tool.name;
        toolSelect.appendChild(option);
    }

    toolSelect.value = tool.name;

    // Switch to the tool execution section
    document.querySelector('[data-tab="mcp"]').click();
}

async function executeMCPTool() {
    const serverName = document.getElementById('tool-server-select').value;
    const toolName = document.getElementById('tool-name-select').value;
    const argsText = document.getElementById('tool-arguments').value;

    if (!serverName || !toolName) {
        showAlert('Please select both server and tool', 'error');
        return;
    }

    let arguments = {};
    if (argsText.trim()) {
        try {
            arguments = JSON.parse(argsText);
        } catch (e) {
            showAlert('Invalid JSON in arguments', 'error');
            return;
        }
    }

    try {
        const response = await fetch('/api/mcp/tool-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                server_name: serverName,
                tool_name: toolName,
                arguments: arguments
            })
        });

        const result = await response.json();
        const resultDiv = document.getElementById('tool-result');

        if (result.success) {
            resultDiv.className = 'mt-4 p-3 bg-green-900 border border-green-700 rounded-lg font-mono text-sm max-h-32 overflow-y-auto';
            resultDiv.innerHTML = `<pre class="text-green-300">${JSON.stringify(result.result, null, 2)}</pre>`;
        } else {
            resultDiv.className = 'mt-4 p-3 bg-red-900 border border-red-700 rounded-lg font-mono text-sm max-h-32 overflow-y-auto';
            resultDiv.innerHTML = `<pre class="text-red-300">Error: ${result.error}</pre>`;
        }

        resultDiv.classList.remove('hidden');
    } catch (error) {
        showAlert(`Tool execution failed: ${error.message}`, 'error');
    }
}

function clearToolForm() {
    document.getElementById('tool-server-select').value = '';
    document.getElementById('tool-name-select').value = '';
    document.getElementById('tool-arguments').value = '';
    document.getElementById('tool-result').classList.add('hidden');
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();

    // Load MCP data when MCP tab is activated
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            if (this.dataset.tab === 'mcp') {
                loadMCPData();
            }
        });
    });
});