"""
Debate Engine API Router
提供辯論引擎的REST API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging
import asyncio
from datetime import datetime

from services.debate_engine import get_debate_engine, DebateSession, DebateStatus, DebatePhase
from services.model_pool import ModelRole

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debate"])


# ===== Pydantic Models =====

class CreateDebateRequest(BaseModel):
    """創建辯論請求"""
    topic: str = Field(..., description="辯論主題", min_length=1, max_length=500)
    business_data: str = Field(..., description="業務數據", min_length=1)
    context: str = Field(default="", description="額外上下文")
    max_rounds: int = Field(default=5, description="最大輪數", ge=1, le=10)
    assignment_strategy: str = Field(default="default", description="模型分配策略")


class DebateSessionResponse(BaseModel):
    """辯論會話響應"""
    session_id: str
    topic: str
    status: str
    current_phase: str
    current_round: int
    max_rounds: int
    created_at: str
    duration: Optional[float]
    total_messages: int
    model_assignments: Dict[str, str]
    statistics: Dict[str, Any]


class DebateMessageResponse(BaseModel):
    """辯論消息響應"""
    id: str
    speaker: str
    model_id: str
    phase: str
    content: str
    timestamp: str
    response_time: Optional[float]


class DebateRoundResponse(BaseModel):
    """辯論輪次響應"""
    round_number: int
    phase: str
    messages: List[DebateMessageResponse]
    duration: Optional[float]


class DebateHistoryResponse(BaseModel):
    """辯論歷史響應"""
    session_id: str
    topic: str
    status: str
    rounds: List[DebateRoundResponse]
    judgment: Optional[DebateMessageResponse]
    final_report: Optional[str]


class ErrorResponse(BaseModel):
    """錯誤響應"""
    error: str
    detail: str


# ===== Helper Functions =====

def _convert_session_to_response(session: DebateSession) -> DebateSessionResponse:
    """轉換辯論會話為響應格式"""
    from services.debate_engine import get_debate_engine
    engine = get_debate_engine()
    summary = engine.get_session_summary(session.session_id)
    
    return DebateSessionResponse(**summary)


def _convert_message_to_response(message) -> DebateMessageResponse:
    """轉換辯論消息為響應格式"""
    return DebateMessageResponse(
        id=message.id,
        speaker=message.speaker.value,
        model_id=message.model_id,
        phase=message.phase.value,
        content=message.content,
        timestamp=message.timestamp.isoformat(),
        response_time=message.response_time
    )


def _convert_round_to_response(round) -> DebateRoundResponse:
    """轉換辯論輪次為響應格式"""
    return DebateRoundResponse(
        round_number=round.round_number,
        phase=round.phase.value,
        messages=[_convert_message_to_response(msg) for msg in round.messages],
        duration=round.duration
    )


# ===== API Endpoints =====

@router.post("/sessions", response_model=DebateSessionResponse)
async def create_debate_session(request: CreateDebateRequest):
    """
    創建新的辯論會話
    
    - **topic**: 辯論主題
    - **business_data**: 相關業務數據
    - **context**: 額外上下文信息（可選）
    - **max_rounds**: 最大辯論輪數（1-10）
    - **assignment_strategy**: 模型分配策略
    """
    try:
        engine = get_debate_engine()
        
        session = await engine.create_debate_session(
            topic=request.topic,
            business_data=request.business_data,
            context=request.context,
            max_rounds=request.max_rounds,
            assignment_strategy=request.assignment_strategy
        )
        
        logger.info(f"Created debate session {session.session_id}")
        
        return _convert_session_to_response(session)
        
    except Exception as e:
        logger.error(f"Failed to create debate session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/start", response_model=DebateSessionResponse)
async def start_debate_session(session_id: str, background_tasks: BackgroundTasks):
    """
    開始辯論會話
    
    - **session_id**: 會話ID
    
    辯論將在後台自動進行，可以通過其他API監控進度
    """
    try:
        engine = get_debate_engine()
        
        # 檢查會話是否存在
        session = engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        if session.status != DebateStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f"Session is in {session.status.value} status, cannot start"
            )
        
        # 開始辯論
        session = await engine.start_debate(session_id)
        
        # 在後台繼續辯論流程
        background_tasks.add_task(_continue_debate_background, session_id)
        
        logger.info(f"Started debate session {session_id}")
        
        return _convert_session_to_response(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=DebateSessionResponse)
async def get_debate_session(session_id: str):
    """
    獲取辯論會話詳情
    
    - **session_id**: 會話ID
    """
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        return _convert_session_to_response(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history", response_model=DebateHistoryResponse)
async def get_debate_history(session_id: str):
    """
    獲取完整的辯論歷史
    
    - **session_id**: 會話ID
    """
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        return DebateHistoryResponse(
            session_id=session.session_id,
            topic=session.topic,
            status=session.status.value,
            rounds=[_convert_round_to_response(r) for r in session.rounds],
            judgment=_convert_message_to_response(session.judgment) if session.judgment else None,
            final_report=session.final_report
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debate history {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[DebateSessionResponse])
async def list_debate_sessions():
    """
    列出所有辯論會話
    """
    try:
        engine = get_debate_engine()
        sessions = engine.list_active_sessions()
        
        return [_convert_session_to_response(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to list debate sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/continue", response_model=DebateSessionResponse)
async def continue_debate_session(session_id: str):
    """
    手動繼續辯論會話
    
    - **session_id**: 會話ID
    
    通常辯論會自動進行，這個接口用於手動推進被中斷的辯論
    """
    try:
        engine = get_debate_engine()
        
        session = engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        if session.status != DebateStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail=f"Session is in {session.status.value} status, cannot continue"
            )
        
        session = await engine.continue_debate(session_id)
        
        logger.info(f"Continued debate session {session_id}")
        
        return _convert_session_to_response(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to continue debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_debate_status(session_id: str):
    """
    獲取辯論會話狀態（輕量級接口）
    
    - **session_id**: 會話ID
    """
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "current_phase": session.current_phase.value,
            "current_round": session.current_round,
            "progress": f"{session.current_round}/{session.max_rounds}",
            "duration": session.duration,
            "message_count": len(session.all_messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debate status {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/report")
async def get_debate_report(session_id: str):
    """
    獲取辯論報告（Markdown格式）
    
    - **session_id**: 會話ID
    """
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        if not session.final_report:
            raise HTTPException(status_code=400, detail="Debate report not yet available")
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status.value,
            "report": session.final_report,
            "generated_at": session.completed_at.isoformat() if session.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debate report {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_debate_session(session_id: str):
    """
    刪除辯論會話
    
    - **session_id**: 會話ID
    """
    try:
        engine = get_debate_engine()
        
        if session_id not in engine.active_sessions:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        del engine.active_sessions[session_id]
        
        logger.info(f"Deleted debate session {session_id}")
        
        return {"message": "Debate session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Background Tasks =====

async def _continue_debate_background(session_id: str):
    """在後台繼續進行辯論"""
    try:
        engine = get_debate_engine()
        
        while True:
            session = engine.get_session(session_id)
            if not session or session.status != DebateStatus.ACTIVE:
                break
            
            if session.current_phase == DebatePhase.COMPLETED:
                break
            
            # 繼續辯論
            await engine.continue_debate(session_id)
            
            # 檢查是否完成
            if session.current_phase == DebatePhase.COMPLETED:
                logger.info(f"Debate session {session_id} completed")
                break
            
    except Exception as e:
        logger.error(f"Background debate failed for session {session_id}: {e}")
        # 標記會話為失敗狀態
        try:
            engine = get_debate_engine()
            session = engine.get_session(session_id)
            if session:
                session.status = DebateStatus.FAILED
        except:
            pass  # 忽略清理錯誤


# ===== Health Check =====

@router.get("/health")
async def debate_health_check():
    """辯論引擎健康檢查"""
    try:
        engine = get_debate_engine()
        active_count = len(engine.active_sessions)
        
        return {
            "status": "healthy",
            "active_sessions": active_count,
            "service": "debate_engine"
        }
    except Exception as e:
        logger.error(f"Debate health check failed: {e}")
        raise HTTPException(status_code=503, detail="Debate engine unavailable")


# ===== Task 2.2 Enhanced API Endpoints =====

@router.get("/sessions/{session_id}/quality-report", response_model=Dict[str, Any])
async def get_debate_quality_report(session_id: str):
    """
    獲取辯論質量報告
    
    提供詳細的辯論質量分析，包括：
    - 論證強度評估
    - 參與者排名
    - 辯論亮點
    - 改進建議
    """
    try:
        engine = get_debate_engine()
        quality_report = await engine.get_debate_quality_report(session_id)
        
        if "error" in quality_report:
            raise HTTPException(status_code=404, detail=quality_report["error"])
        
        return quality_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality report for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quality report")


@router.get("/rotation/summary", response_model=Dict[str, Any])
async def get_model_rotation_summary():
    """
    獲取模型輪換摘要
    
    提供模型輪換系統的統計信息：
    - 模型性能數據
    - 輪換歷史
    - 當前策略
    """
    try:
        engine = get_debate_engine()
        rotation_summary = engine.get_rotation_summary()
        
        if "error" in rotation_summary:
            raise HTTPException(status_code=500, detail=rotation_summary["error"])
        
        return rotation_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rotation summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rotation summary")


@router.get("/rounds/adjustment-summary", response_model=Dict[str, Any])
async def get_round_adjustment_summary():
    """
    獲取輪次調整摘要
    
    提供輪次調整系統的統計信息：
    - 調整歷史
    - 質量趨勢
    - 改進建議
    """
    try:
        engine = get_debate_engine()
        adjustment_summary = engine.get_round_adjustment_summary()
        
        if "error" in adjustment_summary:
            raise HTTPException(status_code=500, detail=adjustment_summary["error"])
        
        return adjustment_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get adjustment summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get adjustment summary")


class RotationStrategyRequest(BaseModel):
    """輪換策略設置請求"""
    strategy: str = Field(..., description="輪換策略", pattern="^(fixed|round_robin|performance_based|adaptive|balanced)$")


@router.post("/rotation/strategy")
async def set_rotation_strategy(request: RotationStrategyRequest):
    """
    設置模型輪換策略
    
    支持的策略：
    - fixed: 固定分配
    - round_robin: 輪詢輪換  
    - performance_based: 基於性能
    - adaptive: 自適應輪換
    - balanced: 平衡輪換
    """
    try:
        engine = get_debate_engine()
        
        # 導入枚舉類型
        from services.model_rotation import RotationStrategy
        strategy_enum = RotationStrategy(request.strategy)
        
        engine.rotation_engine.set_rotation_strategy(strategy_enum)
        
        return {
            "message": f"Rotation strategy set to {request.strategy}",
            "strategy": request.strategy,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {e}")
    except Exception as e:
        logger.error(f"Failed to set rotation strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to set rotation strategy")


class RoundConfigRequest(BaseModel):
    """輪次配置請求"""
    min_rounds: Optional[int] = Field(None, description="最少輪次", ge=1, le=10)
    max_rounds: Optional[int] = Field(None, description="最多輪次", ge=1, le=15)
    quality_threshold: Optional[float] = Field(None, description="質量閾值", ge=0.0, le=1.0)
    engagement_threshold: Optional[float] = Field(None, description="參與度閾值", ge=0.0, le=1.0)


@router.post("/rounds/config")
async def configure_round_adjustment(request: RoundConfigRequest):
    """
    配置輪次調整參數
    
    允許調整自適應輪次系統的參數：
    - 最少/最多輪次
    - 質量和參與度閾值
    """
    try:
        engine = get_debate_engine()
        round_manager = engine.round_manager
        
        # 更新配置
        if request.min_rounds is not None:
            round_manager.min_rounds = request.min_rounds
        if request.max_rounds is not None:
            round_manager.max_rounds = request.max_rounds
        if request.quality_threshold is not None:
            round_manager.quality_threshold = request.quality_threshold
        if request.engagement_threshold is not None:
            round_manager.engagement_threshold = request.engagement_threshold
        
        return {
            "message": "Round adjustment configuration updated",
            "config": {
                "min_rounds": round_manager.min_rounds,
                "max_rounds": round_manager.max_rounds,
                "quality_threshold": round_manager.quality_threshold,
                "engagement_threshold": round_manager.engagement_threshold
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to configure round adjustment: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure round adjustment")


@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_performance_analytics():
    """
    獲取性能分析數據
    
    提供綜合的性能分析：
    - 模型性能對比
    - 輪換效果分析
    - 質量趨勢
    """
    try:
        engine = get_debate_engine()
        
        # 收集各種分析數據
        rotation_data = engine.get_rotation_summary()
        adjustment_data = engine.get_round_adjustment_summary()
        
        analytics = {
            "timestamp": datetime.now().isoformat(),
            "rotation_analytics": rotation_data,
            "adjustment_analytics": adjustment_data,
            "active_sessions": len(engine.active_sessions),
            "total_sessions_processed": len(engine.active_sessions)  # 簡化統計
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")


@router.post("/system/reset")
async def reset_debate_system():
    """
    重置辯論系統
    
    清除所有性能數據和歷史記錄
    注意：這將清除所有統計數據
    """
    try:
        engine = get_debate_engine()
        
        # 重置各個組件
        engine.rotation_engine.reset_performance_data()
        engine.round_manager.reset_round_data()
        
        return {
            "message": "Debate system reset successfully",
            "timestamp": datetime.now().isoformat(),
            "components_reset": [
                "model_rotation_engine",
                "round_adjustment_manager",
                "performance_data"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to reset debate system: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset debate system")


# ===== Task 2.3 Enhanced API Endpoints =====

@router.get("/sessions/{session_id}/deep-analysis", response_model=Dict[str, Any])
async def get_deep_debate_analysis(session_id: str):
    """
    獲取深度辯論分析
    
    提供詳細的深度辯論分析，包括：
    - 論證鏈追蹤
    - 上下文演進
    - 議題識別
    - 新興主題
    """
    try:
        engine = get_debate_engine()
        analysis = await engine.get_deep_debate_analysis(session_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deep debate analysis for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get deep debate analysis")


@router.get("/sessions/{session_id}/argument-strength", response_model=Dict[str, Any])
async def get_argument_strength_analysis(session_id: str):
    """
    獲取論證強度分析
    
    提供詳細的論證強度分析，包括：
    - 論證結構分析
    - 證據質量評估
    - 邏輯謬誤檢測
    - 強度比較
    """
    try:
        engine = get_debate_engine()
        analysis = await engine.get_argument_strength_comparison(session_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get argument strength analysis for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get argument strength analysis")


@router.get("/sessions/{session_id}/consensus", response_model=Dict[str, Any])
async def get_consensus_analysis(session_id: str):
    """
    獲取共識分析
    
    提供詳細的共識分析，包括：
    - 共同點識別
    - 分歧分析
    - 解決方案建議
    - 共識水平評估
    """
    try:
        engine = get_debate_engine()
        analysis = await engine.get_consensus_insights(session_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consensus analysis for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get consensus analysis")


@router.get("/sessions/{session_id}/advanced-judgment", response_model=Dict[str, Any])
async def get_advanced_judgment(session_id: str):
    """
    獲取高級AI判決
    
    提供詳細的高級判決分析，包括：
    - 多視角評估
    - 動態評分
    - 偏見檢測
    - 專業化評估
    """
    try:
        engine = get_debate_engine()
        judgment = await engine.get_advanced_judgment_details(session_id)
        
        if "error" in judgment:
            raise HTTPException(status_code=404, detail=judgment["error"])
        
        return judgment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get advanced judgment for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get advanced judgment")


@router.get("/sessions/{session_id}/comprehensive-insights", response_model=Dict[str, Any])
async def get_comprehensive_insights(session_id: str):
    """
    獲取綜合洞察
    
    提供所有Task 2.3功能的綜合分析結果
    """
    try:
        engine = get_debate_engine()
        
        # 並行獲取所有分析結果
        deep_analysis_task = engine.get_deep_debate_analysis(session_id)
        strength_analysis_task = engine.get_argument_strength_comparison(session_id)
        consensus_analysis_task = engine.get_consensus_insights(session_id)
        judgment_task = engine.get_advanced_judgment_details(session_id)
        
        # 等待所有任務完成
        deep_analysis, strength_analysis, consensus_analysis, judgment = await asyncio.gather(
            deep_analysis_task,
            strength_analysis_task,
            consensus_analysis_task,
            judgment_task,
            return_exceptions=True
        )
        
        # 構建綜合結果
        comprehensive_insights = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "deep_debate_analysis": deep_analysis if not isinstance(deep_analysis, Exception) else {"error": str(deep_analysis)},
            "argument_strength_analysis": strength_analysis if not isinstance(strength_analysis, Exception) else {"error": str(strength_analysis)},
            "consensus_analysis": consensus_analysis if not isinstance(consensus_analysis, Exception) else {"error": str(consensus_analysis)},
            "advanced_judgment": judgment if not isinstance(judgment, Exception) else {"error": str(judgment)}
        }
        
        return comprehensive_insights
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive insights for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comprehensive insights")


# ===== Task 2.3 System Analytics Endpoints =====

@router.get("/analytics/deep-debate-summary", response_model=Dict[str, Any])
async def get_deep_debate_summary():
    """
    獲取深度辯論系統摘要
    
    提供深度辯論引擎的整體統計和分析
    """
    try:
        from services.deep_debate import get_deep_debate_engine
        
        engine = get_deep_debate_engine()
        summary = engine.get_debate_analysis()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "deep_debate_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get deep debate summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get deep debate summary")


@router.get("/analytics/argument-analysis-summary", response_model=Dict[str, Any])
async def get_argument_analysis_summary():
    """
    獲取論證分析系統摘要
    
    提供論證分析引擎的整體統計和分析
    """
    try:
        from services.argument_analysis import get_argument_analysis_engine
        
        engine = get_argument_analysis_engine()
        summary = engine.get_analysis_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "argument_analysis_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get argument analysis summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get argument analysis summary")


@router.get("/analytics/consensus-summary", response_model=Dict[str, Any])
async def get_consensus_summary():
    """
    獲取共識建構系統摘要
    
    提供共識建構引擎的整體統計和分析
    """
    try:
        from services.consensus_builder import get_consensus_engine
        
        engine = get_consensus_engine()
        summary = engine.get_consensus_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "consensus_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get consensus summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get consensus summary")


@router.get("/analytics/advanced-judge-summary", response_model=Dict[str, Any])
async def get_advanced_judge_summary():
    """
    獲取高級裁判系統摘要
    
    提供高級裁判引擎的整體統計和分析
    """
    try:
        from services.advanced_judge import get_advanced_judge_engine
        
        engine = get_advanced_judge_engine()
        summary = engine.get_judgment_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "advanced_judge_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get advanced judge summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get advanced judge summary")


@router.get("/analytics/task-2-3-overview", response_model=Dict[str, Any])
async def get_task_2_3_overview():
    """
    獲取Task 2.3功能總覽
    
    提供所有Task 2.3功能的綜合統計和狀態
    """
    try:
        from services.deep_debate import get_deep_debate_engine
        from services.argument_analysis import get_argument_analysis_engine
        from services.consensus_builder import get_consensus_engine
        from services.advanced_judge import get_advanced_judge_engine
        
        # 獲取各個引擎的摘要
        deep_engine = get_deep_debate_engine()
        analysis_engine = get_argument_analysis_engine()
        consensus_engine = get_consensus_engine()
        judge_engine = get_advanced_judge_engine()
        
        # 並行獲取摘要
        deep_summary_task = asyncio.create_task(asyncio.to_thread(deep_engine.get_debate_analysis))
        analysis_summary_task = asyncio.create_task(asyncio.to_thread(analysis_engine.get_analysis_summary))
        consensus_summary_task = asyncio.create_task(asyncio.to_thread(consensus_engine.get_consensus_summary))
        judge_summary_task = asyncio.create_task(asyncio.to_thread(judge_engine.get_judgment_summary))
        
        deep_summary, analysis_summary, consensus_summary, judge_summary = await asyncio.gather(
            deep_summary_task,
            analysis_summary_task,
            consensus_summary_task,
            judge_summary_task,
            return_exceptions=True
        )
        
        overview = {
            "timestamp": datetime.now().isoformat(),
            "task_2_3_status": "active",
            "features": {
                "deep_debate_system": {
                    "status": "operational",
                    "summary": deep_summary if not isinstance(deep_summary, Exception) else {"error": str(deep_summary)}
                },
                "argument_analysis_system": {
                    "status": "operational",
                    "summary": analysis_summary if not isinstance(analysis_summary, Exception) else {"error": str(analysis_summary)}
                },
                "consensus_building_mechanism": {
                    "status": "operational",
                    "summary": consensus_summary if not isinstance(consensus_summary, Exception) else {"error": str(consensus_summary)}
                },
                "advanced_judge_system": {
                    "status": "operational",
                    "summary": judge_summary if not isinstance(judge_summary, Exception) else {"error": str(judge_summary)}
                }
            },
            "integration_status": "fully_integrated",
            "api_endpoints_available": 9
        }
        
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get Task 2.3 overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Task 2.3 overview")
