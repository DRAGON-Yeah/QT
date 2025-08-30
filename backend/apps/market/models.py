from django.db import models
from decimal import Decimal
from apps.core.models import TenantModel


class Exchange(models.Model):
    """交易所模型"""
    name = models.CharField(max_length=50, verbose_name="交易所名称")
    code = models.CharField(max_length=20, unique=True, verbose_name="交易所代码")
    api_url = models.URLField(verbose_name="API地址")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "交易所"
        verbose_name_plural = "交易所"
        db_table = "market_exchange"

    def __str__(self):
        return f"{self.name}({self.code})"


class Symbol(TenantModel):
    """交易对模型"""
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, verbose_name="交易所")
    symbol = models.CharField(max_length=20, verbose_name="交易对符号")  # BTC/USDT
    base_asset = models.CharField(max_length=10, verbose_name="基础资产")  # BTC
    quote_asset = models.CharField(max_length=10, verbose_name="计价资产")  # USDT
    min_order_size = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="最小订单数量"
    )
    max_order_size = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="最大订单数量"
    )
    price_precision = models.IntegerField(verbose_name="价格精度")
    amount_precision = models.IntegerField(verbose_name="数量精度")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")

    class Meta:
        verbose_name = "交易对"
        verbose_name_plural = "交易对"
        db_table = "market_symbol"
        unique_together = ['tenant', 'exchange', 'symbol']
        indexes = [
            models.Index(fields=['tenant', 'exchange', 'symbol']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.exchange.code}:{self.symbol}"


class Kline(models.Model):
    """K线数据模型"""
    TIMEFRAME_CHOICES = [
        ('1m', '1分钟'),
        ('5m', '5分钟'),
        ('15m', '15分钟'),
        ('30m', '30分钟'),
        ('1h', '1小时'),
        ('4h', '4小时'),
        ('1d', '1天'),
        ('1w', '1周'),
        ('1M', '1月'),
    ]

    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, verbose_name="交易对")
    timeframe = models.CharField(
        max_length=10, choices=TIMEFRAME_CHOICES, verbose_name="时间周期"
    )
    timestamp = models.DateTimeField(verbose_name="时间戳")
    open_price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="开盘价"
    )
    high_price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="最高价"
    )
    low_price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="最低价"
    )
    close_price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="收盘价"
    )
    volume = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="成交量"
    )
    quote_volume = models.DecimalField(
        max_digits=20, decimal_places=8, default=0, verbose_name="成交额"
    )
    trades_count = models.IntegerField(default=0, verbose_name="成交笔数")

    class Meta:
        verbose_name = "K线数据"
        verbose_name_plural = "K线数据"
        db_table = "market_kline"
        unique_together = ['symbol', 'timeframe', 'timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp']),
            models.Index(fields=['symbol', 'timeframe', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol.symbol} {self.timeframe} {self.timestamp}"


class Ticker(models.Model):
    """实时行情数据模型"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, verbose_name="交易对")
    last_price = models.DecimalField(
        max_digits=20, decimal_places=8, verbose_name="最新价格"
    )
    bid_price = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, verbose_name="买一价"
    )
    ask_price = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, verbose_name="卖一价"
    )
    high_24h = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, verbose_name="24小时最高价"
    )
    low_24h = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, verbose_name="24小时最低价"
    )
    volume_24h = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, verbose_name="24小时成交量"
    )
    change_24h = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, verbose_name="24小时涨跌幅"
    )
    timestamp = models.DateTimeField(verbose_name="更新时间")

    class Meta:
        verbose_name = "实时行情"
        verbose_name_plural = "实时行情"
        db_table = "market_ticker"
        unique_together = ['symbol']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol.symbol} {self.last_price}"


class OrderBook(models.Model):
    """订单簿数据模型"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, verbose_name="交易对")
    bids = models.JSONField(verbose_name="买单数据")  # [[price, amount], ...]
    asks = models.JSONField(verbose_name="卖单数据")  # [[price, amount], ...]
    timestamp = models.DateTimeField(verbose_name="时间戳")

    class Meta:
        verbose_name = "订单簿"
        verbose_name_plural = "订单簿"
        db_table = "market_orderbook"
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol.symbol} OrderBook {self.timestamp}"


class Trade(models.Model):
    """成交记录模型"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, verbose_name="交易对")
    trade_id = models.CharField(max_length=100, verbose_name="成交ID")
    price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="成交价格")
    amount = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="成交数量")
    side = models.CharField(max_length=10, verbose_name="成交方向")  # buy/sell
    timestamp = models.DateTimeField(verbose_name="成交时间")

    class Meta:
        verbose_name = "成交记录"
        verbose_name_plural = "成交记录"
        db_table = "market_trade"
        unique_together = ['symbol', 'trade_id']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol.symbol} {self.side} {self.amount}@{self.price}"