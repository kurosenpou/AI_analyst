"""
OpenRouter client service for LLM API calls
Provides unified interface for calling different models through OpenRouter
Enhanced with advanced fault tolerance mechanisms
"""

import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv

from .circuit_breaker import get_circuit_breaker, CircuitBreakerConfig, CircuitBreakerOpenError
from .monitoring import record_metric, trigger_custom_alert, AlertLevel, MetricDecorator
from .advanced_retry import AdvancedRetry, RetryConfig, RetryStrategy, JitterType

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    OpenRouter API client with enhanced fault tolerance mechanisms
    Features: Circuit breaker, advanced retry, monitoring, and fallback
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_fallback_key = os.getenv("OPENAI_API_KEY")
        self.timeout = int(os.getenv("LLM_TIMEOUT", 25))
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))
        self.retry_delay = float(os.getenv("RETRY_DELAY", 0.5))
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        # Initialize OpenRouter client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=self.timeout
        )
        
        # Initialize fallback OpenAI client
        if self.openai_fallback_key:
            self.fallback_client = AsyncOpenAI(
                api_key=self.openai_fallback_key,
                timeout=self.timeout
            )
        else:
            self.fallback_client = None
            logger.warning("No OpenAI fallback key configured")
        
        # Initialize circuit breakers
        self._init_circuit_breakers()
        
        # Initialize retry strategies
        self._init_retry_strategies()
    
    def _init_circuit_breakers(self):
        """初始化斷路器"""
        # OpenRouter 斷路器配置
        openrouter_cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=self.timeout,
            expected_exception=(Exception,)
        )
        self.openrouter_circuit_breaker = get_circuit_breaker("openrouter", openrouter_cb_config)
        
        # OpenAI 斷路器配置
        openai_cb_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30,
            success_threshold=3,
            timeout=self.timeout,
            expected_exception=(Exception,)
        )
        self.openai_circuit_breaker = get_circuit_breaker("openai_fallback", openai_cb_config)
    
    def _init_retry_strategies(self):
        """初始化重試策略"""
        # 主要重試策略（用於OpenRouter）
        self.primary_retry_config = RetryConfig(
            max_attempts=self.max_retries,
            base_delay=self.retry_delay,
            max_delay=30.0,
            multiplier=2.0,
            jitter_type=JitterType.EQUAL,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            retry_budget_enabled=True,
            retry_budget_ttl=3600,
            retry_budget_max_ratio=0.15,
            on_retry=self._on_retry_callback,
            on_giveup=self._on_giveup_callback
        )
        
        # 備用重試策略（用於OpenAI fallback）
        self.fallback_retry_config = RetryConfig(
            max_attempts=2,
            base_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            jitter_type=JitterType.FULL,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            on_retry=self._on_fallback_retry_callback
        )
        
        self.primary_retrier = AdvancedRetry(self.primary_retry_config)
        self.fallback_retrier = AdvancedRetry(self.fallback_retry_config)
    
    def _on_retry_callback(self, retry_attempt, delay):
        """主要重試回調"""
        logger.warning(f"OpenRouter retry attempt {retry_attempt.attempt_number} after {delay:.2f}s delay")
        record_metric("model_retry_attempts", 1, {"provider": "openrouter"})
    
    def _on_giveup_callback(self, retry_attempt, attempts):
        """放棄重試回調"""
        logger.error(f"OpenRouter retries exhausted after {len(attempts)} attempts")
        trigger_custom_alert(
            title="OpenRouter API Failure",
            message=f"All {len(attempts)} retry attempts failed for OpenRouter API",
            level=AlertLevel.ERROR,
            source="openrouter_client",
            metadata={"total_attempts": len(attempts), "last_error": str(retry_attempt.exception)}
        )
    
    def _on_fallback_retry_callback(self, retry_attempt, delay):
        """備用重試回調"""
        logger.warning(f"OpenAI fallback retry attempt {retry_attempt.attempt_number} after {delay:.2f}s delay")
        record_metric("model_retry_attempts", 1, {"provider": "openai"})
    
    @MetricDecorator.time_execution("model_response_time", {"provider": "openrouter"})
    async def _call_openrouter_api(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """調用OpenRouter API（帶斷路器保護）"""
        return await self.openrouter_circuit_breaker.call(
            self._raw_openrouter_call, messages, model, **kwargs
        )
    
    async def _raw_openrouter_call(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """原始OpenRouter API調用"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            **kwargs
        )
        
        # 記錄成功指標
        record_metric("model_requests_total", 1, {"provider": "openrouter", "model": model, "status": "success"})
        if hasattr(response, 'usage') and response.usage:
            record_metric("model_token_usage", response.usage.total_tokens or 0, {"provider": "openrouter", "model": model})
        
        return response.model_dump()
    
    @MetricDecorator.time_execution("model_response_time", {"provider": "openai"})
    async def _call_openai_fallback(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """調用OpenAI備用API（帶斷路器保護）"""
        if not self.fallback_client:
            raise RuntimeError("OpenAI fallback client not configured")
        
        # 將OpenRouter模型映射到OpenAI模型
        openai_model = self._map_to_openai_model(model)
        
        return await self.openai_circuit_breaker.call(
            self._raw_openai_call, messages, openai_model, **kwargs
        )
    
    async def _raw_openai_call(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """原始OpenAI API調用"""
        if not self.fallback_client:
            raise RuntimeError("OpenAI fallback client not configured")
            
        response = await self.fallback_client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            **kwargs
        )
        
        # 記錄成功指標
        record_metric("model_requests_total", 1, {"provider": "openai", "model": model, "status": "success"})
        if hasattr(response, 'usage') and response.usage:
            record_metric("model_token_usage", response.usage.total_tokens or 0, {"provider": "openai", "model": model})
        
        return response.model_dump()
    
    def _map_to_openai_model(self, openrouter_model: str) -> str:
        """將OpenRouter模型映射到OpenAI模型"""
        model_mapping = {
            "openai/gpt-4o": "gpt-4o",
            "openai/gpt-4": "gpt-4",
            "openai/gpt-3.5-turbo": "gpt-3.5-turbo",
            "anthropic/claude-3-5-sonnet-20241022": "gpt-4o",  # 映射到相似的模型
            "google/gemini-pro-1.5": "gpt-4o"  # 映射到相似的模型
        }
        return model_mapping.get(openrouter_model, "gpt-3.5-turbo")
    
    async def chat_completion(
        self, 
        model: str, 
        messages: List[Dict[str, Any]], 
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Send chat completion request with enhanced fault tolerance
        
        Features:
        - Advanced retry strategies with exponential backoff and jitter
        - Circuit breaker protection
        - Automatic fallback to OpenAI
        - Comprehensive monitoring and alerting
        
        Args:
            model: Model identifier (e.g., "anthropic/claude-3-5-sonnet-20241022")
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        start_time = asyncio.get_event_loop().time()
        
        # 記錄請求指標
        record_metric("model_requests_total", 1, {"provider": "openrouter", "model": model, "status": "started"})
        
        try:
            # 首先嘗試OpenRouter API（帶重試和斷路器保護）
            response_data = await self.primary_retrier.execute_async(
                self._call_openrouter_api,
                messages, model, max_tokens=max_tokens, temperature=temperature, **kwargs
            )
            
            # 提取響應內容
            content = self._extract_content_from_response(response_data)
            
            # 記錄成功指標
            elapsed_time = asyncio.get_event_loop().time() - start_time
            record_metric("api_request_duration", elapsed_time, {"provider": "openrouter", "model": model})
            
            return content
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"OpenRouter circuit breaker is open: {e}")
            # 斷路器打開時直接使用備用方案
            return await self._execute_fallback(messages, max_tokens, temperature, **kwargs)
            
        except Exception as e:
            logger.error(f"OpenRouter API failed after all retries: {e}")
            
            # 記錄失敗指標
            record_metric("model_errors_total", 1, {"provider": "openrouter", "model": model})
            
            # 嘗試備用方案
            try:
                return await self._execute_fallback(messages, max_tokens, temperature, **kwargs)
            except Exception as fallback_error:
                # 記錄最終失敗
                elapsed_time = asyncio.get_event_loop().time() - start_time
                record_metric("api_request_duration", elapsed_time, {"provider": "failed", "model": model})
                record_metric("api_errors_total", 1, {"model": model})
                
                # 觸發嚴重報警
                trigger_custom_alert(
                    title="Complete API Failure",
                    message=f"Both OpenRouter and OpenAI fallback failed for model {model}",
                    level=AlertLevel.CRITICAL,
                    source="openrouter_client",
                    metadata={
                        "model": model,
                        "openrouter_error": str(e),
                        "openai_error": str(fallback_error),
                        "elapsed_time": elapsed_time
                    }
                )
                
                raise Exception(f"Complete API failure - OpenRouter: {e}, OpenAI: {fallback_error}")
    
    async def _execute_fallback(self, messages: List[Dict[str, Any]], max_tokens: int, 
                               temperature: float, **kwargs) -> str:
        """執行備用方案（OpenAI API）"""
        if not self.fallback_client:
            raise RuntimeError("No fallback client configured")
        
        logger.info("Attempting OpenAI fallback")
        
        # 使用較為保守的重試策略調用備用API
        response_data = await self.fallback_retrier.execute_async(
            self._call_openai_fallback,
            messages, "gpt-3.5-turbo", max_tokens=max_tokens, temperature=temperature, **kwargs
        )
        
        return self._extract_content_from_response(response_data)
    
    def _extract_content_from_response(self, response_data: Dict[str, Any]) -> str:
        """從響應數據中提取內容"""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        
        # 如果標準格式失敗，嘗試其他可能的格式
        if 'content' in response_data:
            return str(response_data['content'])
        
        raise ValueError(f"Unable to extract content from response: {response_data}")
    
    async def _call_openrouter(
        self, 
        model: str, 
        messages: List[Dict[str, Any]], 
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Call OpenRouter API (legacy method - deprecated)"""
        logger.warning("Using deprecated _call_openrouter method")
        response_data = await self._call_openrouter_api(messages, model, max_tokens=max_tokens, temperature=temperature, **kwargs)
        return self._extract_content_from_response(response_data)
    
    async def test_connection(self) -> Dict[str, bool]:
        """Test connectivity to OpenRouter and fallback services with circuit breaker status"""
        
        results = {
            "openrouter": False,
            "openai_fallback": False,
            "openrouter_circuit_breaker": self.openrouter_circuit_breaker.get_status(),
            "openai_circuit_breaker": self.openai_circuit_breaker.get_status()
        }
        
        test_messages = [{"role": "user", "content": "Hello, respond with 'OK'"}]
        
        # Test OpenRouter
        try:
            await self._call_openrouter_api(
                test_messages,
                "openai/gpt-3.5-turbo", 
                max_tokens=10, 
                temperature=0.1
            )
            results["openrouter"] = True
            logger.info("OpenRouter connection test successful")
        except Exception as e:
            logger.error(f"OpenRouter test failed: {e}")
            record_metric("model_errors_total", 1, {"provider": "openrouter", "test": "connection"})
        
        # Test fallback
        if self.fallback_client:
            try:
                await self._call_openai_fallback(
                    test_messages,
                    "gpt-3.5-turbo",
                    max_tokens=10, 
                    temperature=0.1
                )
                results["openai_fallback"] = True
                logger.info("OpenAI fallback connection test successful")
            except Exception as e:
                logger.error(f"OpenAI fallback test failed: {e}")
                record_metric("model_errors_total", 1, {"provider": "openai", "test": "connection"})
        
        return results
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """獲取所有斷路器狀態"""
        return {
            "openrouter": self.openrouter_circuit_breaker.get_status(),
            "openai_fallback": self.openai_circuit_breaker.get_status()
        }
    
    def reset_circuit_breakers(self):
        """重置所有斷路器"""
        self.openrouter_circuit_breaker.reset()
        self.openai_circuit_breaker.reset()
        logger.info("All circuit breakers have been reset")
    
    def get_retry_budget_stats(self) -> Dict[str, Any]:
        """獲取重試預算統計"""
        return {
            "primary": self.primary_retrier.get_budget_stats(),
            "fallback": self.fallback_retrier.get_budget_stats()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """全面健康檢查"""
        start_time = asyncio.get_event_loop().time()
        
        # 基本連接測試
        connection_results = await self.test_connection()
        
        # 斷路器狀態
        circuit_breaker_status = self.get_circuit_breaker_status()
        
        # 重試預算狀態
        retry_budget_stats = self.get_retry_budget_stats()
        
        # 計算健康分數
        health_score = 0
        total_checks = 2  # openrouter + fallback
        
        if connection_results.get("openrouter", False):
            health_score += 1
        if connection_results.get("openai_fallback", False):
            health_score += 1
        
        health_percentage = (health_score / total_checks) * 100
        
        elapsed_time = asyncio.get_event_loop().time() - start_time
        
        health_status = {
            "healthy": health_score > 0,  # 至少一個服務可用
            "overall_health": "healthy" if health_score > 0 else "unhealthy",  # 添加這個欄位
            "health_score": health_score,
            "health_percentage": health_percentage,
            "check_duration_seconds": elapsed_time,
            "timestamp": asyncio.get_event_loop().time(),
            "connections": connection_results,
            "circuit_breakers": circuit_breaker_status,
            "retry_budgets": retry_budget_stats,
            "details": {
                "primary_service": "openrouter",
                "fallback_service": "openai",
                "fault_tolerance_enabled": True,
                "monitoring_enabled": True
            }
        }
        
        # 記錄健康檢查指標
        record_metric("system_health_check", health_percentage, {"component": "openrouter_client"})
        
        return health_status

# Global client instance
openrouter_client = None

def get_openrouter_client() -> OpenRouterClient:
    """Get or create global OpenRouter client instance"""
    global openrouter_client
    if openrouter_client is None:
        openrouter_client = OpenRouterClient()
    return openrouter_client
