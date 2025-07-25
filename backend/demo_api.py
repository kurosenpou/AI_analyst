"""
簡化的辯論API測試服務器
專門用於演示Task 2.1的辯論引擎功能
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import asyncio
from unittest.mock import patch

# 導入辯論引擎
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.debate_engine import get_debate_engine, DebateStatus, DebatePhase
from services.model_pool import ModelRole

app = FastAPI(title="AI辯論引擎API", version="2.1.0")

# 請求模型
class CreateDebateRequest(BaseModel):
    topic: str
    business_data: str
    context: str = ""
    max_rounds: int = 3

class DebateResponse(BaseModel):
    session_id: str
    topic: str
    status: str
    current_phase: str
    message_count: int
    duration: Optional[float]

# 模擬API調用函數（和之前測試中使用的相同）
MOCK_RESPONSES = {
    ModelRole.DEBATER_A: {
        DebatePhase.OPENING: "正方開場：支持AI客服系統，成本效益顯著...",
        DebatePhase.FIRST_ROUND: "正方反駁：AI技術已經成熟，風險可控...",
        DebatePhase.CLOSING: "正方總結：建議立即實施AI客服方案..."
    },
    ModelRole.DEBATER_B: {
        DebatePhase.OPENING: "反方開場：反對AI客服，客戶體驗風險高...",
        DebatePhase.FIRST_ROUND: "反方反駁：AI無法處理複雜情緒需求...",
        DebatePhase.CLOSING: "反方總結：建議採用人機協作方案..."
    },
    ModelRole.JUDGE: {
        DebatePhase.JUDGMENT: "裁判判決：經過評估，建議分階段實施方案..."
    }
}

async def mock_openrouter_call(*args, **kwargs):
    """模擬OpenRouter API調用"""
    await asyncio.sleep(0.3)  # 模擬API延遲
    
    messages = kwargs.get('messages', [])
    if not messages:
        return "模擬響應"
    
    content = messages[0].get('content', '')
    
    # 簡單的角色和階段推斷
    if '正方' in content or 'debater_a' in content:
        role = ModelRole.DEBATER_A
    elif '反方' in content or 'debater_b' in content:
        role = ModelRole.DEBATER_B
    elif '裁判' in content or 'judge' in content:
        role = ModelRole.JUDGE
    else:
        role = ModelRole.DEBATER_A
    
    if '開場' in content:
        phase = DebatePhase.OPENING
    elif '輪次' in content or '反駁' in content:
        phase = DebatePhase.FIRST_ROUND
    elif '結語' in content or '總結' in content:
        phase = DebatePhase.CLOSING
    elif '裁判' in content:
        phase = DebatePhase.JUDGMENT
    else:
        phase = DebatePhase.OPENING
    
    return MOCK_RESPONSES.get(role, {}).get(phase, f"模擬{role.value}響應")

@app.get("/")
async def root():
    """根路由"""
    return {
        "service": "AI辯論引擎 Demo API",
        "version": "2.1.0",
        "description": "Task 2.1 - 辯論引擎核心實現演示",
        "endpoints": [
            "/debate/create - 創建辯論會話",
            "/debate/start/{session_id} - 開始辯論",
            "/debate/status/{session_id} - 查看辯論狀態",
            "/debate/history/{session_id} - 查看完整辯論記錄"
        ]
    }

@app.post("/debate/create", response_model=DebateResponse)
async def create_debate(request: CreateDebateRequest):
    """創建新的辯論會話"""
    with patch('services.openrouter_client.OpenRouterClient.chat_completion', side_effect=mock_openrouter_call):
        try:
            engine = get_debate_engine()
            
            session = await engine.create_debate_session(
                topic=request.topic,
                business_data=request.business_data,
                context=request.context,
                max_rounds=request.max_rounds
            )
            
            return DebateResponse(
                session_id=session.session_id,
                topic=session.topic,
                status=session.status.value,
                current_phase=session.current_phase.value,
                message_count=len(session.all_messages),
                duration=session.duration
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/debate/start/{session_id}", response_model=DebateResponse)
async def start_debate(session_id: str):
    """開始辯論會話"""
    with patch('services.openrouter_client.OpenRouterClient.chat_completion', side_effect=mock_openrouter_call):
        try:
            engine = get_debate_engine()
            session = engine.get_session(session_id)
            
            if not session:
                raise HTTPException(status_code=404, detail="辯論會話未找到")
            
            # 開始辯論
            session = await engine.start_debate(session_id)
            
            # 自動完成整個辯論流程
            max_iterations = 10
            iteration = 0
            
            while (session.status == DebateStatus.ACTIVE and 
                   session.current_phase != DebatePhase.COMPLETED and 
                   iteration < max_iterations):
                iteration += 1
                try:
                    session = await engine.continue_debate(session_id)
                except Exception as e:
                    print(f"辯論繼續時出錯: {e}")
                    break
                
                if session.current_phase == DebatePhase.COMPLETED:
                    break
            
            return DebateResponse(
                session_id=session.session_id,
                topic=session.topic,
                status=session.status.value,
                current_phase=session.current_phase.value,
                message_count=len(session.all_messages),
                duration=session.duration
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/debate/status/{session_id}")
async def get_debate_status(session_id: str):
    """獲取辯論狀態"""
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="辯論會話未找到")
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status.value,
            "current_phase": session.current_phase.value,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "message_count": len(session.all_messages),
            "duration": session.duration,
            "model_assignments": {
                role.value: config.name 
                for role, config in session.model_assignments.items()
            },
            "statistics": {
                "total_tokens": session.total_tokens,
                "total_cost": session.total_cost,
                "error_count": session.error_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debate/history/{session_id}")
async def get_debate_history(session_id: str):
    """獲取完整辯論記錄"""
    try:
        engine = get_debate_engine()
        session = engine.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="辯論會話未找到")
        
        # 構建辯論記錄
        rounds = []
        for round in session.rounds:
            round_data = {
                "round_number": round.round_number,
                "phase": round.phase.value,
                "duration": round.duration,
                "messages": []
            }
            
            for msg in round.messages:
                round_data["messages"].append({
                    "speaker": msg.speaker.value,
                    "model_id": msg.model_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "response_time": msg.response_time
                })
            
            rounds.append(round_data)
        
        judgment = None
        if session.judgment:
            judgment = {
                "speaker": session.judgment.speaker.value,
                "content": session.judgment.content,
                "timestamp": session.judgment.timestamp.isoformat()
            }
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status.value,
            "rounds": rounds,
            "judgment": judgment,
            "final_report": session.final_report,
            "statistics": {
                "total_tokens": session.total_tokens,
                "total_cost": session.total_cost,
                "error_count": session.error_count,
                "duration": session.duration
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debate/sessions")
async def list_sessions():
    """列出所有辯論會話"""
    try:
        engine = get_debate_engine()
        sessions = engine.list_active_sessions()
        
        return {
            "total": len(sessions),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "topic": session.topic,
                    "status": session.status.value,
                    "current_phase": session.current_phase.value,
                    "message_count": len(session.all_messages),
                    "created_at": session.created_at.isoformat()
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
