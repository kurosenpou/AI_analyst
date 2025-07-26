"""
Advanced AI Judge System Implementation
Task 2.3.4: Advanced AI Judge System

Features:
- Multi-perspective evaluation
- Dynamic scoring system
- Specialized assessment
- Bias detection and correction
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json

from .openrouter_client import get_openrouter_client
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class EvaluationPerspective(Enum):
    """評估視角"""
    LOGICAL = "logical"                 # 邏輯視角
    RHETORICAL = "rhetorical"          # 修辭視角
    FACTUAL = "factual"                # 事實視角
    ETHICAL = "ethical"                # 倫理視角
    PRACTICAL = "practical"            # 實用視角
    EMOTIONAL = "emotional"            # 情感視角
    CULTURAL = "cultural"              # 文化視角
    LEGAL = "legal"                    # 法律視角


class BiasType(Enum):
    """偏見類型"""
    CONFIRMATION_BIAS = "confirmation_bias"         # 確認偏誤
    ANCHORING_BIAS = "anchoring_bias"              # 錨定偏誤
    AVAILABILITY_BIAS = "availability_bias"         # 可得性偏誤
    REPRESENTATIVENESS_BIAS = "representativeness_bias"  # 代表性偏誤
    RECENCY_BIAS = "recency_bias"                  # 近因偏誤
    AUTHORITY_BIAS = "authority_bias"              # 權威偏誤
    CULTURAL_BIAS = "cultural_bias"                # 文化偏誤
    GENDER_BIAS = "gender_bias"                    # 性別偏誤


class JudgmentCriteria(Enum):
    """判決標準"""
    ARGUMENT_STRENGTH = "argument_strength"         # 論證強度
    EVIDENCE_QUALITY = "evidence_quality"          # 證據質量
    LOGICAL_CONSISTENCY = "logical_consistency"     # 邏輯一致性
    PERSUASIVENESS = "persuasiveness"              # 說服力
    RELEVANCE = "relevance"                        # 相關性
    ORIGINALITY = "originality"                    # 原創性
    CLARITY = "clarity"                            # 清晰度
    COMPLETENESS = "completeness"                  # 完整性


@dataclass
class PerspectiveEvaluation:
    """視角評估"""
    perspective: EvaluationPerspective
    score: float                        # 評分 (0-1)
    reasoning: str                      # 評分理由
    key_observations: List[str] = field(default_factory=list)  # 關鍵觀察
    strengths: List[str] = field(default_factory=list)         # 優勢
    weaknesses: List[str] = field(default_factory=list)        # 劣勢
    confidence: float = 0.0             # 信心度
    
    def add_observation(self, observation: str):
        """添加觀察"""
        if observation not in self.key_observations:
            self.key_observations.append(observation)
    
    def add_strength(self, strength: str):
        """添加優勢"""
        if strength not in self.strengths:
            self.strengths.append(strength)
    
    def add_weakness(self, weakness: str):
        """添加劣勢"""
        if weakness not in self.weaknesses:
            self.weaknesses.append(weakness)


@dataclass
class BiasDetection:
    """偏見檢測"""
    bias_type: BiasType
    severity: float                     # 嚴重程度 (0-1)
    description: str                    # 描述
    evidence: List[str] = field(default_factory=list)  # 證據
    correction_suggestion: str = ""     # 糾正建議
    
    def add_evidence(self, evidence_item: str):
        """添加證據"""
        if evidence_item not in self.evidence:
            self.evidence.append(evidence_item)


@dataclass
class DynamicScore:
    """動態評分"""
    criteria: JudgmentCriteria
    base_score: float                   # 基礎分數
    adjustments: List[Dict[str, Any]] = field(default_factory=list)  # 調整項
    final_score: float = 0.0           # 最終分數
    weight: float = 1.0                # 權重
    explanation: str = ""              # 解釋
    
    def add_adjustment(self, reason: str, value: float, description: str = ""):
        """添加調整"""
        adjustment = {
            "reason": reason,
            "value": value,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.adjustments.append(adjustment)
        self._recalculate_final_score()
    
    def _recalculate_final_score(self):
        """重新計算最終分數"""
        adjustment_sum = sum(adj["value"] for adj in self.adjustments)
        self.final_score = max(0.0, min(1.0, self.base_score + adjustment_sum))


@dataclass
class AdvancedJudgment:
    """高級判決"""
    judgment_id: str
    debate_id: str
    topic: str
    
    # 多視角評估
    perspective_evaluations: List[PerspectiveEvaluation] = field(default_factory=list)
    
    # 動態評分
    dynamic_scores: Dict[str, Dict[JudgmentCriteria, DynamicScore]] = field(default_factory=dict)  # participant -> scores
    
    # 偏見檢測
    detected_biases: List[BiasDetection] = field(default_factory=list)
    
    # 綜合判決
    winner: Optional[str] = None        # 獲勝者
    winning_margin: float = 0.0         # 獲勝優勢
    overall_quality: float = 0.0        # 整體質量
    
    # 詳細分析
    key_turning_points: List[str] = field(default_factory=list)  # 關鍵轉折點
    missed_opportunities: List[str] = field(default_factory=list)  # 錯失機會
    improvement_suggestions: Dict[str, List[str]] = field(default_factory=dict)  # 改進建議
    
    # 元數據
    judgment_confidence: float = 0.0    # 判決信心度
    evaluation_time: float = 0.0        # 評估時間
    generated_at: datetime = field(default_factory=datetime.now)
    
    def add_perspective_evaluation(self, evaluation: PerspectiveEvaluation):
        """添加視角評估"""
        self.perspective_evaluations.append(evaluation)
    
    def add_bias_detection(self, bias: BiasDetection):
        """添加偏見檢測"""
        self.detected_biases.append(bias)
    
    def set_dynamic_score(self, participant: str, scores: Dict[JudgmentCriteria, DynamicScore]):
        """設置動態評分"""
        self.dynamic_scores[participant] = scores


class MultiPerspectiveAnalyzer:
    """多視角分析器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def analyze_from_perspective(
        self,
        perspective: EvaluationPerspective,
        debate_content: str,
        participants: List[str]
    ) -> PerspectiveEvaluation:
        """從特定視角分析辯論"""
        try:
            # 構建視角分析提示
            perspective_prompts = {
                EvaluationPerspective.LOGICAL: "從邏輯推理的角度分析辯論的嚴謹性和一致性",
                EvaluationPerspective.RHETORICAL: "從修辭技巧的角度分析辯論的說服力和表達效果",
                EvaluationPerspective.FACTUAL: "從事實準確性的角度分析辯論中證據和數據的可靠性",
                EvaluationPerspective.ETHICAL: "從倫理道德的角度分析辯論中的價值觀和原則",
                EvaluationPerspective.PRACTICAL: "從實用性的角度分析辯論中方案的可行性和效果",
                EvaluationPerspective.EMOTIONAL: "從情感共鳴的角度分析辯論的感染力和影響力",
                EvaluationPerspective.CULTURAL: "從文化背景的角度分析辯論的適切性和包容性",
                EvaluationPerspective.LEGAL: "從法律規範的角度分析辯論的合規性和權威性"
            }
            
            analysis_prompt = f"""
            請{perspective_prompts.get(perspective, '分析')}以下辯論：

            參與者：{', '.join(participants)}
            辯論內容：
            {debate_content}

            請提供：
            1. score: 整體評分 (0-1)
            2. reasoning: 評分理由
            3. key_observations: 3-5個關鍵觀察
            4. strengths: 發現的優勢
            5. weaknesses: 發現的劣勢
            6. confidence: 評估信心度 (0-1)

            請以JSON格式回應：
            {{
                "score": 0.8,
                "reasoning": "評分理由",
                "key_observations": ["觀察1", "觀察2"],
                "strengths": ["優勢1", "優勢2"],
                "weaknesses": ["劣勢1", "劣勢2"],
                "confidence": 0.9
            }}
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            try:
                analysis_data = json.loads(response)
                
                evaluation = PerspectiveEvaluation(
                    perspective=perspective,
                    score=analysis_data.get("score", 0.5),
                    reasoning=analysis_data.get("reasoning", ""),
                    key_observations=analysis_data.get("key_observations", []),
                    strengths=analysis_data.get("strengths", []),
                    weaknesses=analysis_data.get("weaknesses", []),
                    confidence=analysis_data.get("confidence", 0.5)
                )
                
                return evaluation
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse {perspective.value} analysis response")
                return self._create_default_evaluation(perspective)
                
        except Exception as e:
            logger.error(f"Error analyzing from {perspective.value} perspective: {e}")
            return self._create_default_evaluation(perspective)
    
    def _create_default_evaluation(self, perspective: EvaluationPerspective) -> PerspectiveEvaluation:
        """創建默認評估"""
        return PerspectiveEvaluation(
            perspective=perspective,
            score=0.5,
            reasoning="分析過程中出現錯誤",
            confidence=0.3
        )
    
    async def analyze_all_perspectives(
        self,
        debate_content: str,
        participants: List[str],
        selected_perspectives: Optional[List[EvaluationPerspective]] = None
    ) -> List[PerspectiveEvaluation]:
        """從所有視角分析辯論"""
        if selected_perspectives is None:
            selected_perspectives = list(EvaluationPerspective)
        
        evaluations = []
        
        # 並行分析多個視角
        tasks = [
            self.analyze_from_perspective(perspective, debate_content, participants)
            for perspective in selected_perspectives
        ]
        
        try:
            evaluations = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 過濾異常結果
            valid_evaluations = [
                eval for eval in evaluations 
                if isinstance(eval, PerspectiveEvaluation)
            ]
            
            # 記錄分析指標
            record_metric("perspective_analyses_completed", len(valid_evaluations), {
                "total_perspectives": str(len(selected_perspectives)),
                "participants_count": str(len(participants))
            })
            
            return valid_evaluations
            
        except Exception as e:
            logger.error(f"Error in multi-perspective analysis: {e}")
            return []


class DynamicScoringSystem:
    """動態評分系統"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
        self.base_weights = {
            JudgmentCriteria.ARGUMENT_STRENGTH: 0.20,
            JudgmentCriteria.EVIDENCE_QUALITY: 0.18,
            JudgmentCriteria.LOGICAL_CONSISTENCY: 0.15,
            JudgmentCriteria.PERSUASIVENESS: 0.12,
            JudgmentCriteria.RELEVANCE: 0.10,
            JudgmentCriteria.ORIGINALITY: 0.08,
            JudgmentCriteria.CLARITY: 0.10,
            JudgmentCriteria.COMPLETENESS: 0.07
        }
    
    async def calculate_dynamic_scores(
        self,
        participant: str,
        arguments: List[str],
        context: Dict[str, Any]
    ) -> Dict[JudgmentCriteria, DynamicScore]:
        """計算動態評分"""
        scores = {}
        
        try:
            for criteria in JudgmentCriteria:
                base_score = await self._calculate_base_score(
                    criteria, participant, arguments, context
                )
                
                dynamic_score = DynamicScore(
                    criteria=criteria,
                    base_score=base_score,
                    weight=self.base_weights.get(criteria, 0.1)
                )
                
                # 應用上下文調整
                await self._apply_contextual_adjustments(
                    dynamic_score, context
                )
                
                scores[criteria] = dynamic_score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating dynamic scores for {participant}: {e}")
            return self._create_default_scores()
    
    async def _calculate_base_score(
        self,
        criteria: JudgmentCriteria,
        participant: str,
        arguments: List[str],
        context: Dict[str, Any]
    ) -> float:
        """計算基礎分數"""
        try:
            # 構建評分提示
            criteria_descriptions = {
                JudgmentCriteria.ARGUMENT_STRENGTH: "論證的邏輯強度和說服力",
                JudgmentCriteria.EVIDENCE_QUALITY: "證據的可信度和相關性",
                JudgmentCriteria.LOGICAL_CONSISTENCY: "邏輯推理的一致性和嚴謹性",
                JudgmentCriteria.PERSUASIVENESS: "論證的說服效果和影響力",
                JudgmentCriteria.RELEVANCE: "論證與主題的相關程度",
                JudgmentCriteria.ORIGINALITY: "觀點的新穎性和創新性",
                JudgmentCriteria.CLARITY: "表達的清晰度和易理解性",
                JudgmentCriteria.COMPLETENESS: "論證的完整性和全面性"
            }
            
            arguments_text = "\n".join(arguments)
            
            scoring_prompt = f"""
            請評估{participant}在{criteria_descriptions[criteria]}方面的表現：

            論證內容：
            {arguments_text}

            請給出0-1之間的分數，並簡要說明理由。

            請以JSON格式回應：
            {{
                "score": 0.8,
                "explanation": "評分理由"
            }}
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": scoring_prompt}],
                max_tokens=200,
                temperature=0.2
            )
            
            try:
                score_data = json.loads(response)
                return score_data.get("score", 0.5)
            except json.JSONDecodeError:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating base score for {criteria.value}: {e}")
            return 0.5
    
    async def _apply_contextual_adjustments(
        self,
        dynamic_score: DynamicScore,
        context: Dict[str, Any]
    ):
        """應用上下文調整"""
        try:
            # 基於辯論階段的調整
            debate_phase = context.get("phase", "")
            if debate_phase == "opening" and dynamic_score.criteria == JudgmentCriteria.CLARITY:
                dynamic_score.add_adjustment("opening_clarity_bonus", 0.1, "開場陳述清晰度加分")
            
            # 基於輪次的調整
            round_number = context.get("round", 1)
            if round_number > 3 and dynamic_score.criteria == JudgmentCriteria.ORIGINALITY:
                dynamic_score.add_adjustment("late_round_originality", 0.05, "後期輪次創新性加分")
            
            # 基於對手表現的調整
            opponent_strength = context.get("opponent_avg_score", 0.5)
            if opponent_strength > 0.8 and dynamic_score.criteria == JudgmentCriteria.ARGUMENT_STRENGTH:
                dynamic_score.add_adjustment("strong_opponent_bonus", 0.05, "面對強對手的加分")
            
            # 基於辯論質量的調整
            overall_quality = context.get("debate_quality", 0.5)
            if overall_quality > 0.8:
                dynamic_score.add_adjustment("high_quality_debate", 0.02, "高質量辯論環境加分")
            
        except Exception as e:
            logger.error(f"Error applying contextual adjustments: {e}")
    
    def _create_default_scores(self) -> Dict[JudgmentCriteria, DynamicScore]:
        """創建默認評分"""
        scores = {}
        for criteria in JudgmentCriteria:
            scores[criteria] = DynamicScore(
                criteria=criteria,
                base_score=0.5,
                final_score=0.5,
                weight=self.base_weights.get(criteria, 0.1),
                explanation="評分過程中出現錯誤"
            )
        return scores
    
    def calculate_weighted_total(
        self,
        scores: Dict[JudgmentCriteria, DynamicScore]
    ) -> float:
        """計算加權總分"""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for criteria, score in scores.items():
                total_score += score.final_score * score.weight
                total_weight += score.weight
            
            return total_score / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating weighted total: {e}")
            return 0.5


class SpecializedEvaluator:
    """專業化評估器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def detect_biases(
        self,
        debate_content: str,
        participants: List[str]
    ) -> List[BiasDetection]:
        """檢測偏見"""
        try:
            bias_prompt = f"""
            請檢測以下辯論中可能存在的認知偏見：

            參與者：{', '.join(participants)}
            辯論內容：
            {debate_content}

            請識別以下類型的偏見：
            - confirmation_bias: 確認偏誤
            - anchoring_bias: 錨定偏誤
            - availability_bias: 可得性偏誤
            - representativeness_bias: 代表性偏誤
            - recency_bias: 近因偏誤
            - authority_bias: 權威偏誤
            - cultural_bias: 文化偏誤
            - gender_bias: 性別偏誤

            對於每個檢測到的偏見，請提供：
            - bias_type: 偏見類型
            - severity: 嚴重程度 (0-1)
            - description: 描述
            - evidence: 支持證據
            - correction_suggestion: 糾正建議

            請以JSON格式回應：
            [
                {{
                    "bias_type": "confirmation_bias",
                    "severity": 0.7,
                    "description": "偏見描述",
                    "evidence": ["證據1", "證據2"],
                    "correction_suggestion": "糾正建議"
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": bias_prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                bias_data = json.loads(response)
                biases = []
                
                for item in bias_data:
                    # 解析偏見類型
                    bias_type = BiasType.CONFIRMATION_BIAS  # 默認
                    try:
                        bias_type = BiasType(item.get("bias_type", "confirmation_bias"))
                    except ValueError:
                        continue
                    
                    bias = BiasDetection(
                        bias_type=bias_type,
                        severity=item.get("severity", 0.5),
                        description=item.get("description", ""),
                        evidence=item.get("evidence", []),
                        correction_suggestion=item.get("correction_suggestion", "")
                    )
                    
                    biases.append(bias)
                
                # 記錄偏見檢測指標
                record_metric("biases_detected", len(biases), {
                    "participants_count": str(len(participants)),
                    "avg_severity": str(sum(b.severity for b in biases) / len(biases)) if biases else "0"
                })
                
                return biases
                
            except json.JSONDecodeError:
                logger.error("Failed to parse bias detection response")
                return []
                
        except Exception as e:
            logger.error(f"Error detecting biases: {e}")
            return []
    
    async def identify_turning_points(
        self,
        debate_content: str,
        participants: List[str]
    ) -> List[str]:
        """識別關鍵轉折點"""
        try:
            turning_point_prompt = f"""
            請識別以下辯論中的關鍵轉折點：

            參與者：{', '.join(participants)}
            辯論內容：
            {debate_content}

            請識別3-5個關鍵轉折點，這些轉折點可能包括：
            - 強有力的論證或反駁
            - 重要證據的提出
            - 立場的重大轉變
            - 關鍵概念的澄清
            - 情感或氣氛的轉變

            請以JSON列表格式回應：
            ["轉折點1描述", "轉折點2描述", "轉折點3描述"]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": turning_point_prompt}],
                max_tokens=400,
                temperature=0.4
            )
            
            try:
                turning_points = json.loads(response)
                return turning_points if isinstance(turning_points, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Error identifying turning points: {e}")
            return []
    
    async def generate_improvement_suggestions(
        self,
        participant: str,
        arguments: List[str],
        weaknesses: List[str]
    ) -> List[str]:
        """生成改進建議"""
        try:
            arguments_text = "\n".join(arguments)
            weaknesses_text = "\n".join(weaknesses)
            
            improvement_prompt = f"""
            基於{participant}的表現和發現的弱點，請生成具體的改進建議：

            論證內容：
            {arguments_text}

            發現的弱點：
            {weaknesses_text}

            請提供3-5個具體、可操作的改進建議。

            請以JSON列表格式回應：
            ["建議1", "建議2", "建議3"]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": improvement_prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            try:
                suggestions = json.loads(response)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
            return []


class AdvancedJudgeEngine:
    """高級裁判引擎"""
    
    def __init__(self):
        self.perspective_analyzer = MultiPerspectiveAnalyzer()
        self.scoring_system = DynamicScoringSystem()
        self.specialized_evaluator = SpecializedEvaluator()
        
        # 判決歷史
        self.judgment_history: Dict[str, AdvancedJudgment] = {}
        
        logger.info("Advanced judge engine initialized")
    
    async def conduct_advanced_judgment(
        self,
        debate_id: str,
        topic: str,
        participants: List[str],
        debate_content: str,
        participant_arguments: Dict[str, List[str]],
        context: Optional[Dict[str, Any]] = None
    ) -> AdvancedJudgment:
        """進行高級判決"""
        judgment_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            if context is None:
                context = {}
            
            # 1. 多視角分析
            perspective_evaluations = await self.perspective_analyzer.analyze_all_perspectives(
                debate_content, participants
            )
            
            # 2. 動態評分
            dynamic_scores = {}
            for participant in participants:
                participant_args = participant_arguments.get(participant, [])
                scores = await self.scoring_system.calculate_dynamic_scores(
                    participant, participant_args, context
                )
                dynamic_scores[participant] = scores
            
            # 3. 偏見檢測
            detected_biases = await self.specialized_evaluator.detect_biases(
                debate_content, participants
            )
            
            # 4. 識別轉折點
            turning_points = await self.specialized_evaluator.identify_turning_points(
                debate_content, participants
            )
            
            # 5. 計算綜合結果
            winner, winning_margin = self._determine_winner(dynamic_scores)
            overall_quality = self._calculate_overall_quality(
                perspective_evaluations, dynamic_scores
            )
            
            # 6. 生成改進建議
            improvement_suggestions = {}
            for participant in participants:
                # 收集該參與者的弱點
                weaknesses = []
                for eval in perspective_evaluations:
                    weaknesses.extend(eval.weaknesses)
                
                suggestions = await self.specialized_evaluator.generate_improvement_suggestions(
                    participant, participant_arguments.get(participant, []), weaknesses
                )
                improvement_suggestions[participant] = suggestions
            
            # 7. 創建判決
            evaluation_time = (datetime.now() - start_time).total_seconds()
            
            judgment = AdvancedJudgment(
                judgment_id=judgment_id,
                debate_id=debate_id,
                topic=topic,
                perspective_evaluations=perspective_evaluations,
                dynamic_scores=dynamic_scores,
                detected_biases=detected_biases,
                winner=winner,
                winning_margin=winning_margin,
                overall_quality=overall_quality,
                key_turning_points=turning_points,
                improvement_suggestions=improvement_suggestions,
                judgment_confidence=self._calculate_judgment_confidence(
                    perspective_evaluations, dynamic_scores, detected_biases
                ),
                evaluation_time=evaluation_time
            )
            
            # 存儲判決
            self.judgment_history[judgment_id] = judgment
            
            # 記錄判決指標
            record_metric("advanced_judgments_completed", 1, {
                "debate_id": debate_id[:8],
                "participants_count": str(len(participants)),
                "winner": winner or "tie",
                "overall_quality": str(round(overall_quality, 2)),
                "biases_detected": str(len(detected_biases))
            })
            
            logger.info(f"Completed advanced judgment {judgment_id}, winner: {winner}, quality: {overall_quality:.2f}")
            
            return judgment
            
        except Exception as e:
            logger.error(f"Error conducting advanced judgment: {e}")
            return self._create_default_judgment(judgment_id, debate_id, topic, participants)
    
    def _determine_winner(
        self,
        dynamic_scores: Dict[str, Dict[JudgmentCriteria, DynamicScore]]
    ) -> Tuple[Optional[str], float]:
        """確定獲勝者"""
        try:
            participant_totals = {}
            
            for participant, scores in dynamic_scores.items():
                total_score = self.scoring_system.calculate_weighted_total(scores)
                participant_totals[participant] = total_score
            
            if not participant_totals:
                return None, 0.0
            
            # 找到最高分參與者
            sorted_participants = sorted(
                participant_totals.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            if len(sorted_participants) < 2:
                return sorted_participants[0][0], 0.0
            
            winner = sorted_participants[0][0]
            winner_score = sorted_participants[0][1]
            runner_up_score = sorted_participants[1][1]
            
            # 計算獲勝優勢
            winning_margin = winner_score - runner_up_score
            
            # 如果差距太小，視為平局
            if winning_margin < 0.05:
                return None, 0.0
            
            return winner, winning_margin
            
        except Exception as e:
            logger.error(f"Error determining winner: {e}")
            return None, 0.0
    
    def _calculate_overall_quality(
        self,
        perspective_evaluations: List[PerspectiveEvaluation],
        dynamic_scores: Dict[str, Dict[JudgmentCriteria, DynamicScore]]
    ) -> float:
        """計算整體質量"""
        try:
            quality_factors = []
            
            # 視角評估平均分
            if perspective_evaluations:
                avg_perspective_score = sum(eval.score for eval in perspective_evaluations) / len(perspective_evaluations)
                quality_factors.append(avg_perspective_score)
            
            # 參與者平均分
            if dynamic_scores:
                all_participant_scores = []
                for participant, scores in dynamic_scores.items():
                    participant_total = self.scoring_system.calculate_weighted_total(scores)
                    all_participant_scores.append(participant_total)
                
                if all_participant_scores:
                    avg_participant_score = sum(all_participant_scores) / len(all_participant_scores)
                    quality_factors.append(avg_participant_score)
            
            # 計算整體質量
            if quality_factors:
                return sum(quality_factors) / len(quality_factors)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating overall quality: {e}")
            return 0.5
    
    def _calculate_judgment_confidence(
        self,
        perspective_evaluations: List[PerspectiveEvaluation],
        dynamic_scores: Dict[str, Dict[JudgmentCriteria, DynamicScore]],
        detected_biases: List[BiasDetection]
    ) -> float:
        """計算判決信心度"""
        try:
            confidence_factors = []
            
            # 視角評估信心度
            if perspective_evaluations:
                avg_perspective_confidence = sum(eval.confidence for eval in perspective_evaluations) / len(perspective_evaluations)
                confidence_factors.append(avg_perspective_confidence)
            
            # 評分一致性
            if len(dynamic_scores) >= 2:
                participant_scores = []
                for participant, scores in dynamic_scores.items():
                    total_score = self.scoring_system.calculate_weighted_total(scores)
                    participant_scores.append(total_score)
                
                # 計算分數差異
                if len(participant_scores) >= 2:
                    score_range = max(participant_scores) - min(participant_scores)
                    consistency_factor = 1.0 - min(score_range, 1.0)  # 差異越小，一致性越高
                    confidence_factors.append(consistency_factor)
            
            # 偏見影響
            if detected_biases:
                avg_bias_severity = sum(bias.severity for bias in detected_biases) / len(detected_biases)
                bias_factor = 1.0 - avg_bias_severity  # 偏見越少，信心度越高
                confidence_factors.append(bias_factor)
            else:
                confidence_factors.append(1.0)  # 無偏見檢測到
            
            # 計算整體信心度
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating judgment confidence: {e}")
            return 0.5
    
    def _create_default_judgment(
        self,
        judgment_id: str,
        debate_id: str,
        topic: str,
        participants: List[str]
    ) -> AdvancedJudgment:
        """創建默認判決"""
        return AdvancedJudgment(
            judgment_id=judgment_id,
            debate_id=debate_id,
            topic=topic,
            overall_quality=0.5,
            judgment_confidence=0.3,
            evaluation_time=0.0,
            improvement_suggestions={participant: ["建議重新分析"] for participant in participants}
        )
    
    def get_judgment_history(self) -> List[AdvancedJudgment]:
        """獲取判決歷史"""
        return list(self.judgment_history.values())
    
    def get_judgment_summary(self) -> Dict[str, Any]:
        """獲取判決摘要"""
        try:
            if not self.judgment_history:
                return {"message": "No judgment history available"}
            
            judgments = list(self.judgment_history.values())
            
            # 基本統計
            total_judgments = len(judgments)
            avg_quality = sum(j.overall_quality for j in judgments) / total_judgments
            avg_confidence = sum(j.judgment_confidence for j in judgments) / total_judgments
            avg_evaluation_time = sum(j.evaluation_time for j in judgments) / total_judgments
            
            # 獲勝者統計
            winners = [j.winner for j in judgments if j.winner]
            winner_counts = {}
            for winner in winners:
                winner_counts[winner] = winner_counts.get(winner, 0) + 1
            
            # 偏見統計
            total_biases = sum(len(j.detected_biases) for j in judgments)
            bias_types = {}
            for judgment in judgments:
                for bias in judgment.detected_biases:
                    bias_type = bias.bias_type.value
                    bias_types[bias_type] = bias_types.get(bias_type, 0) + 1
            
            return {
                "total_judgments": total_judgments,
                "average_quality": avg_quality,
                "average_confidence": avg_confidence,
                "average_evaluation_time": avg_evaluation_time,
                "winner_distribution": winner_counts,
                "total_biases_detected": total_biases,
                "common_bias_types": sorted(bias_types.items(), key=lambda x: x[1], reverse=True)[:3],
                "analysis_period": {
                    "start": min(j.generated_at for j in judgments).isoformat(),
                    "end": max(j.generated_at for j in judgments).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating judgment summary: {e}")
            return {"error": str(e)}


# 全局高級裁判引擎實例
advanced_judge_engine = None

def get_advanced_judge_engine() -> AdvancedJudgeEngine:
    """獲取高級裁判引擎實例"""
    global advanced_judge_engine
    if advanced_judge_engine is None:
        advanced_judge_engine = AdvancedJudgeEngine()
    return advanced_judge_engine