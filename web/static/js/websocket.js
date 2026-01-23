/**
 * WebSocket Module for ZEJZL.NET Dashboard
 * Handles real-time communication with status indicators and broadcast mechanism
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectInterval = 5000; // 5 seconds
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000; // 30 seconds
        this.lastHeartbeat = null;

        this.eventListeners = new Map();
        this.statusIndicators = new Map();
        this.broadcastChannels = new Map();

        this.init();
    }

    init() {
        this.setupStatusIndicator();
        this.connect();
    }

    setupStatusIndicator() {
        // Create status indicator element if it doesn't exist
        if (!document.getElementById('websocket-status')) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'websocket-status';
            statusDiv.className = 'flex items-center space-x-2 text-sm';
            statusDiv.innerHTML = `
                <div class="w-3 h-3 rounded-full bg-gray-500" id="ws-status-dot"></div>
                <span id="ws-status-text" class="text-gray-400">Connecting...</span>
            `;
            document.querySelector('header .flex.items-center.space-x-4')?.appendChild(statusDiv);
        }

        this.statusIndicators.set('connection', {
            dot: document.getElementById('ws-status-dot'),
            text: document.getElementById('ws-status-text')
        });
    }

    updateStatusIndicator(status, message) {
        const indicator = this.statusIndicators.get('connection');
        if (!indicator) return;

        const { dot, text } = indicator;

        // Remove all status classes
        dot.classList.remove('bg-gray-500', 'bg-green-500', 'bg-red-500', 'bg-yellow-500', 'animate-pulse');

        // Update status
        switch (status) {
            case 'connecting':
                dot.classList.add('bg-yellow-500', 'animate-pulse');
                text.textContent = 'Connecting...';
                text.className = 'text-yellow-400';
                break;
            case 'connected':
                dot.classList.add('bg-green-500');
                text.textContent = 'Real-time Connected';
                text.className = 'text-green-400';
                break;
            case 'disconnected':
                dot.classList.add('bg-red-500');
                text.textContent = message || 'Disconnected';
                text.className = 'text-red-400';
                break;
            case 'reconnecting':
                dot.classList.add('bg-yellow-500', 'animate-pulse');
                text.textContent = `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`;
                text.className = 'text-yellow-400';
                break;
        }
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return; // Already connected
        }

        this.updateStatusIndicator('connecting', 'Connecting...');

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = (event) => this.onOpen(event);
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onclose = (event) => this.onClose(event);
            this.ws.onerror = (event) => this.onError(event);

        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        }
    }

    onOpen(event) {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateStatusIndicator('connected', 'Real-time Connected');

        // Start heartbeat
        this.startHeartbeat();

        // Send initial status
        this.send({
            type: 'client_connected',
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        });
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error, event.data);
        }
    }

    onClose(event) {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();

        if (event.code !== 1000) { // Not a normal closure
            this.updateStatusIndicator('disconnected', 'Connection lost');
            this.handleReconnect();
        } else {
            this.updateStatusIndicator('disconnected', 'Disconnected');
        }
    }

    onError(event) {
        console.error('WebSocket error:', event);
        this.updateStatusIndicator('disconnected', 'Connection error');
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.updateStatusIndicator('disconnected', 'Failed to reconnect');
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        this.updateStatusIndicator('reconnecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'heartbeat', timestamp: new Date().toISOString() });
                this.lastHeartbeat = Date.now();
            }
        }, 25000); // Send heartbeat every 25 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    handleMessage(data) {
        // Update last heartbeat on any message
        this.lastHeartbeat = Date.now();

        // Handle different message types
        switch (data.type) {
            case 'heartbeat_ack':
                // Heartbeat acknowledged
                break;

            case 'system_status':
                this.handleSystemStatus(data);
                break;

            case 'agent_update':
                this.handleAgentUpdate(data);
                break;

            case 'metrics_update':
                this.handleMetricsUpdate(data);
                break;

            case 'chat_message':
                this.handleChatMessage(data);
                break;

            case 'multimodal_update':
                this.handleMultimodalUpdate(data);
                break;

            case 'learning_update':
                this.handleLearningUpdate(data);
                break;

            case 'security_alert':
                this.handleSecurityAlert(data);
                break;

            case 'broadcast':
                this.handleBroadcast(data);
                break;

            default:
                // Emit custom event for unknown message types
                this.emit(data.type, data);
        }
    }

    handleSystemStatus(data) {
        // Update system status indicators
        this.emit('system_status', data);
    }

    handleAgentUpdate(data) {
        // Update agent status in UI
        this.emit('agent_update', data);
    }

    handleMetricsUpdate(data) {
        // Update metrics displays
        this.emit('metrics_update', data);
    }

    handleChatMessage(data) {
        // Handle real-time chat messages
        this.emit('chat_message', data);
    }

    handleMultimodalUpdate(data) {
        // Handle multimodal processing updates
        this.emit('multimodal_update', data);
    }

    handleLearningUpdate(data) {
        // Handle learning cycle updates
        this.emit('learning_update', data);
    }

    handleSecurityAlert(data) {
        // Handle security alerts
        this.emit('security_alert', data);
        this.showNotification('Security Alert', data.message, 'warning');
    }

    handleBroadcast(data) {
        // Handle broadcast messages to all connected clients
        const channel = data.channel || 'general';
        this.emit(`broadcast:${channel}`, data);
        this.showNotification('Broadcast', data.message, data.level || 'info');
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send:', data);
        }
    }

    // Event system for handling WebSocket messages
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // Broadcast system
    subscribe(channel, callback) {
        if (!this.broadcastChannels.has(channel)) {
            this.broadcastChannels.set(channel, []);
        }
        this.broadcastChannels.get(channel).push(callback);

        // Send subscription message to server
        this.send({
            type: 'subscribe',
            channel,
            timestamp: new Date().toISOString()
        });
    }

    unsubscribe(channel, callback) {
        const listeners = this.broadcastChannels.get(channel);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }

        // Send unsubscription message to server
        this.send({
            type: 'unsubscribe',
            channel,
            timestamp: new Date().toISOString()
        });
    }

    broadcast(channel, message, level = 'info') {
        this.send({
            type: 'broadcast',
            channel,
            message,
            level,
            timestamp: new Date().toISOString()
        });
    }

    // Utility methods
    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' :
            type === 'success' ? 'bg-green-500' : 'bg-blue-500'
        } text-white max-w-sm`;

        notification.innerHTML = `
            <div class="flex items-start justify-between">
                <div>
                    <h4 class="font-bold">${title}</h4>
                    <p class="text-sm">${message}</p>
                </div>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            lastHeartbeat: this.lastHeartbeat
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnecting');
        }
        this.stopHeartbeat();
        this.updateStatusIndicator('disconnected', 'Disconnected');
    }
}

// Create and export singleton instance
const wsManager = new WebSocketManager();

// Export for use in other modules
window.WebSocketManager = WebSocketManager;
window.wsManager = wsManager;