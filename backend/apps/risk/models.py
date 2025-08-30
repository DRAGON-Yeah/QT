# -*- coding: utf-8 -*-
"""
风险管理数据模型
"""
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.core.models import TenantModel

User = get_user_model()


class RiskAlert(TenantModel):
    """风险预警规则模型"""
    
    ALERT_LEVELS = [
        ('low', '轻度预警'),
        ('medium', '中度预警'),
        ('high', '重度预警'),
    ]
    
    ALERT_TYPES = [
        ('var', 'VaR风险值'),
        ('drawdown', '最大回撤'),
        ('sharpe', '夏普比率'),
        ('position_ratio', '持仓比例'),
        ('loss_ratio', '亏损比例'),
        ('volatility', '波动率'),
    ]
    
    NOTIFICATION_CHANNELS = [
        ('system', '系统内通知'),
        ('email', '邮件通知'),
        ('sms', '短信通知'),
        ('webhook', 'Webhook通知'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='预警规则名称')
    description = models.TextField(blank=True, verbose_name='规则描述')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name='预警类型')
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, verbose_name='预警级别')
    
    # 阈值配置
    threshold_value = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='阈值')
    comparison_operator = models.CharField(
        max_length=10, 
        choices=[('>', '大于'), ('<', '小于'), ('>=', '大于等于'), ('<=', '小于等于')],
        default='>',
        verbose_name='比较操作符'
    )
    
    # 通知配置
    notification_channels = models.JSONField(default=list, verbose_name='通知渠道')
    notification_template = models.TextField(blank=True, verbose_name='通知模板')
    
    # 触发配置
    trigger_frequency = models.IntegerField(default=60, verbose_name='检查频率(秒)')
    cooldown_period = models.IntegerField(default=300, verbose_name='冷却期(秒)')
    max_triggers_per_day = models.IntegerField(default=10, verbose_name='每日最大触发次数')
    
    # 自动操作配置
    auto_action_enabled = models.BooleanField(default=False, verbose_name='启用自动操作')
    auto_action_type = models.CharField(
        max_length=20,
        choices=[
            ('stop_strategy', '停止策略'),
            ('reduce_position', '减仓'),
            ('close_position', '平仓'),
            ('stop_trading', '停止交易'),
        ],
        blank=True,
        verbose_name='自动操作类型'
    )
    auto_action_params = models.JSONField(default=dict, verbose_name='自动操作参数')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '风险预警规则'
        verbose_name_plural = '风险预警规则'
        indexes = [
            models.Index(fields=['tenant', 'alert_type', 'is_active']),
            models.Index(fields=['tenant', 'alert_level']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_alert_level_display()})"


class RiskAlertTrigger(TenantModel):
    """风险预警触发记录"""
    
    TRIGGER_STATUS = [
        ('triggered', '已触发'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('ignored', '已忽略'),
    ]
    
    alert_rule = models.ForeignKey(RiskAlert, on_delete=models.CASCADE, verbose_name='预警规则')
    trigger_time = models.DateTimeField(auto_now_add=True, verbose_name='触发时间')
    trigger_value = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='触发值')
    status = models.CharField(max_length=20, choices=TRIGGER_STATUS, default='triggered', verbose_name='状态')
    
    # 通知记录
    notifications_sent = models.JSONField(default=list, verbose_name='已发送通知')
    notification_errors = models.JSONField(default=list, verbose_name='通知错误')
    
    # 自动操作记录
    auto_action_executed = models.BooleanField(default=False, verbose_name='自动操作已执行')
    auto_action_result = models.JSONField(default=dict, verbose_name='自动操作结果')
    auto_action_error = models.TextField(blank=True, verbose_name='自动操作错误')
    
    # 处理记录
    resolved_time = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='处理人')
    resolution_notes = models.TextField(blank=True, verbose_name='处理备注')
    
    class Meta:
        verbose_name = '风险预警触发记录'
        verbose_name_plural = '风险预警触发记录'
        indexes = [
            models.Index(fields=['tenant', 'trigger_time']),
            models.Index(fields=['alert_rule', 'status']),
        ]
    
    def __str__(self):
        return f"{self.alert_rule.name} - {self.trigger_time}"


class StopLossRule(TenantModel):
    """止损止盈规则模型"""
    
    RULE_TYPES = [
        ('stop_loss', '止损'),
        ('take_profit', '止盈'),
        ('trailing_stop', '跟踪止损'),
    ]
    
    TRIGGER_CONDITIONS = [
        ('price', '价格触发'),
        ('percentage', '百分比触发'),
        ('amount', '金额触发'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    description = models.TextField(blank=True, verbose_name='规则描述')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    
    # 适用范围
    symbol = models.CharField(max_length=20, blank=True, verbose_name='交易对')
    strategy_id = models.IntegerField(null=True, blank=True, verbose_name='策略ID')
    
    # 触发条件
    trigger_condition = models.CharField(max_length=20, choices=TRIGGER_CONDITIONS, verbose_name='触发条件')
    trigger_value = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='触发值')
    
    # 执行动作
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('market_sell', '市价卖出'),
            ('limit_sell', '限价卖出'),
            ('partial_close', '部分平仓'),
            ('full_close', '全部平仓'),
        ],
        verbose_name='执行动作'
    )
    action_params = models.JSONField(default=dict, verbose_name='动作参数')
    
    # 跟踪止损特有参数
    trailing_distance = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True, verbose_name='跟踪距离'
    )
    trailing_step = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True, verbose_name='跟踪步长'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '止损止盈规则'
        verbose_name_plural = '止损止盈规则'
        indexes = [
            models.Index(fields=['tenant', 'symbol', 'is_active']),
            models.Index(fields=['tenant', 'rule_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class StopLossExecution(TenantModel):
    """止损止盈执行记录"""
    
    EXECUTION_STATUS = [
        ('pending', '待执行'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
        ('cancelled', '已取消'),
    ]
    
    rule = models.ForeignKey(StopLossRule, on_delete=models.CASCADE, verbose_name='止损规则')
    trigger_time = models.DateTimeField(auto_now_add=True, verbose_name='触发时间')
    trigger_price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='触发价格')
    
    # 执行信息
    execution_status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='pending', verbose_name='执行状态')
    order_id = models.CharField(max_length=100, blank=True, verbose_name='订单ID')
    executed_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='执行价格')
    executed_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='执行数量')
    
    # 结果信息
    execution_time = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')
    profit_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='盈亏金额')
    execution_fee = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='执行手续费')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    
    class Meta:
        verbose_name = '止损止盈执行记录'
        verbose_name_plural = '止损止盈执行记录'
        indexes = [
            models.Index(fields=['tenant', 'trigger_time']),
            models.Index(fields=['rule', 'execution_status']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.trigger_time}"


class RiskMetrics(TenantModel):
    """风险指标模型"""
    
    METRIC_TYPES = [
        ('var', 'VaR风险值'),
        ('cvar', 'CVaR条件风险值'),
        ('drawdown', '最大回撤'),
        ('sharpe', '夏普比率'),
        ('sortino', '索提诺比率'),
        ('calmar', '卡玛比率'),
        ('volatility', '波动率'),
        ('beta', 'Beta系数'),
        ('alpha', 'Alpha系数'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES, verbose_name='指标类型')
    symbol = models.CharField(max_length=20, blank=True, verbose_name='交易对')
    strategy_id = models.IntegerField(null=True, blank=True, verbose_name='策略ID')
    
    # 指标值
    metric_value = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='指标值')
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='置信水平')
    time_horizon = models.IntegerField(null=True, blank=True, verbose_name='时间窗口(天)')
    
    # 计算参数
    calculation_params = models.JSONField(default=dict, verbose_name='计算参数')
    data_source = models.CharField(max_length=50, verbose_name='数据源')
    
    # 时间信息
    calculation_time = models.DateTimeField(auto_now_add=True, verbose_name='计算时间')
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name='有效期至')
    
    class Meta:
        verbose_name = '风险指标'
        verbose_name_plural = '风险指标'
        indexes = [
            models.Index(fields=['tenant', 'metric_type', 'calculation_time']),
            models.Index(fields=['tenant', 'symbol', 'metric_type']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.metric_value}"