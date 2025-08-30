import ccxt
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as django_timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Exchange, Symbol, Kline, Ticker, OrderBook, Trade
from apps.trading.models import ExchangeAccount

logger = logging.getLogger(__name__)


class ExchangeConnector:
    """交易所连接器"""
    
    def __init__(self, exchange_account: ExchangeAccount):
        self.exchange_account = exchange_account
        self.exchange = self._create_exchange_instance()
    
    def _create_exchange_instance(self):
        """创建交易所实例"""
        exchange_class = getattr(ccxt, self.exchange_account.exchange)
        
        # 解密API密钥
        api_key, secret_key, passphrase = self.exchange_account.get_api_credentials()
        
        config = {
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': self.exchange_account.is_testnet,
            'enableRateLimit': True,
            'timeout': 30000,
        }
        
        if passphrase:  # OKX需要passphrase
            config['password'] = passphrase
        
        return exchange_class(config)
    
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        try:
            balance = self.exchange.fetch_balance()
            return True, "连接成功"
        except Exception as e:
            logger.error(f"交易所连接测试失败: {e}")
            return False, str(e)
    
    def fetch_markets(self) -> Dict[str, Any]:
        """获取交易市场信息"""
        try:
            return self.exchange.load_markets()
        except Exception as e:
            logger.error(f"获取市场信息失败: {e}")
            raise
    
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取实时行情"""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            raise
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', 
                   since: Optional[int] = None, limit: int = 100) -> List[List]:
        """获取K线数据"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        except Exception as e:
            logger.error(f"获取K线数据失败 {symbol}: {e}")
            raise
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """获取订单簿"""
        try:
            return self.exchange.fetch_order_book(symbol, limit)
        except Exception as e:
            logger.error(f"获取订单簿失败 {symbol}: {e}")
            raise
    
    def fetch_trades(self, symbol: str, since: Optional[int] = None, 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """获取成交记录"""
        try:
            return self.exchange.fetch_trades(symbol, since, limit)
        except Exception as e:
            logger.error(f"获取成交记录失败 {symbol}: {e}")
            raise


class MarketDataCollector:
    """市场数据收集器"""
    
    def __init__(self, exchange_account: ExchangeAccount):
        self.exchange_account = exchange_account
        self.connector = ExchangeConnector(exchange_account)
        self.channel_layer = get_channel_layer()
    
    def sync_symbols(self) -> int:
        """同步交易对信息"""
        try:
            markets = self.connector.fetch_markets()
            exchange_obj = Exchange.objects.get(code=self.exchange_account.exchange)
            
            synced_count = 0
            for symbol, market in markets.items():
                if not market.get('active', True):
                    continue
                
                symbol_obj, created = Symbol.objects.get_or_create(
                    tenant=self.exchange_account.tenant,
                    exchange=exchange_obj,
                    symbol=symbol,
                    defaults={
                        'base_asset': market['base'],
                        'quote_asset': market['quote'],
                        'min_order_size': Decimal(str(market['limits']['amount']['min'] or 0)),
                        'max_order_size': Decimal(str(market['limits']['amount']['max'] or 999999999)),
                        'price_precision': market['precision']['price'] or 8,
                        'amount_precision': market['precision']['amount'] or 8,
                        'is_active': True,
                    }
                )
                
                if created:
                    synced_count += 1
                    logger.info(f"同步交易对: {symbol}")
            
            return synced_count
        
        except Exception as e:
            logger.error(f"同步交易对失败: {e}")
            raise
    
    def collect_ticker_data(self, symbol: str) -> Optional[Ticker]:
        """收集实时行情数据"""
        try:
            ticker_data = self.connector.fetch_ticker(symbol)
            symbol_obj = Symbol.objects.get(
                tenant=self.exchange_account.tenant,
                exchange__code=self.exchange_account.exchange,
                symbol=symbol
            )
            
            ticker, created = Ticker.objects.update_or_create(
                symbol=symbol_obj,
                defaults={
                    'last_price': Decimal(str(ticker_data['last'])),
                    'bid_price': Decimal(str(ticker_data['bid'])) if ticker_data['bid'] else None,
                    'ask_price': Decimal(str(ticker_data['ask'])) if ticker_data['ask'] else None,
                    'high_24h': Decimal(str(ticker_data['high'])) if ticker_data['high'] else None,
                    'low_24h': Decimal(str(ticker_data['low'])) if ticker_data['low'] else None,
                    'volume_24h': Decimal(str(ticker_data['baseVolume'])) if ticker_data['baseVolume'] else None,
                    'change_24h': Decimal(str(ticker_data['percentage'])) if ticker_data['percentage'] else None,
                    'timestamp': django_timezone.now(),
                }
            )
            
            # 发送WebSocket消息
            self._broadcast_ticker_update(symbol, ticker_data)
            
            return ticker
        
        except Exception as e:
            logger.error(f"收集行情数据失败 {symbol}: {e}")
            return None
    
    def collect_kline_data(self, symbol: str, timeframe: str = '1m', 
                          limit: int = 100) -> int:
        """收集K线数据"""
        try:
            ohlcv_data = self.connector.fetch_ohlcv(symbol, timeframe, limit=limit)
            symbol_obj = Symbol.objects.get(
                tenant=self.exchange_account.tenant,
                exchange__code=self.exchange_account.exchange,
                symbol=symbol
            )
            
            saved_count = 0
            for ohlcv in ohlcv_data:
                timestamp = datetime.fromtimestamp(ohlcv[0] / 1000, tz=timezone.utc)
                
                kline, created = Kline.objects.update_or_create(
                    symbol=symbol_obj,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    defaults={
                        'open_price': Decimal(str(ohlcv[1])),
                        'high_price': Decimal(str(ohlcv[2])),
                        'low_price': Decimal(str(ohlcv[3])),
                        'close_price': Decimal(str(ohlcv[4])),
                        'volume': Decimal(str(ohlcv[5])),
                    }
                )
                
                if created:
                    saved_count += 1
            
            logger.info(f"收集K线数据 {symbol} {timeframe}: {saved_count}条新数据")
            return saved_count
        
        except Exception as e:
            logger.error(f"收集K线数据失败 {symbol}: {e}")
            return 0
    
    def collect_orderbook_data(self, symbol: str, limit: int = 20) -> Optional[OrderBook]:
        """收集订单簿数据"""
        try:
            orderbook_data = self.connector.fetch_order_book(symbol, limit)
            symbol_obj = Symbol.objects.get(
                tenant=self.exchange_account.tenant,
                exchange__code=self.exchange_account.exchange,
                symbol=symbol
            )
            
            # 删除旧的订单簿数据（只保留最新的）
            OrderBook.objects.filter(symbol=symbol_obj).delete()
            
            orderbook = OrderBook.objects.create(
                symbol=symbol_obj,
                bids=orderbook_data['bids'],
                asks=orderbook_data['asks'],
                timestamp=django_timezone.now(),
            )
            
            # 发送WebSocket消息
            self._broadcast_orderbook_update(symbol, orderbook_data)
            
            return orderbook
        
        except Exception as e:
            logger.error(f"收集订单簿数据失败 {symbol}: {e}")
            return None
    
    def collect_trades_data(self, symbol: str, limit: int = 50) -> int:
        """收集成交记录数据"""
        try:
            trades_data = self.connector.fetch_trades(symbol, limit=limit)
            symbol_obj = Symbol.objects.get(
                tenant=self.exchange_account.tenant,
                exchange__code=self.exchange_account.exchange,
                symbol=symbol
            )
            
            saved_count = 0
            for trade_data in trades_data:
                timestamp = datetime.fromtimestamp(trade_data['timestamp'] / 1000, tz=timezone.utc)
                
                trade, created = Trade.objects.get_or_create(
                    symbol=symbol_obj,
                    trade_id=str(trade_data['id']),
                    defaults={
                        'price': Decimal(str(trade_data['price'])),
                        'amount': Decimal(str(trade_data['amount'])),
                        'side': trade_data['side'],
                        'timestamp': timestamp,
                    }
                )
                
                if created:
                    saved_count += 1
            
            logger.info(f"收集成交记录 {symbol}: {saved_count}条新数据")
            return saved_count
        
        except Exception as e:
            logger.error(f"收集成交记录失败 {symbol}: {e}")
            return 0
    
    def _broadcast_ticker_update(self, symbol: str, ticker_data: Dict[str, Any]):
        """广播行情更新"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f"market_{symbol}",
                {
                    "type": "ticker_update",
                    "data": {
                        "symbol": symbol,
                        "last": ticker_data['last'],
                        "bid": ticker_data['bid'],
                        "ask": ticker_data['ask'],
                        "change": ticker_data.get('percentage'),
                        "timestamp": django_timezone.now().isoformat(),
                    }
                }
            )
    
    def _broadcast_orderbook_update(self, symbol: str, orderbook_data: Dict[str, Any]):
        """广播订单簿更新"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f"market_{symbol}",
                {
                    "type": "orderbook_update",
                    "data": {
                        "symbol": symbol,
                        "bids": orderbook_data['bids'][:10],  # 只发送前10档
                        "asks": orderbook_data['asks'][:10],
                        "timestamp": django_timezone.now().isoformat(),
                    }
                }
            )


class MarketDataProcessor:
    """市场数据处理器"""
    
    @staticmethod
    def get_kline_data(symbol_obj: Symbol, timeframe: str, 
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 1000) -> List[Dict[str, Any]]:
        """获取K线数据"""
        queryset = Kline.objects.filter(
            symbol=symbol_obj,
            timeframe=timeframe
        ).order_by('-timestamp')
        
        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)
        
        queryset = queryset[:limit]
        
        return [
            {
                'timestamp': kline.timestamp.isoformat(),
                'open': float(kline.open_price),
                'high': float(kline.high_price),
                'low': float(kline.low_price),
                'close': float(kline.close_price),
                'volume': float(kline.volume),
            }
            for kline in queryset
        ]
    
    @staticmethod
    def get_latest_ticker(symbol_obj: Symbol) -> Optional[Dict[str, Any]]:
        """获取最新行情"""
        try:
            ticker = Ticker.objects.get(symbol=symbol_obj)
            return {
                'symbol': symbol_obj.symbol,
                'last': float(ticker.last_price),
                'bid': float(ticker.bid_price) if ticker.bid_price else None,
                'ask': float(ticker.ask_price) if ticker.ask_price else None,
                'high_24h': float(ticker.high_24h) if ticker.high_24h else None,
                'low_24h': float(ticker.low_24h) if ticker.low_24h else None,
                'volume_24h': float(ticker.volume_24h) if ticker.volume_24h else None,
                'change_24h': float(ticker.change_24h) if ticker.change_24h else None,
                'timestamp': ticker.timestamp.isoformat(),
            }
        except Ticker.DoesNotExist:
            return None
    
    @staticmethod
    def get_orderbook(symbol_obj: Symbol) -> Optional[Dict[str, Any]]:
        """获取订单簿"""
        try:
            orderbook = OrderBook.objects.filter(symbol=symbol_obj).first()
            if orderbook:
                return {
                    'symbol': symbol_obj.symbol,
                    'bids': orderbook.bids,
                    'asks': orderbook.asks,
                    'timestamp': orderbook.timestamp.isoformat(),
                }
            return None
        except OrderBook.DoesNotExist:
            return None
    
    @staticmethod
    def get_recent_trades(symbol_obj: Symbol, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近成交记录"""
        trades = Trade.objects.filter(
            symbol=symbol_obj
        ).order_by('-timestamp')[:limit]
        
        return [
            {
                'id': trade.trade_id,
                'price': float(trade.price),
                'amount': float(trade.amount),
                'side': trade.side,
                'timestamp': trade.timestamp.isoformat(),
            }
            for trade in trades
        ]


class MarketDataCache:
    """市场数据缓存管理"""
    
    CACHE_TIMEOUT = {
        'ticker': 5,      # 5秒
        'orderbook': 2,   # 2秒
        'kline': 60,      # 1分钟
        'trades': 30,     # 30秒
    }
    
    @classmethod
    def get_cache_key(cls, data_type: str, symbol: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [f"market_{data_type}", symbol]
        for k, v in kwargs.items():
            key_parts.append(f"{k}_{v}")
        return ":".join(key_parts)
    
    @classmethod
    def set_ticker_cache(cls, symbol: str, data: Dict[str, Any]):
        """设置行情缓存"""
        cache_key = cls.get_cache_key('ticker', symbol)
        cache.set(cache_key, data, cls.CACHE_TIMEOUT['ticker'])
    
    @classmethod
    def get_ticker_cache(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """获取行情缓存"""
        cache_key = cls.get_cache_key('ticker', symbol)
        return cache.get(cache_key)
    
    @classmethod
    def set_kline_cache(cls, symbol: str, timeframe: str, data: List[Dict[str, Any]]):
        """设置K线缓存"""
        cache_key = cls.get_cache_key('kline', symbol, timeframe=timeframe)
        cache.set(cache_key, data, cls.CACHE_TIMEOUT['kline'])
    
    @classmethod
    def get_kline_cache(cls, symbol: str, timeframe: str) -> Optional[List[Dict[str, Any]]]:
        """获取K线缓存"""
        cache_key = cls.get_cache_key('kline', symbol, timeframe=timeframe)
        return cache.get(cache_key)