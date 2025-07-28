# 加密货币投资回测系统

基于 EMA 通道策略的加密货币投资回测 Python 脚本，支持加密货币、美股、港股、A股等多种市场的历史数据回测，可配置回测周期、不同 K 线数据类型，并提供详细的回测结果分析和可视化。

## 功能特性

### 🚀 核心功能
- **多市场支持**：支持加密货币、美股、港股、A股等多种市场 (A 股尚未支持指数数据)
- **多代币支持**: 支持主流加密货币（BTC, ETH, BNB, ADA, SOL等）
- **灵活时间配置**: 支持自定义回测开始和结束时间
- **多时间框架**: 支持1分钟到1个月的各种K线周期
- **EMA通道策略**: 基于指数移动平均线通道的交易策略
- **参数优化**: 支持对比不同EMA周期参数的收益率
- **详细报告**: 生成完整的回测报告和可视化图表

### 📊 分析指标
- **收益指标**: 总收益率、年化收益率、复合年增长率(CAGR)
- **风险指标**: 最大回撤、波动率、夏普比率、索提诺比率
- **交易统计**: 交易次数、胜率、平均持仓时间、盈利因子
- **交易详情**: 每笔交易的时间、价格、数量等
- **基准对比**: 与买入持有策略的对比分析
- **可视化图表**: 价格走势、EMA通道、交易信号等

### 📈 可视化图表
- [x] 价格走势与交易信号图
- [x] 权益曲线与回撤分析图
- [x] EMA参数对比分析图 (终端)
- [ ] 月度收益热力图 (还未在 HTML 报告中展示)
- [ ] 在 HTML 报告中展示多个通道比对分析

### 数据源
- **yfinance**: 支持美股、港股、加密货币
- **binance**: 支持加密货币
- **akshare**: 支持 A 股数据

## 安装指南

### 环境要求
- Python 3.8+
- pip 包管理器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd backtest
```

2. **创建虚拟环境（推荐）**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **安装TA-Lib（可选，用于技术指标计算）**

**MacOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

**Windows:**
- 下载预编译的whl文件：https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
- 安装：`pip install TA_Lib‑0.4.25‑cp39‑cp39‑win_amd64.whl`

## 使用指南

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--symbol, -s` | str | - | 交易对/股票代码 (例如: BTC, ETH, AAPL, 0700, 600519, sh000001) |
| `--market-type, -m` | str | auto | 市场类型 (crypto/us_stock/hk_stock/cn_stock/h_stock，自动判断如果未指定) |
| `--data-source, -d` | str | yfinance | 数据源 (yfinance/binance/akshare) |
| `--start-date` | str | - | 回测开始日期 (格式: YYYY-MM-DD) |
| `--end-date` | str | - | 回测结束日期 (格式: YYYY-MM-DD) |
| `--interval, -i` | str | 1d | K线时间间隔 (1h/4h/1d) |
| `--ema, -e` | str | - | EMA周期参数，支持单个值或逗号分隔的多个值 (例如: 33 或 20,30,33) |
| `--initial-capital` | float | 10000 | 初始资金 |
| `--commission` | float | 0.001 | 交易手续费率 (0.001 即 0.1%) |
| `--output-dir` | str | ./results | 结果输出目录 |
| `--save-plots` | flag | False | 保存图表到文件 |
| `--verbose, -v` | flag | False | 详细输出模式 |
| `--web-report, -w` | flag | False | 生成Web格式的回测报告 |
| `--auto-open` | flag | False | 自动在浏览器中打开Web报告 (需要配合 --web-report 使用) |

### 基本用法

**加密货币回测:**
```bash
python main.py --symbol BTC --market-type crypto --start-date 2022-12-06 --end-date 2025-07-20 --interval 1d --ema 39 --web-report --auto-open # 单个EMA参数回测, 生成 Web 报告并自动打开
python main.py --symbol BTC --data-source binance --start-date 2022-12-06 --end-date 2025-07-20 --interval 1d --ema 20,30,40 # 多个EMA参数对比, 指定数据来源binance
```
**美股回测:**
```bash
python main.py --symbol AAPL --market-type us_stock --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
python main.py --symbol TSLA --market-type us_stock --start-date 2023-01-01 --end-date 2024-01-01 --ema 20,33
```

**港股回测:**
```bash
python main.py --symbol 0700 --market-type hk_stock --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
```

**A股回测:**
```bash
python main.py --symbol 600519 --market-type cn_stock --data-source akshare --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
```

### 自动市场类型判断

系统支持根据股票代码自动判断市场类型：

- **加密货币**: BTC, ETH 等已知代币符号
- **美股**: 字母组合，长度≤5（如AAPL, TSLA）
- **港股**: 4位数字或.HK后缀（如0700, 9988.HK）
- **A股**: 6位数字或 sh/sz 开头或 .SH/.SZ 后缀（如600519, sh000001, 000001.SZ）

### 数据源自动选择

系统会根据市场类型自动选择合适的数据源：

- **加密货币**: 优先yfinance，备选binance
- **美股**: yfinance
- **港股**: yfinance
- **A股**: akshare
- **H股**: yfinance

### 支持的时间间隔

| 间隔 | 说明 |
|------|------|
| 1m | 1分钟 |
| 5m | 5分钟 |
| 15m | 15分钟 |
| 30m | 30分钟 |
| 1h | 1小时 |
| 4h | 4小时 |
| 1d | 1天 |
| 1wk | 1周 |
| 1mo | 1月 |

## 策略说明

### EMA通道策略

本系统实现的是基于指数移动平均线(EMA)通道的交易策略：

**策略逻辑:**
1. 计算EMA指标
2. 构建EMA通道
3. 交易信号：
   - **买入信号**: 收盘价突破通道上轨
   - **卖出信号**: 收盘价跌破通道下轨
4. 无止盈止损，完全基于信号交易

**策略特点:**
- 趋势跟踪策略
- 适合中长期持有
- 减少频繁交易
- 可配置EMA周期参数

## 输出结果

### 控制台输出
- 回测进度显示
- 详细的性能指标
- 风险分析结果
- 交易统计信息
- EMA参数对比分析

### 文件输出
- **图表文件**: PNG格式的可视化图表
- **数据文件**: CSV格式的详细交易记录
- **报告文件**: HTML格式的详细回测报告

### 示例输出
```
============================================================
EMA33 策略回测结果摘要
============================================================

📈 性能指标:
  总收益率: 45.67%
  年化收益率: 38.92%
  复合年增长率: 35.24%
  盈利因子: 1.85

⚠️  风险指标:
  最大回撤: -18.45%
  夏普比率: 1.23
  索提诺比率: 1.67
  卡尔玛比率: 2.11
  波动率: 31.65%

💼 交易统计:
  总交易次数: 24
  完整交易对: 12
  胜率: 58.33%
  平均交易收益: 3.81%
  最佳交易: 15.67%
  最差交易: -8.23%
  平均持仓天数: 15.3
```

## 注意事项

### 数据源限制
- **yfinance**: 免费但有请求频率限制，部分数据有缺失，数据质量不稳定
- **akshare**: 数据源质量不稳定，部分数据接口返回数据量有限
- **binance**: 仅支持在币安上架的代币

### 性能考虑
- 大量历史数据可能需要较长加载时间
- 多参数对比会增加计算时间
- 建议先用较短时间段测试

### 风险提示
- 本系统仅用于教育和研究目的
- 历史回测结果不代表未来表现
- 实际交易请谨慎考虑风险
- 建议结合其他分析方法

## 常见问题

### Q: 如何添加新的交易对？
A: 在 `src/config.py` 的 `SUPPORTED_SYMBOLS` 中添加新的交易对符号。

### Q: 如何修改EMA通道宽度？
A: 在 `src/strategy.py` 的 `EMAChannelStrategy` 类中修改 `channel_width` 参数。

### Q: 如何添加止盈止损？
A: 在 `src/strategy.py` 中的 `generate_signals` 方法中添加止盈止损逻辑。

### Q: 数据获取失败怎么办？
A: 检查网络连接，尝试更换数据源，或减少数据请求频率。

**免责声明**: 本软件仅供教育和研究使用，不构成投资建议。使用者应自行承担投资风险。