#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块

支持从多种数据源获取加密货币历史数据
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None

from src.config import Constants, get_symbol_for_source, get_market_type
from src.utils import setup_logging, clean_data, resample_data


class DataFetcher:
    """
    数据获取器类
    
    支持从yfinance、Binance、akshare等数据源获取历史数据
    支持加密货币、美股、港股、A股等多种市场
    """
    
    def __init__(self, primary_source: str = 'yfinance', market_type: str = 'crypto'):
        """
        初始化数据获取器
        
        Args:
            primary_source: 主要数据源
            market_type: 市场类型
        """
        self.primary_source = primary_source
        self.market_type = market_type
        self.logger = logging.getLogger(__name__)
        
        # 设置请求会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=Constants.DATA_SOURCE_CONFIG['yfinance']['retry_count'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 检查akshare可用性
        if not AKSHARE_AVAILABLE and primary_source == 'akshare':
            self.logger.warning("akshare库未安装，无法获取A股数据")
            self.primary_source = 'yfinance'
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str, 
                   interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            symbol: 交易对/股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            
        Returns:
            Optional[pd.DataFrame]: 历史数据，包含OHLCV列
        """
        # 自动判断市场类型
        market_type = get_market_type(symbol)
        self.logger.info(f"开始获取 {symbol} 的历史数据 (市场类型: {Constants.MARKET_TYPES.get(market_type, market_type)})")
        self.logger.info(f"时间范围: {start_date} 至 {end_date}")
        self.logger.info(f"时间间隔: {interval}")
        
        # 根据市场类型选择合适的数据源
        available_sources = Constants.MARKET_DATA_SOURCES.get(market_type, ['yfinance'])
        
        # 确保主要数据源在可用列表中
        if self.primary_source not in available_sources:
            primary_source = available_sources[0]
            self.logger.info(f"数据源 {self.primary_source} 不支持 {market_type}，使用 {primary_source}")
        else:
            primary_source = self.primary_source
        
        # 尝试主要数据源
        df = self._fetch_from_source(symbol, start_date, end_date, interval, primary_source, market_type)

        # 特殊处理某些加密货币的异常情况
        if market_type == 'crypto' and symbol.lower() in ["uni", "pepe"]:
            # yfinance 的某些交易对价格异常
            df = None
        
        # 如果主要数据源失败，尝试备用数据源
        if df is None or df.empty:
            self.logger.warning(f"主要数据源 {primary_source} 获取失败，尝试备用数据源")
            backup_sources = [s for s in available_sources if s != primary_source]
            
            for source in backup_sources:
                df = self._fetch_from_source(symbol, start_date, end_date, interval, source, market_type)
                if df is not None and not df.empty:
                    self.logger.info(f"成功从备用数据源 {source} 获取数据")
                    break
        
        if df is None or df.empty:
            self.logger.error("所有数据源都无法获取数据")
            return None
        
        # 数据清理和验证
        df = self._process_data(df, interval)
        
        if df is None or df.empty:
            self.logger.error("数据处理后为空")
            return None
        
        self.logger.info(f"成功获取 {len(df)} 条数据记录")
        return df
    
    def _fetch_from_source(self, symbol: str, start_date: str, end_date: str, 
                          interval: str, source: str, market_type: str) -> Optional[pd.DataFrame]:
        """
        从指定数据源获取数据
        
        Args:
            symbol: 交易对/股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            source: 数据源名称
            market_type: 市场类型
            
        Returns:
            Optional[pd.DataFrame]: 原始数据
        """
        try:
            if source == 'yfinance':
                return self._fetch_from_yfinance(symbol, start_date, end_date, interval, market_type)
            elif source == 'binance':
                return self._fetch_from_binance(symbol, start_date, end_date, interval, market_type)
            elif source == 'akshare':
                return self._fetch_from_akshare(symbol, start_date, end_date, interval, market_type)
            else:
                self.logger.error(f"不支持的数据源: {source}")
                return None
                
        except Exception as e:
            self.logger.error(f"从 {source} 获取数据时发生错误: {e}")
            return None
    
    def _fetch_from_yfinance(self, symbol: str, start_date: str, end_date: str, 
                            interval: str, market_type: str) -> Optional[pd.DataFrame]:
        """
        从yfinance获取数据
        
        Args:
            symbol: 交易对/股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            market_type: 市场类型
            
        Returns:
            Optional[pd.DataFrame]: yfinance数据
        """
        # 转换符号格式
        yf_symbol = get_symbol_for_source(symbol, 'yfinance', market_type)
        
        # 转换时间间隔格式
        yf_interval = self._convert_interval_for_yfinance(interval)
        if yf_interval is None:
            return None
        
        self.logger.debug(f"从yfinance获取数据: {yf_symbol}, 间隔: {yf_interval}, 市场: {market_type}")
        
        # A股数据yfinance不直接支持
        if market_type == 'cn_stock':
            self.logger.warning("yfinance不支持A股数据，请使用akshare数据源")
            return None
        
        try:
            # 创建ticker对象
            ticker = yf.Ticker(yf_symbol)
            
            # 获取历史数据
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=False
            )
            
            if df.empty:
                self.logger.warning(f"yfinance返回空数据: {yf_symbol}")
                return None
            
            # 重命名列以保持一致性
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # 确保包含必要的列
            required_columns = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"yfinance数据缺少必要列: {required_columns}")
                return None
            
            return df[required_columns + (['Volume'] if 'Volume' in df.columns else [])]
            
        except Exception as e:
            self.logger.error(f"yfinance获取数据失败: {e}")
            return None
    
    def _fetch_from_binance(self, symbol: str, start_date: str, end_date: str, 
                           interval: str, market_type: str) -> Optional[pd.DataFrame]:
        """
        从Binance API获取数据
        
        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            market_type: 市场类型
            
        Returns:
            Optional[pd.DataFrame]: Binance数据
        """
        # Binance主要支持加密货币
        if market_type != 'crypto':
            self.logger.warning(f"Binance不支持 {market_type} 数据")
            return None
        
        # 转换符号格式
        binance_symbol = get_symbol_for_source(symbol, 'binance', market_type)
        
        # 转换时间间隔格式
        binance_interval = self._convert_interval_for_binance(interval)
        if binance_interval is None:
            return None
        
        self.logger.debug(f"从Binance获取数据: {binance_symbol}, 间隔: {binance_interval}")
        
        try:
            # 转换日期为时间戳
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            # 构建API请求
            base_url = Constants.DATA_SOURCE_CONFIG['binance']['base_url']
            endpoint = f"{base_url}/api/v3/klines"
            
            params = {
                'symbol': binance_symbol,
                'interval': binance_interval,
                'startTime': start_timestamp,
                'endTime': end_timestamp,
                'limit': 1000
            }
            
            all_data = []
            current_start = start_timestamp
            
            # 分批获取数据（Binance限制每次最多1000条）
            while current_start < end_timestamp:
                params['startTime'] = current_start
                
                response = self.session.get(
                    endpoint, 
                    params=params,
                    timeout=Constants.DATA_SOURCE_CONFIG['binance']['timeout']
                )
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    break
                
                all_data.extend(data)
                
                # 更新下一批的开始时间
                current_start = data[-1][6] + 1  # 使用最后一条记录的关闭时间+1
                
                # 避免请求过于频繁
                time.sleep(0.1)
            
            if not all_data:
                self.logger.warning(f"Binance返回空数据: {binance_symbol}")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(all_data, columns=[
                'Open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore'
            ])
            
            # 转换数据类型
            df['Open_time'] = pd.to_datetime(df['Open_time'], unit='ms')
            df = df.set_index('Open_time')
            
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 只保留需要的列
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Binance获取数据失败: {e}")
            return None
    
    def _fetch_from_akshare(self, symbol: str, start_date: str, end_date: str, 
                           interval: str, market_type: str) -> Optional[pd.DataFrame]:
        """
        从akshare获取A股数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            market_type: 市场类型
            
        Returns:
            Optional[pd.DataFrame]: akshare数据
        """
        if not AKSHARE_AVAILABLE:
            self.logger.error("akshare库未安装，无法获取A股数据")
            return None
        
        # akshare主要支持A股
        if market_type != 'cn_stock':
            self.logger.warning(f"akshare主要支持A股数据，当前市场类型: {market_type}")
        
        # 使用新的冲突解决函数处理股票代码冲突
        # from .config import resolve_stock_code_conflict
        
        # conflict_info = resolve_stock_code_conflict(symbol)
        
        # if conflict_info['has_conflict']:
        #     symbol_lower = symbol.lower()
        #     if symbol.upper().endswith('.SH') or symbol_lower.startswith('sh'):
        #         # 用户明确指定上交所
        #         target_info = conflict_info['conflicts']['SH']
        #         self.logger.info(f"使用上交所: {target_info['name']} ({target_info['type']})")
        #         ak_symbol = conflict_info['base_symbol']
        #     elif symbol.upper().endswith('.SZ') or symbol_lower.startswith('sz'):
        #         # 用户明确指定深交所
        #         target_info = conflict_info['conflicts']['SZ']
        #         self.logger.info(f"使用深交所: {target_info['name']} ({target_info['type']})")
        #         ak_symbol = conflict_info['base_symbol']
        #     else:
        #         # 用户没有明确指定，给出详细提示
        #         self.logger.warning(conflict_info['message'])
        #         for exchange, suggestion in conflict_info['suggestions'].items():
        #             self.logger.warning(f"  - {suggestion}")
                
        #         # 使用默认选择
        #         default_exchange = conflict_info['default_choice']
        #         default_info = conflict_info['conflicts'][default_exchange]
        #         self.logger.warning(f"默认使用: {default_info['name']} ({default_info['type']})")
        #         self.logger.warning(f"如需获取其他数据，请明确指定交易所后缀或使用sh/sz前缀")
        #         ak_symbol = conflict_info['base_symbol']
        # else:
        #     # 转换符号格式
        #     ak_symbol = get_symbol_for_source(symbol, 'akshare', market_type)

        ak_symbol = symbol.lower()
        
        # 转换时间间隔格式
        ak_period = self._convert_interval_for_akshare(interval)
        if ak_period is None:
            self.logger.error(f"akshare不支持时间间隔: {interval}")
            return None
        
        self.logger.debug(f"从akshare获取数据: {ak_symbol}, 周期: {ak_period}")
        
        try:
            # 根据时间间隔选择不同的akshare函数
            if ak_period == 'daily':
                # 获取日线数据
                df = ak.stock_zh_a_hist(
                    symbol=ak_symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"  # 前复权
                )
                # df = ak.stock_zh_index_daily(
                #     symbol=ak_symbol
                # )
            else:
                self.logger.error(f"akshare暂不支持 {ak_period} 周期数据")
                return None
            
            if df is None or df.empty:
                self.logger.warning(f"akshare返回空数据: {ak_symbol}")
                return None
            
            # 重命名列以保持一致性
            column_mapping = {
                '日期': 'Date',
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low',
                '收盘': 'Close',
                '成交量': 'Volume'
            }
            
            # 检查列名并重命名
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # 设置日期索引
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
            elif '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
            
            # 确保包含必要的列
            required_columns = ['Open', 'High', 'Low', 'Close']
            available_columns = [col for col in required_columns if col in df.columns]
            
            if len(available_columns) < 4:
                self.logger.error(f"akshare数据缺少必要列，可用列: {df.columns.tolist()}")
                return None
            
            # 转换数据类型
            for col in available_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 添加Volume列（如果存在）
            if 'Volume' in df.columns:
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
                available_columns.append('Volume')
            
            return df[available_columns]
            
        except Exception as e:
            self.logger.error(f"akshare获取数据失败: {e}")
            return None
    
    def _convert_interval_for_yfinance(self, interval: str) -> Optional[str]:
        """
        转换时间间隔格式为yfinance格式
        
        Args:
            interval: 标准时间间隔
            
        Returns:
            Optional[str]: yfinance格式的时间间隔
        """
        mapping = {
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        return mapping.get(interval)
    
    def _convert_interval_for_binance(self, interval: str) -> Optional[str]:
        """
        转换时间间隔格式为Binance格式
        
        Args:
            interval: 标准时间间隔
            
        Returns:
            Optional[str]: Binance格式的时间间隔
        """
        mapping = {
            '1h': '1h',
            '4h': '4h', 
            '1d': '1d'
        }
        return mapping.get(interval)
    
    def _convert_interval_for_akshare(self, interval: str) -> Optional[str]:
        """
        转换时间间隔格式为akshare格式
        
        Args:
            interval: 标准时间间隔
            
        Returns:
            Optional[str]: akshare格式的时间间隔
        """
        mapping = {
            '1d': 'daily'
            # akshare主要支持日线数据，小时级数据支持有限
        }
        return mapping.get(interval)
    
    def _process_data(self, df: pd.DataFrame, interval: str) -> Optional[pd.DataFrame]:
        """
        处理和清理数据
        
        Args:
            df: 原始数据
            interval: 时间间隔
            
        Returns:
            Optional[pd.DataFrame]: 处理后的数据
        """
        if df is None or df.empty:
            return None
        
        try:
            # 数据清理
            df = clean_data(df)
            
            if df.empty:
                self.logger.error("数据清理后为空")
                return None
            
            # 确保索引是日期时间类型
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 按时间排序
            df = df.sort_index()
            
            # 删除重复的时间戳
            df = df[~df.index.duplicated(keep='last')]
            
            # 验证数据完整性
            if not self._validate_data(df):
                self.logger.error("数据验证失败")
                return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            return None
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据的完整性和合理性
        
        Args:
            df: 数据框
            
        Returns:
            bool: 数据是否有效
        """
        # 检查必要列
        required_columns = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_columns):
            self.logger.error(f"缺少必要列: {required_columns}")
            return False
        
        # 检查数据量
        if len(df) < 10:
            self.logger.error(f"数据量太少: {len(df)} 条")
            return False
        
        # 检查价格数据的合理性
        for col in required_columns:
            if (df[col] <= 0).any():
                self.logger.error(f"发现非正价格数据: {col}")
                return False
        
        # 检查High >= Low
        if (df['High'] < df['Low']).any():
            self.logger.error("发现High < Low的异常数据")
            return False
        
        # 检查价格在合理范围内
        for col in required_columns:
            if (df[col] > df[col].median() * 100).any():  # 价格不应超过中位数的100倍
                self.logger.warning(f"发现可能的异常价格数据: {col}")
        
        return True
    
    def get_available_symbols(self) -> Dict[str, str]:
        """
        获取支持的交易对列表
        
        Returns:
            Dict[str, str]: 支持的交易对映射
        """
        return Constants.SUPPORTED_SYMBOLS.copy()
    
    def test_connection(self, symbol: str = 'BTC') -> bool:
        """
        测试数据源连接
        
        Args:
            symbol: 测试用的交易对符号
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 获取最近几天的数据进行测试
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            df = self.fetch_data(symbol, start_date, end_date, '1d')
            
            return df is not None and not df.empty
            
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False