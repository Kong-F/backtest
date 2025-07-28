// 主要交互逻辑模块

// 全局变量
let currentData = null;
let filteredTrades = [];
let currentPage = 1;
const tradesPerPage = 20;

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化...');
    
    // 检查数据是否存在
    if (typeof window.reportData === 'undefined') {
        console.error('报告数据未找到');
        showToast('报告数据加载失败', 'error');
        return;
    }
    
    currentData = window.reportData;
    filteredTrades = currentData.trades || [];
    
    // 初始化各个模块
    initializeEventListeners();
    initializeCharts(currentData);
    initializeTradeTable();
    
    // 显示加载完成提示
    showToast('报告加载完成', 'success', 2000);
    
    console.log('初始化完成');
});

/**
 * 初始化事件监听器
 */
function initializeEventListeners() {
    // 标签页切换事件
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target');
            handleTabSwitch(targetId);
        });
    });
    
    // 交易表格搜索
    const searchInput = document.getElementById('tradeSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleTradeSearch, 300));
    }
    
    // 交易类型筛选
    const filterSelect = document.getElementById('tradeFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', handleTradeFilter);
    }
    
    // 表格排序
    const tableHeaders = document.querySelectorAll('#tradesTable th[data-sort]');
    tableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.getAttribute('data-sort');
            handleTableSort(sortField);
        });
        // 添加排序指示器样式
        header.style.cursor = 'pointer';
        header.title = '点击排序';
    });
    
    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 打印按钮
    const printButtons = document.querySelectorAll('[onclick="window.print()"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handlePrint();
        });
    });
}

/**
 * 处理标签页切换
 * @param {string} targetId - 目标标签页ID
 */
function handleTabSwitch(targetId) {
    console.log('切换到标签页:', targetId);
    
    // 根据不同标签页执行相应操作
    switch (targetId) {
        case '#performance':
            // 资金分析页面，确保图表正确渲染
            setTimeout(() => {
                resizeCharts();
            }, 100);
            break;
        case '#risk':
            // 风险分析页面
            setTimeout(() => {
                resizeCharts();
            }, 100);
            break;
        case '#trades':
            // 交易详情页面，刷新表格
            refreshTradeTable();
            break;
        default:
            break;
    }
}

/**
 * 初始化交易表格
 */
function initializeTradeTable() {
    if (!currentData || !currentData.trades) {
        console.log('无交易数据');
        return;
    }
    
    filteredTrades = [...currentData.trades];
    renderTradeTable();
    renderPagination();
}

/**
 * 处理交易搜索
 */
function handleTradeSearch() {
    const searchTerm = document.getElementById('tradeSearch').value.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredTrades = [...currentData.trades];
    } else {
        filteredTrades = currentData.trades.filter(trade => {
            return (
                trade.type.toLowerCase().includes(searchTerm) ||
                trade.timestamp.toLowerCase().includes(searchTerm) ||
                trade.price.toString().includes(searchTerm) ||
                trade.amount.toString().includes(searchTerm)
            );
        });
    }
    
    currentPage = 1;
    renderTradeTable();
    renderPagination();
}

/**
 * 处理交易类型筛选
 */
function handleTradeFilter() {
    const filterValue = document.getElementById('tradeFilter').value;
    
    if (!filterValue) {
        filteredTrades = [...currentData.trades];
    } else {
        filteredTrades = currentData.trades.filter(trade => trade.type === filterValue);
    }
    
    // 如果还有搜索条件，继续应用搜索
    const searchTerm = document.getElementById('tradeSearch').value.toLowerCase().trim();
    if (searchTerm) {
        filteredTrades = filteredTrades.filter(trade => {
            return (
                trade.type.toLowerCase().includes(searchTerm) ||
                trade.timestamp.toLowerCase().includes(searchTerm) ||
                trade.price.toString().includes(searchTerm) ||
                trade.amount.toString().includes(searchTerm)
            );
        });
    }
    
    currentPage = 1;
    renderTradeTable();
    renderPagination();
}

/**
 * 处理表格排序
 * @param {string} field - 排序字段
 */
function handleTableSort(field) {
    // 获取当前排序状态
    const header = document.querySelector(`#tradesTable th[data-sort="${field}"]`);
    const currentSort = header.getAttribute('data-sort-direction') || 'asc';
    const newSort = currentSort === 'asc' ? 'desc' : 'asc';
    
    // 清除其他列的排序状态
    document.querySelectorAll('#tradesTable th[data-sort]').forEach(th => {
        th.removeAttribute('data-sort-direction');
        th.innerHTML = th.innerHTML.replace(/ ↑| ↓/g, '');
    });
    
    // 设置当前列的排序状态
    header.setAttribute('data-sort-direction', newSort);
    header.innerHTML += newSort === 'asc' ? ' ↑' : ' ↓';
    
    // 执行排序
    filteredTrades.sort((a, b) => {
        let aValue = a[field];
        let bValue = b[field];
        
        // 处理不同数据类型
        if (field === 'timestamp') {
            aValue = new Date(aValue);
            bValue = new Date(bValue);
        } else if (typeof aValue === 'string') {
            aValue = aValue.toLowerCase();
            bValue = bValue.toLowerCase();
        }
        
        if (newSort === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    currentPage = 1;
    renderTradeTable();
    renderPagination();
}

/**
 * 渲染交易表格
 */
function renderTradeTable() {
    const tbody = document.querySelector('#tradesTable tbody');
    if (!tbody) {
        console.error('交易表格tbody不存在');
        return;
    }
    
    // 计算分页数据
    const startIndex = (currentPage - 1) * tradesPerPage;
    const endIndex = startIndex + tradesPerPage;
    const pageData = filteredTrades.slice(startIndex, endIndex);
    
    // 清空现有内容
    tbody.innerHTML = '';
    
    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="fas fa-search me-2"></i>没有找到匹配的交易记录
                </td>
            </tr>
        `;
        return;
    }
    
    // 渲染数据行
    pageData.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.id}</td>
            <td>${formatDate(trade.timestamp, 'YYYY-MM-DD HH:mm')}</td>
            <td>
                <span class="badge ${trade.type === 'BUY' ? 'bg-success' : 'bg-danger'}">
                    ${trade.type}
                </span>
            </td>
            <td>${formatCurrency(trade.price)}</td>
            <td>${formatNumber(trade.quantity, 6)}</td>
            <td>${formatCurrency(trade.amount)}</td>
            <td>${formatCurrency(trade.commission)}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * 渲染分页控件
 */
function renderPagination() {
    // 检查是否存在分页容器，如果不存在则创建
    let paginationContainer = document.getElementById('tradePagination');
    if (!paginationContainer) {
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'tradePagination';
        paginationContainer.className = 'mt-3 d-flex justify-content-between align-items-center';
        
        const tableContainer = document.querySelector('#tradesTable').closest('.card-body');
        if (tableContainer) {
            tableContainer.appendChild(paginationContainer);
        }
    }
    
    const totalPages = Math.ceil(filteredTrades.length / tradesPerPage);
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = `
            <small class="text-muted">
                共 ${filteredTrades.length} 条记录
            </small>
        `;
        return;
    }
    
    let paginationHTML = `
        <small class="text-muted">
            第 ${currentPage} 页，共 ${totalPages} 页 (${filteredTrades.length} 条记录)
        </small>
        <nav>
            <ul class="pagination pagination-sm mb-0">
    `;
    
    // 上一页按钮
    paginationHTML += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 页码按钮
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // 下一页按钮
    paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationHTML += `
            </ul>
        </nav>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
}

/**
 * 切换页面
 * @param {number} page - 目标页码
 */
function changePage(page) {
    const totalPages = Math.ceil(filteredTrades.length / tradesPerPage);
    if (page < 1 || page > totalPages) {
        return;
    }
    
    currentPage = page;
    renderTradeTable();
    renderPagination();
    
    // 滚动到表格顶部
    document.getElementById('tradesTable').scrollIntoView({ behavior: 'smooth' });
}

/**
 * 刷新交易表格
 */
function refreshTradeTable() {
    if (currentData && currentData.trades) {
        filteredTrades = [...currentData.trades];
        currentPage = 1;
        renderTradeTable();
        renderPagination();
    }
}

/**
 * 导出数据
 */
function exportData() {
    if (!currentData) {
        showToast('没有数据可导出', 'warning');
        return;
    }
    
    try {
        // 准备导出数据
        const exportTrades = currentData.trades.map(trade => ({
            '序号': trade.id,
            '时间': trade.timestamp,
            '类型': trade.type,
            '价格': trade.price,
            '数量': trade.quantity,
            '交易额': trade.amount,
            '手续费': trade.commission
        }));
        
        // 生成文件名
        const symbol = currentData.basicInfo.symbol || 'unknown';
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `${symbol}_backtest_trades_${timestamp}.csv`;
        
        // 导出CSV
        exportToCSV(exportTrades, filename);
        
    } catch (error) {
        console.error('导出失败:', error);
        showToast('导出失败，请重试', 'error');
    }
}

/**
 * 处理打印
 */
function handlePrint() {
    // 在打印前确保所有图表都正确渲染
    setTimeout(() => {
        window.print();
    }, 500);
}

/**
 * 处理键盘快捷键
 * @param {KeyboardEvent} event - 键盘事件
 */
function handleKeyboardShortcuts(event) {
    // Ctrl+P: 打印
    if (event.ctrlKey && event.key === 'p') {
        event.preventDefault();
        handlePrint();
    }
    
    // Ctrl+E: 导出
    if (event.ctrlKey && event.key === 'e') {
        event.preventDefault();
        exportData();
    }
    
    // 数字键1-4: 切换标签页
    if (event.key >= '1' && event.key <= '4' && !event.ctrlKey && !event.altKey) {
        const tabIndex = parseInt(event.key) - 1;
        const tabs = ['overview-tab', 'performance-tab', 'risk-tab', 'trades-tab'];
        const targetTab = document.getElementById(tabs[tabIndex]);
        if (targetTab) {
            targetTab.click();
        }
    }
}

/**
 * 显示帮助信息
 */
function showHelp() {
    const helpContent = `
        <div class="help-content">
            <h5>快捷键说明</h5>
            <ul class="list-unstyled">
                <li><kbd>1-4</kbd> 切换标签页</li>
                <li><kbd>Ctrl+P</kbd> 打印报告</li>
                <li><kbd>Ctrl+E</kbd> 导出数据</li>
            </ul>
            <h5>功能说明</h5>
            <ul class="list-unstyled">
                <li>• 点击表格标题可以排序</li>
                <li>• 使用搜索框筛选交易记录</li>
                <li>• 图表支持缩放和悬停查看详情</li>
                <li>• 支持打印和数据导出</li>
            </ul>
        </div>
    `;
    
    // 这里可以使用模态框或其他方式显示帮助信息
    showToast('按F1查看完整帮助文档', 'info', 3000);
}

// 全局函数，供HTML调用
window.changePage = changePage;
window.exportData = exportData;
window.showHelp = showHelp;

// 错误处理
window.addEventListener('error', function(event) {
    console.error('页面错误:', event.error);
    showToast('页面发生错误，请刷新重试', 'error');
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    destroyAllCharts();
});