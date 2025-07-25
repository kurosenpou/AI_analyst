"""
Monitoring and Alerting System
提供系統監控、指標收集和報警功能
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """報警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"      # 計數器
    GAUGE = "gauge"         # 儀表盤
    HISTOGRAM = "histogram"  # 直方圖
    TIMER = "timer"         # 計時器


@dataclass
class MetricValue:
    """指標值"""
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """報警信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """報警規則"""
    name: str
    metric_name: str
    condition: str  # 條件表達式，如 "> 0.8", "< 100", "== 0"
    threshold: float
    level: AlertLevel
    cooldown_seconds: int = 300  # 冷卻時間
    description: str = ""
    enabled: bool = True


class Metric:
    """指標類"""
    
    def __init__(self, name: str, metric_type: MetricType, description: str = ""):
        self.name = name
        self.type = metric_type
        self.description = description
        self.values: deque = deque(maxlen=1000)  # 保留最近1000個值
        self._lock = threading.RLock()
    
    def add_value(self, value: float, labels: Optional[Dict[str, str]] = None):
        """添加指標值"""
        with self._lock:
            metric_value = MetricValue(
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self.values.append(metric_value)
    
    def get_latest_value(self) -> Optional[MetricValue]:
        """獲取最新值"""
        with self._lock:
            return self.values[-1] if self.values else None
    
    def get_values_in_range(self, start_time: datetime, end_time: datetime) -> List[MetricValue]:
        """獲取時間範圍內的值"""
        with self._lock:
            return [
                v for v in self.values 
                if start_time <= v.timestamp <= end_time
            ]
    
    def get_average(self, duration_minutes: int = 5) -> Optional[float]:
        """獲取指定時間內的平均值"""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        values = self.get_values_in_range(start_time, end_time)
        
        if not values:
            return None
        
        return sum(v.value for v in values) / len(values)
    
    def get_max(self, duration_minutes: int = 5) -> Optional[float]:
        """獲取指定時間內的最大值"""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        values = self.get_values_in_range(start_time, end_time)
        
        if not values:
            return None
        
        return max(v.value for v in values)
    
    def get_min(self, duration_minutes: int = 5) -> Optional[float]:
        """獲取指定時間內的最小值"""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        values = self.get_values_in_range(start_time, end_time)
        
        if not values:
            return None
        
        return min(v.value for v in values)


class MonitoringSystem:
    """監控系統"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alerts: List[Alert] = []
        self.alert_rules: List[AlertRule] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self._lock = threading.RLock()
        self._last_alert_times: Dict[str, datetime] = {}
        
        # 啟動監控循環
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        # 初始化預設指標
        self._initialize_default_metrics()
        
        logger.info("Monitoring system initialized")
    
    def _initialize_default_metrics(self):
        """初始化預設指標"""
        # API相關指標
        self.register_metric("api_requests_total", MetricType.COUNTER, "總API請求數")
        self.register_metric("api_request_duration", MetricType.TIMER, "API請求響應時間")
        self.register_metric("api_errors_total", MetricType.COUNTER, "API錯誤總數")
        
        # 模型相關指標
        self.register_metric("model_requests_total", MetricType.COUNTER, "模型請求總數")
        self.register_metric("model_response_time", MetricType.TIMER, "模型響應時間")
        self.register_metric("model_errors_total", MetricType.COUNTER, "模型錯誤總數")
        self.register_metric("model_token_usage", MetricType.COUNTER, "模型Token使用量")
        
        # 系統相關指標
        self.register_metric("system_memory_usage", MetricType.GAUGE, "系統記憶體使用率")
        self.register_metric("system_cpu_usage", MetricType.GAUGE, "系統CPU使用率")
        self.register_metric("system_health_check", MetricType.GAUGE, "系統健康檢查分數")
        
        # 斷路器相關指標
        self.register_metric("circuit_breaker_state", MetricType.GAUGE, "斷路器狀態")
        self.register_metric("circuit_breaker_failures", MetricType.COUNTER, "斷路器失敗數")
        
        # 預設報警規則
        self._initialize_default_alert_rules()
    
    def _initialize_default_alert_rules(self):
        """初始化預設報警規則"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="api_errors_total",
                condition=">",
                threshold=10,
                level=AlertLevel.WARNING,
                description="API錯誤率過高",
                cooldown_seconds=300
            ),
            AlertRule(
                name="high_response_time",
                metric_name="api_request_duration",
                condition=">",
                threshold=30,
                level=AlertLevel.WARNING,
                description="API響應時間過長",
                cooldown_seconds=180
            ),
            AlertRule(
                name="model_unavailable",
                metric_name="model_errors_total",
                condition=">",
                threshold=5,
                level=AlertLevel.ERROR,
                description="模型連續失敗",
                cooldown_seconds=600
            ),
            AlertRule(
                name="circuit_breaker_open",
                metric_name="circuit_breaker_state",
                condition="==",
                threshold=1,  # 1表示打開狀態
                level=AlertLevel.CRITICAL,
                description="斷路器已打開",
                cooldown_seconds=60
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def register_metric(self, name: str, metric_type: MetricType, description: str = ""):
        """註冊指標"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Metric(name, metric_type, description)
                logger.debug(f"Registered metric: {name}")
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """記錄指標值"""
        with self._lock:
            if name in self.metrics:
                self.metrics[name].add_value(value, labels)
            else:
                logger.warning(f"Metric '{name}' not registered")
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """獲取指標"""
        return self.metrics.get(name)
    
    def add_alert_rule(self, rule: AlertRule):
        """添加報警規則"""
        with self._lock:
            self.alert_rules.append(rule)
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """移除報警規則"""
        with self._lock:
            self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加報警回調函數"""
        self.alert_callbacks.append(callback)
    
    def _evaluate_alert_rules(self):
        """評估報警規則"""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # 檢查冷卻時間
            last_alert_time = self._last_alert_times.get(rule.name)
            if (last_alert_time and 
                (current_time - last_alert_time).total_seconds() < rule.cooldown_seconds):
                continue
            
            metric = self.get_metric(rule.metric_name)
            if not metric:
                continue
            
            latest_value = metric.get_latest_value()
            if not latest_value:
                continue
            
            # 評估條件
            triggered = self._evaluate_condition(
                latest_value.value, 
                rule.condition, 
                rule.threshold
            )
            
            if triggered:
                alert = Alert(
                    id=f"{rule.name}_{int(current_time.timestamp())}",
                    level=rule.level,
                    title=f"Alert: {rule.name}",
                    message=f"{rule.description}. Current value: {latest_value.value}, Threshold: {rule.threshold}",
                    source=f"metric:{rule.metric_name}",
                    timestamp=current_time,
                    metadata={
                        'metric_name': rule.metric_name,
                        'metric_value': latest_value.value,
                        'threshold': rule.threshold,
                        'condition': rule.condition,
                        'rule_name': rule.name
                    }
                )
                
                self._trigger_alert(alert)
                self._last_alert_times[rule.name] = current_time
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """評估條件"""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return abs(value - threshold) < 0.001  # 浮點數比較
        elif condition == "!=":
            return abs(value - threshold) >= 0.001
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False
    
    def _trigger_alert(self, alert: Alert):
        """觸發報警"""
        with self._lock:
            self.alerts.append(alert)
            
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
        
        # 調用回調函數
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def resolve_alert(self, alert_id: str):
        """解決報警"""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    logger.info(f"Alert resolved: {alert_id}")
                    break
    
    def get_alerts(self, 
                   level: Optional[AlertLevel] = None, 
                   resolved: Optional[bool] = None,
                   limit: int = 100) -> List[Alert]:
        """獲取報警列表"""
        with self._lock:
            filtered_alerts = self.alerts
            
            if level:
                filtered_alerts = [a for a in filtered_alerts if a.level == level]
            
            if resolved is not None:
                filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved]
            
            # 按時間降序排序
            filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return filtered_alerts[:limit]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        with self._lock:
            summary = {}
            for name, metric in self.metrics.items():
                latest = metric.get_latest_value()
                summary[name] = {
                    'type': metric.type.value,
                    'description': metric.description,
                    'latest_value': latest.value if latest else None,
                    'latest_timestamp': latest.timestamp.isoformat() if latest else None,
                    'average_5m': metric.get_average(5),
                    'max_5m': metric.get_max(5),
                    'min_5m': metric.get_min(5),
                    'total_samples': len(metric.values)
                }
            return summary
    
    def _monitoring_loop(self):
        """監控循環"""
        while self._monitoring_active:
            try:
                self._evaluate_alert_rules()
                time.sleep(10)  # 每10秒檢查一次
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # 出錯時等待30秒
    
    def shutdown(self):
        """關閉監控系統"""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        logger.info("Monitoring system shutdown")


# 全局監控系統實例
monitoring_system = MonitoringSystem()


def get_monitoring_system() -> MonitoringSystem:
    """獲取監控系統實例"""
    return monitoring_system


# 便捷函數
def record_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """記錄指標值"""
    monitoring_system.record_metric(name, value, labels)


def trigger_custom_alert(title: str, message: str, level: AlertLevel = AlertLevel.INFO, 
                        source: str = "custom", metadata: Optional[Dict[str, Any]] = None):
    """觸發自定義報警"""
    alert = Alert(
        id=f"custom_{int(datetime.now().timestamp())}",
        level=level,
        title=title,
        message=message,
        source=source,
        timestamp=datetime.now(),
        metadata=metadata or {}
    )
    monitoring_system._trigger_alert(alert)


class MetricDecorator:
    """指標裝飾器"""
    
    @staticmethod
    def count_calls(metric_name: str, labels: Optional[Dict[str, str]] = None):
        """計數調用次數"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                record_metric(metric_name, 1, labels)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def time_execution(metric_name: str, labels: Optional[Dict[str, str]] = None):
        """計時執行時間"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    record_metric(metric_name, execution_time, labels)
            return wrapper
        return decorator
