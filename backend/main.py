"""
FastAPI main application entry point
Enhanced with fault tolerance monitoring and advanced error handling
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager

from routers import fault_tolerance, debate, generate, upload, model_management
from services.monitoring import get_monitoring_system, record_metric, trigger_custom_alert, AlertLevel
from database.config import init_database, close_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Business Agent MVP with fault tolerance")
    
    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        trigger_custom_alert(
            title="Database Initialization Failed",
            message=f"Failed to initialize SQLite database: {str(e)}",
            level=AlertLevel.ERROR,
            source="startup"
        )
        raise
    
    # Initialize monitoring system (already initialized globally)
    monitoring = get_monitoring_system()
    logger.info("Monitoring system initialized")
    
    # Test initial connectivity
    try:
        from services.openrouter_client import get_openrouter_client
        client = get_openrouter_client()
        health_status = await client.health_check()
        logger.info(f"Initial health check completed: {health_status['overall_health']}")
    except Exception as e:
        logger.error(f"Initial health check failed: {e}")
        trigger_custom_alert(
            title="Startup Health Check Failed",
            message=f"Initial system health check failed: {str(e)}",
            level=AlertLevel.WARNING,
            source="startup"
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Business Agent MVP")
    
    # Close database connections
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    monitoring.shutdown()


app = FastAPI(
    title="AI Business Agent MVP",
    description="Generate business reports using AI with advanced fault tolerance",
    version="1.0.0",
    lifespan=lifespan
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域異常處理器"""
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    
    # 記錄錯誤指標
    record_metric("api_errors_total", 1, {
        "endpoint": str(request.url.path),
        "method": request.method,
        "error_type": type(exc).__name__
    })
    
    # 觸發報警（如果是嚴重錯誤）
    if not isinstance(exc, (ValueError, KeyError)):
        trigger_custom_alert(
            title="Unhandled API Exception",
            message=f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            level=AlertLevel.ERROR,
            source="api_exception_handler",
            metadata={
                "endpoint": str(request.url.path),
                "method": request.method,
                "error_type": type(exc).__name__
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "type": type(exc).__name__
        }
    )

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request/response monitoring
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """監控中間件"""
    import time
    
    start_time = time.time()
    
    # 記錄請求開始
    record_metric("api_requests_total", 1, {
        "endpoint": request.url.path,
        "method": request.method
    })
    
    try:
        response = await call_next(request)
        
        # 記錄響應時間
        elapsed_time = time.time() - start_time
        record_metric("api_request_duration", elapsed_time, {
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": str(response.status_code)
        })
        
        return response
        
    except Exception as e:
        # 記錄異常
        elapsed_time = time.time() - start_time
        record_metric("api_request_duration", elapsed_time, {
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": "500"
        })
        raise

# Include API routers
app.include_router(fault_tolerance.router, prefix="/api/fault-tolerance", tags=["fault_tolerance"])
app.include_router(debate.router, prefix="/api/debate", tags=["debate"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(model_management.router, prefix="/api/models", tags=["models"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Business Agent MVP API is running",
        "version": "1.0.0",
        "features": [
            "multi_model_debate",
            "openrouter_integration", 
            "fault_tolerance",
            "circuit_breakers",
            "advanced_retry",
            "monitoring_alerts"
        ]
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with fault tolerance status"""
    from services.openrouter_client import get_openrouter_client
    from services.monitoring import get_monitoring_system
    from services.circuit_breaker import circuit_breaker_manager
    
    # Record health check metric
    record_metric("api_requests_total", 1, {"endpoint": "/health", "method": "GET"})
    
    health_data = {
        "status": "unknown",
        "timestamp": "unknown",
        "version": "1.0.0",
        "configuration": {
            "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "fault_tolerance_enabled": True
        },
        "services": {},
        "fault_tolerance": {}
    }
    
    try:
        # OpenRouter service health
        client = get_openrouter_client()
        openrouter_health = await client.health_check()
        health_data["services"]["openrouter"] = openrouter_health
        
        # Circuit breaker status
        circuit_breakers = circuit_breaker_manager.get_all_status()
        health_data["fault_tolerance"]["circuit_breakers"] = circuit_breakers
        
        # Monitoring system status
        monitoring = get_monitoring_system()
        active_alerts = monitoring.get_alerts(resolved=False, limit=10)
        health_data["fault_tolerance"]["monitoring"] = {
            "active": True,
            "active_alerts_count": len(active_alerts),
            "metrics_count": len(monitoring.metrics)
        }
        
        # Determine overall status
        openrouter_healthy = openrouter_health.get("healthy", False)
        critical_alerts = len([a for a in active_alerts if a.level.value == "critical"])
        
        if openrouter_healthy and critical_alerts == 0:
            health_data["status"] = "healthy"
        elif openrouter_healthy or critical_alerts < 3:
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "unhealthy"
        
        health_data["timestamp"] = openrouter_health.get("timestamp", "unknown")
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_data.update({
            "status": "unhealthy",
            "error": str(e),
            "services": {"openrouter": {"healthy": False, "error": str(e)}}
        })
        
        # Record health check failure
        record_metric("api_errors_total", 1, {"endpoint": "/health", "method": "GET"})
        
        return health_data

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", 8000))
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
