"""
Fault Tolerance Monitoring API Router
提供容錯機制的監控、管理和報警API端點
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from services.circuit_breaker import circuit_breaker_manager
from services.monitoring import get_monitoring_system, AlertLevel
from services.openrouter_client import get_openrouter_client

router = APIRouter()

# ============== Response Models ==============

class CircuitBreakerStatusResponse(BaseModel):
    success: bool
    circuit_breakers: Dict[str, Dict[str, Any]]

class MonitoringStatusResponse(BaseModel):
    success: bool
    metrics_summary: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
    system_health: Dict[str, Any]

class AlertResponse(BaseModel):
    success: bool
    alerts: List[Dict[str, Any]]
    total_count: int

class HealthCheckResponse(BaseModel):
    success: bool
    overall_health: str  # "healthy", "degraded", "unhealthy"
    health_score: float
    components: Dict[str, Any]
    timestamp: datetime

class SystemStatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]

# ============== Circuit Breaker Endpoints ==============

@router.get("/circuit-breakers", response_model=CircuitBreakerStatusResponse, 
            summary="獲取所有斷路器狀態")
async def get_circuit_breakers_status():
    """獲取系統中所有斷路器的狀態"""
    try:
        circuit_breakers = circuit_breaker_manager.get_all_status()
        return CircuitBreakerStatusResponse(
            success=True,
            circuit_breakers=circuit_breakers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get circuit breaker status: {str(e)}")

@router.post("/circuit-breakers/{breaker_name}/reset", 
             summary="重置指定斷路器")
async def reset_circuit_breaker(breaker_name: str):
    """重置指定的斷路器狀態"""
    try:
        circuit_breaker_manager.reset_breaker(breaker_name)
        return {"success": True, "message": f"Circuit breaker '{breaker_name}' has been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {str(e)}")

@router.post("/circuit-breakers/reset-all", 
             summary="重置所有斷路器")
async def reset_all_circuit_breakers():
    """重置系統中所有斷路器的狀態"""
    try:
        circuit_breaker_manager.reset_all()
        return {"success": True, "message": "All circuit breakers have been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset all circuit breakers: {str(e)}")

# ============== Monitoring Endpoints ==============

@router.get("/monitoring/status", response_model=MonitoringStatusResponse,
            summary="獲取監控系統狀態")
async def get_monitoring_status():
    """獲取監控系統的整體狀態"""
    try:
        monitoring = get_monitoring_system()
        
        # 獲取指標摘要
        metrics_summary = monitoring.get_metrics_summary()
        
        # 獲取活躍報警
        active_alerts = [
            {
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            for alert in monitoring.get_alerts(resolved=False, limit=50)
        ]
        
        # 系統健康狀態
        openrouter_client = get_openrouter_client()
        system_health = await openrouter_client.health_check()
        
        return MonitoringStatusResponse(
            success=True,
            metrics_summary=metrics_summary,
            active_alerts=active_alerts,
            system_health=system_health
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")

@router.get("/monitoring/alerts", response_model=AlertResponse,
            summary="獲取報警列表")
async def get_alerts(
    level: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100
):
    """獲取系統報警列表"""
    try:
        monitoring = get_monitoring_system()
        
        alert_level = None
        if level:
            try:
                alert_level = AlertLevel(level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid alert level: {level}")
        
        alerts = monitoring.get_alerts(level=alert_level, resolved=resolved, limit=limit)
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": alert.metadata
            })
        
        return AlertResponse(
            success=True,
            alerts=alert_data,
            total_count=len(alert_data)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/monitoring/alerts/{alert_id}/resolve",
             summary="解決報警")
async def resolve_alert(alert_id: str):
    """標記指定報警為已解決"""
    try:
        monitoring = get_monitoring_system()
        monitoring.resolve_alert(alert_id)
        return {"success": True, "message": f"Alert {alert_id} has been resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

# ============== Health Check Endpoints ==============

@router.get("/health", response_model=HealthCheckResponse,
            summary="系統健康檢查")
async def system_health_check():
    """執行全面的系統健康檢查"""
    try:
        openrouter_client = get_openrouter_client()
        monitoring = get_monitoring_system()
        
        # 獲取各組件健康狀態
        openrouter_health = await openrouter_client.health_check()
        circuit_breakers = circuit_breaker_manager.get_all_status()
        
        # 計算整體健康狀態
        components = {
            "openrouter_client": openrouter_health,
            "circuit_breakers": circuit_breakers,
            "monitoring_system": {
                "active": True,
                "metrics_count": len(monitoring.metrics),
                "active_alerts_count": len(monitoring.get_alerts(resolved=False))
            }
        }
        
        # 計算健康分數
        health_score = openrouter_health.get("health_percentage", 0) / 100.0
        
        # 確定整體健康狀態
        if health_score >= 0.8:
            overall_health = "healthy"
        elif health_score >= 0.5:
            overall_health = "degraded"
        else:
            overall_health = "unhealthy"
        
        return HealthCheckResponse(
            success=True,
            overall_health=overall_health,
            health_score=health_score,
            components=components,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/health/openrouter", 
            summary="OpenRouter客戶端健康檢查")
async def openrouter_health_check():
    """檢查OpenRouter客戶端的健康狀態"""
    try:
        openrouter_client = get_openrouter_client()
        health_status = await openrouter_client.health_check()
        return {"success": True, **health_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter health check failed: {str(e)}")

# ============== System Statistics Endpoints ==============

@router.get("/stats", response_model=SystemStatsResponse,
            summary="獲取系統統計信息")
async def get_system_stats():
    """獲取系統運行統計信息"""
    try:
        monitoring = get_monitoring_system()
        openrouter_client = get_openrouter_client()
        
        # 獲取指標統計
        metrics_summary = monitoring.get_metrics_summary()
        
        # 獲取報警統計
        all_alerts = monitoring.get_alerts(limit=1000)
        alert_stats = {
            "total": len(all_alerts),
            "resolved": len([a for a in all_alerts if a.resolved]),
            "unresolved": len([a for a in all_alerts if not a.resolved]),
            "by_level": {}
        }
        
        for level in AlertLevel:
            alert_stats["by_level"][level.value] = len([
                a for a in all_alerts if a.level == level
            ])
        
        # 獲取斷路器統計
        circuit_breakers = circuit_breaker_manager.get_all_status()
        cb_stats = {
            "total": len(circuit_breakers),
            "closed": len([cb for cb in circuit_breakers.values() if cb["state"] == "closed"]),
            "open": len([cb for cb in circuit_breakers.values() if cb["state"] == "open"]),
            "half_open": len([cb for cb in circuit_breakers.values() if cb["state"] == "half_open"])
        }
        
        # 獲取重試預算統計
        retry_stats = openrouter_client.get_retry_budget_stats()
        
        stats = {
            "uptime": datetime.now().isoformat(),
            "metrics": {
                "total_metrics": len(metrics_summary),
                "metrics_with_data": len([m for m in metrics_summary.values() if m["latest_value"] is not None])
            },
            "alerts": alert_stats,
            "circuit_breakers": cb_stats,
            "retry_budgets": retry_stats,
            "fault_tolerance": {
                "enabled": True,
                "features": [
                    "circuit_breaker",
                    "advanced_retry",
                    "monitoring",
                    "automatic_fallback"
                ]
            }
        }
        
        return SystemStatsResponse(success=True, stats=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

# ============== Administrative Endpoints ==============

@router.post("/admin/reset-all", 
             summary="重置所有容錯組件")
async def reset_all_fault_tolerance():
    """重置所有容錯相關組件（管理員功能）"""
    try:
        # 重置斷路器
        circuit_breaker_manager.reset_all()
        
        # 重置OpenRouter客戶端的斷路器
        openrouter_client = get_openrouter_client()
        openrouter_client.reset_circuit_breakers()
        
        return {
            "success": True,
            "message": "All fault tolerance components have been reset",
            "components_reset": [
                "circuit_breakers",
                "openrouter_client_circuit_breakers"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset fault tolerance components: {str(e)}")

@router.get("/admin/diagnostic", 
            summary="系統診斷信息")
async def get_diagnostic_info():
    """獲取詳細的系統診斷信息（管理員功能）"""
    try:
        monitoring = get_monitoring_system()
        openrouter_client = get_openrouter_client()
        
        diagnostic = {
            "timestamp": datetime.now().isoformat(),
            "system_health": await openrouter_client.health_check(),
            "circuit_breakers": circuit_breaker_manager.get_all_status(),
            "retry_budgets": openrouter_client.get_retry_budget_stats(),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in monitoring.get_alerts(limit=20)
            ],
            "metrics_summary": monitoring.get_metrics_summary()
        }
        
        return {"success": True, "diagnostic": diagnostic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get diagnostic info: {str(e)}")
