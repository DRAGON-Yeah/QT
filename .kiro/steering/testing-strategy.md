# 测试策略和质量保证

## 测试环境配置
### Python测试环境
```bash
# 创建独立的测试虚拟环境
python3.12 -m venv .venv-test
source .venv-test/bin/activate

# 安装测试依赖
pip install -r requirements-test.txt
```

### 测试依赖包
```txt
# requirements-test.txt
pytest>=7.0.0
pytest-django>=4.5.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
factory-boy>=3.2.0
faker>=18.0.0
responses>=0.23.0
freezegun>=1.2.0
```

### Django测试设置
```python
# settings/test.py
from .base import *

# 测试数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 禁用缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# 测试环境安全设置
SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['testserver']

# 禁用外部服务
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 测试邮件后端
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

## 单元测试策略
### 模型测试
```python
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.trading.models import Order, ExchangeAccount
from apps.users.models import User, Tenant

class OrderModelTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
        self.user = User.objects.create(
            username='testuser',
            tenant=self.tenant
        )
        self.exchange_account = ExchangeAccount.objects.create(
            tenant=self.tenant,
            name='Test Exchange',
            exchange='binance',
            api_key='test_key',
            secret_key='test_secret'
        )
    
    def test_order_creation(self):
        """测试订单创建"""
        order = Order.objects.create(
            tenant=self.tenant,
            exchange_account=self.exchange_account,
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=Decimal('0.1'),
            price=Decimal('45000'),
            remaining=Decimal('0.1'),
            status='open'
        )
        
        self.assertEqual(order.symbol, 'BTC/USDT')
        self.assertEqual(order.amount, Decimal('0.1'))
        self.assertEqual(order.status, 'open')
    
    def test_order_validation(self):
        """测试订单验证"""
        with self.assertRaises(ValidationError):
            Order.objects.create(
                tenant=self.tenant,
                exchange_account=self.exchange_account,
                symbol='INVALID',  # 无效的交易对格式
                type='limit',
                side='buy',
                amount=Decimal('-0.1'),  # 负数金额
                price=Decimal('45000'),
                remaining=Decimal('0.1'),
                status='open'
            )
```

### 视图测试
```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
import json

class OrderAPITest(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
        self.user = User.objects.create(
            username='testuser',
            tenant=self.tenant
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_order(self):
        """测试创建订单API"""
        url = reverse('order-list')
        data = {
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': '0.1',
            'price': '45000'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['symbol'], 'BTC/USDT')
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        url = reverse('order-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_tenant_isolation(self):
        """测试租户数据隔离"""
        # 创建另一个租户的订单
        other_tenant = Tenant.objects.create(name='Other Tenant')
        other_user = User.objects.create(
            username='otheruser',
            tenant=other_tenant
        )
        
        Order.objects.create(
            tenant=other_tenant,
            exchange_account=self.exchange_account,
            symbol='ETH/USDT',
            type='market',
            side='sell',
            amount=Decimal('1.0'),
            remaining=Decimal('1.0'),
            status='open'
        )
        
        # 当前用户不应该看到其他租户的订单
        url = reverse('order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # 应该为空
```

### 服务层测试
```python
import pytest
from unittest.mock import Mock, patch
from apps.trading.services import OrderExecutionService
from apps.trading.exceptions import InsufficientFundsError

class TestOrderExecutionService:
    def setup_method(self):
        self.exchange_account = Mock()
        self.service = OrderExecutionService(self.exchange_account)
    
    @patch('apps.trading.services.ccxt')
    def test_create_market_order_success(self, mock_ccxt):
        """测试成功创建市价单"""
        # 模拟CCXT返回
        mock_exchange = Mock()
        mock_exchange.create_market_order.return_value = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'type': 'market',
            'side': 'buy',
            'amount': 0.1,
            'status': 'closed'
        }
        mock_ccxt.binance.return_value = mock_exchange
        
        # 执行测试
        result = self.service.create_market_order('BTC/USDT', 'buy', 0.1)
        
        # 验证结果
        assert result['id'] == '12345'
        assert result['symbol'] == 'BTC/USDT'
        mock_exchange.create_market_order.assert_called_once_with(
            'BTC/USDT', 'buy', 0.1
        )
    
    @patch('apps.trading.services.ccxt')
    def test_create_order_insufficient_funds(self, mock_ccxt):
        """测试余额不足异常"""
        mock_exchange = Mock()
        mock_exchange.create_market_order.side_effect = ccxt.InsufficientFunds()
        mock_ccxt.binance.return_value = mock_exchange
        
        with pytest.raises(InsufficientFundsError):
            self.service.create_market_order('BTC/USDT', 'buy', 0.1)
```

## 集成测试
### 交易所集成测试
```python
import pytest
from django.test import TransactionTestCase
from apps.trading.services import ExchangeIntegrationService

class ExchangeIntegrationTest(TransactionTestCase):
    def setUp(self):
        # 使用测试网API
        self.exchange_config = {
            'exchange': 'binance',
            'api_key': 'test_api_key',
            'secret': 'test_secret',
            'sandbox': True
        }
        self.service = ExchangeIntegrationService(self.exchange_config)
    
    @pytest.mark.integration
    def test_exchange_connection(self):
        """测试交易所连接"""
        is_connected, message = self.service.test_connection()
        self.assertTrue(is_connected, f"连接失败: {message}")
    
    @pytest.mark.integration
    def test_fetch_balance(self):
        """测试获取余额"""
        balance = self.service.fetch_balance()
        self.assertIsInstance(balance, dict)
        self.assertIn('USDT', balance)
    
    @pytest.mark.integration
    def test_fetch_ticker(self):
        """测试获取行情"""
        ticker = self.service.fetch_ticker('BTC/USDT')
        self.assertIn('bid', ticker)
        self.assertIn('ask', ticker)
        self.assertIn('last', ticker)
```

### WebSocket测试
```python
import pytest
import asyncio
from channels.testing import WebsocketCommunicator
from apps.market.consumers import MarketDataConsumer

@pytest.mark.asyncio
class TestMarketDataConsumer:
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        communicator = WebsocketCommunicator(
            MarketDataConsumer.as_asgi(),
            "/ws/market/"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected
        
        # 发送订阅消息
        await communicator.send_json_to({
            'action': 'subscribe',
            'symbol': 'BTC/USDT'
        })
        
        # 接收确认消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'subscription_confirmed'
        
        await communicator.disconnect()
    
    async def test_market_data_broadcast(self):
        """测试市场数据广播"""
        communicator = WebsocketCommunicator(
            MarketDataConsumer.as_asgi(),
            "/ws/market/"
        )
        
        await communicator.connect()
        
        # 订阅市场数据
        await communicator.send_json_to({
            'action': 'subscribe',
            'symbol': 'BTC/USDT'
        })
        
        # 模拟市场数据更新
        from apps.market.services import MarketDataService
        service = MarketDataService()
        await service.broadcast_ticker_update('BTC/USDT', {
            'symbol': 'BTC/USDT',
            'price': 45000,
            'change': 0.02
        })
        
        # 验证接收到数据
        response = await communicator.receive_json_from()
        assert response['type'] == 'ticker_update'
        assert response['data']['symbol'] == 'BTC/USDT'
        
        await communicator.disconnect()
```

## 性能测试
### 负载测试
```python
import time
import concurrent.futures
from django.test import TestCase
from django.test.utils import override_settings

class PerformanceTest(TestCase):
    def test_concurrent_order_creation(self):
        """测试并发订单创建性能"""
        def create_order():
            # 模拟创建订单
            start_time = time.time()
            # ... 订单创建逻辑
            end_time = time.time()
            return end_time - start_time
        
        # 并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_order) for _ in range(100)]
            response_times = [future.result() for future in futures]
        
        # 验证性能指标
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        self.assertLess(avg_response_time, 0.5, "平均响应时间应小于500ms")
        self.assertLess(max_response_time, 2.0, "最大响应时间应小于2秒")
    
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            # 重置查询计数
            connection.queries_log.clear()
            
            # 执行查询
            orders = Order.objects.select_related('exchange_account').all()[:100]
            list(orders)  # 强制执行查询
            
            # 验证查询数量
            query_count = len(connection.queries)
            self.assertLess(query_count, 5, "查询数量应该被优化")
```

### 压力测试
```python
import pytest
from locust import HttpUser, task, between

class TradingSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录用户"""
        response = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def view_orders(self):
        """查看订单列表"""
        self.client.get("/api/orders/")
    
    @task(2)
    def view_balance(self):
        """查看余额"""
        self.client.get("/api/accounts/balance/")
    
    @task(1)
    def create_order(self):
        """创建订单"""
        self.client.post("/api/orders/", {
            "symbol": "BTC/USDT",
            "type": "limit",
            "side": "buy",
            "amount": "0.001",
            "price": "45000"
        })
```

## 安全测试
### 权限测试
```python
class SecurityTest(TestCase):
    def setUp(self):
        self.tenant1 = Tenant.objects.create(name='Tenant 1')
        self.tenant2 = Tenant.objects.create(name='Tenant 2')
        
        self.user1 = User.objects.create(username='user1', tenant=self.tenant1)
        self.user2 = User.objects.create(username='user2', tenant=self.tenant2)
    
    def test_tenant_data_isolation(self):
        """测试租户数据隔离"""
        # 用户1创建订单
        order1 = Order.objects.create(
            tenant=self.tenant1,
            symbol='BTC/USDT',
            # ... 其他字段
        )
        
        # 用户2不应该能访问用户1的订单
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/orders/{order1.id}/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        malicious_input = "'; DROP TABLE orders; --"
        
        response = self.client.get(f'/api/orders/?symbol={malicious_input}')
        
        # 应该返回400或者空结果，而不是500错误
        self.assertIn(response.status_code, [400, 200])
        
        # 验证表仍然存在
        self.assertTrue(Order.objects.model._meta.db_table)
```

### 输入验证测试
```python
class InputValidationTest(TestCase):
    def test_invalid_trading_symbol(self):
        """测试无效交易对输入"""
        invalid_symbols = [
            'BTCUSDT',  # 缺少分隔符
            'BTC-USDT',  # 错误分隔符
            'btc/usdt',  # 小写
            'BTC/USD/T',  # 多个分隔符
            '<script>alert("xss")</script>',  # XSS尝试
        ]
        
        for symbol in invalid_symbols:
            response = self.client.post('/api/orders/', {
                'symbol': symbol,
                'type': 'limit',
                'side': 'buy',
                'amount': '0.1',
                'price': '45000'
            })
            
            self.assertEqual(response.status_code, 400)
    
    def test_price_validation(self):
        """测试价格验证"""
        invalid_prices = [
            '-100',  # 负数
            '0',     # 零
            'abc',   # 非数字
            '1e100', # 过大的数
        ]
        
        for price in invalid_prices:
            response = self.client.post('/api/orders/', {
                'symbol': 'BTC/USDT',
                'type': 'limit',
                'side': 'buy',
                'amount': '0.1',
                'price': price
            })
            
            self.assertEqual(response.status_code, 400)
```

## 测试数据管理
### Factory模式
```python
import factory
from factory.django import DjangoModelFactory
from apps.users.models import User, Tenant
from apps.trading.models import Order, ExchangeAccount

class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant
    
    name = factory.Sequence(lambda n: f"Tenant {n}")

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    tenant = factory.SubFactory(TenantFactory)

class ExchangeAccountFactory(DjangoModelFactory):
    class Meta:
        model = ExchangeAccount
    
    name = factory.Faker('company')
    exchange = 'binance'
    api_key = factory.Faker('uuid4')
    secret_key = factory.Faker('uuid4')
    tenant = factory.SubFactory(TenantFactory)

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order
    
    symbol = 'BTC/USDT'
    type = 'limit'
    side = 'buy'
    amount = factory.Faker('pydecimal', left_digits=2, right_digits=8, positive=True)
    price = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    status = 'open'
    tenant = factory.SubFactory(TenantFactory)
    exchange_account = factory.SubFactory(ExchangeAccountFactory)
```

### 测试数据清理
```python
import pytest
from django.test import TransactionTestCase

class BaseTestCase(TransactionTestCase):
    def setUp(self):
        """测试前准备"""
        self.setup_test_data()
    
    def tearDown(self):
        """测试后清理"""
        self.cleanup_test_data()
    
    def setup_test_data(self):
        """设置测试数据"""
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.exchange_account = ExchangeAccountFactory(tenant=self.tenant)
    
    def cleanup_test_data(self):
        """清理测试数据"""
        # Django会自动回滚事务，但可以在这里做额外清理
        pass

@pytest.fixture
def test_data():
    """Pytest fixture for test data"""
    tenant = TenantFactory()
    user = UserFactory(tenant=tenant)
    exchange_account = ExchangeAccountFactory(tenant=tenant)
    
    yield {
        'tenant': tenant,
        'user': user,
        'exchange_account': exchange_account
    }
    
    # 清理代码（如果需要）
```

## 持续集成测试
### GitHub Actions配置
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python 3.12
      uses: actions/setup-python@v2
      with:
        python-version: 3.12
    
    - name: Create virtual environment
      run: |
        python -m venv .venv
        source .venv/bin/activate
        echo "VIRTUAL_ENV=$VIRTUAL_ENV" >> $GITHUB_ENV
        echo "$VIRTUAL_ENV/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest --cov=apps --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### 测试报告
```python
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = 
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```