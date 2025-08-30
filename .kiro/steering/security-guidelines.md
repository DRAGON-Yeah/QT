# 安全指南和最佳实践

## 身份认证和授权
### JWT认证机制
```python
# JWT Token生成
def generate_jwt_token(user):
    payload = {
        'user_id': user.id,
        'tenant_id': user.tenant.id,
        'username': user.username,
        'roles': [role.name for role in user.roles.all()],
        'permissions': user.get_all_permissions(),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

# JWT Token验证
def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token已过期')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('无效的Token')
```

### 权限装饰器
```python
from functools import wraps
from django.http import HttpResponseForbidden

def require_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('未登录')
            
            if not request.user.has_permission(permission_name):
                return HttpResponseForbidden('权限不足')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@require_permission('trading.create_order')
def create_order_view(request):
    pass
```

## 数据加密和保护
### 敏感数据加密
```python
from cryptography.fernet import Fernet
from django.conf import settings

class EncryptionService:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt(self, encrypted_data):
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

# API密钥加密存储
class SecureExchangeAccount(models.Model):
    api_key_encrypted = models.TextField()
    secret_key_encrypted = models.TextField()
    
    def set_credentials(self, api_key, secret_key):
        encryption = EncryptionService()
        self.api_key_encrypted = encryption.encrypt(api_key)
        self.secret_key_encrypted = encryption.encrypt(secret_key)
    
    def get_credentials(self):
        encryption = EncryptionService()
        api_key = encryption.decrypt(self.api_key_encrypted)
        secret_key = encryption.decrypt(self.secret_key_encrypted)
        return api_key, secret_key
```

### 密码安全
```python
from django.contrib.auth.hashers import make_password, check_password
import secrets
import string

class PasswordService:
    @staticmethod
    def generate_secure_password(length=12):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def hash_password(password):
        return make_password(password)
    
    @staticmethod
    def verify_password(password, hashed_password):
        return check_password(password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password):
        if len(password) < 8:
            return False, "密码长度至少8位"
        
        if not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        
        if not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        
        if not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        
        return True, "密码强度符合要求"
```

## API安全
### 请求验证
```python
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib

class APISecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # API请求频率限制
        if not self.check_rate_limit(request):
            return HttpResponse('请求过于频繁', status=429)
        
        # API签名验证
        if request.path.startswith('/api/'):
            if not self.verify_api_signature(request):
                return HttpResponse('签名验证失败', status=401)
        
        response = self.get_response(request)
        return response
    
    def verify_api_signature(self, request):
        signature = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        
        if not signature or not timestamp:
            return False
        
        # 验证时间戳（防重放攻击）
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 300:  # 5分钟有效期
            return False
        
        # 验证签名
        expected_signature = self.generate_signature(request, timestamp)
        return hmac.compare_digest(signature, expected_signature)
```

### 输入验证和清理
```python
from django.core.validators import validate_email
from decimal import Decimal, InvalidOperation
import re

class InputValidator:
    @staticmethod
    def validate_trading_symbol(symbol):
        pattern = r'^[A-Z]{2,10}/[A-Z]{2,10}$'
        if not re.match(pattern, symbol):
            raise ValidationError('无效的交易对格式')
        return symbol
    
    @staticmethod
    def validate_price(price):
        try:
            price_decimal = Decimal(str(price))
            if price_decimal <= 0:
                raise ValidationError('价格必须大于0')
            return price_decimal
        except (InvalidOperation, ValueError):
            raise ValidationError('无效的价格格式')
    
    @staticmethod
    def validate_amount(amount):
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValidationError('数量必须大于0')
            return amount_decimal
        except (InvalidOperation, ValueError):
            raise ValidationError('无效的数量格式')
    
    @staticmethod
    def sanitize_string(input_string, max_length=255):
        if not isinstance(input_string, str):
            raise ValidationError('输入必须是字符串')
        
        # 移除危险字符
        sanitized = re.sub(r'[<>"\']', '', input_string)
        
        # 限制长度
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
```

## 数据库安全
### SQL注入防护
```python
from django.db import connection

class SecureQueryService:
    @staticmethod
    def execute_raw_query(query, params=None):
        # 使用参数化查询防止SQL注入
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()
    
    @staticmethod
    def validate_table_name(table_name):
        # 验证表名，防止SQL注入
        allowed_tables = [
            'users', 'orders', 'strategies', 'exchange_accounts'
        ]
        if table_name not in allowed_tables:
            raise ValueError('不允许访问的表')
        return table_name

# 使用ORM而不是原生SQL
class SecureOrderService:
    def get_user_orders(self, user_id, status=None):
        # 好的做法：使用ORM
        queryset = Order.objects.filter(user_id=user_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def bad_example(self, user_id, status):
        # 坏的做法：容易SQL注入
        query = f"SELECT * FROM orders WHERE user_id = {user_id} AND status = '{status}'"
        # 不要这样做！
```

### 数据库连接安全
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # 强制SSL连接
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

# 数据库访问日志
LOGGING = {
    'version': 1,
    'handlers': {
        'db_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'db_queries.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['db_log'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## 网络安全
### HTTPS配置
```python
# settings.py - 生产环境安全设置
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cookie安全
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

### CORS配置
```python
# CORS安全配置
CORS_ALLOWED_ORIGINS = [
    "https://quanttrade.example.com",
    "https://app.quanttrade.example.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-signature',
    'x-timestamp',
]
```

## 审计和日志
### 安全审计日志
```python
import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete

security_logger = logging.getLogger('security')

class SecurityAuditService:
    @staticmethod
    def log_user_login(sender, request, user, **kwargs):
        security_logger.info(
            f"用户登录: {user.username}, IP: {request.META.get('REMOTE_ADDR')}, "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        )
    
    @staticmethod
    def log_user_logout(sender, request, user, **kwargs):
        security_logger.info(
            f"用户登出: {user.username}, IP: {request.META.get('REMOTE_ADDR')}"
        )
    
    @staticmethod
    def log_sensitive_operation(user, operation, details):
        security_logger.warning(
            f"敏感操作: 用户={user.username}, 操作={operation}, "
            f"详情={details}, 时间={timezone.now()}"
        )

# 连接信号
user_logged_in.connect(SecurityAuditService.log_user_login)
user_logged_out.connect(SecurityAuditService.log_user_logout)
```

### 操作审计
```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)
    old_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class AuditMixin:
    def save(self, *args, **kwargs):
        # 记录修改前的值
        old_values = {}
        if self.pk:
            old_instance = self.__class__.objects.get(pk=self.pk)
            for field in self._meta.fields:
                old_values[field.name] = getattr(old_instance, field.name)
        
        super().save(*args, **kwargs)
        
        # 记录审计日志
        new_values = {field.name: getattr(self, field.name) for field in self._meta.fields}
        AuditLog.objects.create(
            user=get_current_user(),
            tenant=get_current_tenant(),
            action='UPDATE' if old_values else 'CREATE',
            resource_type=self.__class__.__name__,
            resource_id=str(self.pk),
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )
```

## 交易安全
### 订单安全验证
```python
class OrderSecurityService:
    @staticmethod
    def validate_order_security(user, order_data):
        # 验证用户权限
        if not user.has_permission('trading.create_order'):
            raise PermissionDenied('无交易权限')
        
        # 验证交易对权限
        symbol = order_data['symbol']
        if not user.can_trade_symbol(symbol):
            raise PermissionDenied(f'无权限交易 {symbol}')
        
        # 验证订单金额限制
        amount = Decimal(order_data['amount'])
        max_order_amount = user.get_max_order_amount(symbol)
        if amount > max_order_amount:
            raise ValidationError(f'订单金额超过限制: {max_order_amount}')
        
        # 验证余额
        if not OrderSecurityService.check_sufficient_balance(user, order_data):
            raise ValidationError('余额不足')
        
        return True
    
    @staticmethod
    def check_sufficient_balance(user, order_data):
        # 实现余额检查逻辑
        pass
```

### API密钥安全管理
```python
class APIKeySecurityService:
    @staticmethod
    def validate_api_key_permissions(api_key, required_permissions):
        # 验证API密钥权限
        key_permissions = APIKeySecurityService.get_key_permissions(api_key)
        
        for permission in required_permissions:
            if permission not in key_permissions:
                raise PermissionDenied(f'API密钥缺少权限: {permission}')
        
        return True
    
    @staticmethod
    def rotate_api_keys(exchange_account):
        # 定期轮换API密钥
        old_key = exchange_account.api_key
        
        # 生成新的API密钥（需要调用交易所API）
        new_key, new_secret = ExchangeAPIService.generate_new_keys()
        
        # 更新存储的密钥
        exchange_account.set_credentials(new_key, new_secret)
        exchange_account.save()
        
        # 记录密钥轮换日志
        SecurityAuditService.log_sensitive_operation(
            exchange_account.user,
            'API_KEY_ROTATION',
            f'交易所: {exchange_account.exchange}'
        )
```

## 环境安全
### 环境变量管理
```python
# .env 文件示例
SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
ENCRYPTION_KEY=your-encryption-key-here

# Binance API (生产环境)
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key

# Binance API (测试环境)
BINANCE_TESTNET_API_KEY=your-testnet-api-key
BINANCE_TESTNET_SECRET_KEY=your-testnet-secret-key
```

### Docker安全配置
```dockerfile
# 使用非root用户运行
FROM python:3.12-slim
RUN groupadd -r quanttrade && useradd -r -g quanttrade quanttrade
USER quanttrade

# 最小化镜像
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 安全的文件权限
COPY --chown=quanttrade:quanttrade . /app
WORKDIR /app
RUN chmod 755 /app
```

## 监控和告警
### 安全监控
```python
class SecurityMonitorService:
    @staticmethod
    def detect_suspicious_activity(user, request):
        # 检测异常登录
        if SecurityMonitorService.is_unusual_login_location(user, request):
            SecurityMonitorService.send_security_alert(
                user, 'UNUSUAL_LOGIN_LOCATION', request
            )
        
        # 检测异常交易行为
        if SecurityMonitorService.is_unusual_trading_pattern(user):
            SecurityMonitorService.send_security_alert(
                user, 'UNUSUAL_TRADING_PATTERN', request
            )
    
    @staticmethod
    def send_security_alert(user, alert_type, request):
        # 发送安全告警
        pass
```