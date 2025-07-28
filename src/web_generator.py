#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web报告生成器模块
用于将回测结果生成为美观的HTML报告
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
import webbrowser
from pathlib import Path


class WebReportGenerator:
    """Web报告生成器"""
    
    def __init__(self, template_dir: str = None, output_dir: str = None):
        """
        初始化Web报告生成器
        
        Args:
            template_dir: 模板文件目录
            output_dir: 输出目录
        """
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent
        
        # 设置模板目录
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = self.project_root / "web_templates"
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.project_root / "web_reports"
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"模板目录: {self.template_dir}")
        print(f"输出目录: {self.output_dir}")
    
    def generate_report(self, results: Dict[str, Any], analysis: Dict[str, Any], symbol: str, 
                       auto_open: bool = False) -> str:
        """
        生成Web报告
        
        Args:
            results: 回测结果数据
            analysis: 分析结果数据
            symbol: 交易标的符号
            auto_open: 是否自动打开报告
        
        Returns:
            生成的报告文件路径
        """
        try:
            print("开始生成Web报告...")
            
            # 处理数据
            processed_data = self._process_data(results, analysis, symbol)
            
            # 生成报告文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{symbol}_backtest_report_{timestamp}.html"
            report_path = self.output_dir / report_filename
            
            # 复制静态资源
            self._copy_assets()
            
            # 生成HTML文件
            self._generate_html(processed_data, report_path)
            
            print(f"Web报告生成成功: {report_path}")
            
            # 自动打开报告
            if auto_open:
                self._open_report(report_path)
            
            return str(report_path)
            
        except Exception as e:
            print(f"生成Web报告失败: {e}")
            raise
    
    def _process_data(self, results: Dict[str, Any], analysis: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        处理回测数据，转换为前端需要的格式
        
        Args:
            results: 原始回测结果
            analysis: 分析结果数据
            symbol: 交易标的符号
        
        Returns:
            处理后的数据
        """
        # 获取期间信息
        period_info = results.get('period', {})
        start_date = period_info.get('start_date', 'N/A')
        end_date = period_info.get('end_date', 'N/A')
        
        # 基本信息
        strategy_info = results.get('strategy_info', {})
        basic_info = {
            'symbol': symbol,
            'strategy': strategy_info.get('name', '未知策略') if isinstance(strategy_info, dict) else str(strategy_info),
            'period': f"{start_date} 至 {end_date}",
            'generated_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 资金信息
        capital_info = results.get('capital', {})
        
        # 风险指标 - 处理百分比数据
        raw_risk_metrics = results.get('risk_metrics', {})
        raw_performance_metrics = analysis.get('performance_metrics', {})
        raw_drawdown = analysis.get('drawdown_analysis', {})
        raw_benchmark = analysis.get('benchmark_comparison', {})
        risk_metrics = {
            'max_drawdown': raw_risk_metrics.get('max_drawdown', 0) * 100,  # 转换为百分比
            'volatility': raw_risk_metrics.get('volatility', 0) * 100,  # 转换为百分比
            'sharpe_ratio': raw_risk_metrics.get('sharpe_ratio', 0),
            'sortino_ratio': raw_risk_metrics.get('sortino_ratio', 0),  # 添加索提诺比率
            'calmar_ratio': raw_performance_metrics.get('calmar_ratio', 0),  # 从performance_metrics获取
            'information_ratio': raw_benchmark.get('information_ratio', 0),
            'avg_drawdown': raw_drawdown.get('avg_drawdown', 0) * 100,  # 转换为百分比
            'drawdown_periods': raw_drawdown.get('drawdown_periods', 0), # 回撤次数
            'longest_drawdown_days': raw_drawdown.get('longest_drawdown_days', 0),
            'current_drawdown': raw_drawdown.get('current_drawdown', 0) * 100
        }
        
        # 交易统计 - 处理百分比和其他数据
        raw_trade_stats = results.get('trade_statistics', {})
        trade_stats = {
            'total_trades': raw_trade_stats.get('total_trades', 0),
            'win_rate': raw_trade_stats.get('win_rate', 0) * 100,  # 转换为百分比
            'avg_holding_days': raw_trade_stats.get('avg_holding_period', 0),
            'profit_factor': raw_performance_metrics.get('profit_factor', 0),  # 从performance_metrics获取
            'winning_trades': raw_trade_stats.get('winning_trades', 0),
            'losing_trades': raw_trade_stats.get('losing_trades', 0)
        }
        
        # 合并性能指标 - 将小数形式的百分比转换为百分比数值
        performance_metrics = {
            'initial_capital': capital_info.get('initial_capital', 0),
            'final_equity': capital_info.get('final_equity', 0),
            'total_return': capital_info.get('total_return', 0) * 100,  # 转换为百分比
            'annual_return': capital_info.get('annual_return', 0) * 100,  # 转换为百分比
            'total_commission': capital_info.get('total_commission', 0),
            'max_drawdown': raw_risk_metrics.get('max_drawdown', 0) * 100,  # 转换为百分比
            'volatility': raw_risk_metrics.get('volatility', 0) * 100,  # 转换为百分比
            'sharpe_ratio': raw_risk_metrics.get('sharpe_ratio', 0),
            'profit_factor': raw_performance_metrics.get('profit_factor', 0)  # 从performance_metrics获取
        }
        
        # 处理交易记录
        trades = self._process_trades(results.get('trades'))
        
        # 处理资金曲线数据
        equity_curve = self._process_equity_curve(results.get('equity_curve'))
        
        # 处理回撤数据 - 从资金曲线计算
        drawdown_data = self._calculate_drawdown_from_equity(equity_curve)
        
        # 基准比较数据
        benchmark_info = analysis.get('benchmark_comparison', {})
        benchmark_data = {
            'buy_hold_return': benchmark_info.get('buy_hold_return', 0),  # 保持原始小数形式
            'excess_return': benchmark_info.get('excess_return', 0),  # 保持原始小数形式
            'outperformed': bool(benchmark_info.get('outperformance', False)),  # 确保是布尔值
            'information_ratio': benchmark_info.get('information_ratio', 0)
        }
        
        return {
            'basicInfo': basic_info,
            'performanceMetrics': performance_metrics,
            'riskMetrics': risk_metrics,
            'tradeStatistics': trade_stats,
            'trades': trades,
            'equityCurve': equity_curve,
            'drawdownData': drawdown_data,
            'benchmarkData': benchmark_data
        }
    
    def _process_trades(self, trades) -> list:
        """
        处理交易记录数据
        
        Args:
            trades: 原始交易记录 (DataFrame或list)
        
        Returns:
            处理后的交易记录
        """
        processed_trades = []
        
        if trades is None:
            return processed_trades
        
        # 如果是DataFrame，转换为字典列表
        if hasattr(trades, 'to_dict'):
            trades_list = trades.to_dict('records')
        elif isinstance(trades, list):
            trades_list = trades
        else:
            return processed_trades
        
        for i, trade in enumerate(trades_list, 1):
            processed_trade = {
                'id': i,
                'timestamp': str(trade.get('timestamp', '')),
                'type': trade.get('trade_type', trade.get('type', '')),
                'price': float(trade.get('price', 0)),
                'quantity': float(trade.get('quantity', 0)),
                'amount': float(trade.get('value', trade.get('amount', 0))),
                'commission': float(trade.get('commission', 0))
            }
            processed_trades.append(processed_trade)
        
        return processed_trades
    
    def _process_equity_curve(self, equity_data) -> list:
        """
        处理资金曲线数据
        
        Args:
            equity_data: 原始资金曲线数据 (DataFrame或list)
        
        Returns:
            处理后的资金曲线数据
        """
        if equity_data is None:
            return []
        
        processed_data = []
        
        # 如果是DataFrame
        if hasattr(equity_data, 'index') and hasattr(equity_data, 'equity'):
            for timestamp, equity in equity_data['equity'].items():
                processed_data.append({
                    'date': str(timestamp),
                    'equity': float(equity)
                })
        elif isinstance(equity_data, list):
            for point in equity_data:
                if isinstance(point, dict):
                    processed_data.append({
                        'date': str(point.get('timestamp', point.get('date', ''))),
                        'equity': float(point.get('equity', 0))
                    })
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    processed_data.append({
                        'date': str(point[0]),
                        'equity': float(point[1])
                    })
        
        return processed_data
    
    def _process_drawdown_data(self, drawdown_data: list) -> list:
        """
        处理回撤数据
        
        Args:
            drawdown_data: 原始回撤数据
        
        Returns:
            处理后的回撤数据
        """
        if not drawdown_data:
            return []
        
        processed_data = []
        for point in drawdown_data:
            if isinstance(point, dict):
                processed_data.append({
                    'date': point.get('date', ''),
                    'drawdown': float(point.get('drawdown', 0))
                })
            elif isinstance(point, (list, tuple)) and len(point) >= 2:
                processed_data.append({
                    'date': str(point[0]),
                    'drawdown': float(point[1])
                })
        
        return processed_data
    
    def _calculate_drawdown_from_equity(self, equity_curve: list) -> list:
        """
        从资金曲线计算回撤数据
        
        Args:
            equity_curve: 资金曲线数据
        
        Returns:
            回撤数据
        """
        if not equity_curve:
            return []
        
        drawdown_data = []
        peak = 0
        
        for point in equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            
            drawdown = (equity - peak) / peak if peak > 0 else 0
            drawdown_data.append({
                'date': point['date'],
                'drawdown': drawdown * 100  # 转换为百分比
            })
        
        return drawdown_data
    
    def _process_benchmark_data(self, benchmark: dict) -> dict:
        """
        处理基准数据
        
        Args:
            benchmark: 原始基准数据
        
        Returns:
            处理后的基准数据
        """
        if not benchmark:
            return {}
        
        return {
            'name': benchmark.get('name', '基准'),
            'total_return': float(benchmark.get('total_return', 0)),
            'annual_return': float(benchmark.get('annual_return', 0)),
            'volatility': float(benchmark.get('volatility', 0)),
            'sharpe_ratio': float(benchmark.get('sharpe_ratio', 0)),
            'max_drawdown': float(benchmark.get('max_drawdown', 0))
        }
    
    def _copy_assets(self):
        """
        复制静态资源文件到输出目录
        """
        assets_src = self.template_dir / "assets"
        assets_dst = self.output_dir / "assets"
        
        if assets_src.exists():
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)
            print(f"静态资源已复制到: {assets_dst}")
        else:
            print(f"警告: 静态资源目录不存在: {assets_src}")
    
    def _generate_html(self, data: Dict[str, Any], output_path: Path):
        """
        生成HTML文件
        
        Args:
            data: 处理后的数据
            output_path: 输出文件路径
        """
        try:
            from jinja2 import Template
            
            # 读取HTML模板
            template_path = self.template_dir / "index.html"
            
            if not template_path.exists():
                raise FileNotFoundError(f"HTML模板文件不存在: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 创建Jinja2模板
            template = Template(template_content)
            
            # 准备渲染数据
            render_data = data.copy()
            render_data['data_json'] = json.dumps({
                'equityCurve': data.get('equityCurve', []),
                'drawdownData': data.get('drawdownData', []),
                'trades': data.get('trades', []),
                'performanceMetrics': data.get('performanceMetrics', {}),
                'riskMetrics': data.get('riskMetrics', {}),
                'tradeStatistics': data.get('tradeStatistics', {}),
                'basicInfo': data.get('basicInfo', {}),
                'benchmarkData': data.get('benchmarkData', {})
            }, ensure_ascii=False, indent=2)
            
            # 渲染模板
            rendered_html = template.render(**render_data)
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            print(f"HTML文件已生成: {output_path}")
            
        except ImportError:
            print("警告: 未安装jinja2，使用简单的数据注入方式")
            # 读取HTML模板
            template_path = self.template_dir / "index.html"
            
            if not template_path.exists():
                raise FileNotFoundError(f"HTML模板文件不存在: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 将数据注入到模板中
            data_json = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 替换数据占位符
            html_content = template_content.replace(
                '// DATA_PLACEHOLDER',
                f'window.reportData = {data_json};'
            )
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML文件已生成: {output_path}")
    
    def _open_report(self, report_path: Path):
        """
        在浏览器中打开报告
        
        Args:
            report_path: 报告文件路径
        """
        try:
            # 转换为file:// URL
            file_url = f"file://{report_path.absolute()}"
            webbrowser.open(file_url)
            print(f"报告已在浏览器中打开: {file_url}")
        except Exception as e:
            print(f"无法自动打开报告: {e}")
            print(f"请手动打开: {report_path}")


def create_web_report(results: Dict[str, Any], analysis: Dict[str, Any], symbol: str, 
                     auto_open: bool = False, 
                     template_dir: str = None,
                     output_dir: str = None) -> str:
    """
    便捷函数：创建Web报告
    
    Args:
        results: 回测结果数据
        analysis: 分析结果数据
        symbol: 交易标的符号
        auto_open: 是否自动打开报告
        template_dir: 模板目录
        output_dir: 输出目录
    
    Returns:
        生成的报告文件路径
    """
    generator = WebReportGenerator(template_dir, output_dir)
    return generator.generate_report(results, analysis, symbol, auto_open)


if __name__ == "__main__":
    # 测试代码
    test_results = {
        'strategy': '测试策略',
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'performance_metrics': {
            'total_return': 0.15,
            'annual_return': 0.15,
            'max_drawdown': -0.08,
            'sharpe_ratio': 1.2,
            'volatility': 0.12
        },
        'trade_statistics': {
            'total_trades': 50,
            'winning_trades': 30,
            'losing_trades': 20,
            'win_rate': 0.6
        },
        'trades': [
            {
                'timestamp': '2023-01-15 09:30:00',
                'type': 'BUY',
                'price': 100.0,
                'quantity': 100,
                'amount': 10000.0,
                'commission': 5.0
            }
        ]
    }
    
    try:
        report_path = create_web_report(test_results, 'TEST', auto_open=True)
        print(f"测试报告已生成: {report_path}")
    except Exception as e:
        print(f"测试失败: {e}")