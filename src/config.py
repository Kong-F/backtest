#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块

定义系统配置类和常量
"""

from dataclasses import dataclass
from typing import Dict, Any
import os


@dataclass
class Config:
    """
    回测系统配置类
    """
    symbol: str                 # 交易对符号
    start_date: str            # 开始日期
    end_date: str              # 结束日期
    interval: str              # 时间间隔
    initial_capital: float     # 初始资金
    commission: float          # 手续费率
    output_dir: str            # 输出目录
    save_plots: bool           # 是否保存图表
    market_type: str = None    # 市场类型
    data_source: str = 'yfinance'  # 数据源
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 自动判断市场类型
        if self.market_type is None:
            self.market_type = get_market_type(self.symbol)
        
        # 根据市场类型选择合适的数据源
        if self.market_type in Constants.MARKET_DATA_SOURCES:
            available_sources = Constants.MARKET_DATA_SOURCES[self.market_type]
            if self.data_source not in available_sources:
                self.data_source = available_sources[0]  # 使用第一个可用的数据源


class Constants:
    """
    系统常量定义
    """
    
    # 市场类型
    MARKET_TYPES = {
        'crypto': '加密货币',
        'us_stock': '美股',
        'hk_stock': '港股', 
        'cn_stock': 'A股',
        'h_stock': 'H股'
    }
    
    # 支持的交易对/股票代码
    SUPPORTED_SYMBOLS = {
        # 加密货币
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD', 
        'UNI': 'UNI-USD',
        'SOL': 'SOL-USD',
        'ADA': 'ADA-USD',
        'DOT': 'DOT-USD',
        'LINK': 'LINK-USD',
        'MATIC': 'MATIC-USD',
        'AVAX': 'AVAX-USD',
        'ATOM': 'ATOM-USD'
    }
    
    # 美股示例代码
    US_STOCK_SYMBOLS = {
        'AAPL': 'AAPL',
        'MSFT': 'MSFT',
        'GOOGL': 'GOOGL',
        'AMZN': 'AMZN',
        'TSLA': 'TSLA',
        'META': 'META',
        'NVDA': 'NVDA',
        'NFLX': 'NFLX'
    }
    
    # 港股示例代码
    HK_STOCK_SYMBOLS = {
        '0700': '0700.HK',  # 腾讯
        '9988': '9988.HK',  # 阿里巴巴
        '3690': '3690.HK',  # 美团
        '1810': '1810.HK',  # 小米
        '2318': '2318.HK',  # 中国平安
        '0941': '0941.HK',  # 中国移动
        '1398': '1398.HK',  # 工商银行
        '0388': '0388.HK'   # 香港交易所
    }
    
    # A股示例代码 - 明确区分不同交易所
    CN_STOCK_SYMBOLS = {
        # 深交所主板 (000xxx)
        '000001': '000001.SZ',  # 平安银行
        '000002': '000002.SZ',  # 万科A
        '000858': '000858.SZ',  # 五粮液
        
        # 深交所中小板 (002xxx)
        '002415': '002415.SZ',  # 海康威视
        
        # 深交所创业板 (300xxx)
        '300059': '300059.SZ',  # 东方财富
        
        # 上交所主板 (600xxx, 601xxx, 603xxx, 605xxx)
        '600000': '600000.SH',  # 浦发银行
        '600036': '600036.SH',  # 招商银行
        '600519': '600519.SH',  # 贵州茅台
        '601318': '601318.SH',  # 中国平安
        '000001.SH': '000001.SH',  # 上证指数 (特殊处理)
        
        # sh/sz前缀格式的A股代码
        'sh000001': '000001',  # 上证指数
        'sz399001': '399001',  # 深证成指
        'sz399006': '399006',  # 创业板指
        'sh000300': '000300',  # 沪深300
        'sh000905': '000905',  # 中证500
    }
    
    # 股票代码规则映射 - 用于自动判断交易所
    CN_STOCK_EXCHANGE_RULES = {
        # 上交所规则
        'SH': {
            'patterns': ['60', '68', '90'],  # 600xxx, 601xxx等, 688xxx科创板, 900xxx B股
            'description': '上海证券交易所'
        },
        # 深交所规则  
        'SZ': {
            'patterns': ['00', '30', '20'],  # 000xxx主板, 300xxx创业板, 200xxx B股
            'description': '深圳证券交易所'
        }
    }
    
    # 特殊股票代码处理 - 解决代码冲突问题
    CN_STOCK_SPECIAL_CASES = {
        '000001': {
            'SZ': {'code': '000001.SZ', 'name': '平安银行', 'type': 'stock'},
            'SH': {'code': '000001.SH', 'name': '上证指数', 'type': 'index'}
        }
    }
    
    # 时间间隔映射
    INTERVAL_MAPPING = {
        '1h': '1h',
        '4h': '4h', 
        '1d': '1d'
    }
    
    # 默认配置
    DEFAULT_EMA_PERIOD = 33
    DEFAULT_INITIAL_CAPITAL = 10000.0
    DEFAULT_COMMISSION = 0.001  # 0.1%
    
    # 图表配置
    CHART_COLORS = {
        'price': '#1f77b4',
        'ema_upper': '#2ca02c', 
        'ema_lower': '#d62728',
        'buy_signal': '#ff7f0e',
        'sell_signal': '#9467bd',
        'profit': '#2ca02c',
        'loss': '#d62728',
        'background': '#f8f9fa'
    }
    
    # 性能指标阈值
    PERFORMANCE_THRESHOLDS = {
        'excellent_return': 0.5,    # 50%以上为优秀
        'good_return': 0.2,         # 20%以上为良好
        'acceptable_return': 0.05,   # 5%以上为可接受
        'max_drawdown_warning': 0.3, # 最大回撤超过30%警告
        'min_sharpe_ratio': 1.0      # 夏普比率低于1.0警告
    }
    
    # 数据源配置
    DATA_SOURCE_CONFIG = {
        'yfinance': {
            'timeout': 30,
            'retry_count': 3,
            'retry_delay': 1
        },
        'binance': {
            'base_url': 'https://api.binance.com',
            'timeout': 30,
            'retry_count': 3
        },
        'akshare': {
            'timeout': 30,
            'retry_count': 3,
            'retry_delay': 1
        }
    }
    
    # 市场数据源映射
    MARKET_DATA_SOURCES = {
        'crypto': ['yfinance', 'binance'],
        'us_stock': ['yfinance'],
        'hk_stock': ['yfinance'],
        'cn_stock': ['akshare'],
        'h_stock': ['yfinance']
    }
    
    # 文件输出配置
    OUTPUT_CONFIG = {
        'chart_dpi': 300,
        'chart_figsize': (15, 10),
        'report_format': 'html',
        'csv_encoding': 'utf-8'
    }


def get_market_type(symbol: str) -> str:
    """
    根据符号判断市场类型
    
    Args:
        symbol: 交易对/股票代码
        
    Returns:
        str: 市场类型
    """
    symbol = symbol.upper()
    
    # 加密货币
    if symbol in Constants.SUPPORTED_SYMBOLS:
        return 'crypto'
    
    # 美股 (通常是字母组合)
    if symbol in Constants.US_STOCK_SYMBOLS or (symbol.isalpha() and len(symbol) <= 5):
        return 'us_stock'
    
    # 港股 (4位数字或带.HK后缀)
    if (symbol.isdigit() and len(symbol) == 4) or symbol.endswith('.HK'):
        return 'hk_stock'
    
    # A股 (6位数字或带.SH/.SZ后缀，或sh/sz前缀格式)
    if ((symbol.isdigit() and len(symbol) == 6) or 
        symbol.endswith('.SH') or symbol.endswith('.SZ') or symbol.endswith('.SS') or
        symbol.lower().startswith('sh') or symbol.lower().startswith('sz')):
        return 'cn_stock'
    
    # 默认为加密货币
    return 'crypto'


# def get_cn_stock_exchange(symbol: str) -> str:
#     """
#     根据股票代码自动判断所属交易所
    
#     Args:
#         symbol: 股票代码
        
#     Returns:
#         str: 交易所代码 ('SH' 或 'SZ')
#     """
#     symbol = symbol.upper().replace('.SH', '').replace('.SZ', '')
    
#     # 检查特殊情况
#     if symbol in Constants.CN_STOCK_SPECIAL_CASES:
#         # 对于有冲突的代码，默认返回深交所（股票），用户可以明确指定.SH获取指数
#         return 'SZ'
    
#     # 根据代码规则判断
#     for exchange, rules in Constants.CN_STOCK_EXCHANGE_RULES.items():
#         for pattern in rules['patterns']:
#             if symbol.startswith(pattern):
#                 return exchange
    
#     # 默认返回深交所
#     return 'SZ'


def get_symbol_for_source(symbol: str, source: str = 'yfinance', market_type: str = None) -> str:
    """
    根据数据源和市场类型获取正确的交易对符号格式
    
    Args:
        symbol: 原始符号
        source: 数据源名称
        market_type: 市场类型，如果为None则自动判断
        
    Returns:
        str: 格式化后的符号
    """
    if market_type is None:
        market_type = get_market_type(symbol)
    
    symbol = symbol.upper()
    
    if source == 'yfinance':
        if market_type == 'crypto':
            return Constants.SUPPORTED_SYMBOLS.get(symbol, f"{symbol}-USD")
        elif market_type == 'us_stock':
            return Constants.US_STOCK_SYMBOLS.get(symbol, symbol)
        elif market_type == 'hk_stock':
            if symbol.isdigit() and len(symbol) == 4:
                return f"{symbol}.HK"
            return Constants.HK_STOCK_SYMBOLS.get(symbol, symbol)
        elif market_type == 'cn_stock':
            # yfinance不直接支持A股，返回原符号
            return symbol
        elif market_type == 'h_stock':
            # H股在港股市场交易，使用港股格式
            if symbol.isdigit() and len(symbol) == 4:
                return f"{symbol}.HK"
            return symbol
    
    elif source == 'binance':
        if market_type == 'crypto':
            return f"{symbol}USDT"
        else:
            # Binance主要支持加密货币
            return symbol
    
    elif source == 'akshare':
        if market_type == 'cn_stock':
            # 处理A股代码格式
            symbol_lower = symbol.lower()
            
            # 处理sh/sz前缀格式 (如 sh000001, sz399001)
            if symbol_lower.startswith('sh'):
                # return symbol[2:]  # 移除sh前缀
                return symbol
            elif symbol_lower.startswith('sz'):
                # return symbol[2:]  # 移除sz前缀
                return symbol
            elif '.' in symbol:
                # 已经包含交易所后缀，直接移除后缀返回
                return symbol.split('.')[0]
            else:
                # 没有交易所后缀，需要智能判断
                base_symbol = symbol.replace('.SH', '').replace('.SZ', '')
                
                # 检查是否在预定义的符号字典中
                if symbol in Constants.CN_STOCK_SYMBOLS:
                    return base_symbol
                
                # 检查特殊情况
                if base_symbol in Constants.CN_STOCK_SPECIAL_CASES:
                    # 对于有冲突的代码，需要用户明确指定
                    if symbol.endswith('.SH'):
                        return base_symbol  # 用户明确指定上交所
                    else:
                        return base_symbol  # 默认深交所
                
                # 使用自动判断逻辑
                return base_symbol
        else:
            return symbol
    
    return symbol


# def resolve_stock_code_conflict(symbol: str) -> dict:
#     """
#     解决股票代码冲突问题
    
#     Args:
#         symbol: 股票代码
        
#     Returns:
#         dict: 包含冲突信息和建议的字典
#     """
#     symbol_upper = symbol.upper()
#     symbol_lower = symbol.lower()
    
#     # 处理不同格式的股票代码
#     if symbol_lower.startswith('sh'):
#         base_symbol = symbol[2:]
#         specified_exchange = 'SH'
#     elif symbol_lower.startswith('sz'):
#         base_symbol = symbol[2:]
#         specified_exchange = 'SZ'
#     elif symbol_upper.endswith('.SH'):
#         base_symbol = symbol_upper.replace('.SH', '')
#         specified_exchange = 'SH'
#     elif symbol_upper.endswith('.SZ'):
#         base_symbol = symbol_upper.replace('.SZ', '')
#         specified_exchange = 'SZ'
#     else:
#         base_symbol = symbol_upper
#         specified_exchange = None
    
#     # 检查是否存在冲突
#     if base_symbol in Constants.CN_STOCK_SPECIAL_CASES:
#         special_cases = Constants.CN_STOCK_SPECIAL_CASES[base_symbol]
        
#         # 如果用户已明确指定交易所（通过sh/sz前缀或.SH/.SZ后缀），则不视为冲突
#         if specified_exchange:
#             target_info = special_cases[specified_exchange]
#             return {
#                 'has_conflict': False,
#                 'base_symbol': base_symbol,
#                 'exchange': specified_exchange,
#                 'resolved_info': target_info,
#                 'message': f"使用{specified_exchange}交易所: {target_info['name']} ({target_info['type']})"
#             }
        
#         return {
#             'has_conflict': True,
#             'base_symbol': base_symbol,
#             'conflicts': special_cases,
#             'default_choice': 'SZ',  # 默认选择深交所
#             'suggestions': {
#                 'SZ': f"{base_symbol}.SZ - {special_cases['SZ']['name']} ({special_cases['SZ']['type']})",
#                 'SH': f"{base_symbol}.SH - {special_cases['SH']['name']} ({special_cases['SH']['type']})"
#             },
#             'message': f"检测到股票代码冲突 {base_symbol}，请明确指定交易所后缀"
#         }
    
#     return {
#         'has_conflict': False,
#         'base_symbol': base_symbol,
#         'exchange': get_cn_stock_exchange(base_symbol),
#         'message': f"股票代码 {base_symbol} 无冲突"
#     }


def validate_config(config: Config) -> bool:
    """
    验证配置的有效性
    
    Args:
        config: 配置对象
        
    Returns:
        bool: 配置是否有效
    """
    # 验证交易对
    if config.symbol not in Constants.SUPPORTED_SYMBOLS:
        print(f"警告: 交易对 {config.symbol} 可能不被支持")
    
    # 验证时间间隔
    if config.interval not in Constants.INTERVAL_MAPPING:
        print(f"错误: 不支持的时间间隔 {config.interval}")
        return False
    
    # 验证资金和手续费
    if config.initial_capital <= 0:
        print("错误: 初始资金必须大于0")
        return False
        
    if config.commission < 0 or config.commission >= 1:
        print("错误: 手续费率必须在0到1之间")
        return False
    
    return True