/**
 * API Module for ZEJZL.NET Dashboard
 * Handles all communication with the backend API
 */

class APIManager {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Generic API request method
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Analytics API methods
    async getUsageAnalytics(days = 7) {
        return this.get('/analytics/usage', { days });
    }

    async getPerformanceMetrics() {
        return this.get('/analytics/performance');
    }

    async getTokenUsage() {
        return this.get('/analytics/tokens');
    }

    async getCostAnalytics() {
        return this.get('/analytics/cost');
    }

    // Chat API methods
    async sendChatMessage(message, provider = 'grok', history = []) {
        return this.post('/chat', {
            message,
            provider,
            history,
            timestamp: new Date().toISOString()
        });
    }

    async getChatHistory(limit = 50) {
        return this.get('/chat/history', { limit });
    }

    async clearChatHistory() {
        return this.delete('/chat/history');
    }

    // Multi-modal API methods
    async uploadFile(file, modality = 'auto') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('modality', modality);

        return this.request('/multimodal/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }

    async processMultimodalContent(content, modality) {
        return this.post('/multimodal/process', {
            content,
            modality,
            timestamp: new Date().toISOString()
        });
    }

    async getMultimodalHistory(limit = 20) {
        return this.get('/multimodal/history', { limit });
    }

    // Agent API methods
    async getAgentStatus() {
        return this.get('/agents/status');
    }

    async getAgentMetrics(agentId) {
        return this.get(`/agents/${agentId}/metrics`);
    }

    async triggerAgentAction(agentId, action, params = {}) {
        return this.post(`/agents/${agentId}/action`, {
            action,
            params,
            timestamp: new Date().toISOString()
        });
    }

    // Magic system API methods
    async getMagicStatus() {
        return this.get('/magic/status');
    }

    async triggerRitual(ritualType, target = null) {
        return this.post('/magic/ritual', {
            ritual_type: ritualType,
            target,
            timestamp: new Date().toISOString()
        });
    }

    // Monitoring API methods
    async getSystemHealth() {
        return this.get('/health');
    }

    async getDetailedHealth() {
        return this.get('/health/detailed');
    }

    async getMetrics() {
        return this.get('/metrics');
    }

    async getDebugSnapshot() {
        return this.get('/debug/snapshot');
    }

    async getRecentLogs(lines = 50) {
        return this.get('/debug/logs', { lines });
    }

    async getPerformanceData() {
        return this.get('/debug/performance');
    }

    async setLogLevel(level) {
        return this.post('/debug/log-level', { level });
    }

    // Security API methods
    async getSecurityStatus() {
        return this.get('/security/status');
    }

    async runSecurityScan() {
        return this.post('/security/scan');
    }

    // MCP API methods
    async getMCPServers() {
        return this.get('/mcp/servers');
    }

    async getMCPTools(serverId = null) {
        const endpoint = serverId ? `/mcp/tools/${serverId}` : '/mcp/tools';
        return this.get(endpoint);
    }

    async callMCPTool(serverId, toolName, params = {}) {
        return this.post(`/mcp/call/${serverId}/${toolName}`, {
            params,
            timestamp: new Date().toISOString()
        });
    }

    // Learning API methods
    async triggerLearningCycle() {
        return this.post('/learning/cycle');
    }

    async getLearningInsights() {
        return this.get('/learning/insights');
    }

    async getLearningHistory(limit = 10) {
        return this.get('/learning/history', { limit });
    }

    // Utility methods
    async ping() {
        try {
            const start = Date.now();
            await this.get('/health');
            return { latency: Date.now() - start };
        } catch (error) {
            return { error: error.message };
        }
    }

    setAuthToken(token) {
        this.defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    removeAuthToken() {
        delete this.defaultHeaders['Authorization'];
    }
}

// Create and export singleton instance
const apiManager = new APIManager();

// Export for use in other modules
window.APIManager = APIManager;
window.apiManager = apiManager;