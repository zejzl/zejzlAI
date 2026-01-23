/**
 * Charts Module for ZEJZL.NET Dashboard
 * Handles data visualization components using Chart.js
 */

class ChartsManager {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = new Map();
        this.themes = {
            dark: {
                backgroundColor: 'rgba(31, 41, 55, 0.8)',
                borderColor: 'rgba(75, 85, 99, 0.8)',
                gridColor: 'rgba(55, 65, 81, 0.5)',
                textColor: '#e5e7eb',
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#1e40af'
            },
            light: {
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                borderColor: 'rgba(209, 213, 219, 0.8)',
                gridColor: 'rgba(156, 163, 175, 0.5)',
                textColor: '#374151',
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#1e40af'
            }
        };

        this.currentTheme = 'dark';
        this.init();
    }

    init() {
        // Listen for theme changes
        if (window.uiManager) {
            window.uiManager.on('themeChanged', (data) => {
                this.setTheme(data.theme);
            });
        }

        // Setup Chart.js defaults
        this.setupChartDefaults();
    }

    setupChartDefaults() {
        const theme = this.themes[this.currentTheme];

        Chart.defaults.color = theme.textColor;
        Chart.defaults.borderColor = theme.gridColor;
        Chart.defaults.plugins.legend.labels.color = theme.textColor;
        Chart.defaults.plugins.tooltip.backgroundColor = theme.backgroundColor;
        Chart.defaults.plugins.tooltip.titleColor = theme.textColor;
        Chart.defaults.plugins.tooltip.bodyColor = theme.textColor;
    }

    setTheme(theme) {
        this.currentTheme = theme;
        this.setupChartDefaults();

        // Update all existing charts
        this.charts.forEach((chart, id) => {
            this.updateChartTheme(chart);
        });
    }

    updateChartTheme(chart) {
        const theme = this.themes[this.currentTheme];

        // Update chart background and colors
        if (chart.config.options.plugins?.legend?.labels) {
            chart.config.options.plugins.legend.labels.color = theme.textColor;
        }

        if (chart.config.options.plugins?.tooltip) {
            chart.config.options.plugins.tooltip.backgroundColor = theme.backgroundColor;
            chart.config.options.plugins.tooltip.titleColor = theme.textColor;
            chart.config.options.plugins.tooltip.bodyColor = theme.textColor;
        }

        chart.update();
    }

    createChart(canvasId, type, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        // Destroy existing chart if it exists
        this.destroyChart(canvasId);

        const theme = this.themes[this.currentTheme];
        const defaultOptions = this.getDefaultOptions(type, theme);

        const config = {
            type,
            data,
            options: { ...defaultOptions, ...options }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        this.chartConfigs.set(canvasId, config);

        return chart;
    }

    getDefaultOptions(type, theme) {
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: theme.textColor,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: theme.backgroundColor,
                    titleColor: theme.textColor,
                    bodyColor: theme.textColor,
                    borderColor: theme.borderColor,
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: true,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: {
                        color: theme.gridColor,
                        borderColor: theme.borderColor
                    },
                    ticks: {
                        color: theme.textColor,
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: theme.gridColor,
                        borderColor: theme.borderColor
                    },
                    ticks: {
                        color: theme.textColor,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        };

        // Type-specific options
        switch (type) {
            case 'line':
                return {
                    ...baseOptions,
                    elements: {
                        point: {
                            radius: 3,
                            hoverRadius: 6,
                            backgroundColor: theme.pointBackgroundColor,
                            borderColor: theme.pointBorderColor,
                            borderWidth: 2
                        },
                        line: {
                            borderWidth: 2,
                            tension: 0.1
                        }
                    }
                };

            case 'bar':
                return {
                    ...baseOptions,
                    scales: {
                        ...baseOptions.scales,
                        x: {
                            ...baseOptions.scales.x,
                            grid: {
                                display: false
                            }
                        }
                    }
                };

            case 'doughnut':
            case 'pie':
                return {
                    ...baseOptions,
                    plugins: {
                        ...baseOptions.plugins,
                        legend: {
                            ...baseOptions.plugins.legend,
                            position: 'right'
                        }
                    },
                    scales: {} // No scales for pie/doughnut
                };

            case 'radar':
                return {
                    ...baseOptions,
                    elements: {
                        point: {
                            radius: 3,
                            hoverRadius: 6,
                            backgroundColor: theme.pointBackgroundColor,
                            borderColor: theme.pointBorderColor,
                            borderWidth: 2
                        },
                        line: {
                            borderWidth: 2
                        }
                    },
                    scales: {
                        r: {
                            grid: {
                                color: theme.gridColor
                            },
                            angleLines: {
                                color: theme.gridColor
                            },
                            pointLabels: {
                                color: theme.textColor,
                                font: {
                                    size: 11
                                }
                            },
                            ticks: {
                                color: theme.textColor,
                                font: {
                                    size: 10
                                },
                                backdropColor: 'transparent'
                            }
                        }
                    }
                };

            default:
                return baseOptions;
        }
    }

    updateChart(canvasId, newData, newOptions = {}) {
        const chart = this.charts.get(canvasId);
        if (!chart) return false;

        // Update data
        if (newData) {
            chart.data = { ...chart.data, ...newData };
        }

        // Update options
        if (newOptions) {
            chart.options = { ...chart.options, ...newOptions };
        }

        chart.update();
        return true;
    }

    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
            this.chartConfigs.delete(canvasId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach((chart, id) => {
            this.destroyChart(id);
        });
    }

    // Pre-built chart creators
    createUsageChart(canvasId, data) {
        const chartData = {
            labels: data.map(d => new Date(d.timestamp).toLocaleDateString()),
            datasets: [{
                label: 'API Requests',
                data: data.map(d => d.requests),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true
            }, {
                label: 'Tokens Used',
                data: data.map(d => d.tokens),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                yAxisID: 'y1'
            }]
        };

        const options = {
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Requests'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Tokens'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        };

        return this.createChart(canvasId, 'line', chartData, options);
    }

    createCostChart(canvasId, data) {
        const chartData = {
            labels: data.map(d => new Date(d.timestamp).toLocaleDateString()),
            datasets: [{
                label: 'Daily Cost ($)',
                data: data.map(d => d.cost),
                backgroundColor: 'rgba(245, 158, 11, 0.8)',
                borderColor: '#f59e0b',
                borderWidth: 1
            }]
        };

        return this.createChart(canvasId, 'bar', chartData);
    }

    createAgentPerformanceChart(canvasId, data) {
        const chartData = {
            labels: Object.keys(data),
            datasets: [{
                label: 'Success Rate (%)',
                data: Object.values(data).map(agent => agent.success_rate * 100),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: '#10b981',
                borderWidth: 1
            }, {
                label: 'Average Response Time (s)',
                data: Object.values(data).map(agent => agent.avg_response_time),
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                yAxisID: 'y1'
            }]
        };

        const options = {
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Success Rate (%)'
                    },
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Response Time (s)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        };

        return this.createChart(canvasId, 'bar', chartData, options);
    }

    createProviderDistributionChart(canvasId, data) {
        const chartData = {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                    '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'
                ],
                borderWidth: 1
            }]
        };

        const options = {
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        };

        return this.createChart(canvasId, 'doughnut', chartData, options);
    }

    createSystemHealthChart(canvasId, data) {
        const chartData = {
            labels: ['CPU', 'Memory', 'Disk', 'Network'],
            datasets: [{
                label: 'Usage (%)',
                data: [data.cpu_percent, data.memory_percent, data.disk_percent, data.network_usage || 0],
                backgroundColor: [
                    data.cpu_percent > 80 ? '#ef4444' : '#10b981',
                    data.memory_percent > 80 ? '#ef4444' : '#10b981',
                    data.disk_percent > 80 ? '#ef4444' : '#10b981',
                    '#3b82f6'
                ],
                borderWidth: 1
            }]
        };

        return this.createChart(canvasId, 'bar', chartData, {
            scales: {
                y: {
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        });
    }

    createTimeSeriesChart(canvasId, data, title = 'Time Series Data') {
        const chartData = {
            labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
            datasets: [{
                label: title,
                data: data.map(d => d.value),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        };

        return this.createChart(canvasId, 'line', chartData);
    }

    createRealtimeChart(canvasId, maxPoints = 50) {
        const chartData = {
            labels: [],
            datasets: [{
                label: 'Real-time Data',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        };

        const chart = this.createChart(canvasId, 'line', chartData, {
            animation: {
                duration: 0 // Disable animations for real-time updates
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm'
                        }
                    }
                }
            }
        });

        // Add real-time update method
        chart.addPoint = (timestamp, value) => {
            const timeLabel = new Date(timestamp).toISOString();

            chart.data.labels.push(timeLabel);
            chart.data.datasets[0].data.push(value);

            // Keep only the last maxPoints
            if (chart.data.labels.length > maxPoints) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }

            chart.update('none'); // Update without animation
        };

        return chart;
    }

    // Utility methods
    exportChart(canvasId, format = 'png') {
        const chart = this.charts.get(canvasId);
        if (!chart) return null;

        return chart.toBase64Image();
    }

    resizeChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.resize();
        }
    }

    resizeAllCharts() {
        this.charts.forEach((chart, id) => {
            this.resizeChart(id);
        });
    }
}

// Create and export singleton instance
const chartsManager = new ChartsManager();

// Export for use in other modules
window.ChartsManager = ChartsManager;
window.chartsManager = chartsManager;