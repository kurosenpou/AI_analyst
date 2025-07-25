"""
Adaptive Round Adjustment System
自適應輪次調整機制
Features: 動態輪次管理、質量驅動的延長/縮短、智能終止條件
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import math

from .debate_quality import get_quality_assessor, QualityDimension, ArgumentAnalysis
from .model_rotation import get_rotation_engine, RotationDecision
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class RoundAdjustmentReason(Enum):
    """輪次調整原因"""
    QUALITY_INSUFFICIENT = "quality_insufficient"     # 質量不足，需要更多輪次
    DEPTH_LACKING = "depth_lacking"                  # 深度不夠，需要深入討論
    ARGUMENTS_STRONG = "arguments_strong"            # 論證強勁，可以延長
    CONSENSUS_REACHED = "consensus_reached"          # 達成共識，可以提前結束
    REPETITIVE_CONTENT = "repetitive_content"        # 內容重複，可以縮短
    TIME_CONSTRAINT = "time_constraint"              # 時間限制，需要調整
    PARTICIPANT_FATIGUE = "participant_fatigue"      # 參與者疲勞，需要結束
    TOPIC_EXHAUSTED = "topic_exhausted"             # 話題已充分討論


class RoundDecision(Enum):
    """輪次決策"""
    CONTINUE_NORMAL = "continue_normal"              # 正常繼續
    EXTEND_ROUNDS = "extend_rounds"                  # 延長輪次
    REDUCE_ROUNDS = "reduce_rounds"                  # 減少輪次
    TERMINATE_EARLY = "terminate_early"              # 提前終止
    ADD_SPECIAL_ROUND = "add_special_round"          # 添加特殊輪次


@dataclass
class RoundMetrics:
    """輪次指標"""
    round_number: int
    quality_scores: Dict[str, float]                 # 參與者質量評分
    average_quality: float                          # 平均質量
    engagement_level: float                         # 參與度
    novelty_score: float                           # 新穎度評分
    depth_score: float                             # 深度評分
    convergence_score: float                       # 收斂度評分
    time_elapsed: float                            # 已用時間
    
    # 趨勢指標
    quality_trend: List[float] = field(default_factory=list)
    engagement_trend: List[float] = field(default_factory=list)
    novelty_trend: List[float] = field(default_factory=list)


@dataclass
class AdjustmentDecision:
    """調整決策"""
    decision: RoundDecision
    target_rounds: Optional[int]                    # 目標輪次數
    reasons: List[RoundAdjustmentReason]           # 調整原因
    confidence: float                              # 決策信心
    expected_improvement: float                    # 預期改善
    alternative_actions: List[str]                 # 替代行動
    
    # 實施參數
    adjustment_parameters: Dict[str, Any] = field(default_factory=dict)
    monitoring_thresholds: Dict[str, float] = field(default_factory=dict)


class AdaptiveRoundManager:
    """
    自適應輪次管理器
    
    負責：
    1. 監控辯論質量和進展
    2. 評估是否需要調整輪次
    3. 決定延長、縮短或終止辯論
    4. 優化辯論體驗
    """
    
    def __init__(self):
        self.quality_assessor = get_quality_assessor()
        self.rotation_engine = get_rotation_engine()
        
        # 調整配置
        self.min_rounds = 3                        # 最少輪次
        self.max_rounds = 10                       # 最多輪次
        self.quality_threshold = 0.7               # 質量閾值
        self.engagement_threshold = 0.6            # 參與度閾值
        self.novelty_threshold = 0.4               # 新穎度閾值
        self.convergence_threshold = 0.8           # 收斂閾值
        
        # 時間限制
        self.max_debate_time = 3600                # 最大辯論時間（秒）
        self.target_round_time = 180               # 目標單輪時間
        
        # 歷史數據
        self.round_history: List[RoundMetrics] = []
        self.adjustment_history: List[AdjustmentDecision] = []
        
        logger.info("Adaptive round manager initialized")
    
    async def evaluate_round_adjustment(
        self,
        current_round: int,
        planned_total_rounds: int,
        round_arguments: List[Dict[str, Any]],
        debate_context: Dict[str, Any]
    ) -> AdjustmentDecision:
        """評估是否需要輪次調整"""
        
        logger.info(f"Evaluating round adjustment for round {current_round}/{planned_total_rounds}")
        
        # 分析當前輪次的指標
        round_metrics = await self._calculate_round_metrics(
            current_round, round_arguments, debate_context
        )
        
        self.round_history.append(round_metrics)
        
        # 收集評估因素
        evaluation_factors = await self._collect_evaluation_factors(
            current_round, planned_total_rounds, round_metrics, debate_context
        )
        
        # 基於因素做出決策
        decision = await self._make_adjustment_decision(
            evaluation_factors, current_round, planned_total_rounds
        )
        
        # 記錄決策
        self.adjustment_history.append(decision)
        
        # 記錄監控指標
        record_metric("round_adjustment_evaluation", 1, {
            "round": str(current_round),
            "decision": decision.decision.value,
            "confidence": str(decision.confidence),
            "quality": str(round_metrics.average_quality)
        })
        
        logger.info(f"Round adjustment decision: {decision.decision.value} (confidence: {decision.confidence:.3f})")
        
        return decision
    
    async def _calculate_round_metrics(
        self,
        round_number: int,
        round_arguments: List[Dict[str, Any]],
        debate_context: Dict[str, Any]
    ) -> RoundMetrics:
        """計算輪次指標"""
        
        if not round_arguments:
            return RoundMetrics(
                round_number=round_number,
                quality_scores={},
                average_quality=0.5,
                engagement_level=0.5,
                novelty_score=0.5,
                depth_score=0.5,
                convergence_score=0.5,
                time_elapsed=0.0
            )
        
        # 並行分析所有論證
        analysis_tasks = []
        for arg in round_arguments:
            from .debate_quality import DebateRole
            role = DebateRole.OPENING_STATEMENT  # 可根據實際情況調整
            task = self.quality_assessor.analyze_argument(
                content=arg.get('content', ''),
                role=role,
                speaker=arg.get('speaker', 'unknown'),
                context={'topic': debate_context.get('topic', ''), 'round': round_number}
            )
            analysis_tasks.append(task)
        
        analyses = await asyncio.gather(*analysis_tasks)
        
        # 計算質量評分
        quality_scores = {}
        total_quality = 0
        
        for analysis in analyses:
            quality_scores[analysis.speaker] = analysis.overall_quality
            total_quality += analysis.overall_quality
        
        average_quality = total_quality / len(analyses) if analyses else 0.5
        
        # 計算參與度（基於論證長度和參與者數）
        total_words = sum(analysis.word_count for analysis in analyses)
        participant_count = len(set(analysis.speaker for analysis in analyses))
        engagement_level = min(1.0, (total_words / len(analyses)) / 100) if analyses else 0.5
        
        # 計算新穎度（與之前輪次的相似度）
        novelty_score = await self._calculate_novelty(analyses, round_number)
        
        # 計算深度評分（基於證據數量和論證複雜度）
        depth_score = await self._calculate_depth(analyses)
        
        # 計算收斂度（論證之間的相似性增加表示收斂）
        convergence_score = await self._calculate_convergence(analyses, round_number)
        
        # 計算已用時間
        start_time = debate_context.get('start_time', datetime.now())
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        time_elapsed = (datetime.now() - start_time).total_seconds()
        
        metrics = RoundMetrics(
            round_number=round_number,
            quality_scores=quality_scores,
            average_quality=average_quality,
            engagement_level=engagement_level,
            novelty_score=novelty_score,
            depth_score=depth_score,
            convergence_score=convergence_score,
            time_elapsed=time_elapsed
        )
        
        # 更新趨勢
        self._update_trends(metrics)
        
        return metrics
    
    async def _calculate_novelty(self, current_analyses: List[ArgumentAnalysis], round_number: int) -> float:
        """計算新穎度評分"""
        
        if round_number <= 1 or not self.round_history:
            return 0.8  # 第一輪認為是新穎的
        
        # 提取當前輪次的關鍵詞
        current_words = set()
        for analysis in current_analyses:
            words = analysis.content.lower().split()
            current_words.update(words)
        
        # 計算與之前輪次的重疊度
        overlap_scores = []
        
        for prev_metrics in self.round_history[-3:]:  # 檢查最近3輪
            # 這裡簡化處理，實際應該從歷史數據中獲取詞彙
            # 暫時使用模擬數據
            prev_overlap = len(current_words) * 0.3  # 假設30%重疊
            overlap_score = 1.0 - (prev_overlap / len(current_words)) if current_words else 0.5
            overlap_scores.append(overlap_score)
        
        return sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.7
    
    async def _calculate_depth(self, analyses: List[ArgumentAnalysis]) -> float:
        """計算深度評分"""
        
        if not analyses:
            return 0.5
        
        total_evidence = sum(len(analysis.supporting_evidence) for analysis in analyses)
        total_claims = sum(len(analysis.main_claims) for analysis in analyses)
        avg_sentence_count = sum(analysis.sentence_count for analysis in analyses) / len(analyses)
        
        # 深度評分基於證據數量、論點數量和論證長度
        evidence_score = min(1.0, total_evidence / (len(analyses) * 2))  # 每個論證期望2個證據
        claim_score = min(1.0, total_claims / len(analyses))              # 每個論證期望1個主要論點
        length_score = min(1.0, avg_sentence_count / 8)                   # 期望8句話
        
        depth_score = (evidence_score * 0.4 + claim_score * 0.3 + length_score * 0.3)
        return depth_score
    
    async def _calculate_convergence(self, current_analyses: List[ArgumentAnalysis], round_number: int) -> float:
        """計算收斂度評分"""
        
        if round_number <= 2 or not self.round_history:
            return 0.3  # 早期輪次收斂度較低
        
        # 分析論證的相似性趨勢
        current_quality_variance = 0
        if len(current_analyses) > 1:
            qualities = [analysis.overall_quality for analysis in current_analyses]
            avg_quality = sum(qualities) / len(qualities)
            current_quality_variance = sum((q - avg_quality) ** 2 for q in qualities) / len(qualities)
        
        # 與之前輪次比較方差變化
        if len(self.round_history) >= 2:
            prev_variance = 0.3  # 簡化：使用默認值
            convergence = max(0, 1.0 - current_quality_variance / (prev_variance + 0.1))
        else:
            convergence = 0.3
        
        return min(1.0, convergence)
    
    def _update_trends(self, metrics: RoundMetrics):
        """更新趨勢數據"""
        
        # 更新質量趨勢
        metrics.quality_trend = [m.average_quality for m in self.round_history[-5:]]
        metrics.quality_trend.append(metrics.average_quality)
        
        # 更新參與度趨勢
        metrics.engagement_trend = [m.engagement_level for m in self.round_history[-5:]]
        metrics.engagement_trend.append(metrics.engagement_level)
        
        # 更新新穎度趨勢
        metrics.novelty_trend = [m.novelty_score for m in self.round_history[-5:]]
        metrics.novelty_trend.append(metrics.novelty_score)
    
    async def _collect_evaluation_factors(
        self,
        current_round: int,
        planned_total_rounds: int,
        metrics: RoundMetrics,
        debate_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集評估因素"""
        
        factors = {
            # 基本指標
            'current_round': current_round,
            'planned_rounds': planned_total_rounds,
            'remaining_rounds': planned_total_rounds - current_round,
            
            # 質量因素
            'average_quality': metrics.average_quality,
            'quality_below_threshold': metrics.average_quality < self.quality_threshold,
            'quality_trend': self._calculate_trend(metrics.quality_trend),
            
            # 參與度因素
            'engagement_level': metrics.engagement_level,
            'engagement_below_threshold': metrics.engagement_level < self.engagement_threshold,
            'engagement_trend': self._calculate_trend(metrics.engagement_trend),
            
            # 新穎度因素
            'novelty_score': metrics.novelty_score,
            'novelty_below_threshold': metrics.novelty_score < self.novelty_threshold,
            'novelty_trend': self._calculate_trend(metrics.novelty_trend),
            
            # 收斂度因素
            'convergence_score': metrics.convergence_score,
            'high_convergence': metrics.convergence_score > self.convergence_threshold,
            
            # 時間因素
            'time_elapsed': metrics.time_elapsed,
            'time_per_round': metrics.time_elapsed / current_round if current_round > 0 else 0,
            'approaching_time_limit': metrics.time_elapsed > self.max_debate_time * 0.8,
            'exceeded_time_limit': metrics.time_elapsed > self.max_debate_time,
            
            # 深度因素
            'depth_score': metrics.depth_score,
            'insufficient_depth': metrics.depth_score < 0.5,
            
            # 結構因素
            'at_minimum_rounds': current_round >= self.min_rounds,
            'approaching_maximum': current_round >= self.max_rounds - 1,
            'at_maximum_rounds': current_round >= self.max_rounds
        }
        
        return factors
    
    def _calculate_trend(self, trend_data: List[float]) -> float:
        """計算趨勢（正數表示上升，負數表示下降）"""
        if len(trend_data) < 2:
            return 0.0
        
        # 簡單線性趨勢
        x = list(range(len(trend_data)))
        y = trend_data
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    async def _make_adjustment_decision(
        self,
        factors: Dict[str, Any],
        current_round: int,
        planned_total_rounds: int
    ) -> AdjustmentDecision:
        """基於評估因素做出調整決策"""
        
        reasons = []
        decision = RoundDecision.CONTINUE_NORMAL
        target_rounds = planned_total_rounds
        confidence = 0.5
        expected_improvement = 0.0
        
        # 強制終止條件
        if factors['exceeded_time_limit']:
            decision = RoundDecision.TERMINATE_EARLY
            reasons.append(RoundAdjustmentReason.TIME_CONSTRAINT)
            confidence = 0.95
            return AdjustmentDecision(
                decision=decision,
                target_rounds=current_round,
                reasons=reasons,
                confidence=confidence,
                expected_improvement=0.0,
                alternative_actions=["保存當前進度", "生成摘要報告"]
            )
        
        if factors['at_maximum_rounds']:
            decision = RoundDecision.TERMINATE_EARLY
            reasons.append(RoundAdjustmentReason.TIME_CONSTRAINT)
            confidence = 0.9
            return AdjustmentDecision(
                decision=decision,
                target_rounds=current_round,
                reasons=reasons,
                confidence=confidence,
                expected_improvement=0.0,
                alternative_actions=["進入總結階段"]
            )
        
        # 評估是否需要延長
        extend_score = 0.0
        reduce_score = 0.0
        continue_score = 0.5
        
        # 質量因素
        if factors['quality_below_threshold'] and factors['quality_trend'] < 0:
            extend_score += 0.3
            reasons.append(RoundAdjustmentReason.QUALITY_INSUFFICIENT)
        elif factors['average_quality'] > 0.8 and factors['quality_trend'] > 0:
            extend_score += 0.2
            reasons.append(RoundAdjustmentReason.ARGUMENTS_STRONG)
        
        # 深度因素
        if factors['insufficient_depth']:
            extend_score += 0.2
            reasons.append(RoundAdjustmentReason.DEPTH_LACKING)
        
        # 新穎度因素
        if factors['novelty_below_threshold'] and factors['novelty_trend'] < -0.1:
            reduce_score += 0.3
            reasons.append(RoundAdjustmentReason.REPETITIVE_CONTENT)
        elif factors['novelty_score'] > 0.7:
            extend_score += 0.1
        
        # 收斂度因素
        if factors['high_convergence']:
            reduce_score += 0.2
            reasons.append(RoundAdjustmentReason.CONSENSUS_REACHED)
        
        # 參與度因素
        if factors['engagement_below_threshold'] and factors['engagement_trend'] < -0.1:
            reduce_score += 0.2
            reasons.append(RoundAdjustmentReason.PARTICIPANT_FATIGUE)
        
        # 時間因素
        if factors['approaching_time_limit']:
            reduce_score += 0.3
            reasons.append(RoundAdjustmentReason.TIME_CONSTRAINT)
        
        # 決策邏輯
        if extend_score > max(reduce_score, continue_score) and factors['at_minimum_rounds']:
            if not factors['approaching_maximum']:
                decision = RoundDecision.EXTEND_ROUNDS
                target_rounds = min(self.max_rounds, planned_total_rounds + 2)
                confidence = min(0.9, 0.5 + extend_score)
                expected_improvement = extend_score * 0.3
            else:
                decision = RoundDecision.CONTINUE_NORMAL
                confidence = 0.7
        
        elif reduce_score > max(extend_score, continue_score) and factors['at_minimum_rounds']:
            decision = RoundDecision.REDUCE_ROUNDS
            target_rounds = max(current_round + 1, factors['remaining_rounds'] - 1)
            confidence = min(0.9, 0.5 + reduce_score)
        
        else:
            decision = RoundDecision.CONTINUE_NORMAL
            confidence = 0.5 + continue_score * 0.4
        
        # 特殊情況處理
        alternative_actions = []
        if factors['quality_below_threshold']:
            alternative_actions.append("考慮更換模型")
            alternative_actions.append("調整辯論策略")
        
        if factors['novelty_below_threshold']:
            alternative_actions.append("引入新的角度")
            alternative_actions.append("提供額外資料")
        
        adjustment_parameters = {
            'quality_threshold': self.quality_threshold,
            'engagement_threshold': self.engagement_threshold,
            'time_per_round_target': self.target_round_time
        }
        
        monitoring_thresholds = {
            'min_quality': 0.4,
            'min_engagement': 0.3,
            'max_time_per_round': self.target_round_time * 1.5
        }
        
        return AdjustmentDecision(
            decision=decision,
            target_rounds=target_rounds,
            reasons=reasons,
            confidence=confidence,
            expected_improvement=expected_improvement,
            alternative_actions=alternative_actions,
            adjustment_parameters=adjustment_parameters,
            monitoring_thresholds=monitoring_thresholds
        )
    
    def get_round_recommendations(self, current_metrics: RoundMetrics) -> List[str]:
        """獲取輪次改進建議"""
        
        recommendations = []
        
        if current_metrics.average_quality < self.quality_threshold:
            recommendations.append("建議參與者提供更多具體證據和例證")
            recommendations.append("加強論證的邏輯結構")
        
        if current_metrics.engagement_level < self.engagement_threshold:
            recommendations.append("鼓勵更詳細的論述")
            recommendations.append("引入更具爭議性的觀點")
        
        if current_metrics.novelty_score < self.novelty_threshold:
            recommendations.append("探索新的論證角度")
            recommendations.append("避免重複之前的觀點")
        
        if current_metrics.depth_score < 0.5:
            recommendations.append("深入分析核心議題")
            recommendations.append("提供更多背景資訊")
        
        return recommendations
    
    def reset_round_data(self):
        """重置輪次數據"""
        self.round_history.clear()
        self.adjustment_history.clear()
        logger.info("Round adjustment data reset")
    
    def get_adjustment_summary(self) -> Dict[str, Any]:
        """獲取調整摘要"""
        
        if not self.round_history:
            return {"message": "No round data available"}
        
        latest_metrics = self.round_history[-1]
        
        return {
            "total_rounds_analyzed": len(self.round_history),
            "total_adjustments_made": len(self.adjustment_history),
            "current_round": latest_metrics.round_number,
            "latest_quality": latest_metrics.average_quality,
            "latest_engagement": latest_metrics.engagement_level,
            "latest_novelty": latest_metrics.novelty_score,
            "quality_trend": self._calculate_trend(latest_metrics.quality_trend),
            "recommendations": self.get_round_recommendations(latest_metrics),
            "adjustment_reasons": [
                reason.value for decision in self.adjustment_history 
                for reason in decision.reasons
            ]
        }


# 全局自適應輪次管理器實例
round_manager = None

def get_round_manager() -> AdaptiveRoundManager:
    """獲取自適應輪次管理器實例"""
    global round_manager
    if round_manager is None:
        round_manager = AdaptiveRoundManager()
    return round_manager
