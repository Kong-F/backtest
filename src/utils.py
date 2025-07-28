#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块

包含日志设置、日期验证、数据处理等辅助功能
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Union, List
import pandas as pd
import numpy as np


def setup_logging(verbose: bool = False) -> None:
    """
    设置日志配置
    
    Args:
        verbose: 是否启用详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


def validate_date_format(date_string: str) -> bool:
    """
    验证日期格式是否为 YYYY-MM-DD
    
    Args:
        date_string: 日期字符串
        
    Returns:
        bool: 格式是否正确
    """
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_string):
        return False
    
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线 (EMA)
    
    Args:
        data: 价格数据序列
        period: EMA周期
        
    Returns:
        pd.Series: EMA值序列
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_returns(prices: pd.Series) -> pd.Series:
    """
    计算收益率
    
    Args:
        prices: 价格序列
        
    Returns:
        pd.Series: 收益率序列
    """
    return prices.pct_change().fillna(0)


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    计算累积收益率
    
    Args:
        returns: 收益率序列
        
    Returns:
        pd.Series: 累积收益率序列
    """
    return (1 + returns).cumprod() - 1


def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """
    计算最大回撤
    
    Args:
        cumulative_returns: 累积收益率序列
        
    Returns:
        float: 最大回撤值
    """
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / (1 + peak)
    return drawdown.min()


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率 (年化)
        
    Returns:
        float: 夏普比率
    """
    if returns.std() == 0:
        return 0
    
    # 转换为年化收益率和波动率
    annual_return = returns.mean() * 252  # 假设252个交易日
    annual_volatility = returns.std() * np.sqrt(252)
    
    return (annual_return - risk_free_rate) / annual_volatility


def calculate_win_rate(returns: pd.Series) -> float:
    """
    计算胜率
    
    Args:
        returns: 收益率序列
        
    Returns:
        float: 胜率 (0-1之间)
    """
    if len(returns) == 0:
        return 0
    
    winning_trades = (returns > 0).sum()
    total_trades = len(returns[returns != 0])  # 排除无交易的时期
    
    return winning_trades / total_trades if total_trades > 0 else 0


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 数值 (如 0.1234 表示 12.34%)
        decimals: 小数位数
        
    Returns:
        str: 格式化后的百分比字符串
    """
    return f"{value:.{decimals}%}"


def format_currency(value: float, currency: str = '$') -> str:
    """
    格式化货币显示
    
    Args:
        value: 金额
        currency: 货币符号
        
    Returns:
        str: 格式化后的货币字符串
    """
    return f"{currency}{value:,.2f}"


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        float: 除法结果
    """
    return numerator / denominator if denominator != 0 else default


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清理数据，处理缺失值和异常值
    
    Args:
        df: 原始数据框
        
    Returns:
        pd.DataFrame: 清理后的数据框
    """
    # 复制数据避免修改原始数据
    cleaned_df = df.copy()
    
    # 删除完全重复的行
    cleaned_df = cleaned_df.drop_duplicates()
    
    # 处理缺失值 - 使用前向填充
    cleaned_df = cleaned_df.fillna(method='ffill')
    
    # 删除仍有缺失值的行
    cleaned_df = cleaned_df.dropna()
    
    # 检查价格数据的合理性
    price_columns = ['Open', 'High', 'Low', 'Close']
    for col in price_columns:
        if col in cleaned_df.columns:
            # 删除价格为0或负数的行
            cleaned_df = cleaned_df[cleaned_df[col] > 0]
            
            # 检查High >= Low, High >= Open, High >= Close
            if 'High' in cleaned_df.columns and 'Low' in cleaned_df.columns:
                cleaned_df = cleaned_df[cleaned_df['High'] >= cleaned_df['Low']]
                
                if 'Open' in cleaned_df.columns:
                    cleaned_df = cleaned_df[
                        (cleaned_df['High'] >= cleaned_df['Open']) &
                        (cleaned_df['Low'] <= cleaned_df['Open'])
                    ]
                    
                if 'Close' in cleaned_df.columns:
                    cleaned_df = cleaned_df[
                        (cleaned_df['High'] >= cleaned_df['Close']) &
                        (cleaned_df['Low'] <= cleaned_df['Close'])
                    ]
    
    return cleaned_df


def resample_data(df: pd.DataFrame, target_interval: str) -> pd.DataFrame:
    """
    重新采样数据到目标时间间隔
    
    Args:
        df: 原始数据框
        target_interval: 目标时间间隔
        
    Returns:
        pd.DataFrame: 重新采样后的数据框
    """
    # 确保索引是日期时间类型
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 定义重采样规则
    agg_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }
    
    # 只对存在的列进行聚合
    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
    
    return df.resample(target_interval).agg(agg_dict).dropna()


def get_trading_days_count(start_date: str, end_date: str) -> int:
    """
    计算交易日数量 (简化版本，不考虑具体的节假日)
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        int: 交易日数量
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    total_days = (end - start).days
    # 简化计算：假设每周5个交易日
    return int(total_days * 5 / 7)


def print_progress_bar(iteration: int, total: int, prefix: str = '', 
                      suffix: str = '', length: int = 50) -> None:
    """
    打印进度条
    
    Args:
        iteration: 当前迭代次数
        total: 总迭代次数
        prefix: 前缀文本
        suffix: 后缀文本
        length: 进度条长度
    """
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    
    if iteration == total:
        print()  # 完成时换行