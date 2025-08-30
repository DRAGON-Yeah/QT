# 交易所集成和CCXT框架使用指南

## CCXT框架集成
CCXT是统一的加密货币交易所接口库，为QuantTrade提供多交易所支持。

### 支持的交易所
- **币安(Binance)**：全球最大的加密货币交易所
- **欧易(OKX)**：支持现货、合约、期权、DEX交易
- **其他交易所**：可根据需要扩展支持

### CCXT基础配置
```python
import ccxt

class ExchangeManager:
    def __init__(self, exchange_name, api_key, secret, sandbox=False):
        self.exchange_class = getattr(ccxt, exchange_name)
        self.exchange = self.exchange_class({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
    
    def test_connection(self):
        try:
            balance = self.exchange.fetch_balance()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)
```

## 交易所账户管理
### 账户配置模型
```python
class ExchangeAccount(TenantModel):
    EXCHANGE_CHOICES = [
        ('binance', '币安'),
        ('okx', '欧易'),
    ]
    
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES)
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200)
    passphrase = models.CharField(max_length=100, blank=True)  # OKX需要
    is_active = models.BooleanField(default=True)
    is_sandbox = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['tenant', 'name']
```

### API密钥安全存储
```python
from cryptography.fernet import Fernet

class EncryptedExchangeAccount(ExchangeAccount):
    def set_api_credentials(self, api_key, secret_key, passphrase=None):
        cipher = Fernet(settings.ENCRYPTION_KEY)
        self.api_key = cipher.encrypt(api_key.encode()).decode()
        self.secret_key = cipher.encrypt(secret_key.encode()).decode()
        if passphrase:
            self.passphrase = cipher.encrypt(passphrase.encode()).decode()
    
    def get_api_credentials(self):
        cipher = Fernet(settings.ENCRYPTION_KEY)
        api_key = cipher.decrypt(self.api_key.encode()).decode()
        secret_key = cipher.decrypt(self.secret_key.encode()).decode()
        passphrase = cipher.decrypt(self.passphrase.encode()).decode() if self.passphrase else None
        return api_key, secret_key, passphrase
```

## 交易对管理
### 交易对配置
```python
class TradingPair(TenantModel):
    exchange_account = models.ForeignKey(ExchangeAccount, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=20)  # BTC/USDT
    base_currency = models.CharField(max_length=10)  # BTC
    quote_currency = models.CharField(max_length=10)  # USDT
    min_order_size = models.DecimalField(max_digits=20, decimal_places=8)
    max_order_size = models.DecimalField(max_digits=20, decimal_places=8)
    price_precision = models.IntegerField()
    amount_precision = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['tenant', 'exchange_account', 'symbol']
```

### 交易对同步
```python
class TradingPairSyncService:
    def sync_trading_pairs(self, exchange_account):
        exchange = self.get_exchange_instance(exchange_account)
        markets = exchange.load_markets()
        
        for symbol, market in markets.items():
            pair, created = TradingPair.objects.get_or_create(
                tenant=exchange_account.tenant,
                exchange_account=exchange_account,
                symbol=symbol,
                defaults={
                    'base_currency': market['base'],
                    'quote_currency': market['quote'],
                    'min_order_size': market['limits']['amount']['min'],
                    'max_order_size': market['limits']['amount']['max'],
                    'price_precision': market['precision']['price'],
                    'amount_precision': market['precision']['amount'],
                }
            )
```

## 市场数据获取
### 实时数据服务
```python
class MarketDataService:
    def __init__(self, exchange_account):
        self.exchange = self.get_exchange_instance(exchange_account)
    
    def get_ticker(self, symbol):
        return self.exchange.fetch_ticker(symbol)
    
    def get_orderbook(self, symbol, limit=20):
        return self.exchange.fetch_order_book(symbol, limit)
    
    def get_ohlcv(self, symbol, timeframe='1m', since=None, limit=100):
        return self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
    
    def get_trades(self, symbol, since=None, limit=50):
        return self.exchange.fetch_trades(symbol, since, limit)
```

### WebSocket实时数据
```python
class WebSocketDataService:
    def __init__(self, exchange_account):
        self.exchange = self.get_exchange_instance(exchange_account)
    
    async def subscribe_ticker(self, symbol, callback):
        if hasattr(self.exchange, 'watch_ticker'):
            while True:
                ticker = await self.exchange.watch_ticker(symbol)
                await callback(ticker)
    
    async def subscribe_orderbook(self, symbol, callback):
        if hasattr(self.exchange, 'watch_order_book'):
            while True:
                orderbook = await self.exchange.watch_order_book(symbol)
                await callback(orderbook)
```

## 订单管理
### 订单模型
```python
class Order(TenantModel):
    ORDER_TYPES = [
        ('market', '市价单'),
        ('limit', '限价单'),
        ('stop', '止损单'),
        ('stop_limit', '止损限价单'),
    ]
    
    ORDER_SIDES = [
        ('buy', '买入'),
        ('sell', '卖出'),
    ]
    
    ORDER_STATUS = [
        ('open', '待成交'),
        ('closed', '已成交'),
        ('canceled', '已取消'),
        ('expired', '已过期'),
        ('rejected', '已拒绝'),
    ]
    
    exchange_account = models.ForeignKey(ExchangeAccount, on_delete=models.CASCADE)
    exchange_order_id = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    type = models.CharField(max_length=20, choices=ORDER_TYPES)
    side = models.CharField(max_length=10, choices=ORDER_SIDES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    filled = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    remaining = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    fee = models.JSONField(default=dict)
    trades = models.JSONField(default=list)
```

### 订单执行服务
```python
class OrderExecutionService:
    def __init__(self, exchange_account):
        self.exchange = self.get_exchange_instance(exchange_account)
    
    def create_market_order(self, symbol, side, amount):
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            return self.save_order(order)
        except Exception as e:
            logger.error(f"创建市价单失败: {e}")
            raise
    
    def create_limit_order(self, symbol, side, amount, price):
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            return self.save_order(order)
        except Exception as e:
            logger.error(f"创建限价单失败: {e}")
            raise
    
    def cancel_order(self, order_id, symbol):
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            self.update_order_status(order_id, 'canceled')
            return result
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            raise
```

## 资产管理
### 资产余额同步
```python
class AssetService:
    def __init__(self, exchange_account):
        self.exchange = self.get_exchange_instance(exchange_account)
        self.exchange_account = exchange_account
    
    def sync_balance(self):
        balance = self.exchange.fetch_balance()
        
        for currency, amounts in balance.items():
            if currency in ['free', 'used', 'total', 'info']:
                continue
                
            asset, created = Asset.objects.update_or_create(
                tenant=self.exchange_account.tenant,
                exchange_account=self.exchange_account,
                currency=currency,
                defaults={
                    'free': amounts['free'] or 0,
                    'used': amounts['used'] or 0,
                    'total': amounts['total'] or 0,
                }
            )
```

## 错误处理和重试机制
### 统一错误处理
```python
class ExchangeErrorHandler:
    RETRY_ERRORS = [
        ccxt.NetworkError,
        ccxt.RequestTimeout,
        ccxt.ExchangeNotAvailable,
    ]
    
    def handle_exchange_error(self, func, *args, **kwargs):
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except tuple(self.RETRY_ERRORS) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise
            except ccxt.InsufficientFunds as e:
                logger.error(f"余额不足: {e}")
                raise
            except ccxt.InvalidOrder as e:
                logger.error(f"无效订单: {e}")
                raise
```

## 交易所配置最佳实践
### 环境配置
```python
# settings.py
EXCHANGE_CONFIG = {
    'binance': {
        'sandbox_url': 'https://testnet.binance.vision',
        'rate_limit': 1200,  # requests per minute
        'timeout': 30000,
    },
    'okx': {
        'sandbox_url': 'https://www.okx.com',
        'rate_limit': 600,
        'timeout': 30000,
    }
}
```

### 连接池管理
```python
class ExchangeConnectionPool:
    def __init__(self):
        self.connections = {}
    
    def get_connection(self, exchange_account):
        key = f"{exchange_account.id}_{exchange_account.exchange}"
        
        if key not in self.connections:
            self.connections[key] = self.create_exchange_instance(exchange_account)
        
        return self.connections[key]
    
    def refresh_connection(self, exchange_account):
        key = f"{exchange_account.id}_{exchange_account.exchange}"
        if key in self.connections:
            del self.connections[key]
        return self.get_connection(exchange_account)
```