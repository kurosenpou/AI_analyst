"""
Advanced Retry Strategies
實現高級重試策略，包括指數退避、抖動、重試預算等
"""

import asyncio
import random
import time
import logging
from typing import Any, Callable, Optional, Union, List, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重試策略類型"""
    FIXED_DELAY = "fixed_delay"              # 固定延遲
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指數退避
    LINEAR_BACKOFF = "linear_backoff"        # 線性退避
    FIBONACCI_BACKOFF = "fibonacci_backoff"  # 斐波那契退避
    CUSTOM = "custom"                        # 自定義


class JitterType(Enum):
    """抖動類型"""
    NONE = "none"          # 無抖動
    FULL = "full"          # 全抖動
    EQUAL = "equal"        # 等抖動
    DECORRELATED = "decorrelated"  # 去相關抖動


@dataclass
class RetryConfig:
    """重試配置"""
    max_attempts: int = 3                    # 最大重試次數
    base_delay: float = 1.0                 # 基礎延遲時間（秒）
    max_delay: float = 60.0                 # 最大延遲時間（秒）
    multiplier: float = 2.0                 # 退避乘數
    jitter_type: JitterType = JitterType.EQUAL  # 抖動類型
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF  # 重試策略
    
    # 條件控制
    retry_on_exceptions: tuple = (Exception,)  # 重試的異常類型
    stop_on_exceptions: tuple = ()             # 停止重試的異常類型
    
    # 預算控制
    retry_budget_enabled: bool = False         # 是否啟用重試預算
    retry_budget_ttl: int = 3600              # 重試預算TTL（秒）
    retry_budget_max_ratio: float = 0.1       # 最大重試比例
    
    # 回調函數
    on_retry: Optional[Callable] = None        # 重試時的回調
    on_giveup: Optional[Callable] = None       # 放棄時的回調


@dataclass
class RetryAttempt:
    """重試嘗試記錄"""
    attempt_number: int
    delay: float
    exception: Optional[Exception]
    timestamp: datetime
    total_elapsed: float


class RetryBudget:
    """重試預算管理器"""
    
    def __init__(self, ttl: int = 3600, max_ratio: float = 0.1):
        self.ttl = ttl
        self.max_ratio = max_ratio
        self._requests: List[datetime] = []
        self._retries: List[datetime] = []
        self._lock = threading.RLock()
    
    def _cleanup_old_records(self):
        """清理過期記錄"""
        cutoff_time = datetime.now() - timedelta(seconds=self.ttl)
        self._requests = [r for r in self._requests if r > cutoff_time]
        self._retries = [r for r in self._retries if r > cutoff_time]
    
    def can_retry(self) -> bool:
        """檢查是否可以重試"""
        with self._lock:
            self._cleanup_old_records()
            
            if not self._requests:
                return True
            
            retry_ratio = len(self._retries) / len(self._requests)
            return retry_ratio < self.max_ratio
    
    def record_request(self):
        """記錄請求"""
        with self._lock:
            self._requests.append(datetime.now())
    
    def record_retry(self):
        """記錄重試"""
        with self._lock:
            self._retries.append(datetime.now())
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        with self._lock:
            self._cleanup_old_records()
            total_requests = len(self._requests)
            total_retries = len(self._retries)
            retry_ratio = total_retries / total_requests if total_requests > 0 else 0.0
            
            return {
                'total_requests': total_requests,
                'total_retries': total_retries,
                'retry_ratio': retry_ratio,
                'max_ratio': self.max_ratio,
                'can_retry': self.can_retry(),
                'ttl_seconds': self.ttl
            }


class AdvancedRetry:
    """高級重試器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.retry_budget = None
        
        if self.config.retry_budget_enabled:
            self.retry_budget = RetryBudget(
                ttl=self.config.retry_budget_ttl,
                max_ratio=self.config.retry_budget_max_ratio
            )
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """判斷是否應該重試"""
        # 檢查是否超過最大重試次數
        if attempt >= self.config.max_attempts:
            return False
        
        # 檢查是否是停止重試的異常
        if isinstance(exception, self.config.stop_on_exceptions):
            return False
        
        # 檢查是否是可重試的異常
        if not isinstance(exception, self.config.retry_on_exceptions):
            return False
        
        # 檢查重試預算
        if self.retry_budget and not self.retry_budget.can_retry():
            logger.warning("Retry budget exhausted, skipping retry")
            return False
        
        return True
    
    def _calculate_delay(self, attempt: int, last_delay: float = 0) -> float:
        """計算延遲時間"""
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.multiplier ** (attempt - 1))
        
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        
        elif self.config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            if attempt <= 2:
                delay = self.config.base_delay
            else:
                # 簡化的斐波那契計算
                fib_multiplier = self._fibonacci(attempt)
                delay = self.config.base_delay * fib_multiplier
        
        else:  # CUSTOM or fallback
            delay = self.config.base_delay
        
        # 限制最大延遲
        delay = min(delay, self.config.max_delay)
        
        # 應用抖動
        delay = self._apply_jitter(delay, attempt, last_delay)
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """計算斐波那契數"""
        if n <= 1:
            return 1
        elif n == 2:
            return 1
        else:
            a, b = 1, 1
            for _ in range(3, n + 1):
                a, b = b, a + b
            return b
    
    def _apply_jitter(self, delay: float, attempt: int, last_delay: float) -> float:
        """應用抖動"""
        if self.config.jitter_type == JitterType.NONE:
            return delay
        
        elif self.config.jitter_type == JitterType.FULL:
            # 全抖動：0 到 delay 之間的隨機值
            return random.uniform(0, delay)
        
        elif self.config.jitter_type == JitterType.EQUAL:
            # 等抖動：delay/2 到 delay 之間的隨機值
            return random.uniform(delay * 0.5, delay)
        
        elif self.config.jitter_type == JitterType.DECORRELATED:
            # 去相關抖動：基於上次延遲的隨機值
            if last_delay == 0:
                last_delay = self.config.base_delay
            return random.uniform(self.config.base_delay, last_delay * 3)
        
        return delay
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """執行異步函數重試"""
        attempts: List[RetryAttempt] = []
        start_time = time.time()
        last_delay = 0.0
        
        if self.retry_budget:
            self.retry_budget.record_request()
        
        for attempt in range(1, self.config.max_attempts + 1):
            attempt_start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                # 成功執行，返回結果
                total_elapsed = time.time() - start_time
                if attempt > 1:
                    logger.info(f"Function succeeded on attempt {attempt} after {total_elapsed:.2f}s")
                return result
            
            except Exception as e:
                attempt_elapsed = time.time() - attempt_start
                total_elapsed = time.time() - start_time
                
                # 記錄嘗試
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    delay=last_delay,
                    exception=e,
                    timestamp=datetime.now(),
                    total_elapsed=total_elapsed
                )
                attempts.append(retry_attempt)
                
                logger.warning(f"Attempt {attempt} failed after {attempt_elapsed:.2f}s: {e}")
                
                # 檢查是否應該重試
                if not self._should_retry(e, attempt):
                    if self.config.on_giveup:
                        try:
                            self.config.on_giveup(retry_attempt, attempts)
                        except Exception as callback_error:
                            logger.error(f"Error in on_giveup callback: {callback_error}")
                    
                    # 重新拋出最後的異常
                    raise e
                
                # 計算延遲時間
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt, last_delay)
                    last_delay = delay
                    
                    if self.retry_budget:
                        self.retry_budget.record_retry()
                    
                    if self.config.on_retry:
                        try:
                            self.config.on_retry(retry_attempt, delay)
                        except Exception as callback_error:
                            logger.error(f"Error in on_retry callback: {callback_error}")
                    
                    logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_attempts})")
                    await asyncio.sleep(delay)
        
        # 如果到這裡說明所有重試都失敗了，這不應該發生
        # 因為最後一次嘗試的異常應該在上面被重新拋出
        raise RuntimeError("Unexpected end of retry loop")
    
    def execute_sync(self, func: Callable, *args, **kwargs) -> Any:
        """執行同步函數重試"""
        attempts: List[RetryAttempt] = []
        start_time = time.time()
        last_delay = 0.0
        
        if self.retry_budget:
            self.retry_budget.record_request()
        
        for attempt in range(1, self.config.max_attempts + 1):
            attempt_start = time.time()
            
            try:
                result = func(*args, **kwargs)
                # 成功執行，返回結果
                total_elapsed = time.time() - start_time
                if attempt > 1:
                    logger.info(f"Function succeeded on attempt {attempt} after {total_elapsed:.2f}s")
                return result
            
            except Exception as e:
                attempt_elapsed = time.time() - attempt_start
                total_elapsed = time.time() - start_time
                
                # 記錄嘗試
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    delay=last_delay,
                    exception=e,
                    timestamp=datetime.now(),
                    total_elapsed=total_elapsed
                )
                attempts.append(retry_attempt)
                
                logger.warning(f"Attempt {attempt} failed after {attempt_elapsed:.2f}s: {e}")
                
                # 檢查是否應該重試
                if not self._should_retry(e, attempt):
                    if self.config.on_giveup:
                        try:
                            self.config.on_giveup(retry_attempt, attempts)
                        except Exception as callback_error:
                            logger.error(f"Error in on_giveup callback: {callback_error}")
                    
                    # 重新拋出最後的異常
                    raise e
                
                # 計算延遲時間
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt, last_delay)
                    last_delay = delay
                    
                    if self.retry_budget:
                        self.retry_budget.record_retry()
                    
                    if self.config.on_retry:
                        try:
                            self.config.on_retry(retry_attempt, delay)
                        except Exception as callback_error:
                            logger.error(f"Error in on_retry callback: {callback_error}")
                    
                    logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_attempts})")
                    time.sleep(delay)
        
        # 如果到這裡說明所有重試都失敗了，這不應該發生
        raise RuntimeError("Unexpected end of retry loop")
    
    def get_budget_stats(self) -> Optional[Dict[str, Any]]:
        """獲取重試預算統計"""
        if self.retry_budget:
            return self.retry_budget.get_stats()
        return None


# 便捷函數和裝飾器

def retry_async(config: Optional[RetryConfig] = None):
    """異步重試裝飾器"""
    def decorator(func):
        retrier = AdvancedRetry(config)
        
        async def wrapper(*args, **kwargs):
            return await retrier.execute_async(func, *args, **kwargs)
        
        return wrapper
    return decorator


def retry_sync(config: Optional[RetryConfig] = None):
    """同步重試裝飾器"""
    def decorator(func):
        retrier = AdvancedRetry(config)
        
        def wrapper(*args, **kwargs):
            return retrier.execute_sync(func, *args, **kwargs)
        
        return wrapper
    return decorator


# 預設配置
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    multiplier=2.0,
    jitter_type=JitterType.EQUAL,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)

AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=0.5,
    max_delay=30.0,
    multiplier=1.5,
    jitter_type=JitterType.FULL,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)

CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=2.0,
    max_delay=120.0,
    multiplier=3.0,
    jitter_type=JitterType.NONE,
    strategy=RetryStrategy.LINEAR_BACKOFF
)
