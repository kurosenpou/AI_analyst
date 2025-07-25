"""
Model Rotation Engine
動態模型輪換算法實現
Features: 智能輪換、性能評估、動態調整
"""

import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import math

from .model_pool import ModelRole, ModelConfig, get_model_pool
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class RotationStrategy(Enum):
    """輪換策略"""
    FIXED = "fixed"                    # 固定分配
    ROUND_ROBIN = "round_robin"        # 輪詢輪換
    PERFORMANCE_BASED = "performance_based"  # 基於性能
    RANDOM = "random"                  # 隨機輪換
    ADAPTIVE = "adaptive"              # 自適應輪換
    BALANCED = "balanced"              # 平衡輪換


class ModelPerformanceMetric(Enum):
    """模型性能指標"""
    RESPONSE_TIME = "response_time"           # 響應時間
    ARGUMENT_QUALITY = "argument_quality"    # 論證質量
    COHERENCE = "coherence"                  # 連貫性
    PERSUASIVENESS = "persuasiveness"        # 說服力
    ENGAGEMENT = "engagement"                # 參與度
    ERROR_RATE = "error_rate"               # 錯誤率


@dataclass
class ModelPerformanceData:
    """模型性能數據"""
    model_id: str
    role: ModelRole
    
    # 基礎性能指標
    total_calls: int = 0
    successful_calls: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    
    # 辯論質量指標
    argument_scores: List[float] = field(default_factory=list)
    coherence_scores: List[float] = field(default_factory=list)
    persuasiveness_scores: List[float] = field(default_factory=list)
    
    # 綜合評分
    overall_score: float = 0.0
    confidence_level: float = 0.0
    
    # 時間跟蹤
    last_used: Optional[datetime] = None
    performance_trend: List[float] = field(default_factory=list)
    
    def update_basic_metrics(self, response_time: float, success: bool):
        """更新基礎指標"""
        self.total_calls += 1
        self.last_used = datetime.now()
        
        if success:
            self.successful_calls += 1
            self.total_response_time += response_time
            self.average_response_time = self.total_response_time / self.successful_calls
        else:
            self.error_count += 1
        
        self.error_rate = self.error_count / self.total_calls if self.total_calls > 0 else 0.0
    
    def add_quality_score(self, argument: float, coherence: float, persuasiveness: float):
        """添加質量評分"""
        self.argument_scores.append(argument)
        self.coherence_scores.append(coherence)
        self.persuasiveness_scores.append(persuasiveness)
        
        # 計算綜合評分
        self._calculate_overall_score()
    
    def _calculate_overall_score(self):
        """計算綜合評分"""
        if not self.argument_scores:
            return
        
        # 各項指標權重
        weights = {
            'argument': 0.3,
            'coherence': 0.25,
            'persuasiveness': 0.25,
            'response_time': 0.1,
            'reliability': 0.1
        }
        
        # 計算各項平均分
        avg_argument = sum(self.argument_scores) / len(self.argument_scores)
        avg_coherence = sum(self.coherence_scores) / len(self.coherence_scores)
        avg_persuasiveness = sum(self.persuasiveness_scores) / len(self.persuasiveness_scores)
        
        # 響應時間評分（越快越好，歸一化到0-1）
        response_score = max(0, min(1, (5.0 - self.average_response_time) / 5.0))
        
        # 可靠性評分
        reliability_score = 1.0 - self.error_rate
        
        # 綜合評分
        self.overall_score = (
            weights['argument'] * avg_argument +
            weights['coherence'] * avg_coherence +
            weights['persuasiveness'] * avg_persuasiveness +
            weights['response_time'] * response_score +
            weights['reliability'] * reliability_score
        )
        
        # 更新性能趨勢
        self.performance_trend.append(self.overall_score)
        if len(self.performance_trend) > 10:  # 保留最近10次記錄
            self.performance_trend.pop(0)
        
        # 計算信心水平（基於數據點數量和趨勢穩定性）
        data_points = len(self.argument_scores)
        stability = self._calculate_trend_stability()
        self.confidence_level = min(1.0, (data_points / 10.0) * stability)
    
    def _calculate_trend_stability(self) -> float:
        """計算趨勢穩定性"""
        if len(self.performance_trend) < 2:
            return 0.5
        
        # 計算方差，方差越小越穩定
        mean_score = sum(self.performance_trend) / len(self.performance_trend)
        variance = sum((x - mean_score) ** 2 for x in self.performance_trend) / len(self.performance_trend)
        
        # 將方差轉換為穩定性評分（0-1）
        stability = max(0, min(1, 1 - variance))
        return stability


@dataclass
class RotationDecision:
    """輪換決策"""
    should_rotate: bool
    new_assignments: Optional[Dict[ModelRole, ModelConfig]]
    reason: str
    confidence: float
    expected_improvement: float


class ModelRotationEngine:
    """
    模型輪換引擎
    
    負責：
    1. 監控模型性能
    2. 決策何時輪換
    3. 選擇最佳模型組合
    4. 優化辯論質量
    """
    
    def __init__(self):
        self.model_pool = get_model_pool()
        self.performance_data: Dict[str, ModelPerformanceData] = {}
        self.rotation_history: List[Dict[str, Any]] = []
        self.current_strategy = RotationStrategy.ADAPTIVE
        
        # 輪換配置
        self.min_calls_before_rotation = 3  # 至少3次調用後才考慮輪換
        self.performance_threshold = 0.7    # 性能低於此值考慮輪換
        self.improvement_threshold = 0.1    # 期望改進超過此值才輪換
        
        logger.info("Model rotation engine initialized")
    
    def get_performance_data(self, model_id: str, role: ModelRole) -> ModelPerformanceData:
        """獲取或創建模型性能數據"""
        key = f"{model_id}:{role.value}"
        if key not in self.performance_data:
            self.performance_data[key] = ModelPerformanceData(
                model_id=model_id,
                role=role
            )
        return self.performance_data[key]
    
    def record_model_performance(
        self,
        model_id: str,
        role: ModelRole,
        response_time: float,
        success: bool,
        argument_quality: Optional[float] = None,
        coherence: Optional[float] = None,
        persuasiveness: Optional[float] = None
    ):
        """記錄模型性能數據"""
        perf_data = self.get_performance_data(model_id, role)
        perf_data.update_basic_metrics(response_time, success)
        
        if argument_quality is not None and coherence is not None and persuasiveness is not None:
            perf_data.add_quality_score(argument_quality, coherence, persuasiveness)
        
        # 記錄監控指標
        record_metric("model_performance_update", 1, {
            "model_id": model_id,
            "role": role.value,
            "success": str(success),
            "overall_score": str(perf_data.overall_score)
        })
        
        logger.debug(f"Updated performance for {model_id}:{role.value}, score: {perf_data.overall_score:.3f}")
    
    async def evaluate_rotation_need(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        debate_context: Dict[str, Any]
    ) -> RotationDecision:
        """評估是否需要進行模型輪換"""
        
        logger.info("Evaluating rotation need...")
        
        # 收集當前模型的性能數據
        current_performance = {}
        total_calls = 0
        
        for role, config in current_assignments.items():
            perf_data = self.get_performance_data(config.id, role)
            current_performance[role] = perf_data
            total_calls += perf_data.total_calls
        
        # 檢查是否有足夠的數據進行決策
        if total_calls < self.min_calls_before_rotation:
            return RotationDecision(
                should_rotate=False,
                new_assignments=None,
                reason=f"Insufficient data (calls: {total_calls}, min: {self.min_calls_before_rotation})",
                confidence=0.0,
                expected_improvement=0.0
            )
        
        # 根據策略評估輪換需求
        if self.current_strategy == RotationStrategy.FIXED:
            return await self._evaluate_fixed_strategy(current_assignments, current_performance)
        elif self.current_strategy == RotationStrategy.ROUND_ROBIN:
            return await self._evaluate_round_robin_strategy(current_assignments, current_performance)
        elif self.current_strategy == RotationStrategy.PERFORMANCE_BASED:
            return await self._evaluate_performance_based_strategy(current_assignments, current_performance)
        elif self.current_strategy == RotationStrategy.ADAPTIVE:
            return await self._evaluate_adaptive_strategy(current_assignments, current_performance, debate_context)
        else:
            return await self._evaluate_balanced_strategy(current_assignments, current_performance)
    
    async def _evaluate_fixed_strategy(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData]
    ) -> RotationDecision:
        """固定策略評估"""
        return RotationDecision(
            should_rotate=False,
            new_assignments=None,
            reason="Fixed strategy - no rotation",
            confidence=1.0,
            expected_improvement=0.0
        )
    
    async def _evaluate_round_robin_strategy(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData]
    ) -> RotationDecision:
        """輪詢策略評估"""
        # 簡單的輪詢：每N次調用後輪換
        total_calls = sum(perf.total_calls for perf in current_performance.values())
        rotation_interval = 5  # 每5次調用輪換一次
        
        if total_calls % rotation_interval == 0:
            new_assignments = await self._generate_round_robin_assignments(current_assignments)
            return RotationDecision(
                should_rotate=True,
                new_assignments=new_assignments,
                reason=f"Round-robin rotation (calls: {total_calls})",
                confidence=0.8,
                expected_improvement=0.05
            )
        
        return RotationDecision(
            should_rotate=False,
            new_assignments=None,
            reason="Round-robin interval not reached",
            confidence=0.8,
            expected_improvement=0.0
        )
    
    async def _evaluate_performance_based_strategy(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData]
    ) -> RotationDecision:
        """基於性能的策略評估"""
        
        # 找出性能最差的模型
        worst_role = None
        worst_score = float('inf')
        
        for role, perf_data in current_performance.items():
            if perf_data.overall_score < worst_score and perf_data.confidence_level > 0.5:
                worst_score = perf_data.overall_score
                worst_role = role
        
        # 如果最差模型的性能低於閾值，考慮輪換
        if worst_role and worst_score < self.performance_threshold:
            # 尋找更好的替代模型
            better_model = await self._find_better_model(worst_role, worst_score)
            
            if better_model:
                new_assignments = current_assignments.copy()
                new_assignments[worst_role] = better_model
                
                expected_improvement = better_model.estimated_performance - worst_score
                
                return RotationDecision(
                    should_rotate=True,
                    new_assignments=new_assignments,
                    reason=f"Performance-based rotation for {worst_role.value} (score: {worst_score:.3f})",
                    confidence=0.9,
                    expected_improvement=expected_improvement
                )
        
        return RotationDecision(
            should_rotate=False,
            new_assignments=None,
            reason="All models performing adequately",
            confidence=0.9,
            expected_improvement=0.0
        )
    
    async def _evaluate_adaptive_strategy(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData],
        debate_context: Dict[str, Any]
    ) -> RotationDecision:
        """自適應策略評估"""
        
        # 綜合考慮多個因素
        factors = {}
        
        # 1. 性能因素
        avg_performance = sum(perf.overall_score for perf in current_performance.values()) / len(current_performance)
        factors['performance'] = avg_performance
        
        # 2. 趨勢因素
        declining_models = []
        for role, perf_data in current_performance.items():
            if len(perf_data.performance_trend) >= 3:
                recent_trend = sum(perf_data.performance_trend[-3:]) / 3
                earlier_trend = sum(perf_data.performance_trend[-6:-3]) / 3 if len(perf_data.performance_trend) >= 6 else recent_trend
                
                if recent_trend < earlier_trend - 0.05:  # 下降趨勢
                    declining_models.append(role)
        
        factors['declining_count'] = len(declining_models)
        
        # 3. 辯論複雜度因素
        topic_complexity = debate_context.get('complexity_score', 0.5)
        factors['complexity'] = topic_complexity
        
        # 4. 時間因素
        time_since_rotation = debate_context.get('time_since_last_rotation', 0)
        factors['time_factor'] = min(1.0, time_since_rotation / 3600)  # 1小時後時間因素為1
        
        # 綜合決策
        rotation_score = self._calculate_adaptive_score(factors)
        
        if rotation_score > 0.6:  # 輪換閾值
            new_assignments = await self._generate_adaptive_assignments(
                current_assignments, current_performance, factors
            )
            
            return RotationDecision(
                should_rotate=True,
                new_assignments=new_assignments,
                reason=f"Adaptive rotation (score: {rotation_score:.3f}, factors: {factors})",
                confidence=rotation_score,
                expected_improvement=rotation_score * 0.2
            )
        
        return RotationDecision(
            should_rotate=False,
            new_assignments=None,
            reason=f"Adaptive score below threshold ({rotation_score:.3f})",
            confidence=1.0 - rotation_score,
            expected_improvement=0.0
        )
    
    async def _evaluate_balanced_strategy(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData]
    ) -> RotationDecision:
        """平衡策略評估"""
        
        # 檢查模型使用的平衡性
        all_models = self.model_pool.get_available_models()
        usage_stats = {}
        
        for model in all_models:
            total_usage = 0
            for role in ModelRole:
                perf_data = self.performance_data.get(f"{model.id}:{role.value}")
                if perf_data:
                    total_usage += perf_data.total_calls
            usage_stats[model.id] = total_usage
        
        # 計算使用不平衡度
        if usage_stats:
            max_usage = max(usage_stats.values())
            min_usage = min(usage_stats.values())
            imbalance = (max_usage - min_usage) / (max_usage + 1)
            
            if imbalance > 0.5:  # 不平衡閾值
                # 選擇使用較少的模型
                underused_models = [
                    model for model in all_models 
                    if usage_stats.get(model.id, 0) < max_usage * 0.5
                ]
                
                if underused_models:
                    new_assignments = await self._generate_balanced_assignments(
                        current_assignments, underused_models
                    )
                    
                    return RotationDecision(
                        should_rotate=True,
                        new_assignments=new_assignments,
                        reason=f"Balanced rotation (imbalance: {imbalance:.3f})",
                        confidence=0.7,
                        expected_improvement=0.1
                    )
        
        return RotationDecision(
            should_rotate=False,
            new_assignments=None,
            reason="Models usage is balanced",
            confidence=0.8,
            expected_improvement=0.0
        )
    
    def _calculate_adaptive_score(self, factors: Dict[str, float]) -> float:
        """計算自適應評分"""
        weights = {
            'performance': -0.4,      # 性能越低，輪換分數越高
            'declining_count': 0.3,   # 下降模型越多，輪換分數越高
            'complexity': 0.2,        # 複雜度越高，越需要輪換
            'time_factor': 0.1        # 時間越長，越傾向輪換
        }
        
        score = 0.0
        for factor, value in factors.items():
            if factor in weights:
                if factor == 'performance':
                    # 性能因素：1-performance，即性能越低分數越高
                    score += weights[factor] * (1 - value)
                else:
                    score += weights[factor] * value
        
        return max(0.0, min(1.0, score + 0.5))  # 基線0.5，確保在0-1範圍內
    
    async def _find_better_model(self, role: ModelRole, current_score: float) -> Optional[ModelConfig]:
        """尋找更好的模型"""
        available_models = list(self.model_pool.get_available_models().values())
        
        best_model = None
        best_estimated_score = current_score
        
        for model in available_models:
            # 檢查該模型的歷史性能
            perf_data = self.performance_data.get(f"{model.id}:{role.value}")
            
            if perf_data and perf_data.confidence_level > 0.3:
                # 有足夠的歷史數據
                estimated_score = perf_data.overall_score
            else:
                # 沒有足夠數據，使用基礎評分（基於模型優勢）
                estimated_score = self._estimate_model_performance(model, role)
            
            if estimated_score > best_estimated_score + self.improvement_threshold:
                best_estimated_score = estimated_score
                best_model = model
        
        return best_model
    
    def _estimate_model_performance(self, model: ModelConfig, role: ModelRole) -> float:
        """基於模型特性估算性能"""
        base_score = 0.6  # 基礎分數
        
        # 根據模型優勢和角色匹配度調整分數
        role_strengths = {
            ModelRole.DEBATER_A: ["reasoning", "analysis", "creativity"],
            ModelRole.DEBATER_B: ["problem_solving", "broad_knowledge", "creativity"],
            ModelRole.JUDGE: ["factual_accuracy", "logical_reasoning", "neutral_judgment"]
        }
        
        required_strengths = role_strengths.get(role, [])
        matching_strengths = set(model.strengths) & set(required_strengths)
        
        # 每個匹配的優勢增加0.1分
        bonus = len(matching_strengths) * 0.1
        
        # 基於提供商的調整
        provider_bonus = {
            "anthropic": 0.05,    # Claude系列通常在分析方面較強
            "openai": 0.03,       # GPT系列在創造性方面較強
            "google": 0.04        # Gemini在事實準確性方面較強
        }.get(model.provider, 0.0)
        
        return min(1.0, base_score + bonus + provider_bonus)
    
    async def _generate_round_robin_assignments(
        self,
        current_assignments: Dict[ModelRole, ModelConfig]
    ) -> Dict[ModelRole, ModelConfig]:
        """生成輪詢輪換分配"""
        new_assignments = {}
        available_models = list(self.model_pool.get_available_models().values())
        
        for role in ModelRole:
            if available_models:
                # 找到當前模型在列表中的位置，選擇下一個
                current_model = current_assignments[role]
                try:
                    current_index = next(i for i, m in enumerate(available_models) if m.id == current_model.id)
                    next_index = (current_index + 1) % len(available_models)
                    new_assignments[role] = available_models[next_index]
                except (StopIteration, ValueError):
                    # 當前模型不在可用列表中，選擇第一個
                    new_assignments[role] = available_models[0]
            else:
                # 沒有可用模型，保持當前分配
                new_assignments[role] = current_assignments[role]
        
        return new_assignments
    
    async def _generate_adaptive_assignments(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        current_performance: Dict[ModelRole, ModelPerformanceData],
        factors: Dict[str, float]
    ) -> Dict[ModelRole, ModelConfig]:
        """生成自適應輪換分配"""
        new_assignments = current_assignments.copy()
        
        # 優先替換表現最差的模型
        performance_ranking = sorted(
            current_performance.items(),
            key=lambda x: x[1].overall_score
        )
        
        for role, perf_data in performance_ranking:
            if perf_data.overall_score < self.performance_threshold:
                better_model = await self._find_better_model(role, perf_data.overall_score)
                if better_model:
                    new_assignments[role] = better_model
                    break  # 一次只替換一個模型
        
        return new_assignments
    
    async def _generate_balanced_assignments(
        self,
        current_assignments: Dict[ModelRole, ModelConfig],
        underused_models: List[ModelConfig]
    ) -> Dict[ModelRole, ModelConfig]:
        """生成平衡輪換分配"""
        new_assignments = current_assignments.copy()
        
        # 隨機選擇一個角色進行替換
        roles = list(ModelRole)
        random.shuffle(roles)
        
        for role in roles:
            # 從使用較少的模型中選擇適合的模型
            suitable_models = [
                model for model in underused_models
                if self._is_model_suitable_for_role(model, role)
            ]
            
            if suitable_models:
                new_assignments[role] = random.choice(suitable_models)
                break
        
        return new_assignments
    
    def _is_model_suitable_for_role(self, model: ModelConfig, role: ModelRole) -> bool:
        """檢查模型是否適合特定角色"""
        role_requirements = {
            ModelRole.DEBATER_A: ["reasoning", "analysis", "creativity"],
            ModelRole.DEBATER_B: ["problem_solving", "broad_knowledge", "creativity"],
            ModelRole.JUDGE: ["factual_accuracy", "logical_reasoning", "neutral_judgment"]
        }
        
        required_strengths = role_requirements.get(role, [])
        model_strengths = set(model.strengths)
        
        # 至少需要匹配一個所需優勢
        return bool(model_strengths & set(required_strengths))
    
    def set_rotation_strategy(self, strategy: RotationStrategy):
        """設置輪換策略"""
        self.current_strategy = strategy
        logger.info(f"Rotation strategy changed to: {strategy.value}")
        
        record_metric("rotation_strategy_changed", 1, {
            "new_strategy": strategy.value
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        summary = {
            "total_models_tracked": len(self.performance_data),
            "rotation_history_count": len(self.rotation_history),
            "current_strategy": self.current_strategy.value,
            "models": {}
        }
        
        for key, perf_data in self.performance_data.items():
            model_id, role = key.split(":", 1)
            summary["models"][key] = {
                "model_id": model_id,
                "role": role,
                "total_calls": perf_data.total_calls,
                "success_rate": (perf_data.successful_calls / perf_data.total_calls) if perf_data.total_calls > 0 else 0,
                "average_response_time": perf_data.average_response_time,
                "overall_score": perf_data.overall_score,
                "confidence_level": perf_data.confidence_level
            }
        
        return summary
    
    def reset_performance_data(self):
        """重置性能數據"""
        self.performance_data.clear()
        self.rotation_history.clear()
        logger.info("Performance data reset")


# 全局輪換引擎實例
rotation_engine = None

def get_rotation_engine() -> ModelRotationEngine:
    """獲取模型輪換引擎實例"""
    global rotation_engine
    if rotation_engine is None:
        rotation_engine = ModelRotationEngine()
    return rotation_engine
