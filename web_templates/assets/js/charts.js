// 图表渲染模块

// 全局图表配置
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#495057';

// 图表实例存储
const chartInstances = {};

/**
 * 创建资金曲线图
 * @param {Array} equityData - 资金曲线数据
 */
function createEquityChart(equityData) {
    const ctx = document.getElementById('equityChart');
    if (!ctx || !equityData || equityData.length === 0) {
        console.error('资金曲线数据无效或画布元素不存在');
        return;
    }

    // 销毁现有图表
    if (chartInstances.equityChart) {
        chartInstances.equityChart.destroy();
    }

    // 准备数据
    const labels = equityData.map(item => formatDate(item.date));
    const equityValues = equityData.map(item => item.equity);
    const drawdownValues = equityData.map(item => item.drawdown || 0);

    chartInstances.equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '资金曲线',
                    data: equityValues,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#3b82f6',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: '资金曲线变化趋势',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return '日期: ' + context[0].label;
                        },
                        label: function(context) {
                            return '资金: ' + formatCurrency(context.parsed.y);
                        },
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const drawdown = drawdownValues[index];
                            if (drawdown !== 0) {
                                // 回撤值已经是百分比形式
                                return '回撤: -' + Math.abs(drawdown).toFixed(2) + '%';
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '日期',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        callback: function(value, index, values) {
                            // 只显示部分标签以避免拥挤
                            if (index % Math.ceil(values.length / 8) === 0) {
                                return this.getLabelForValue(value);
                            }
                            return '';
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '资金 ($)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            elements: {
                point: {
                    hoverRadius: 8
                }
            }
        }
    });
}

/**
 * 创建回撤分析图
 * @param {Array} equityData - 资金曲线数据（包含回撤信息）
 */
function createDrawdownChart(equityData) {
    const ctx = document.getElementById('drawdownChart');
    if (!ctx || !equityData || equityData.length === 0) {
        console.error('回撤数据无效或画布元素不存在');
        return;
    }

    // 销毁现有图表
    if (chartInstances.drawdownChart) {
        chartInstances.drawdownChart.destroy();
    }

    // 准备数据
    const labels = equityData.map(item => formatDate(item.date));
    // 回撤值已经在后端转换为百分比，直接使用绝对值
    const drawdownValues = equityData.map(item => {
        const drawdown = item.drawdown || 0;
        // 回撤值已经是百分比形式，取绝对值显示
        return Math.abs(drawdown);
    });

    chartInstances.drawdownChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '回撤深度',
                    data: drawdownValues,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#ef4444',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: '回撤分析',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return '日期: ' + context[0].label;
                        },
                        label: function(context) {
                            return '回撤: -' + context.parsed.y.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '日期',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        callback: function(value, index, values) {
                            if (index % Math.ceil(values.length / 8) === 0) {
                                return this.getLabelForValue(value);
                            }
                            return '';
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '回撤深度 (%)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '-' + value.toFixed(1) + '%';
                        }
                    },
                    reverse: false
                }
            }
        }
    });
}

/**
 * 创建交易分布图
 * @param {Array} trades - 交易数据
 */
function createTradeDistributionChart(trades) {
    const ctx = document.getElementById('tradeDistributionChart');
    if (!ctx || !trades || trades.length === 0) {
        console.log('交易分布图画布不存在或无交易数据');
        return;
    }

    // 销毁现有图表
    if (chartInstances.tradeDistributionChart) {
        chartInstances.tradeDistributionChart.destroy();
    }

    // 统计买入和卖出交易
    const buyTrades = trades.filter(trade => trade.type === 'BUY').length;
    const sellTrades = trades.filter(trade => trade.type === 'SELL').length;

    chartInstances.tradeDistributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['买入', '卖出'],
            datasets: [{
                data: [buyTrades, sellTrades],
                backgroundColor: [
                    '#10b981',
                    '#ef4444'
                ],
                borderColor: [
                    '#ffffff',
                    '#ffffff'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '交易类型分布',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 创建月度收益热力图（简化版，使用柱状图）
 * @param {Array} equityData - 资金曲线数据
 */
function createMonthlyReturnsChart(equityData) {
    const ctx = document.getElementById('monthlyReturnsChart');
    if (!ctx || !equityData || equityData.length === 0) {
        console.log('月度收益图画布不存在或无数据');
        return;
    }

    // 销毁现有图表
    if (chartInstances.monthlyReturnsChart) {
        chartInstances.monthlyReturnsChart.destroy();
    }

    // 计算月度收益
    const monthlyReturns = calculateMonthlyReturns(equityData);
    const labels = monthlyReturns.map(item => item.month);
    const returns = monthlyReturns.map(item => item.return);

    chartInstances.monthlyReturnsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '月度收益率',
                data: returns,
                backgroundColor: returns.map(value => value >= 0 ? '#10b981' : '#ef4444'),
                borderColor: returns.map(value => value >= 0 ? '#059669' : '#dc2626'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '月度收益率分布',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: 20
                },
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return '收益率: ' + formatPercentage(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '月份',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '收益率 (%)',
                        font: {
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatPercentage(value);
                        }
                    }
                }
            }
        }
    });
}

/**
 * 计算月度收益率
 * @param {Array} equityData - 资金曲线数据
 * @returns {Array} 月度收益率数组
 */
function calculateMonthlyReturns(equityData) {
    const monthlyData = {};
    
    equityData.forEach(item => {
        const date = new Date(item.date);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        
        if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
                start: item.equity,
                end: item.equity,
                month: monthKey
            };
        } else {
            monthlyData[monthKey].end = item.equity;
        }
    });
    
    return Object.values(monthlyData).map(month => ({
        month: month.month,
        return: ((month.end - month.start) / month.start) * 100
    }));
}

/**
 * 初始化所有图表
 * @param {Object} data - 报告数据
 */
function initializeCharts(data) {
    try {
        // 创建资金曲线图
        if (data.equityCurve && data.equityCurve.length > 0) {
            createEquityChart(data.equityCurve);
        }
        
        // 创建回撤分析图
        if (data.drawdownData && data.drawdownData.length > 0) {
            createDrawdownChart(data.drawdownData);
        }
        
        // 创建交易分布图（如果有对应的画布）
        if (data.trades && data.trades.length > 0) {
            createTradeDistributionChart(data.trades);
        }
        
        // 创建月度收益图（如果有对应的画布）
        // if (data.equityCurve && data.equityCurve.length > 0) {
        //     createMonthlyReturnsChart(data.equityCurve);
        // }
        
        console.log('所有图表初始化完成');
    } catch (error) {
        console.error('图表初始化失败:', error);
        showToast('图表加载失败，请刷新页面重试', 'error');
    }
}

/**
 * 销毁所有图表实例
 */
function destroyAllCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    // 清空图表实例存储
    Object.keys(chartInstances).forEach(key => {
        delete chartInstances[key];
    });
}

/**
 * 响应式图表调整
 */
function resizeCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

// 窗口大小改变时调整图表
window.addEventListener('resize', debounce(resizeCharts, 300));

// 导出函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createEquityChart,
        createDrawdownChart,
        createTradeDistributionChart,
        createMonthlyReturnsChart,
        initializeCharts,
        destroyAllCharts,
        resizeCharts
    };
}