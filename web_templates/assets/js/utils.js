// 工具函数库

/**
 * 格式化数字为货币格式
 * @param {number} value - 数值
 * @param {string} currency - 货币符号，默认为 '$'
 * @returns {string} 格式化后的货币字符串
 */
function formatCurrency(value, currency = '$') {
    if (typeof value !== 'number') {
        return currency + '0.00';
    }
    return currency + value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * 格式化百分比
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数，默认为2
 * @returns {string} 格式化后的百分比字符串
 */
function formatPercentage(value, decimals = 2) {
    if (typeof value !== 'number') {
        return '0.00%';
    }
    return value.toFixed(decimals) + '%';
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式，默认为 'YYYY-MM-DD'
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    if (isNaN(d.getTime())) {
        return 'Invalid Date';
    }
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    switch (format) {
        case 'YYYY-MM-DD':
            return `${year}-${month}-${day}`;
        case 'YYYY-MM-DD HH:mm':
            return `${year}-${month}-${day} ${hours}:${minutes}`;
        case 'MM/DD/YYYY':
            return `${month}/${day}/${year}`;
        default:
            return `${year}-${month}-${day}`;
    }
}

/**
 * 格式化数字，添加千分位分隔符
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数，默认为2
 * @returns {string} 格式化后的数字字符串
 */
function formatNumber(value, decimals = 2) {
    if (typeof value !== 'number') {
        return '0';
    }
    return value.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * 计算两个日期之间的天数差
 * @param {string|Date} startDate - 开始日期
 * @param {string|Date} endDate - 结束日期
 * @returns {number} 天数差
 */
function daysBetween(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * 获取颜色值（根据正负值返回不同颜色）
 * @param {number} value - 数值
 * @param {string} positiveColor - 正值颜色，默认为绿色
 * @param {string} negativeColor - 负值颜色，默认为红色
 * @returns {string} 颜色值
 */
function getValueColor(value, positiveColor = '#10b981', negativeColor = '#ef4444') {
    return value >= 0 ? positiveColor : negativeColor;
}

/**
 * 生成随机颜色
 * @param {number} alpha - 透明度，默认为1
 * @returns {string} RGBA颜色值
 */
function generateRandomColor(alpha = 1) {
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
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

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间（毫秒）
 * @returns {Function} 节流后的函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 深拷贝对象
 * @param {Object} obj - 要拷贝的对象
 * @returns {Object} 拷贝后的对象
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

/**
 * 显示加载状态
 * @param {string} elementId - 元素ID
 * @param {boolean} show - 是否显示加载状态
 */
function showLoading(elementId, show = true) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (show) {
        element.innerHTML = '<div class="text-center"><div class="loading"></div><p class="mt-2">加载中...</p></div>';
    } else {
        // 这里应该恢复原始内容，具体实现根据需求调整
    }
}

/**
 * 显示提示消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型：success, error, warning, info
 * @param {number} duration - 显示时长（毫秒），默认3000
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建toast容器（如果不存在）
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toast = document.createElement('div');
    const bgColor = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    }[type] || '#3b82f6';
    
    toast.style.cssText = `
        background-color: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // 显示动画
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // 自动隐藏
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

/**
 * 导出数据为CSV文件
 * @param {Array} data - 数据数组
 * @param {string} filename - 文件名
 */
function exportToCSV(data, filename = 'data.csv') {
    if (!data || data.length === 0) {
        showToast('没有数据可导出', 'warning');
        return;
    }
    
    // 获取表头
    const headers = Object.keys(data[0]);
    
    // 构建CSV内容
    let csvContent = headers.join(',') + '\n';
    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header];
            // 如果值包含逗号或引号，需要用引号包围并转义
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                return '"' + value.replace(/"/g, '""') + '"';
            }
            return value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('数据导出成功', 'success');
    } else {
        showToast('浏览器不支持文件下载', 'error');
    }
}

/**
 * 检查是否为移动设备
 * @returns {boolean} 是否为移动设备
 */
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * 获取浏览器信息
 * @returns {Object} 浏览器信息对象
 */
function getBrowserInfo() {
    const ua = navigator.userAgent;
    let browser = 'Unknown';
    let version = 'Unknown';
    
    if (ua.indexOf('Chrome') > -1) {
        browser = 'Chrome';
        version = ua.match(/Chrome\/(\d+)/)[1];
    } else if (ua.indexOf('Firefox') > -1) {
        browser = 'Firefox';
        version = ua.match(/Firefox\/(\d+)/)[1];
    } else if (ua.indexOf('Safari') > -1) {
        browser = 'Safari';
        version = ua.match(/Version\/(\d+)/)[1];
    } else if (ua.indexOf('Edge') > -1) {
        browser = 'Edge';
        version = ua.match(/Edge\/(\d+)/)[1];
    }
    
    return { browser, version };
}

// 导出所有函数（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatPercentage,
        formatDate,
        formatNumber,
        daysBetween,
        getValueColor,
        generateRandomColor,
        debounce,
        throttle,
        deepClone,
        showLoading,
        showToast,
        exportToCSV,
        isMobileDevice,
        getBrowserInfo
    };
}