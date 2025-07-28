#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎模块

实现模拟交易执行和资金管理
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from src.strategy import BaseStrategy
from src.utils import safe_divide


class Trade:
    """
    交易记录类
    """
    
    def __init__(self, trade_id: int, timestamp: pd.Timestamp, trade_type: str, 
                 price: float, quantity: float, commission: float = 0):
        """
        初始化交易记录
        
        Args:
            trade_id: 交易ID
            timestamp: 交易时间
            trade_type: 交易类型 ('BUY' 或 'SELL')
            price: 交易价格
            quantity: 交易数量
            commission: 手续费
        """
        self.trade_id = trade_id
        self.timestamp = timestamp
        self.trade_type = trade_type
        self.price = price
        self.quantity = quantity
        self.commission = commission
        self.value = price * quantity
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            Dict: 交易记录字典
        """
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp,
            'trade_type': self.trade_type,
            'price': self.price,
            'quantity': self.quantity,
            'value': self.value,
            'commission': self.commission
        }


class Portfolio:
    """
    投资组合类
    """
    
    def __init__(self, initial_capital: float):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings = 0.0  # 持有的加密货币数量
        self.total_commission = 0.0
        
    def get_total_value(self, current_price: float) -> float:
        """
        获取投资组合总价值
        
        Args:
            current_price: 当前价格
            
        Returns:
            float: 总价值
        """
        return self.cash + self.holdings * current_price
    
    def get_position_value(self, current_price: float) -> float:
        """
        获取持仓价值
        
        Args:
            current_price: 当前价格
            
        Returns:
            float: 持仓价值
        """
        return self.holdings * current_price
    
    def buy(self, price: float, commission_rate: float) -> Tuple[float, float]:
        """
        执行买入操作（全仓买入）
        
        Args:
            price: 买入价格
            commission_rate: 手续费率
            
        Returns:
            Tuple[float, float]: (买入数量, 手续费)
        """
        if self.cash <= 0:
            return 0, 0
        
        # 计算可买入的数量（考虑手续费）
        available_cash = self.cash
        quantity = available_cash / (price * (1 + commission_rate))
        commission = quantity * price * commission_rate
        
        # 更新持仓和现金
        self.holdings += quantity
        self.cash -= (quantity * price + commission)
        self.total_commission += commission
        
        return quantity, commission
    
    def sell(self, price: float, commission_rate: float) -> Tuple[float, float]:
        """
        执行卖出操作（全仓卖出）
        
        Args:
            price: 卖出价格
            commission_rate: 手续费率
            
        Returns:
            Tuple[float, float]: (卖出数量, 手续费)
        """
        if self.holdings <= 0:
            return 0, 0
        
        quantity = self.holdings
        gross_proceeds = quantity * price
        commission = gross_proceeds * commission_rate
        net_proceeds = gross_proceeds - commission
        
        # 更新持仓和现金
        self.holdings = 0
        self.cash += net_proceeds
        self.total_commission += commission
        
        return quantity, commission


class BacktestEngine:
    """
    回测引擎类
    """
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.logger = logging.getLogger(__name__)
        
        # 回测状态
        self.portfolio = None
        self.trades = []
        self.equity_curve = []
        self.trade_counter = 0
    
    def run_backtest(self, df: pd.DataFrame, strategy: BaseStrategy) -> Optional[Dict]:
        """
        运行回测
        
        Args:
            df: 包含价格数据和信号的DataFrame
            strategy: 交易策略
            
        Returns:
            Optional[Dict]: 回测结果
        """
        if df is None or df.empty:
            self.logger.error("输入数据为空")
            return None
        
        self.logger.info(f"开始回测，数据期间: {df.index[0]} 至 {df.index[-1]}")
        self.logger.info(f"初始资金: ${self.initial_capital:,.2f}")
        self.logger.info(f"手续费率: {self.commission:.3%}")
        
        # 生成交易信号
        try:
            df_with_signals = strategy.generate_signals(df)
        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")
            return None
        
        # 验证信号
        if not strategy.validate_signals(df_with_signals):
            self.logger.error("交易信号验证失败")
            return None
        
        # 初始化回测状态
        self._initialize_backtest()
        
        # 执行回测
        try:
            self._execute_backtest(df_with_signals)
        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            return None
        
        # 生成回测结果
        results = self._generate_results(df_with_signals, strategy)
        
        self.logger.info(f"回测完成，共执行 {len(self.trades)} 笔交易")
        
        return results
    
    def _initialize_backtest(self):
        """
        初始化回测状态
        """
        self.portfolio = Portfolio(self.initial_capital)
        self.trades = []
        self.equity_curve = []
        self.trade_counter = 0
    
    def _execute_backtest(self, df: pd.DataFrame):
        """
        执行回测逻辑
        
        Args:
            df: 包含信号的数据
        """
        for timestamp, row in df.iterrows():
            current_price = row['Close']
            signal = row['signal']
            
            # 记录当前权益
            current_equity = self.portfolio.get_total_value(current_price)
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'cash': self.portfolio.cash,
                'holdings': self.portfolio.holdings,
                'position_value': self.portfolio.get_position_value(current_price),
                'price': current_price
            })
            
            # 执行交易
            if signal == 1:  # 买入信号
                self._execute_buy(timestamp, current_price)
            elif signal == -1:  # 卖出信号
                self._execute_sell(timestamp, current_price)
    
    def _execute_buy(self, timestamp: pd.Timestamp, price: float):
        """
        执行买入操作
        
        Args:
            timestamp: 交易时间
            price: 交易价格
        """
        if self.portfolio.cash <= 0:
            return
        
        quantity, commission = self.portfolio.buy(price, self.commission)
        
        if quantity > 0:
            self.trade_counter += 1
            trade = Trade(
                trade_id=self.trade_counter,
                timestamp=timestamp,
                trade_type='BUY',
                price=price,
                quantity=quantity,
                commission=commission
            )
            self.trades.append(trade)
            
            self.logger.debug(
                f"买入: {quantity:.6f} @ ${price:.2f}, "
                f"手续费: ${commission:.2f}, 时间: {timestamp}"
            )
    
    def _execute_sell(self, timestamp: pd.Timestamp, price: float):
        """
        执行卖出操作
        
        Args:
            timestamp: 交易时间
            price: 交易价格
        """
        if self.portfolio.holdings <= 0:
            return
        
        quantity, commission = self.portfolio.sell(price, self.commission)
        
        if quantity > 0:
            self.trade_counter += 1
            trade = Trade(
                trade_id=self.trade_counter,
                timestamp=timestamp,
                trade_type='SELL',
                price=price,
                quantity=quantity,
                commission=commission
            )
            self.trades.append(trade)
            
            self.logger.debug(
                f"卖出: {quantity:.6f} @ ${price:.2f}, "
                f"手续费: ${commission:.2f}, 时间: {timestamp}"
            )
    
    def _generate_results(self, df: pd.DataFrame, strategy: BaseStrategy) -> Dict:
        """
        生成回测结果
        
        Args:
            df: 包含信号的数据
            strategy: 交易策略
            
        Returns:
            Dict: 回测结果
        """
        if not self.equity_curve:
            return {}
        
        # 转换为DataFrame便于分析
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        trades_df = pd.DataFrame([trade.to_dict() for trade in self.trades])
        
        # 计算基本指标
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # 计算收益率序列
        equity_returns = equity_df['equity'].pct_change().fillna(0)
        
        # 计算最大回撤
        peak = equity_df['equity'].expanding().max()
        drawdown = (equity_df['equity'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # 计算夏普比率
        if len(equity_returns) > 1 and equity_returns.std() > 0:
            sharpe_ratio = equity_returns.mean() / equity_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 计算交易统计
        trade_stats = self._calculate_trade_statistics(trades_df, df)
        
        # 计算年化收益率
        days = (df.index[-1] - df.index[0]).days
        years = max(days / 365.25, 1/365.25)  # 至少1天
        annual_return = (1 + total_return) ** (1/years) - 1
        
        return {
            'strategy_info': strategy.get_strategy_info(),
            'period': {
                'start_date': df.index[0],
                'end_date': df.index[-1],
                'days': days,
                'years': years
            },
            'capital': {
                'initial_capital': self.initial_capital,
                'final_equity': final_equity,
                'total_return': total_return,
                'annual_return': annual_return,
                'total_commission': self.portfolio.total_commission
            },
            'risk_metrics': {
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'volatility': equity_returns.std() * np.sqrt(252)
            },
            'trade_statistics': trade_stats,
            'equity_curve': equity_df,
            'trades': trades_df,
            'signals_summary': strategy.get_signal_summary(df)
        }
    
    def _calculate_trade_statistics(self, trades_df: pd.DataFrame, 
                                   price_df: pd.DataFrame) -> Dict:
        """
        计算交易统计信息
        
        Args:
            trades_df: 交易记录DataFrame
            price_df: 价格数据DataFrame
            
        Returns:
            Dict: 交易统计信息
        """
        if trades_df.empty:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0,
                'avg_trade_return': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_holding_period': 0
            }
        
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['trade_type'] == 'BUY'])
        sell_trades = len(trades_df[trades_df['trade_type'] == 'SELL'])
        
        # 计算交易对收益
        trade_returns = []
        holding_periods = []
        
        buy_trades_list = trades_df[trades_df['trade_type'] == 'BUY'].to_dict('records')
        sell_trades_list = trades_df[trades_df['trade_type'] == 'SELL'].to_dict('records')
        
        # 配对买卖交易
        for i, buy_trade in enumerate(buy_trades_list):
            if i < len(sell_trades_list):
                sell_trade = sell_trades_list[i]
                
                # 计算收益率
                buy_cost = buy_trade['value'] + buy_trade['commission']
                sell_proceeds = sell_trade['value'] - sell_trade['commission']
                trade_return = (sell_proceeds - buy_cost) / buy_cost
                trade_returns.append(trade_return)
                
                # 计算持有期
                holding_period = (sell_trade['timestamp'] - buy_trade['timestamp']).days
                holding_periods.append(holding_period)
        
        # 计算统计指标
        if trade_returns:
            win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns)
            avg_trade_return = np.mean(trade_returns)
            best_trade = max(trade_returns)
            worst_trade = min(trade_returns)
        else:
            win_rate = avg_trade_return = best_trade = worst_trade = 0
        
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'completed_round_trips': len(trade_returns),
            'win_rate': win_rate,
            'avg_trade_return': avg_trade_return,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_holding_period': avg_holding_period,
            'trade_returns': trade_returns
        }
    
    def get_backtest_summary(self) -> Dict:
        """
        获取回测摘要信息
        
        Returns:
            Dict: 回测摘要
        """
        if not self.equity_curve:
            return {}
        
        final_equity = self.equity_curve[-1]['equity']
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'total_commission': self.portfolio.total_commission,
            'commission_rate': self.commission
        }