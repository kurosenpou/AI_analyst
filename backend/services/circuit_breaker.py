"""
Circuit Breaker Pattern Implementation
提供斷路器模式以防止級聯故障和系統過載
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import threading

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """斷路器狀態"""
    CLOSED = "closed"      # 正常狀態，允許請求通過
    OPEN = "open"          # 斷路器打開，阻止請求
    HALF_OPEN = "half_open"  # 半開狀態，允許少量請求測試


@dataclass
class CircuitBreakerConfig:
    """斷路器配置"""
    failure_threshold: int = 5  # 失敗閾值
    recovery_timeout: int = 60  # 恢復超時時間（秒）
    expected_exception: tuple = (Exception,)  # 預期的異常類型
    success_threshold: int = 3  # 半開狀態下成功閾值
    timeout: float = 30.0  # 請求超時時間


@dataclass
class CircuitBreakerStats:
    """斷路器統計信息"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state_changes: list = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """失敗率"""
        return 1.0 - self.success_rate


class CircuitBreaker:
    """
    斷路器實現
    
    用於保護服務免受級聯故障的影響，當檢測到下游服務故障時
    自動切斷請求，避免資源浪費和系統過載。
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._next_attempt_time = None
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    def _record_success(self):
        """記錄成功"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.now()
            
            # 如果在半開狀態下連續成功，則關閉斷路器
            if (self.state == CircuitState.HALF_OPEN and 
                self.stats.consecutive_successes >= self.config.success_threshold):
                self._change_state(CircuitState.CLOSED)
    
    def _record_failure(self, exception: Exception):
        """記錄失敗"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = datetime.now()
            
            # 檢查是否需要打開斷路器
            if (self.state == CircuitState.CLOSED and 
                self.stats.consecutive_failures >= self.config.failure_threshold):
                self._change_state(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                # 半開狀態下失敗，重新打開斷路器
                self._change_state(CircuitState.OPEN)
    
    def _change_state(self, new_state: CircuitState):
        """改變斷路器狀態"""
        old_state = self.state
        self.state = new_state
        
        # 記錄狀態變化
        self.stats.state_changes.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': datetime.now(),
            'failure_count': self.stats.consecutive_failures,
            'success_count': self.stats.consecutive_successes
        })
        
        if new_state == CircuitState.OPEN:
            # 設置下次嘗試時間
            self._next_attempt_time = datetime.now() + timedelta(seconds=self.config.recovery_timeout)
        
        logger.warning(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}")
    
    def _can_attempt(self) -> bool:
        """檢查是否可以嘗試請求"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # 檢查是否到了嘗試恢復的時間
            if self._next_attempt_time and datetime.now() >= self._next_attempt_time:
                self._change_state(CircuitState.HALF_OPEN)
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        執行被保護的異步函數調用
        
        Args:
            func: 要執行的異步函數
            *args: 函數參數
            **kwargs: 函數關鍵字參數
            
        Returns:
            函數執行結果
            
        Raises:
            CircuitBreakerOpenError: 斷路器處於打開狀態
            Exception: 函數執行時的異常
        """
        if not self._can_attempt():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Next attempt at {self._next_attempt_time}"
            )
        
        try:
            # 設置超時
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            self._record_success()
            return result
        
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise
        except asyncio.TimeoutError as e:
            self._record_failure(e)
            raise CircuitBreakerTimeoutError(
                f"Circuit breaker '{self.name}' timeout after {self.config.timeout}s"
            ) from e
    
    def call_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        執行被保護的同步函數調用
        
        Args:
            func: 要執行的同步函數
            *args: 函數參數
            **kwargs: 函數關鍵字參數
            
        Returns:
            函數執行結果
            
        Raises:
            CircuitBreakerOpenError: 斷路器處於打開狀態
            Exception: 函數執行時的異常
        """
        if not self._can_attempt():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Next attempt at {self._next_attempt_time}"
            )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """獲取斷路器狀態"""
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'stats': {
                    'total_requests': self.stats.total_requests,
                    'successful_requests': self.stats.successful_requests,
                    'failed_requests': self.stats.failed_requests,
                    'success_rate': self.stats.success_rate,
                    'failure_rate': self.stats.failure_rate,
                    'consecutive_failures': self.stats.consecutive_failures,
                    'consecutive_successes': self.stats.consecutive_successes,
                    'last_failure_time': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                    'last_success_time': self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
                },
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'success_threshold': self.config.success_threshold,
                    'timeout': self.config.timeout,
                },
                'next_attempt_time': self._next_attempt_time.isoformat() if self._next_attempt_time else None,
                'recent_state_changes': self.stats.state_changes[-10:]  # 最近10次狀態變化
            }
    
    def reset(self):
        """重置斷路器狀態"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self._next_attempt_time = None
            logger.info(f"Circuit breaker '{self.name}' has been reset")


class CircuitBreakerOpenError(Exception):
    """斷路器打開時的異常"""
    pass


class CircuitBreakerTimeoutError(Exception):
    """斷路器超時異常"""
    pass


class CircuitBreakerManager:
    """斷路器管理器"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """獲取或創建斷路器"""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有斷路器狀態"""
        with self._lock:
            return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def reset_breaker(self, name: str):
        """重置指定斷路器"""
        with self._lock:
            if name in self._breakers:
                self._breakers[name].reset()
    
    def reset_all(self):
        """重置所有斷路器"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# 全局斷路器管理器實例
circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """獲取斷路器實例"""
    return circuit_breaker_manager.get_breaker(name, config)
