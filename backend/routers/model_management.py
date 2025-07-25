"""
Model Management API Router
Provides endpoints for managing models and debate sessions
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from services.model_pool import get_model_pool, ModelRole
from services.prompt_templates import get_prompt_manager

router = APIRouter()

# ============== Request/Response Models ==============

class ModelAssignmentRequest(BaseModel):
    strategy: str = "default"  # default, random, optimal, cost_aware
    exclude_models: Optional[List[str]] = None

class DebateSessionRequest(BaseModel):
    topic: str
    business_data: str
    context: Optional[str] = ""
    assignment_strategy: str = "default"

class DebateSessionResponse(BaseModel):
    session_id: str
    topic: str
    participants: Dict[str, str]
    created_at: str
    estimated_cost: Dict[str, float]

class ModelHealthResponse(BaseModel):
    models: Dict[str, bool]
    all_healthy: bool
    total_models: int

class PromptTemplateResponse(BaseModel):
    template_id: str
    role: str
    prompt_type: str
    variables: List[str]
    description: str

# ============== Model Management Endpoints ==============

@router.get("/models", summary="獲取所有可用模型")
async def get_available_models():
    """獲取所有可用的AI模型信息"""
    pool = get_model_pool()
    models = pool.get_available_models()
    
    result = {}
    for key, model in models.items():
        result[key] = {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "max_tokens": model.max_tokens,
            "temperature": model.temperature,
            "strengths": model.strengths,
            "cost_per_token": model.cost_per_token
        }
    
    return {
        "success": True,
        "total_models": len(result),
        "models": result
    }

@router.post("/models/assign", summary="分配模型到辯論角色")
async def assign_models(request: ModelAssignmentRequest):
    """為辯論分配模型到不同角色"""
    pool = get_model_pool()
    
    try:
        assignments = pool.assign_models_to_roles(
            strategy=request.strategy,
            exclude_models=request.exclude_models
        )
        
        # 估算成本
        costs = pool.estimate_cost(assignments)
        
        result = {}
        for role, model in assignments.items():
            result[role.value] = {
                "model_id": model.id,
                "model_name": model.name,
                "provider": model.provider
            }
        
        return {
            "success": True,
            "strategy": request.strategy,
            "assignments": result,
            "estimated_cost": costs
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/models/rotate", summary="輪換模型角色")
async def rotate_model_assignments(current_assignments: Dict[str, str]):
    """
    輪換當前的模型角色分配
    current_assignments: {"debater_a": "model_id", "debater_b": "model_id", "judge": "model_id"}
    """
    pool = get_model_pool()
    
    try:
        # 轉換輸入格式
        assignments = {}
        for role_str, model_id in current_assignments.items():
            role = ModelRole(role_str)
            model = pool.get_model_by_id(model_id)
            if not model:
                raise ValueError(f"模型未找到: {model_id}")
            assignments[role] = model
        
        # 執行輪換
        rotated = pool.rotate_models(assignments)
        
        result = {}
        for role, model in rotated.items():
            result[role.value] = {
                "model_id": model.id,
                "model_name": model.name,
                "provider": model.provider
            }
        
        return {
            "success": True,
            "rotated_assignments": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/models/health", response_model=ModelHealthResponse, summary="檢查模型健康狀態")
async def check_model_health():
    """檢查所有模型的健康狀態"""
    pool = get_model_pool()
    
    try:
        health_results = await pool.test_model_health()
        all_healthy = all(health_results.values())
        
        return ModelHealthResponse(
            models=health_results,
            all_healthy=all_healthy,
            total_models=len(health_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")

# ============== Debate Session Endpoints ==============

@router.post("/debate/create", response_model=DebateSessionResponse, summary="創建辯論會話")
async def create_debate_session(request: DebateSessionRequest):
    """創建新的辯論會話"""
    pool = get_model_pool()
    
    try:
        # 分配模型
        assignments = pool.assign_models_to_roles(strategy=request.assignment_strategy)
        
        # 創建會話
        session = pool.create_debate_session(
            topic=request.topic,
            model_assignments=assignments
        )
        
        # 估算成本
        costs = pool.estimate_cost(assignments)
        
        return DebateSessionResponse(
            session_id=session.session_id,
            topic=session.topic,
            participants={role.value: model_id for role, model_id in session.participants.items()},
            created_at=session.created_at,
            estimated_cost=costs
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/debate/{session_id}", summary="獲取辯論會話信息")
async def get_debate_session(session_id: str):
    """獲取指定的辯論會話信息"""
    pool = get_model_pool()
    
    session = pool.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="辯論會話未找到")
    
    return {
        "success": True,
        "session": {
            "session_id": session.session_id,
            "topic": session.topic,
            "round_number": session.round_number,
            "participants": {role.value: model_id for role, model_id in session.participants.items()},
            "history": session.history,
            "created_at": session.created_at
        }
    }

@router.get("/debate", summary="獲取所有活躍的辯論會話")
async def list_debate_sessions():
    """獲取所有活躍的辯論會話"""
    pool = get_model_pool()
    
    sessions = []
    for session_id, session in pool.active_sessions.items():
        sessions.append({
            "session_id": session.session_id,
            "topic": session.topic,
            "round_number": session.round_number,
            "participants": {role.value: model_id for role, model_id in session.participants.items()},
            "created_at": session.created_at
        })
    
    return {
        "success": True,
        "total_sessions": len(sessions),
        "sessions": sessions
    }

# ============== Prompt Template Endpoints ==============

@router.get("/templates", summary="獲取所有Prompt模板")
async def get_prompt_templates():
    """獲取所有可用的prompt模板"""
    manager = get_prompt_manager()
    templates = manager.list_all_templates()
    
    return {
        "success": True,
        "total_templates": len(templates),
        "templates": templates
    }

@router.get("/templates/{template_id}", summary="獲取特定模板")
async def get_template(template_id: str):
    """獲取指定的prompt模板"""
    manager = get_prompt_manager()
    template = manager.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板未找到")
    
    return {
        "success": True,
        "template": {
            "template_id": template.template_id,
            "role": template.role.value,
            "prompt_type": template.prompt_type.value,
            "template": template.template,
            "variables": template.variables,
            "description": template.description
        }
    }

@router.post("/templates/{template_id}/render", summary="渲染模板")
async def render_template(template_id: str, variables: Dict[str, Any]):
    """渲染指定的prompt模板"""
    manager = get_prompt_manager()
    
    try:
        # 驗證變數
        missing = manager.validate_template_variables(template_id, variables)
        if missing:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必需的變數: {missing}"
            )
        
        # 渲染模板
        rendered = manager.render_template(template_id, **variables)
        
        return {
            "success": True,
            "template_id": template_id,
            "rendered_prompt": rendered,
            "character_count": len(rendered)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失敗: {str(e)}")

# ============== Utility Endpoints ==============

@router.get("/cost/estimate", summary="估算辯論成本")
async def estimate_debate_cost(
    strategy: str = "default",
    tokens_per_model: int = 1000
):
    """估算使用指定策略進行辯論的成本"""
    pool = get_model_pool()
    
    try:
        assignments = pool.assign_models_to_roles(strategy=strategy)
        costs = pool.estimate_cost(assignments, tokens_per_model)
        
        return {
            "success": True,
            "strategy": strategy,
            "tokens_per_model": tokens_per_model,
            "cost_breakdown": costs
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
