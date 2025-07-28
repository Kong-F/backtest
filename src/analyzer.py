#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果分析模块

实现回测结果的统计分析和可视化
"""

import logging
import os
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
from datetime import datetime

from src.config import Constants
from src.utils import format_percentage, format_currency, safe_divide

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ResultAnalyzer:
    """
    结果分析器类
    
    提供回测结果的统计分析和可视化功能
    """
    
    def __init__(self):
        """
        初始化结果分析器
        """
        self.logger = logging.getLogger(__name__)
        
        # 设置绘图样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def analyze_results(self, results: Dict, price_data: pd.DataFrame) -> Dict:
        """
        分析回测结果
        
        Args:
            results: 回测结果字典
            price_data: 原始价格数据
            
        Returns:
            Dict: 分析结果
        """
        if not results or 'equity_curve' not in results:
            self.logger.error("回测结果数据不完整")
            return {}
        
        self.logger.info("开始分析回测结果")
        
        analysis = {
            'performance_metrics': self._calculate_performance_metrics(results),
            'risk_metrics': self._calculate_risk_metrics(results),
            'trade_analysis': self._analyze_trades(results),
            'benchmark_comparison': self._compare_with_benchmark(results, price_data),
            'monthly_returns': self._calculate_monthly_returns(results),
            'drawdown_analysis': self._analyze_drawdowns(results),
            'signal_analysis': self._analyze_signals(results)
        }
        
        self.logger.info("回测结果分析完成")
        return analysis
    
    def _calculate_performance_metrics(self, results: Dict) -> Dict:
        """
        计算性能指标
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 性能指标
        """
        capital = results.get('capital', {})
        period = results.get('period', {})
        
        total_return = capital.get('total_return', 0)
        annual_return = capital.get('annual_return', 0)
        
        # 计算CAGR（复合年增长率）
        years = period.get('years', 1)
        cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        return {
            'initial_capital': capital.get('initial_capital', 0),
            'final_equity': capital.get('final_equity', 0),
            'total_return': total_return,
            'annual_return': annual_return,
            'cagr': cagr,
            'total_commission': capital.get('total_commission', 0),
            'commission_impact': safe_divide(capital.get('total_commission', 0), 
                                           capital.get('initial_capital', 1)),
            'profit_factor': self._calculate_profit_factor(results),
            'calmar_ratio': self._calculate_calmar_ratio(results)
        }
    
    def _calculate_risk_metrics(self, results: Dict) -> Dict:
        """
        计算风险指标
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 风险指标
        """
        risk_metrics = results.get('risk_metrics', {})
        equity_curve = results.get('equity_curve', pd.DataFrame())
        
        if equity_curve.empty:
            return risk_metrics
        
        # 计算VaR和CVaR
        returns = equity_curve['equity'].pct_change().dropna()
        var_95 = returns.quantile(0.05) if len(returns) > 0 else 0
        cvar_95 = returns[returns <= var_95].mean() if len(returns) > 0 else 0
        
        # 计算下行偏差
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        
        # 计算Sortino比率
        mean_return = returns.mean()
        sortino_ratio = safe_divide(mean_return, downside_deviation) * np.sqrt(252)
        
        risk_metrics.update({
            'var_95': var_95,
            'cvar_95': cvar_95,
            'downside_deviation': downside_deviation,
            'sortino_ratio': sortino_ratio,
            'skewness': returns.skew() if len(returns) > 0 else 0,
            'kurtosis': returns.kurtosis() if len(returns) > 0 else 0
        })
        
        return risk_metrics
    
    def _analyze_trades(self, results: Dict) -> Dict:
        """
        分析交易记录
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 交易分析结果
        """
        trade_stats = results.get('trade_statistics', {})
        trades_df = results.get('trades', pd.DataFrame())
        
        if trades_df.empty:
            return trade_stats
        
        # 计算交易频率
        period = results.get('period', {})
        days = period.get('days', 1)
        trade_frequency = len(trades_df) / days * 365 if days > 0 else 0
        
        # 分析交易时间分布
        if 'timestamp' in trades_df.columns:
            trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour
            trades_df['weekday'] = pd.to_datetime(trades_df['timestamp']).dt.weekday
            
            hourly_distribution = trades_df['hour'].value_counts().sort_index()
            weekly_distribution = trades_df['weekday'].value_counts().sort_index()
        else:
            hourly_distribution = pd.Series()
            weekly_distribution = pd.Series()
        
        trade_stats.update({
            'trade_frequency_annual': trade_frequency,
            'avg_trade_value': trades_df['value'].mean() if 'value' in trades_df.columns else 0,
            'max_trade_value': trades_df['value'].max() if 'value' in trades_df.columns else 0,
            'min_trade_value': trades_df['value'].min() if 'value' in trades_df.columns else 0,
            'hourly_distribution': hourly_distribution.to_dict(),
            'weekly_distribution': weekly_distribution.to_dict()
        })
        
        return trade_stats
    
    def _compare_with_benchmark(self, results: Dict, price_data: pd.DataFrame) -> Dict:
        """
        与基准（买入持有）比较
        
        Args:
            results: 回测结果
            price_data: 价格数据
            
        Returns:
            Dict: 基准比较结果
        """
        if price_data.empty or 'Close' not in price_data.columns:
            return {}
        
        # 计算买入持有策略收益
        initial_price = price_data['Close'].iloc[0]
        final_price = price_data['Close'].iloc[-1]
        buy_hold_return = (final_price - initial_price) / initial_price
        
        # 策略收益
        strategy_return = results.get('capital', {}).get('total_return', 0)
        
        # 计算超额收益
        excess_return = strategy_return - buy_hold_return
        
        # 计算信息比率
        equity_curve = results.get('equity_curve', pd.DataFrame())
        if not equity_curve.empty and len(price_data) == len(equity_curve):
            strategy_returns = equity_curve['equity'].pct_change().fillna(0)
            benchmark_returns = price_data['Close'].pct_change().fillna(0)
            
            excess_returns = strategy_returns - benchmark_returns
            information_ratio = safe_divide(excess_returns.mean(), excess_returns.std()) * np.sqrt(252)
        else:
            information_ratio = 0
        
        return {
            'buy_hold_return': buy_hold_return,
            'strategy_return': strategy_return,
            'excess_return': excess_return,
            'information_ratio': information_ratio,
            'outperformance': excess_return > 0
        }
    
    def _calculate_monthly_returns(self, results: Dict) -> Dict:
        """
        计算月度收益
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 月度收益分析
        """
        equity_curve = results.get('equity_curve', pd.DataFrame())
        
        if equity_curve.empty:
            return {}
        
        # 重采样为月度数据
        monthly_equity = equity_curve['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        return {
            'monthly_returns': monthly_returns.to_dict(),
            'best_month': monthly_returns.max(),
            'worst_month': monthly_returns.min(),
            'positive_months': (monthly_returns > 0).sum(),
            'negative_months': (monthly_returns < 0).sum(),
            'avg_monthly_return': monthly_returns.mean(),
            'monthly_volatility': monthly_returns.std()
        }
    
    def _analyze_drawdowns(self, results: Dict) -> Dict:
        """
        分析回撤
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 回撤分析
        """
        equity_curve = results.get('equity_curve', pd.DataFrame())
        
        if equity_curve.empty:
            return {}
        
        equity = equity_curve['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        
        # 找出回撤期间
        drawdown_periods = []
        in_drawdown = False
        start_date = None
        
        for date, dd in drawdown.items():
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                start_date = date
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                if start_date:
                    drawdown_periods.append({
                        'start': start_date,
                        'end': date,
                        'duration': (date - start_date).days,
                        'max_drawdown': drawdown[start_date:date].min()
                    })
        
        # 如果回测结束时仍在回撤中
        if in_drawdown and start_date:
            drawdown_periods.append({
                'start': start_date,
                'end': equity.index[-1],
                'duration': (equity.index[-1] - start_date).days,
                'max_drawdown': drawdown[start_date:].min()
            })
        
        return {
            'max_drawdown': drawdown.min(),
            'avg_drawdown': drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0,
            'drawdown_periods': len(drawdown_periods),
            'longest_drawdown_days': max([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0,
            'deepest_drawdown': min([p['max_drawdown'] for p in drawdown_periods]) if drawdown_periods else 0,
            'current_drawdown': drawdown.iloc[-1],
            'drawdown_details': drawdown_periods
        }
    
    def _analyze_signals(self, results: Dict) -> Dict:
        """
        分析交易信号
        
        Args:
            results: 回测结果
            
        Returns:
            Dict: 信号分析
        """
        return results.get('signals_summary', {})
    
    def _calculate_profit_factor(self, results: Dict) -> float:
        """
        计算盈利因子
        
        Args:
            results: 回测结果
            
        Returns:
            float: 盈利因子
        """
        trade_stats = results.get('trade_statistics', {})
        trade_returns = trade_stats.get('trade_returns', [])
        
        if not trade_returns:
            return 0
        
        gross_profit = sum(r for r in trade_returns if r > 0)
        gross_loss = abs(sum(r for r in trade_returns if r < 0))
        
        return safe_divide(gross_profit, gross_loss)
    
    def _calculate_calmar_ratio(self, results: Dict) -> float:
        """
        计算卡尔玛比率
        
        Args:
            results: 回测结果
            
        Returns:
            float: 卡尔玛比率
        """
        annual_return = results.get('capital', {}).get('annual_return', 0)
        max_drawdown = abs(results.get('risk_metrics', {}).get('max_drawdown', 0))
        
        return safe_divide(annual_return, max_drawdown)
    
    def print_summary(self, analysis: Dict, results: Dict, ema_period: int):
        """
        打印回测结果摘要
        
        Args:
            analysis: 分析结果
            ema_period: EMA周期
        """
        print(f"\n{'='*60}")
        print(f"EMA{ema_period} 策略回测结果摘要")
        print(f"{'='*60}")
        
        # 性能指标
        perf = analysis.get('performance_metrics', {})
        print(f"\n📈 性能指标:")
        print(f"  初始资金: {format_currency(perf.get('initial_capital', 0))}")
        print(f"  最终资金: {format_currency(perf.get('final_equity', 0))}")
        print(f"  总收益率: {format_percentage(perf.get('total_return', 0))}")
        print(f"  年化收益率: {format_percentage(perf.get('annual_return', 0))}")
        print(f"  复合年增长率: {format_percentage(perf.get('cagr', 0))}")
        print(f"  盈利因子: {perf.get('profit_factor', 0):.2f}")
        
        # 风险指标
        risk = analysis.get('risk_metrics', {})
        print(f"\n⚠️  风险指标:")
        print(f"  最大回撤: {format_percentage(risk.get('max_drawdown', 0))}")
        print(f"  夏普比率: {risk.get('sharpe_ratio', 0):.2f}")
        print(f"  索提诺比率: {risk.get('sortino_ratio', 0):.2f}")
        print(f"  卡尔玛比率: {perf.get('calmar_ratio', 0):.2f}")
        print(f"  波动率: {format_percentage(risk.get('volatility', 0))}")
        
        # 交易统计
        trade = analysis.get('trade_analysis', {})
        print(f"\n💼 交易统计:")
        print(f"  总交易次数: {trade.get('total_trades', 0)}")
        print(f"  完整交易对: {trade.get('completed_round_trips', 0)}")
        print(f"  胜率: {format_percentage(trade.get('win_rate', 0))}")
        print(f"  平均交易收益: {format_percentage(trade.get('avg_trade_return', 0))}")
        print(f"  最佳交易: {format_percentage(trade.get('best_trade', 0))}")
        print(f"  最差交易: {format_percentage(trade.get('worst_trade', 0))}")
        print(f"  平均持仓天数: {trade.get('avg_holding_period', 0):.1f}")
        
        # 交易详情
        trades_df = results.get('trades', pd.DataFrame())
        if not trades_df.empty:
            print(f"\n📋 交易详情:")
            print(f"{'序号':<6} {'时间':<20} {'类型':<6} {'价格':<12} {'数量':<15} {'交易额':<12} {'手续费':<10}")
            print("-" * 85)
            
            for _, trade_row in trades_df.iterrows():
                timestamp_str = trade_row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                trade_type = trade_row['trade_type']
                price = trade_row['price']
                quantity = trade_row['quantity']
                value = trade_row['value']
                commission = trade_row['commission']
                
                print(f"{trade_row['trade_id']:<6} {timestamp_str:<20} {trade_type:<6} "
                      f"${price:<11.2f} {quantity:<15.6f} ${value:<11.2f} ${commission:<9.2f}")
        
        # 基准比较
        benchmark = analysis.get('benchmark_comparison', {})
        if benchmark:
            print(f"\n📊 基准比较:")
            print(f"  买入持有收益: {format_percentage(benchmark.get('buy_hold_return', 0))}")
            print(f"  策略超额收益: {format_percentage(benchmark.get('excess_return', 0))}")
            print(f"  信息比率: {benchmark.get('information_ratio', 0):.2f}")
            
            if benchmark.get('outperformance', False):
                print(f"  ✅ 策略跑赢基准")
            else:
                print(f"  ❌ 策略跑输基准")
        
        # 回撤分析
        drawdown = analysis.get('drawdown_analysis', {})
        if drawdown:
            print(f"\n📉 回撤分析:")
            print(f"  最大回撤: {format_percentage(drawdown.get('max_drawdown', 0))}")
            print(f"  平均回撤: {format_percentage(drawdown.get('avg_drawdown', 0))}")
            print(f"  回撤次数: {drawdown.get('drawdown_periods', 0)}")
            print(f"  最长回撤天数: {drawdown.get('longest_drawdown_days', 0)}")
            print(f"  当前回撤: {format_percentage(drawdown.get('current_drawdown', 0))}")
    
    def save_plots(self, price_data: pd.DataFrame, results: Dict, analysis: Dict,
                   ema_period: int, output_dir: str, symbol: str):
        """
        保存图表
        
        Args:
            price_data: 价格数据
            results: 回测结果
            analysis: 分析结果
            ema_period: EMA周期
            output_dir: 输出目录
            symbol: 交易对符号
        """
        self.logger.info(f"开始生成图表，保存到: {output_dir}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成主要图表
        self._plot_price_and_signals(price_data, results, ema_period, output_dir, symbol)
        self._plot_equity_curve(results, analysis, ema_period, output_dir, symbol)
        self._plot_drawdown(results, ema_period, output_dir, symbol)
        self._plot_monthly_returns(analysis, ema_period, output_dir, symbol)
        
        self.logger.info("图表生成完成")
    
    def _plot_price_and_signals(self, price_data: pd.DataFrame, results: Dict,
                               ema_period: int, output_dir: str, symbol: str):
        """
        绘制价格走势和交易信号图
        """
        fig, ax = plt.subplots(figsize=Constants.OUTPUT_CONFIG['chart_figsize'])
        
        # 绘制价格
        ax.plot(price_data.index, price_data['Close'], 
               label='收盘价', color=Constants.CHART_COLORS['price'], linewidth=1)
        
        # 绘制EMA通道
        if 'ema_upper' in price_data.columns and 'ema_lower' in price_data.columns:
            ax.plot(price_data.index, price_data['ema_upper'], 
                   label=f'EMA{ema_period}上轨', color=Constants.CHART_COLORS['ema_upper'], linewidth=1)
            ax.plot(price_data.index, price_data['ema_lower'], 
                   label=f'EMA{ema_period}下轨', color=Constants.CHART_COLORS['ema_lower'], linewidth=1)
            
            # 填充通道
            ax.fill_between(price_data.index, price_data['ema_upper'], price_data['ema_lower'],
                           alpha=0.1, color='gray')
        
        # 绘制交易信号
        trades_df = results.get('trades', pd.DataFrame())
        if not trades_df.empty and 'timestamp' in trades_df.columns:
            buy_trades = trades_df[trades_df['trade_type'] == 'BUY']
            sell_trades = trades_df[trades_df['trade_type'] == 'SELL']
            
            if not buy_trades.empty:
                ax.scatter(buy_trades['timestamp'], buy_trades['price'],
                          marker='^', color=Constants.CHART_COLORS['buy_signal'], 
                          s=100, label='买入信号', zorder=5)
            
            if not sell_trades.empty:
                ax.scatter(sell_trades['timestamp'], sell_trades['price'],
                          marker='v', color=Constants.CHART_COLORS['sell_signal'], 
                          s=100, label='卖出信号', zorder=5)
        
        ax.set_title(f'{symbol} - EMA{ema_period}通道策略交易信号', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('价格 ($)', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{symbol}_EMA{ema_period}_signals.png'), 
                   dpi=Constants.OUTPUT_CONFIG['chart_dpi'], bbox_inches='tight')
        plt.close()
    
    def _plot_equity_curve(self, results: Dict, analysis: Dict,
                          ema_period: int, output_dir: str, symbol: str):
        """
        绘制权益曲线图
        """
        equity_curve = results.get('equity_curve', pd.DataFrame())
        if equity_curve.empty:
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=Constants.OUTPUT_CONFIG['chart_figsize'], 
                                      height_ratios=[3, 1])
        
        # 权益曲线
        ax1.plot(equity_curve.index, equity_curve['equity'], 
                label='策略权益', color=Constants.CHART_COLORS['profit'], linewidth=2)
        
        # 基准线（初始资金）
        initial_capital = results.get('capital', {}).get('initial_capital', 10000)
        ax1.axhline(y=initial_capital, color='gray', linestyle='--', alpha=0.7, label='初始资金')
        
        ax1.set_title(f'{symbol} - EMA{ema_period}策略权益曲线', fontsize=16, fontweight='bold')
        ax1.set_ylabel('权益 ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 回撤图
        equity = equity_curve['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        
        ax2.fill_between(equity_curve.index, drawdown, 0, 
                        color=Constants.CHART_COLORS['loss'], alpha=0.7)
        ax2.set_ylabel('回撤', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 格式化y轴为百分比
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
        
        # 格式化x轴日期
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{symbol}_EMA{ema_period}_equity.png'), 
                   dpi=Constants.OUTPUT_CONFIG['chart_dpi'], bbox_inches='tight')
        plt.close()
    
    def _plot_drawdown(self, results: Dict, ema_period: int, output_dir: str, symbol: str):
        """
        绘制回撤分析图
        """
        equity_curve = results.get('equity_curve', pd.DataFrame())
        if equity_curve.empty:
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        equity = equity_curve['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        
        # 绘制回撤
        ax.fill_between(equity_curve.index, drawdown * 100, 0, 
                       color=Constants.CHART_COLORS['loss'], alpha=0.7, label='回撤')
        
        # 标记最大回撤点
        max_dd_idx = drawdown.idxmin()
        max_dd_value = drawdown.min()
        ax.scatter(max_dd_idx, max_dd_value * 100, color='red', s=100, zorder=5)
        ax.annotate(f'最大回撤: {max_dd_value:.2%}', 
                   xy=(max_dd_idx, max_dd_value * 100),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        ax.set_title(f'{symbol} - EMA{ema_period}策略回撤分析', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('回撤 (%)', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{symbol}_EMA{ema_period}_drawdown.png'), 
                   dpi=Constants.OUTPUT_CONFIG['chart_dpi'], bbox_inches='tight')
        plt.close()
    
    def _plot_monthly_returns(self, analysis: Dict, ema_period: int, output_dir: str, symbol: str):
        """
        绘制月度收益热力图
        """
        monthly_data = analysis.get('monthly_returns', {})
        monthly_returns = monthly_data.get('monthly_returns', {})
        
        if not monthly_returns:
            return
        
        # 转换为DataFrame
        returns_series = pd.Series(monthly_returns)
        returns_series.index = pd.to_datetime(returns_series.index)
        
        # 创建年月矩阵
        returns_df = returns_series.to_frame('returns')
        returns_df['year'] = returns_df.index.year
        returns_df['month'] = returns_df.index.month
        
        pivot_table = returns_df.pivot_table(values='returns', index='year', columns='month')
        
        # 绘制热力图
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sns.heatmap(pivot_table * 100, annot=True, fmt='.1f', cmap='RdYlGn', 
                   center=0, ax=ax, cbar_kws={'label': '月度收益 (%)'})
        
        ax.set_title(f'{symbol} - EMA{ema_period}策略月度收益热力图', fontsize=16, fontweight='bold')
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('年份', fontsize=12)
        
        # 设置月份标签
        month_labels = ['1月', '2月', '3月', '4月', '5月', '6月',
                       '7月', '8月', '9月', '10月', '11月', '12月']
        # 只设置实际存在的月份标签
        if pivot_table.shape[1] > 0:
            actual_months = pivot_table.columns.tolist()
            actual_labels = [month_labels[m-1] for m in actual_months if 1 <= m <= 12]
            ax.set_xticklabels(actual_labels)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{symbol}_EMA{ema_period}_monthly.png'), 
                   dpi=Constants.OUTPUT_CONFIG['chart_dpi'], bbox_inches='tight')
        plt.close()
    
    def compare_results(self, all_results: List[Dict]):
        """
        对比多个EMA参数的结果
        
        Args:
            all_results: 所有回测结果列表
        """
        if len(all_results) < 2:
            return
        
        print(f"\n{'='*100}")
        print("EMA参数对比分析")
        print(f"{'='*100}")
        
        # 创建对比表格
        comparison_data = []
        
        for result in all_results:
            ema_period = result['ema_period']
            analysis = result['analysis']
            
            perf = analysis.get('performance_metrics', {})
            risk = analysis.get('risk_metrics', {})
            trade = analysis.get('trade_analysis', {})
            
            comparison_data.append({
                'EMA周期': ema_period,
                '总收益率': format_percentage(perf.get('total_return', 0)),
                '年化收益率': format_percentage(perf.get('annual_return', 0)),
                '最大回撤': format_percentage(risk.get('max_drawdown', 0)),
                '夏普比率': f"{risk.get('sharpe_ratio', 0):.2f}",
                '交易次数': trade.get('total_trades', 0),
                '胜率': format_percentage(trade.get('win_rate', 0)),
                '盈利因子': f"{perf.get('profit_factor', 0):.2f}"
            })
        
        # 转换为DataFrame并打印
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
        
        # 找出最佳参数
        best_return_idx = max(range(len(all_results)), 
                             key=lambda i: all_results[i]['analysis'].get('performance_metrics', {}).get('total_return', 0))
        best_sharpe_idx = max(range(len(all_results)), 
                             key=lambda i: all_results[i]['analysis'].get('risk_metrics', {}).get('sharpe_ratio', 0))
        
        print(f"\n🏆 最佳收益率: EMA{all_results[best_return_idx]['ema_period']} - {format_percentage(all_results[best_return_idx]['analysis'].get('performance_metrics', {}).get('total_return', 0))}")
        print(f"🏆 最佳夏普比率: EMA{all_results[best_sharpe_idx]['ema_period']} - {all_results[best_sharpe_idx]['analysis'].get('risk_metrics', {}).get('sharpe_ratio', 0):.2f}")
    
    def save_comparison_plot(self, all_results: List[Dict], output_dir: str, symbol: str):
        """
        保存参数对比图表
        
        Args:
            all_results: 所有回测结果
            output_dir: 输出目录
            symbol: 交易对符号
        """
        if len(all_results) < 2:
            return
        
        # 提取数据
        ema_periods = []
        total_returns = []
        sharpe_ratios = []
        max_drawdowns = []
        
        for result in all_results:
            ema_periods.append(result['ema_period'])
            total_returns.append(result['analysis'].get('performance_metrics', {}).get('total_return', 0))
            sharpe_ratios.append(result['analysis'].get('risk_metrics', {}).get('sharpe_ratio', 0))
            max_drawdowns.append(abs(result['analysis'].get('risk_metrics', {}).get('max_drawdown', 0)))
        
        # 创建对比图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 总收益率对比
        bars1 = ax1.bar(ema_periods, [r * 100 for r in total_returns], 
                        color=Constants.CHART_COLORS['profit'], alpha=0.7)
        ax1.set_title('总收益率对比', fontweight='bold')
        ax1.set_xlabel('EMA周期')
        ax1.set_ylabel('总收益率 (%)')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, value in zip(bars1, total_returns):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{value:.1%}', ha='center', va='bottom')
        
        # 夏普比率对比
        bars2 = ax2.bar(ema_periods, sharpe_ratios, 
                        color=Constants.CHART_COLORS['ema_upper'], alpha=0.7)
        ax2.set_title('夏普比率对比', fontweight='bold')
        ax2.set_xlabel('EMA周期')
        ax2.set_ylabel('夏普比率')
        ax2.grid(True, alpha=0.3)
        
        for bar, value in zip(bars2, sharpe_ratios):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{value:.2f}', ha='center', va='bottom')
        
        # 最大回撤对比
        bars3 = ax3.bar(ema_periods, [d * 100 for d in max_drawdowns], 
                        color=Constants.CHART_COLORS['loss'], alpha=0.7)
        ax3.set_title('最大回撤对比', fontweight='bold')
        ax3.set_xlabel('EMA周期')
        ax3.set_ylabel('最大回撤 (%)')
        ax3.grid(True, alpha=0.3)
        
        for bar, value in zip(bars3, max_drawdowns):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{value:.1%}', ha='center', va='bottom')
        
        # 风险收益散点图
        ax4.scatter([d * 100 for d in max_drawdowns], [r * 100 for r in total_returns], 
                   s=100, alpha=0.7, c=Constants.CHART_COLORS['buy_signal'])
        
        for i, ema in enumerate(ema_periods):
            ax4.annotate(f'EMA{ema}', 
                        (max_drawdowns[i] * 100, total_returns[i] * 100),
                        xytext=(5, 5), textcoords='offset points')
        
        ax4.set_title('风险收益分布', fontweight='bold')
        ax4.set_xlabel('最大回撤 (%)')
        ax4.set_ylabel('总收益率 (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.suptitle(f'{symbol} - EMA参数对比分析', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{symbol}_EMA_comparison.png'), 
                   dpi=Constants.OUTPUT_CONFIG['chart_dpi'], bbox_inches='tight')
        plt.close()