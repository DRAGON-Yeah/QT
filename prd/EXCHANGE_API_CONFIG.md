# QuantTrade 交易所API配置文档

## 概述
本文档详细说明了QuantTrade系统与各大交易所的API对接配置，包括API密钥管理、权限配置、接口限制等信息。

## 支持的交易所

### 1. 币安 (Binance)
- **交易所类型**：中心化交易所
- **官方网站**：https://www.binance.com
- **API文档**：https://binance-docs.github.io/apidocs/
- **支持市场**：现货、合约、期权
- **主要特点**：全球最大的加密货币交易所，流动性最佳

### 2. 欧易 (OKX)
- **交易所类型**：中心化交易所
- **官方网站**：https://www.okx.com
- **API文档**：https://www.okx.com/docs-v5/
- **支持市场**：现货、合约、期权、DEX
- **主要特点**：全球领先的数字资产交易平台，支持多种交易类型

## API密钥配置

### 币安 (Binance) 配置

#### 生产环境配置
```bash
# 币安API配置
BINANCE_API_KEY=mPzZzKQ7aUzn001gJQfUmD0ktz8SCQnmx5jllnu6ntTKWKJ7BioF5UnRewHgXo3w
BINANCE_SECRET_KEY=xtZZZyfvVpGVitI04bSk9wvIRqNWjy260BW38vkeKuN3d4zVJ7xmi9pqzMX70dST
BINANCE_TESTNET=false
BINANCE_SANDBOX=false
```

#### 测试环境配置
```bash
# 币安测试网配置 (推荐开发测试使用)
BINANCE_API_KEY=your_test_api_key
BINANCE_SECRET_KEY=your_test_secret_key
BINANCE_TESTNET=true
BINANCE_SANDBOX=true
```

#### 权限要求
- **读取权限**：账户信息、交易历史、市场数据
- **交易权限**：现货交易、合约交易
- **提现权限**：禁用（安全考虑）

### 欧易 (OKX) 配置

#### 生产环境配置
```bash
# 欧易API配置
OKX_API_KEY=e08a8413-80ac-4257-a5e6-bdc91840e38b
OKX_SECRET_KEY=12F7F093E5670F32DF4C9008DB213CAE
OKX_PASSPHRASE=Womeng20250101@
OKX_TESTNET=false
OKX_SANDBOX=false
```

#### 测试环境配置
```bash
# 欧易测试网配置 (推荐开发测试使用)
OKX_API_KEY=your_test_api_key
OKX_SECRET_KEY=your_test_secret_key
OKX_PASSPHRASE=your_test_passphrase
OKX_TESTNET=true
OKX_SANDBOX=true
```

#### 权限要求
- **读取权限**：账户信息、交易历史、市场数据
- **交易权限**：现货交易、合约交易
- **提现权限**：禁用（安全考虑）

## 环境变量配置

### 开发环境 (.env.development)
```bash
# 开发环境配置
ENVIRONMENT=development
DEBUG=true

# 币安配置 (测试网)
BINANCE_API_KEY=your_dev_binance_api_key
BINANCE_SECRET_KEY=your_dev_binance_secret_key
BINANCE_TESTNET=true

# 欧易配置 (测试网)
OKX_API_KEY=your_dev_okx_api_key
OKX_SECRET_KEY=your_dev_okx_secret_key
OKX_PASSPHRASE=your_dev_passphrase
OKX_TESTNET=true
```

### 测试环境 (.env.test)
```bash
# 测试环境配置
ENVIRONMENT=test
DEBUG=false

# 币安配置 (测试网)
BINANCE_API_KEY=your_test_binance_api_key
BINANCE_SECRET_KEY=your_test_binance_secret_key
BINANCE_TESTNET=true

# 欧易配置 (测试网)
OKX_API_KEY=your_test_okx_api_key
OKX_SECRET_KEY=your_test_okx_secret_key
OKX_PASSPHRASE=your_test_passphrase
OKX_TESTNET=true
```

### 生产环境 (.env.production)
```bash
# 生产环境配置
ENVIRONMENT=production
DEBUG=false

# 币安配置 (主网)
BINANCE_API_KEY=mPzZzKQ7aUzn001gJQfUmD0ktz8SCQnmx5jllnu6ntTKWKJ7BioF5UnRewHgXo3w
BINANCE_SECRET_KEY=xtZZZyfvVpGVitI04bSk9wvIRqNWjy260BW38vkeKuN3d4zVJ7xmi9pqzMX70dST
BINANCE_TESTNET=false

# 欧易配置 (主网)
OKX_API_KEY=e08a8413-80ac-4257-a5e6-bdc91840e38b
OKX_SECRET_KEY=12F7F093E5670F32DF4C9008DB213CAE
OKX_PASSPHRASE=Womeng20250101@
OKX_TESTNET=false
```

## Django设置配置

### settings.py 配置
```python
# 交易所API配置
EXCHANGE_CONFIG = {
    'binance': {
        'api_key': os.getenv('BINANCE_API_KEY'),
        'secret_key': os.getenv('BINANCE_SECRET_KEY'),
        'testnet': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
        'sandbox': os.getenv('BINANCE_SANDBOX', 'false').lower() == 'true',
        'rate_limit': 1200,  # 每分钟请求限制
        'timeout': 30,        # 请求超时时间
    },
    'okx': {
        'api_key': os.getenv('OKX_API_KEY'),
        'secret_key': os.getenv('OKX_SECRET_KEY'),
        'passphrase': os.getenv('OKX_PASSPHRASE'),
        'testnet': os.getenv('OKX_TESTNET', 'false').lower() == 'true',
        'sandbox': os.getenv('OKX_SANDBOX', 'false').lower() == 'true',
        'rate_limit': 100,    # 每秒请求限制
        'timeout': 30,        # 请求超时时间
    }
}

# CCXT配置
CCXT_CONFIG = {
    'default_timeout': 30000,
    'enableRateLimit': True,
    'rateLimit': 1000,  # 毫秒
}
```

## CCXT集成配置

### 交易所实例化
```python
import ccxt
from django.conf import settings

def get_exchange_instance(exchange_name):
    """获取交易所实例"""
    config = settings.EXCHANGE_CONFIG.get(exchange_name)
    if not config:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    
    if exchange_name == 'binance':
        exchange = ccxt.binance({
            'apiKey': config['api_key'],
            'secret': config['secret_key'],
            'sandbox': config['sandbox'],
            'testnet': config['testnet'],
            'enableRateLimit': True,
            'timeout': config['timeout'] * 1000,
        })
    elif exchange_name == 'okx':
        exchange = ccxt.okx({
            'apiKey': config['api_key'],
            'secret': config['secret_key'],
            'password': config['passphrase'],
            'sandbox': config['sandbox'],
            'testnet': config['testnet'],
            'enableRateLimit': True,
            'timeout': config['timeout'] * 1000,
        })
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    
    return exchange
```

### 市场数据获取
```python
def get_market_data(exchange_name, symbol):
    """获取市场数据"""
    try:
        exchange = get_exchange_instance(exchange_name)
        
        # 获取Ticker数据
        ticker = exchange.fetch_ticker(symbol)
        
        # 获取K线数据
        ohlcv = exchange.fetch_ohlcv(symbol, '1m', limit=100)
        
        # 获取订单簿
        orderbook = exchange.fetch_order_book(symbol)
        
        return {
            'ticker': ticker,
            'ohlcv': ohlcv,
            'orderbook': orderbook,
            'timestamp': exchange.milliseconds()
        }
    except Exception as e:
        logger.error(f"Failed to fetch market data from {exchange_name}: {e}")
        return None
```

## 安全配置

### API密钥安全
- **环境变量**：所有API密钥通过环境变量管理，不硬编码
- **权限最小化**：只授予必要的读取和交易权限
- **IP白名单**：建议配置API访问IP白名单
- **定期轮换**：定期更换API密钥

### 访问控制
```python
# 权限检查装饰器
from functools import wraps
from django.http import JsonResponse

def require_exchange_permission(exchange_name):
    """检查交易所访问权限"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 检查用户是否有该交易所的访问权限
            if not has_exchange_access(request.user, exchange_name):
                return JsonResponse({
                    'error': 'Insufficient permissions for this exchange'
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

## 错误处理和重试

### 异常处理
```python
import time
from ccxt import NetworkError, ExchangeError

def execute_with_retry(func, max_retries=3, delay=1):
    """带重试机制的执行函数"""
    for attempt in range(max_retries):
        try:
            return func()
        except NetworkError as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))  # 指数退避
        except ExchangeError as e:
            # 交易所错误不重试
            raise e
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)
```

### 错误日志
```python
import logging

logger = logging.getLogger(__name__)

def log_exchange_error(exchange_name, operation, error):
    """记录交易所错误日志"""
    logger.error(f"Exchange {exchange_name} {operation} failed: {error}")
    
    # 记录详细错误信息
    if hasattr(error, 'response'):
        logger.error(f"Response: {error.response}")
    
    # 记录请求信息
    if hasattr(error, 'request'):
        logger.error(f"Request: {error.request}")
```

## 监控和告警

### 健康检查
```python
def check_exchange_health(exchange_name):
    """检查交易所连接健康状态"""
    try:
        exchange = get_exchange_instance(exchange_name)
        
        # 测试API连接
        exchange.fetch_time()
        
        # 检查账户状态
        balance = exchange.fetch_balance()
        
        return {
            'status': 'healthy',
            'timestamp': exchange.milliseconds(),
            'balance_count': len(balance['total'])
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
```

### 性能监控
```python
import time
from functools import wraps

def monitor_exchange_performance(exchange_name):
    """监控交易所API性能"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录性能指标
                logger.info(f"Exchange {exchange_name} {func.__name__} executed in {execution_time:.3f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Exchange {exchange_name} {func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator
```

## 测试配置

### 测试环境设置
```python
# tests/test_exchanges.py
import pytest
from unittest.mock import patch
from django.test import TestCase

class ExchangeAPITestCase(TestCase):
    def setUp(self):
        # 使用测试网配置
        self.test_config = {
            'binance': {
                'api_key': 'test_api_key',
                'secret_key': 'test_secret_key',
                'testnet': True,
                'sandbox': True,
            },
            'okx': {
                'api_key': 'test_api_key',
                'secret_key': 'test_secret_key',
                'passphrase': 'test_passphrase',
                'testnet': True,
                'sandbox': True,
            }
        }
    
    @patch('django.conf.settings.EXCHANGE_CONFIG')
    def test_binance_connection(self, mock_config):
        mock_config.return_value = self.test_config
        # 测试币安连接
        pass
    
    @patch('django.conf.settings.EXCHANGE_CONFIG')
    def test_okx_connection(self, mock_config):
        mock_config.return_value = self.test_config
        # 测试欧易连接
        pass
```

## 部署检查清单

### 环境配置检查
- [ ] 所有API密钥已正确配置到环境变量
- [ ] 生产环境使用主网API，测试环境使用测试网API
- [ ] 环境变量文件(.env.production)已正确配置
- [ ] API密钥权限已正确设置（禁用提现权限）
- [ ] IP白名单已配置（如需要）

### 功能测试检查
- [ ] 币安API连接测试通过
- [ ] 欧易API连接测试通过
- [ ] 市场数据获取功能正常
- [ ] 交易功能测试通过
- [ ] 错误处理和重试机制正常

### 监控配置检查
- [ ] 交易所健康检查已配置
- [ ] 性能监控已启用
- [ ] 错误日志记录正常
- [ ] 告警机制已配置

## 常见问题

### Q: API密钥权限不足怎么办？
A: 检查API密钥的权限设置，确保已授予必要的读取和交易权限。

### Q: 测试网和主网有什么区别？
A: 测试网用于开发和测试，使用测试币，不会产生真实交易；主网用于生产环境，使用真实币种。

### Q: 如何提高API调用频率？
A: 联系交易所客服升级账户等级，或使用多个API密钥分散请求。

### Q: API密钥泄露怎么办？
A: 立即在交易所后台禁用该API密钥，生成新的密钥，并检查是否有异常交易。

## 联系信息

### 技术支持
- **邮箱**：support@quanttrade.com
- **文档**：https://docs.quanttrade.com
- **GitHub**：https://github.com/quanttrade

### 交易所支持
- **币安支持**：https://support.binance.com
- **欧易支持**：https://support.okx.com

---

**注意**：本文档包含敏感的API密钥信息，请妥善保管，不要泄露给无关人员。建议定期更换API密钥以提高安全性。
