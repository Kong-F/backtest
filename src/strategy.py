#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模块

实现EMA通道交易策略
"""

import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

from src.utils import calculate_ema
from src.config import Constants


class BaseStrategy:
    """
    策略基类
    """
    
    def __init__(self, name: str):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 包含信号的DataFrame
        """
        raise NotImplementedError("子类必须实现generate_signals方法")
    
    def get_strategy_info(self) -> Dict:
        """
        获取策略信息
        
        Returns:
            Dict: 策略信息字典
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__
        }


class EMAChannelStrategy(BaseStrategy):
    """
    EMA通道策略
    
    策略逻辑：
    1. 计算高价的EMA作为上轨
    2. 计算低价的EMA作为下轨
    3. 当收盘价突破上轨时生成买入信号
    4. 当收盘价跌破下轨时生成卖出信号
    """
    
    def __init__(self, ema_period: int = Constants.DEFAULT_EMA_PERIOD):
        """
        初始化EMA通道策略
        
        Args:
            ema_period: EMA周期
        """
        super().__init__(f"EMA通道策略(周期={ema_period})")
        self.ema_period = ema_period
        
        if ema_period <= 0:
            raise ValueError("EMA周期必须大于0")
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成EMA通道交易信号
        
        Args:
            df: 包含OHLCV数据的DataFrame，必须包含High、Low、Close列
            
        Returns:
            pd.DataFrame: 包含信号和指标的DataFrame
        """
        if df is None or df.empty:
            raise ValueError("输入数据不能为空")
        
        # 验证必要列
        required_columns = ['High', 'Low', 'Close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要列: {missing_columns}")
        
        # 复制数据避免修改原始数据
        result_df = df.copy()
        
        self.logger.info(f"开始计算EMA通道指标，周期={self.ema_period}")
        
        # 计算EMA通道
        result_df['ema_upper'] = calculate_ema(df['High'], self.ema_period)
        result_df['ema_lower'] = calculate_ema(df['Low'], self.ema_period)
        
        # 生成交易信号
        result_df = self._generate_trading_signals(result_df)
        
        # 计算额外指标
        result_df = self._calculate_additional_indicators(result_df)
        
        self.logger.info(f"信号生成完成，共生成 {len(result_df)} 个数据点")
        
        return result_df
    
    def _generate_trading_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成具体的交易信号
        
        Args:
            df: 包含EMA指标的DataFrame
            
        Returns:
            pd.DataFrame: 包含交易信号的DataFrame
        """
        # 初始化信号列
        df['signal'] = 0  # 0: 无信号, 1: 买入, -1: 卖出
        df['position'] = 0  # 0: 空仓, 1: 持仓
        df['trade_type'] = ''  # 交易类型描述
        
        # 生成买入和卖出信号
        # 买入信号：收盘价突破上轨
        buy_condition = (
            (df['Close'] > df['ema_upper']) &
            (df['Close'].shift(1) <= df['ema_upper'].shift(1))
        )
        
        # 卖出信号：收盘价跌破下轨
        sell_condition = (
            (df['Close'] < df['ema_lower']) &
            (df['Close'].shift(1) >= df['ema_lower'].shift(1))
        )
        
        # 设置信号
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        # 设置交易类型
        df.loc[buy_condition, 'trade_type'] = 'BUY'
        df.loc[sell_condition, 'trade_type'] = 'SELL'
        
        # 计算持仓状态
        df = self._calculate_positions(df)
        
        return df
    
    def _calculate_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算持仓状态
        
        Args:
            df: 包含交易信号的DataFrame
            
        Returns:
            pd.DataFrame: 包含持仓状态的DataFrame
        """
        current_position = 0
        positions = []
        
        for i, row in df.iterrows():
            if row['signal'] == 1:  # 买入信号
                current_position = 1
            elif row['signal'] == -1:  # 卖出信号
                current_position = 0
            
            positions.append(current_position)
        
        df['position'] = positions
        
        return df
    
    def _calculate_additional_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算额外的技术指标
        
        Args:
            df: 基础DataFrame
            
        Returns:
            pd.DataFrame: 包含额外指标的DataFrame
        """
        # 计算通道宽度
        df['channel_width'] = (df['ema_upper'] - df['ema_lower']) / df['Close']
        
        # 计算价格相对于通道的位置
        df['price_position'] = (
            (df['Close'] - df['ema_lower']) / (df['ema_upper'] - df['ema_lower'])
        )
        
        # 计算通道中轴
        df['ema_middle'] = (df['ema_upper'] + df['ema_lower']) / 2
        
        # 计算价格偏离度
        df['price_deviation'] = (df['Close'] - df['ema_middle']) / df['ema_middle']
        
        return df
    
    def get_signal_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取信号统计摘要
        
        Args:
            df: 包含信号的DataFrame
            
        Returns:
            Dict: 信号统计信息
        """
        if 'signal' not in df.columns:
            return {}
        
        buy_signals = (df['signal'] == 1).sum()
        sell_signals = (df['signal'] == -1).sum()
        total_signals = buy_signals + sell_signals
        
        # 计算信号间隔统计
        signal_dates = df[df['signal'] != 0].index
        if len(signal_dates) > 1:
            intervals = [(signal_dates[i] - signal_dates[i-1]).days 
                        for i in range(1, len(signal_dates))]
            avg_interval = np.mean(intervals) if intervals else 0
            max_interval = max(intervals) if intervals else 0
            min_interval = min(intervals) if intervals else 0
        else:
            avg_interval = max_interval = min_interval = 0
        
        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'signal_frequency': total_signals / len(df) if len(df) > 0 else 0,
            'avg_signal_interval_days': avg_interval,
            'max_signal_interval_days': max_interval,
            'min_signal_interval_days': min_interval
        }
    
    def validate_signals(self, df: pd.DataFrame) -> bool:
        """
        验证生成的信号是否合理
        
        Args:
            df: 包含信号的DataFrame
            
        Returns:
            bool: 信号是否有效
        """
        if df is None or df.empty:
            return False
        
        # 检查必要列
        required_columns = ['signal', 'position', 'ema_upper', 'ema_lower']
        if not all(col in df.columns for col in required_columns):
            self.logger.error(f"缺少必要的信号列: {required_columns}")
            return False
        
        # 检查EMA值的合理性
        if (df['ema_upper'] < df['ema_lower']).any():
            self.logger.error("发现上轨低于下轨的异常情况")
            return False
        
        # 检查信号值的合理性
        valid_signals = df['signal'].isin([0, 1, -1]).all()
        if not valid_signals:
            self.logger.error("发现无效的信号值")
            return False
        
        # 检查持仓状态的合理性
        valid_positions = df['position'].isin([0, 1]).all()
        if not valid_positions:
            self.logger.error("发现无效的持仓状态")
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict:
        """
        获取策略详细信息
        
        Returns:
            Dict: 策略信息
        """
        base_info = super().get_strategy_info()
        base_info.update({
            'ema_period': self.ema_period,
            'description': f'基于{self.ema_period}周期EMA的通道突破策略',
            'parameters': {
                'ema_period': self.ema_period
            },
            'signals': {
                'buy': '收盘价突破EMA上轨',
                'sell': '收盘价跌破EMA下轨'
            }
        })
        return base_info
    
    def optimize_parameters(self, df: pd.DataFrame, 
                          ema_range: Tuple[int, int] = (10, 50)) -> Dict:
        """
        参数优化（简化版本）
        
        Args:
            df: 历史数据
            ema_range: EMA周期范围
            
        Returns:
            Dict: 优化结果
        """
        self.logger.info(f"开始参数优化，EMA范围: {ema_range}")
        
        best_ema = self.ema_period
        best_score = -float('inf')
        results = []
        
        for ema_period in range(ema_range[0], ema_range[1] + 1):
            try:
                # 创建临时策略
                temp_strategy = EMAChannelStrategy(ema_period)
                temp_df = temp_strategy.generate_signals(df)
                
                # 简单评分：信号数量和价格变化的相关性
                signals = temp_df['signal']
                returns = temp_df['Close'].pct_change().fillna(0)
                
                # 计算信号后的收益
                signal_returns = []
                for i in range(1, len(temp_df)):
                    if temp_df.iloc[i-1]['signal'] != 0:
                        signal_returns.append(returns.iloc[i])
                
                if signal_returns:
                    avg_signal_return = np.mean(signal_returns)
                    score = avg_signal_return * len(signal_returns)  # 考虑信号数量
                else:
                    score = 0
                
                results.append({
                    'ema_period': ema_period,
                    'score': score,
                    'signal_count': (signals != 0).sum(),
                    'avg_signal_return': avg_signal_return if signal_returns else 0
                })
                
                if score > best_score:
                    best_score = score
                    best_ema = ema_period
                    
            except Exception as e:
                self.logger.warning(f"优化EMA={ema_period}时出错: {e}")
                continue
        
        self.logger.info(f"参数优化完成，最佳EMA周期: {best_ema}")
        
        return {
            'best_ema_period': best_ema,
            'best_score': best_score,
            'all_results': results
        }