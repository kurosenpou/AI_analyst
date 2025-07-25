"""
Test script for enhanced fault tolerance mechanisms
測試增強的容錯機制功能
"""

import asyncio
import time
import json
from services.openrouter_client import get_openrouter_client
from services.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from services.monitoring import get_monitoring_system, record_metric
from services.advanced_retry import AdvancedRetry, RetryConfig, RetryStrategy

async def test_fault_tolerance():
    """測試容錯機制功能"""
    
    print("=== Enhanced Fault Tolerance Test ===\n")
    
    # 1. 測試OpenRouter客戶端健康檢查
    print("1. Testing OpenRouter Client Health Check...")
    client = get_openrouter_client()
    health_status = await client.health_check()
    print(f"Health Status: {health_status['overall_health']}")
    print(f"Health Score: {health_status['health_score']:.2f}")
    print(f"Check Duration: {health_status['check_duration_seconds']:.2f}s\n")
    
    # 2. 測試斷路器狀態
    print("2. Testing Circuit Breaker Status...")
    cb_status = client.get_circuit_breaker_status()
    for name, status in cb_status.items():
        print(f"  {name}: {status['state']} (failures: {status['stats']['consecutive_failures']})")
    print()
    
    # 3. 測試正常API調用
    print("3. Testing Normal API Call...")
    try:
        start_time = time.time()
        response = await client.chat_completion(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Test successful' in Chinese"}],
            max_tokens=50,
            temperature=0.1
        )
        elapsed_time = time.time() - start_time
        print(f"Response: {response}")
        print(f"Response time: {elapsed_time:.2f}s\n")
    except Exception as e:
        print(f"API call failed: {e}\n")
    
    # 4. 測試監控系統指標
    print("4. Testing Monitoring System...")
    monitoring = get_monitoring_system()
    metrics_summary = monitoring.get_metrics_summary()
    
    print("Key Metrics:")
    for metric_name in ["api_requests_total", "model_requests_total", "api_request_duration"]:
        if metric_name in metrics_summary:
            metric = metrics_summary[metric_name]
            print(f"  {metric_name}: {metric['latest_value']} (avg 5m: {metric['average_5m']})")
    print()
    
    # 5. 測試報警系統
    print("5. Testing Alert System...")
    alerts = monitoring.get_alerts(limit=5)
    print(f"Total alerts: {len(alerts)}")
    for alert in alerts[:3]:  # 顯示最近3個報警
        print(f"  - {alert.level.value.upper()}: {alert.title} ({alert.timestamp.strftime('%H:%M:%S')})")
    print()
    
    # 6. 測試重試預算
    print("6. Testing Retry Budget...")
    retry_stats = client.get_retry_budget_stats()
    if retry_stats:
        for budget_type, stats in retry_stats.items():
            if stats:
                print(f"  {budget_type}: {stats['total_retries']}/{stats['total_requests']} retries ({stats['retry_ratio']:.2%})")
    print()
    
    # 7. 測試手動觸發斷路器
    print("7. Testing Circuit Breaker Trigger...")
    
    # 獲取測試用的斷路器
    test_cb_config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=5,
        expected_exception=(ValueError,)
    )
    test_cb = get_circuit_breaker("test_circuit_breaker", test_cb_config)
    
    # 觸發一些失敗
    async def failing_function():
        raise ValueError("Intentional test failure")
    
    for i in range(3):
        try:
            await test_cb.call(failing_function)
        except Exception as e:
            print(f"  Attempt {i+1}: {e}")
    
    # 檢查斷路器狀態
    test_status = test_cb.get_status()
    print(f"  Test circuit breaker state: {test_status['state']}")
    print(f"  Consecutive failures: {test_status['stats']['consecutive_failures']}\n")
    
    # 8. 測試重試機制
    print("8. Testing Advanced Retry Mechanism...")
    
    retry_config = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        multiplier=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF
    )
    retrier = AdvancedRetry(retry_config)
    
    # 測試會成功的函數（第2次嘗試）
    attempt_count = 0
    async def sometimes_failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ConnectionError(f"Temporary failure {attempt_count}")
        return f"Success on attempt {attempt_count}"
    
    try:
        result = await retrier.execute_async(sometimes_failing_function)
        print(f"  Retry result: {result}")
    except Exception as e:
        print(f"  Retry failed: {e}")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_fault_tolerance())
