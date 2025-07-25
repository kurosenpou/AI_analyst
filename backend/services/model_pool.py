"""
Model Pool Management System
Manages multiple AI models for debate scenarios with role rotation
"""

import os
import random
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from services.openrouter_client import get_openrouter_client
import logging

logger = logging.getLogger(__name__)

class ModelRole(Enum):
    """定義模型在辯論中的角色"""
    DEBATER_A = "debater_a"  # 正方辯論者
    DEBATER_B = "debater_b"  # 反方辯論者
    JUDGE = "judge"          # 裁判

@dataclass
class ModelConfig:
    """模型配置信息"""
    id: str                    # OpenRouter模型ID
    name: str                  # 顯示名稱
    provider: str              # 提供商（anthropic, openai, google等）
    max_tokens: int           # 最大token數
    temperature: float        # 溫度參數
    strengths: List[str]      # 模型優勢（用於角色分配）
    cost_per_token: float     # 每token成本（用於成本控制）

@dataclass
class DebateSession:
    """辯論會話信息"""
    session_id: str
    topic: str
    round_number: int
    participants: Dict[ModelRole, str]  # 角色 -> 模型ID映射
    history: List[Dict[str, Any]]       # 辯論歷史
    created_at: str

class ModelPool:
    """
    多模型管理池
    負責模型的選擇、輪換和角色分配
    """
    
    def __init__(self):
        self.client = get_openrouter_client()
        
        # 可用模型配置
        self.models = {
            "claude-3.5-sonnet": ModelConfig(
                id="anthropic/claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                max_tokens=4096,
                temperature=0.7,
                strengths=["reasoning", "analysis", "structured_thinking"],
                cost_per_token=0.000015
            ),
            "gpt-4o": ModelConfig(
                id="openai/gpt-4o",
                name="GPT-4o",
                provider="openai", 
                max_tokens=4096,
                temperature=0.7,
                strengths=["creativity", "problem_solving", "broad_knowledge"],
                cost_per_token=0.00001
            ),
            "gemini-pro": ModelConfig(
                id="google/gemini-pro-1.5",
                name="Gemini Pro 1.5",
                provider="google",
                max_tokens=4096,
                temperature=0.6,
                strengths=["factual_accuracy", "logical_reasoning", "neutral_judgment"],
                cost_per_token=0.000007
            )
        }
        
        # 從環境變量加載默認配置
        self.default_assignments = {
            ModelRole.DEBATER_A: os.getenv("DEFAULT_DEBATER_A_MODEL", "anthropic/claude-3-5-sonnet-20241022"),
            ModelRole.DEBATER_B: os.getenv("DEFAULT_DEBATER_B_MODEL", "openai/gpt-4o"),
            ModelRole.JUDGE: os.getenv("DEFAULT_JUDGE_MODEL", "google/gemini-pro-1.5")
        }
        
        # 活躍的辯論會話
        self.active_sessions: Dict[str, DebateSession] = {}
        
        logger.info(f"ModelPool initialized with {len(self.models)} models")
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelConfig]:
        """根據OpenRouter ID獲取模型配置"""
        for model in self.models.values():
            if model.id == model_id:
                return model
        return None
    
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """獲取所有可用模型"""
        return self.models.copy()
    
    def assign_models_to_roles(
        self, 
        strategy: str = "default",
        exclude_models: Optional[List[str]] = None
    ) -> Dict[ModelRole, ModelConfig]:
        """
        為辯論角色分配模型
        
        Args:
            strategy: 分配策略 ("default", "random", "optimal", "cost_aware")
            exclude_models: 排除的模型列表
            
        Returns:
            角色到模型配置的映射
        """
        exclude_models = exclude_models or []
        available_models = {
            k: v for k, v in self.models.items() 
            if v.id not in exclude_models
        }
        
        if len(available_models) < 3:
            raise ValueError("需要至少3個可用模型進行辯論")
        
        assignments = {}
        
        if strategy == "default":
            # 使用環境變量中的默認配置
            for role, model_id in self.default_assignments.items():
                model = self.get_model_by_id(model_id)
                if model and model_id not in exclude_models:
                    assignments[role] = model
                    
        elif strategy == "random":
            # 隨機分配
            model_list = list(available_models.values())
            random.shuffle(model_list)
            assignments = {
                ModelRole.DEBATER_A: model_list[0],
                ModelRole.DEBATER_B: model_list[1],
                ModelRole.JUDGE: model_list[2]
            }
            
        elif strategy == "optimal":
            # 基於模型優勢的最優分配
            assignments = self._optimal_assignment(available_models)
            
        elif strategy == "cost_aware":
            # 成本意識分配（選擇較便宜的模型）
            sorted_models = sorted(
                available_models.values(),
                key=lambda m: m.cost_per_token
            )
            assignments = {
                ModelRole.DEBATER_A: sorted_models[0],
                ModelRole.DEBATER_B: sorted_models[1],
                ModelRole.JUDGE: sorted_models[2] if len(sorted_models) > 2 else sorted_models[0]
            }
        
        # 確保所有角色都有分配
        if len(assignments) < 3:
            remaining_models = [
                m for m in available_models.values()
                if m not in assignments.values()
            ]
            
            for role in ModelRole:
                if role not in assignments and remaining_models:
                    assignments[role] = remaining_models.pop(0)
        
        logger.info(f"模型分配完成 - 策略: {strategy}")
        for role, model in assignments.items():
            logger.info(f"  {role.value}: {model.name} ({model.id})")
            
        return assignments
    
    def _optimal_assignment(self, available_models: Dict[str, ModelConfig]) -> Dict[ModelRole, ModelConfig]:
        """基於模型優勢進行最優分配"""
        assignments = {}
        
        # 為裁判選擇最適合的模型（邏輯推理能力強）
        judge_candidates = [
            m for m in available_models.values()
            if "logical_reasoning" in m.strengths or "neutral_judgment" in m.strengths
        ]
        if judge_candidates:
            assignments[ModelRole.JUDGE] = judge_candidates[0]
        
        # 為辯論者選擇互補的模型
        remaining_models = [
            m for m in available_models.values()
            if m not in assignments.values()
        ]
        
        if len(remaining_models) >= 2:
            # 選擇擅長不同領域的模型作為辯論者
            reasoning_models = [m for m in remaining_models if "reasoning" in m.strengths]
            creative_models = [m for m in remaining_models if "creativity" in m.strengths]
            
            if reasoning_models and creative_models:
                assignments[ModelRole.DEBATER_A] = reasoning_models[0]
                assignments[ModelRole.DEBATER_B] = creative_models[0]
            else:
                assignments[ModelRole.DEBATER_A] = remaining_models[0]
                assignments[ModelRole.DEBATER_B] = remaining_models[1]
        
        return assignments
    
    def rotate_models(self, current_assignments: Dict[ModelRole, ModelConfig]) -> Dict[ModelRole, ModelConfig]:
        """
        輪換模型角色
        確保每個模型都有機會擔任不同角色
        """
        models = list(current_assignments.values())
        roles = list(ModelRole)
        
        # 順時針輪換
        new_assignments = {}
        for i, role in enumerate(roles):
            new_assignments[role] = models[(i + 1) % len(models)]
        
        logger.info("模型角色輪換完成")
        for role, model in new_assignments.items():
            logger.info(f"  {role.value}: {model.name}")
            
        return new_assignments
    
    def create_debate_session(
        self, 
        topic: str, 
        model_assignments: Optional[Dict[ModelRole, ModelConfig]] = None
    ) -> DebateSession:
        """創建新的辯論會話"""
        import uuid
        from datetime import datetime
        
        session_id = str(uuid.uuid4())[:8]
        
        if model_assignments is None:
            model_assignments = self.assign_models_to_roles("default")
        
        participants = {
            role: model.id for role, model in model_assignments.items()
        }
        
        session = DebateSession(
            session_id=session_id,
            topic=topic,
            round_number=0,
            participants=participants,
            history=[],
            created_at=datetime.now().isoformat()
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"創建辯論會話: {session_id} - 主題: {topic}")
        return session
    
    def get_session(self, session_id: str) -> Optional[DebateSession]:
        """獲取辯論會話"""
        return self.active_sessions.get(session_id)
    
    def estimate_cost(
        self, 
        assignments: Dict[ModelRole, ModelConfig],
        estimated_tokens_per_model: int = 1000
    ) -> Dict[str, float]:
        """估算辯論成本"""
        costs = {}
        total_cost = 0
        
        for role, model in assignments.items():
            model_cost = model.cost_per_token * estimated_tokens_per_model
            costs[f"{role.value} ({model.name})"] = model_cost
            total_cost += model_cost
        
        costs["總計"] = total_cost
        return costs
    
    async def test_model_health(self) -> Dict[str, bool]:
        """測試所有模型的健康狀態"""
        results = {}
        test_prompt = "請簡短回答：今天是星期幾？"
        
        for model_key, model_config in self.models.items():
            try:
                response = await self.client.chat_completion(
                    model=model_config.id,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
                results[model_key] = bool(response and len(response.strip()) > 0)
                logger.info(f"模型健康檢查 - {model_config.name}: {'✅' if results[model_key] else '❌'}")
                
            except Exception as e:
                results[model_key] = False
                logger.error(f"模型健康檢查失敗 - {model_config.name}: {e}")
        
        return results

# 全局模型池實例
model_pool = None

def get_model_pool() -> ModelPool:
    """獲取或創建全局模型池實例"""
    global model_pool
    if model_pool is None:
        model_pool = ModelPool()
    return model_pool
