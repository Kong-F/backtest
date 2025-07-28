#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币投资回测系统 - 主程序

基于EMA通道策略的加密货币投资回测工具
支持多种代币、时间周期和EMA参数配置

作者: Solo Coding
日期: 2024
"""

import argparse
import sys
from datetime import datetime
from typing import List, Dict, Any

from src.data_fetcher import DataFetcher
from src.strategy import EMAChannelStrategy
from src.backtest_engine import BacktestEngine
from src.analyzer import ResultAnalyzer
from src.config import Config, Constants
from src.utils import setup_logging, validate_date_format
from src.web_generator import create_web_report


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='多市场投资回测系统 - 基于EMA通道策略，支持加密货币、美股、港股、A股',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 加密货币回测
  python main.py --symbol BTC --start-date 2024-01-01 --end-date 2025-01-01 --interval 1d --ema 33
  python main.py --symbol ETH --start-date 2023-06-01 --end-date 2024-06-01 --interval 4h --ema 20,30,33
  
  # 美股回测
  python main.py --symbol AAPL --market-type us_stock --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
  python main.py --symbol TSLA --data-source yfinance --start-date 2023-01-01 --end-date 2024-01-01 --ema 20,33
  
  # 港股回测
  python main.py --symbol 0700 --market-type hk_stock --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
  
  # A股回测
  python main.py --symbol 600519 --market-type cn_stock --data-source akshare --start-date 2024-01-01 --end-date 2024-12-31 --ema 33
        """
    )
    
    # 必需参数
    parser.add_argument(
        '--symbol', '-s',
        type=str,
        required=True,
        help='交易对/股票代码 (例如: BTC, ETH, AAPL, 0700, 600519)'
    )
    
    parser.add_argument(
        '--market-type', '-m',
        type=str,
        choices=['crypto', 'us_stock', 'hk_stock', 'cn_stock', 'h_stock'],
        help='市场类型 (自动判断如果未指定)'
    )
    
    parser.add_argument(
        '--data-source', '-d',
        type=str,
        choices=['yfinance', 'binance', 'akshare'],
        default='yfinance',
        help='数据源 (默认: yfinance)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='回测开始日期 (格式: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='回测结束日期 (格式: YYYY-MM-DD)'
    )
    
    # 可选参数
    parser.add_argument(
        '--interval', '-i',
        type=str,
        default='1d',
        choices=['1h', '4h', '1d'],
        help='K线时间间隔 (默认: 1d)'
    )
    
    parser.add_argument(
        '--ema', '-e',
        type=str,
        default='33',
        help='EMA周期参数，支持单个值或逗号分隔的多个值 (例如: 33 或 20,30,33)'
    )
    
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=10000.0,
        help='初始资金 (默认: 10000)'
    )
    
    parser.add_argument(
        '--commission',
        type=float,
        default=0.001,
        help='交易手续费率 (默认: 0.001 即 0.1%%)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./results',
        help='结果输出目录 (默认: ./results)'
    )
    
    parser.add_argument(
        '--save-plots',
        action='store_true',
        help='保存图表到文件'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    
    parser.add_argument(
        '--web-report', '-w',
        action='store_true',
        help='生成Web格式的回测报告'
    )
    
    parser.add_argument(
        '--auto-open',
        action='store_true',
        help='自动在浏览器中打开Web报告 (需要配合 --web-report 使用)'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    验证命令行参数的有效性
    
    Args:
        args: 命令行参数对象
        
    Returns:
        bool: 参数是否有效
    """
    # 验证日期格式
    if not validate_date_format(args.start_date):
        print(f"错误: 开始日期格式无效: {args.start_date}")
        return False
        
    if not validate_date_format(args.end_date):
        print(f"错误: 结束日期格式无效: {args.end_date}")
        return False
    
    # 验证日期逻辑
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    if start_date >= end_date:
        print("错误: 开始日期必须早于结束日期")
        return False
    
    # 验证EMA参数
    try:
        ema_values = [int(x.strip()) for x in args.ema.split(',')]
        if any(ema <= 0 for ema in ema_values):
            print("错误: EMA参数必须为正整数")
            return False
    except ValueError:
        print(f"错误: EMA参数格式无效: {args.ema}")
        return False
    
    # 验证资金和手续费
    if args.initial_capital <= 0:
        print("错误: 初始资金必须大于0")
        return False
        
    if args.commission < 0 or args.commission >= 1:
        print("错误: 手续费率必须在0到1之间")
        return False
    
    return True


def run_single_backtest(config: Config, ema_period: int) -> Dict[str, Any]:
    """
    运行单个EMA参数的回测
    
    Args:
        config: 配置对象
        ema_period: EMA周期
        
    Returns:
        Dict[str, Any]: 回测结果
    """
    print(f"\n{'='*60}")
    print(f"开始回测 - EMA周期: {ema_period}")
    print(f"{'='*60}")
    
    # 获取数据
    print("正在获取历史数据...")
    data_fetcher = DataFetcher(
        primary_source=config.data_source,
        market_type=config.market_type
    )
    df = data_fetcher.fetch_data(
        symbol=config.symbol,
        start_date=config.start_date,
        end_date=config.end_date,
        interval=config.interval
    )
    
    if df is None or df.empty:
        print("错误: 无法获取数据")
        return None
    
    print(f"成功获取 {len(df)} 条数据记录")
    
    # 初始化策略
    strategy = EMAChannelStrategy(ema_period=ema_period)
    
    # 运行回测
    print("正在运行回测...")
    engine = BacktestEngine(
        initial_capital=config.initial_capital,
        commission=config.commission
    )
    
    results = engine.run_backtest(df, strategy)
    
    if results is None:
        print("错误: 回测运行失败")
        return None
    
    # 分析结果
    analyzer = ResultAnalyzer()
    analysis = analyzer.analyze_results(results, df)
    
    # 输出结果
    analyzer.print_summary(analysis, results, ema_period)
    
    # 保存图表
    if config.save_plots:
        analyzer.save_plots(
            df, results, analysis, 
            ema_period, config.output_dir, config.symbol
        )
    
    # 生成Web报告
    if hasattr(config, 'web_report') and config.web_report:
        try:
            print("\n正在生成Web报告...")
            web_report_path = create_web_report(
                results=results,
                analysis=analysis,
                symbol=config.symbol,
                auto_open=getattr(config, 'auto_open', False)
            )
            print(f"Web报告已生成: {web_report_path}")
        except Exception as e:
            print(f"生成Web报告失败: {e}")
            if config.verbose:
                import traceback
                traceback.print_exc()
    
    return {
        'ema_period': ema_period,
        'analysis': analysis,
        'results': results
    }


def run_multiple_backtest(config: Config, ema_periods: List[int]) -> List[Dict[str, Any]]:
    """
    运行多个EMA参数的回测对比
    
    Args:
        config: 配置对象
        ema_periods: EMA周期列表
        
    Returns:
        List[Dict[str, Any]]: 所有回测结果
    """
    all_results = []
    
    for ema_period in ema_periods:
        result = run_single_backtest(config, ema_period)
        if result:
            all_results.append(result)
    
    # 对比分析
    if len(all_results) > 1:
        print(f"\n{'='*80}")
        print("EMA参数对比分析")
        print(f"{'='*80}")
        
        analyzer = ResultAnalyzer()
        analyzer.compare_results(all_results)
        
        if config.save_plots:
            analyzer.save_comparison_plot(
                all_results, config.output_dir, config.symbol
            )
    
    return all_results


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 验证参数
    if not validate_arguments(args):
        sys.exit(1)
    
    # 设置日志
    setup_logging(verbose=args.verbose)
    
    # 创建配置对象
    config = Config(
        symbol=args.symbol.upper(),
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval,
        initial_capital=args.initial_capital,
        commission=args.commission,
        output_dir=args.output_dir,
        save_plots=args.save_plots,
        market_type=args.market_type,
        data_source=args.data_source
    )
    
    # 添加Web报告相关配置
    config.web_report = args.web_report
    config.auto_open = args.auto_open
    config.verbose = args.verbose
    
    # 解析EMA参数
    ema_periods = [int(x.strip()) for x in args.ema.split(',')]
    
    print(f"\n{'='*80}")
    print("多市场投资回测系统")
    print(f"{'='*80}")
    print(f"交易对/股票代码: {config.symbol}")
    print(f"市场类型: {config.market_type} ({Constants.MARKET_TYPES.get(config.market_type, config.market_type)})")
    print(f"数据源: {config.data_source}")
    print(f"回测期间: {config.start_date} 至 {config.end_date}")
    print(f"时间间隔: {config.interval}")
    print(f"EMA参数: {ema_periods}")
    print(f"初始资金: ${config.initial_capital:,.2f}")
    print(f"手续费率: {config.commission:.3%}")
    
    try:
        # 运行回测
        if len(ema_periods) == 1:
            run_single_backtest(config, ema_periods[0])
        else:
            run_multiple_backtest(config, ema_periods)
            
        print(f"\n{'='*80}")
        print("回测完成!")
        if config.save_plots:
            print(f"结果已保存到: {config.output_dir}")
        print(f"{'='*80}")
        
    except KeyboardInterrupt:
        print("\n回测被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n回测过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()