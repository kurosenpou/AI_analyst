"""
Argument Strength Analysis System Implementation
Task 2.3.2: Argument Strength Analysis System

Features:
- Argument structure analysis
- Evidence evaluation
- Rebuttal effectiveness analysis
- Strength calculation
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import re

from .openrouter_client import get_openrouter_client
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """證據類型"""
    STATISTICAL = "statistical"         # 統計數據
    EXPERT_OPINION = "expert_opinion"   # 專家意見
    CASE_STUDY = "case_study"          # 案例研究
    RESEARCH = "research"              # 研究報告
    ANECDOTAL = "anecdotal"            # 軼事證據
    LOGICAL = "logical"                # 邏輯推理
    EMPIRICAL = "empirical"            # 經驗證據
    AUTHORITATIVE = "authoritative"     # 權威引用


class LogicalFallacy(Enum):
    """邏輯謬誤類型"""
    AD_HOMINEM = "ad_hominem"                    # 人身攻擊
    STRAW_MAN = "straw_man"                      # 稻草人謬誤
    FALSE_DICHOTOMY = "false_dichotomy"          # 假二分法
    SLIPPERY_SLOPE = "slippery_slope"            # 滑坡謬誤
    CIRCULAR_REASONING = "circular_reasoning"     # 循環論證
    APPEAL_TO_AUTHORITY = "appeal_to_authority"   # 訴諸權威
    HASTY_GENERALIZATION = "hasty_generalization" # 草率概括
    RED_HERRING = "red_herring"                  # 轉移話題
    NONE = "none"                                # 無謬誤


class RebuttalType(Enum):
    """反駁類型"""
    DIRECT_REFUTATION = "direct_refutation"     # 直接反駁
    COUNTER_EVIDENCE = "counter_evidence"       # 反證
    ALTERNATIVE_EXPLANATION = "alternative_explanation"  # 替代解釋
    QUESTIONING_ASSUMPTIONS = "questioning_assumptions"  # 質疑假設
    EXPOSING_FALLACY = "exposing_fallacy"       # 揭露謬誤
    REFRAMING = "reframing"                     # 重新框架
    PRECEDENT_CHALLENGE = "precedent_challenge"  # 先例挑戰


@dataclass
class ArgumentStructure:
    """論證結構"""
    id: str
    premises: List[str] = field(default_factory=list)      # 前提
    conclusions: List[str] = field(default_factory=list)   # 結論
    assumptions: List[str] = field(default_factory=list)   # 假設
    inferences: List[str] = field(default_factory=list)    # 推論
    
    # 結構評分
    clarity_score: float = 0.0          # 清晰度
    completeness_score: float = 0.0     # 完整性
    logical_flow_score: float = 0.0     # 邏輯流暢度
    
    # 檢測到的問題
    logical_gaps: List[str] = field(default_factory=list)
    weak_connections: List[str] = field(default_factory=list)


@dataclass
class EvidenceItem:
    """證據項目"""
    id: str
    content: str
    evidence_type: EvidenceType
    source: Optional[str] = None
    
    # 評估分數
    credibility_score: float = 0.0      # 可信度
    relevance_score: float = 0.0        # 相關性
    sufficiency_score: float = 0.0      # 充分性
    recency_score: float = 0.0          # 時效性
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RebuttalAnalysis:
    """反駁分析"""
    id: str
    target_argument_id: str
    rebuttal_type: RebuttalType
    attack_points: List[str] = field(default_factory=list)  # 攻擊點
    
    # 效力評分
    effectiveness_score: float = 0.0    # 有效性
    precision_score: float = 0.0        # 精確性
    impact_score: float = 0.0           # 影響力
    
    # 分析結果
    vulnerabilities_exposed: List[str] = field(default_factory=list)
    counter_strategies: List[str] = field(default_factory=list)


@dataclass
class ArgumentStrengthReport:
    """論證強度報告"""
    argument_id: str
    content: str
    speaker: str
    timestamp: datetime
    
    # 結構分析
    structure: ArgumentStructure
    
    # 證據分析
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    
    # 邏輯分析
    logical_fallacies: List[LogicalFallacy] = field(default_factory=list)
    logical_soundness_score: float = 0.0
    
    # 綜合評分
    overall_strength: float = 0.0
    confidence_level: float = 0.0
    
    # 改進建議
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # 生成時間
    generated_at: datetime = field(default_factory=datetime.now)


class ArgumentStructureAnalyzer:
    """論證結構分析器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def analyze_structure(self, content: str) -> ArgumentStructure:
        """分析論證結構"""
        structure_id = str(uuid.uuid4())
        
        try:
            # 構建結構分析提示
            analysis_prompt = f"""
            請分析以下論證的邏輯結構：

            論證內容：{content}

            請識別並提取：
            1. 前提 (premises) - 支持結論的基礎陳述
            2. 結論 (conclusions) - 論證要證明的主張
            3. 假設 (assumptions) - 隱含的前提條件
            4. 推論 (inferences) - 從前提到結論的推理步驟

            同時評估：
            - clarity_score: 結構清晰度 (0-1)
            - completeness_score: 結構完整性 (0-1)
            - logical_flow_score: 邏輯流暢度 (0-1)

            並識別：
            - logical_gaps: 邏輯缺口
            - weak_connections: 薄弱連接

            請以JSON格式回應：
            {{
                "premises": ["前提1", "前提2"],
                "conclusions": ["結論1"],
                "assumptions": ["假設1"],
                "inferences": ["推論1"],
                "clarity_score": 0.8,
                "completeness_score": 0.7,
                "logical_flow_score": 0.9,
                "logical_gaps": ["缺口描述"],
                "weak_connections": ["薄弱連接描述"]
            }}
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            # 解析響應
            try:
                analysis_data = json.loads(response)
                
                structure = ArgumentStructure(
                    id=structure_id,
                    premises=analysis_data.get("premises", []),
                    conclusions=analysis_data.get("conclusions", []),
                    assumptions=analysis_data.get("assumptions", []),
                    inferences=analysis_data.get("inferences", []),
                    clarity_score=analysis_data.get("clarity_score", 0.5),
                    completeness_score=analysis_data.get("completeness_score", 0.5),
                    logical_flow_score=analysis_data.get("logical_flow_score", 0.5),
                    logical_gaps=analysis_data.get("logical_gaps", []),
                    weak_connections=analysis_data.get("weak_connections", [])
                )
                
                # 記錄分析指標
                record_metric("argument_structure_analyzed", 1, {
                    "clarity_score": str(structure.clarity_score),
                    "completeness_score": str(structure.completeness_score),
                    "logical_gaps_count": str(len(structure.logical_gaps))
                })
                
                return structure
                
            except json.JSONDecodeError:
                logger.error("Failed to parse structure analysis response")
                return self._create_default_structure(structure_id)
                
        except Exception as e:
            logger.error(f"Error analyzing argument structure: {e}")
            return self._create_default_structure(structure_id)
    
    def _create_default_structure(self, structure_id: str) -> ArgumentStructure:
        """創建默認結構"""
        return ArgumentStructure(
            id=structure_id,
            clarity_score=0.5,
            completeness_score=0.5,
            logical_flow_score=0.5
        )


class EvidenceEvaluator:
    """證據評估器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def evaluate_evidence(self, content: str) -> List[EvidenceItem]:
        """評估論證中的證據"""
        try:
            # 構建證據識別提示
            evidence_prompt = f"""
            請識別並評估以下論證中的證據：

            論證內容：{content}

            請識別所有證據項目，對每個證據評估：
            1. evidence_type: 證據類型 (statistical, expert_opinion, case_study, research, anecdotal, logical, empirical, authoritative)
            2. credibility_score: 可信度 (0-1)
            3. relevance_score: 相關性 (0-1)
            4. sufficiency_score: 充分性 (0-1)
            5. recency_score: 時效性 (0-1)

            請以JSON格式回應：
            [
                {{
                    "content": "證據內容",
                    "evidence_type": "statistical",
                    "source": "來源（如果有）",
                    "credibility_score": 0.8,
                    "relevance_score": 0.9,
                    "sufficiency_score": 0.7,
                    "recency_score": 0.6
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": evidence_prompt}],
                max_tokens=1200,
                temperature=0.3
            )
            
            try:
                evidence_data = json.loads(response)
                evidence_items = []
                
                for item in evidence_data:
                    evidence_id = str(uuid.uuid4())
                    
                    # 解析證據類型
                    evidence_type = EvidenceType.LOGICAL  # 默認
                    try:
                        evidence_type = EvidenceType(item.get("evidence_type", "logical"))
                    except ValueError:
                        pass
                    
                    evidence = EvidenceItem(
                        id=evidence_id,
                        content=item.get("content", ""),
                        evidence_type=evidence_type,
                        source=item.get("source"),
                        credibility_score=item.get("credibility_score", 0.5),
                        relevance_score=item.get("relevance_score", 0.5),
                        sufficiency_score=item.get("sufficiency_score", 0.5),
                        recency_score=item.get("recency_score", 0.5)
                    )
                    
                    evidence_items.append(evidence)
                
                # 記錄評估指標
                record_metric("evidence_items_evaluated", len(evidence_items), {
                    "avg_credibility": str(sum(e.credibility_score for e in evidence_items) / len(evidence_items)) if evidence_items else "0"
                })
                
                return evidence_items
                
            except json.JSONDecodeError:
                logger.error("Failed to parse evidence evaluation response")
                return []
                
        except Exception as e:
            logger.error(f"Error evaluating evidence: {e}")
            return []


class RebuttalAnalyzer:
    """反駁分析器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def analyze_rebuttal(
        self,
        rebuttal_content: str,
        target_argument: str,
        target_argument_id: str
    ) -> RebuttalAnalysis:
        """分析反駁效力"""
        analysis_id = str(uuid.uuid4())
        
        try:
            # 構建反駁分析提示
            rebuttal_prompt = f"""
            請分析以下反駁的效力：

            目標論證：{target_argument}
            反駁內容：{rebuttal_content}

            請分析：
            1. rebuttal_type: 反駁類型 (direct_refutation, counter_evidence, alternative_explanation, questioning_assumptions, exposing_fallacy, reframing, precedent_challenge)
            2. attack_points: 攻擊的具體點
            3. effectiveness_score: 有效性 (0-1)
            4. precision_score: 精確性 (0-1)
            5. impact_score: 影響力 (0-1)
            6. vulnerabilities_exposed: 暴露的弱點
            7. counter_strategies: 可能的反制策略

            請以JSON格式回應：
            {{
                "rebuttal_type": "direct_refutation",
                "attack_points": ["攻擊點1", "攻擊點2"],
                "effectiveness_score": 0.8,
                "precision_score": 0.7,
                "impact_score": 0.9,
                "vulnerabilities_exposed": ["弱點1", "弱點2"],
                "counter_strategies": ["策略1", "策略2"]
            }}
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": rebuttal_prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            try:
                analysis_data = json.loads(response)
                
                # 解析反駁類型
                rebuttal_type = RebuttalType.DIRECT_REFUTATION  # 默認
                try:
                    rebuttal_type = RebuttalType(analysis_data.get("rebuttal_type", "direct_refutation"))
                except ValueError:
                    pass
                
                analysis = RebuttalAnalysis(
                    id=analysis_id,
                    target_argument_id=target_argument_id,
                    rebuttal_type=rebuttal_type,
                    attack_points=analysis_data.get("attack_points", []),
                    effectiveness_score=analysis_data.get("effectiveness_score", 0.5),
                    precision_score=analysis_data.get("precision_score", 0.5),
                    impact_score=analysis_data.get("impact_score", 0.5),
                    vulnerabilities_exposed=analysis_data.get("vulnerabilities_exposed", []),
                    counter_strategies=analysis_data.get("counter_strategies", [])
                )
                
                # 記錄分析指標
                record_metric("rebuttal_analyzed", 1, {
                    "type": rebuttal_type.value,
                    "effectiveness": str(analysis.effectiveness_score),
                    "impact": str(analysis.impact_score)
                })
                
                return analysis
                
            except json.JSONDecodeError:
                logger.error("Failed to parse rebuttal analysis response")
                return self._create_default_rebuttal_analysis(analysis_id, target_argument_id)
                
        except Exception as e:
            logger.error(f"Error analyzing rebuttal: {e}")
            return self._create_default_rebuttal_analysis(analysis_id, target_argument_id)
    
    def _create_default_rebuttal_analysis(self, analysis_id: str, target_argument_id: str) -> RebuttalAnalysis:
        """創建默認反駁分析"""
        return RebuttalAnalysis(
            id=analysis_id,
            target_argument_id=target_argument_id,
            rebuttal_type=RebuttalType.DIRECT_REFUTATION,
            effectiveness_score=0.5,
            precision_score=0.5,
            impact_score=0.5
        )


class StrengthCalculator:
    """強度計算器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def calculate_strength(
        self,
        structure: ArgumentStructure,
        evidence_items: List[EvidenceItem],
        logical_fallacies: List[LogicalFallacy]
    ) -> Tuple[float, float, List[str]]:
        """計算論證強度"""
        try:
            # 結構強度 (30%)
            structure_strength = (
                structure.clarity_score * 0.4 +
                structure.completeness_score * 0.3 +
                structure.logical_flow_score * 0.3
            )
            
            # 證據強度 (40%)
            if evidence_items:
                evidence_strength = sum(
                    item.credibility_score * 0.3 +
                    item.relevance_score * 0.3 +
                    item.sufficiency_score * 0.2 +
                    item.recency_score * 0.2
                    for item in evidence_items
                ) / len(evidence_items)
            else:
                evidence_strength = 0.3  # 無證據的懲罰
            
            # 邏輯強度 (30%)
            fallacy_penalty = len([f for f in logical_fallacies if f != LogicalFallacy.NONE]) * 0.15
            logical_strength = max(0.0, 1.0 - fallacy_penalty)
            
            # 綜合強度計算
            overall_strength = (
                structure_strength * 0.3 +
                evidence_strength * 0.4 +
                logical_strength * 0.3
            )
            
            # 信心度計算
            confidence_factors = [
                structure.clarity_score,
                1.0 if evidence_items else 0.5,
                1.0 if not logical_fallacies or logical_fallacies == [LogicalFallacy.NONE] else 0.7
            ]
            confidence_level = sum(confidence_factors) / len(confidence_factors)
            
            # 生成改進建議
            suggestions = await self._generate_improvement_suggestions(
                structure, evidence_items, logical_fallacies, overall_strength
            )
            
            return overall_strength, confidence_level, suggestions
            
        except Exception as e:
            logger.error(f"Error calculating argument strength: {e}")
            return 0.5, 0.5, ["無法生成改進建議"]
    
    async def _generate_improvement_suggestions(
        self,
        structure: ArgumentStructure,
        evidence_items: List[EvidenceItem],
        logical_fallacies: List[LogicalFallacy],
        current_strength: float
    ) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        try:
            # 基於結構問題的建議
            if structure.clarity_score < 0.7:
                suggestions.append("提高論證結構的清晰度，明確區分前提和結論")
            
            if structure.completeness_score < 0.7:
                suggestions.append("補充缺失的前提或推理步驟，使論證更完整")
            
            if structure.logical_gaps:
                suggestions.append("填補邏輯缺口：" + "、".join(structure.logical_gaps[:2]))
            
            # 基於證據問題的建議
            if not evidence_items:
                suggestions.append("添加支持證據以增強論證說服力")
            else:
                low_credibility_count = len([e for e in evidence_items if e.credibility_score < 0.6])
                if low_credibility_count > 0:
                    suggestions.append("提供更可信的證據來源")
                
                low_relevance_count = len([e for e in evidence_items if e.relevance_score < 0.6])
                if low_relevance_count > 0:
                    suggestions.append("確保證據與論證主題更相關")
            
            # 基於邏輯謬誤的建議
            for fallacy in logical_fallacies:
                if fallacy != LogicalFallacy.NONE:
                    fallacy_suggestions = {
                        LogicalFallacy.AD_HOMINEM: "避免人身攻擊，專注於論證內容",
                        LogicalFallacy.STRAW_MAN: "準確表述對方觀點，避免歪曲",
                        LogicalFallacy.FALSE_DICHOTOMY: "考慮更多可能性，避免非黑即白的思維",
                        LogicalFallacy.SLIPPERY_SLOPE: "提供中間步驟的證據，避免極端推論",
                        LogicalFallacy.CIRCULAR_REASONING: "確保前提獨立於結論",
                        LogicalFallacy.APPEAL_TO_AUTHORITY: "提供權威的具體論證，而非僅依賴地位",
                        LogicalFallacy.HASTY_GENERALIZATION: "增加樣本大小，避免過度概括",
                        LogicalFallacy.RED_HERRING: "保持論證焦點，避免轉移話題"
                    }
                    if fallacy in fallacy_suggestions:
                        suggestions.append(fallacy_suggestions[fallacy])
            
            # 基於整體強度的建議
            if current_strength < 0.5:
                suggestions.append("論證整體需要大幅改進，建議重新構建論證框架")
            elif current_strength < 0.7:
                suggestions.append("論證有一定基礎，但需要在證據和邏輯方面加強")
            
            return suggestions[:5]  # 限制建議數量
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
            return ["建議諮詢專業人士以改進論證質量"]
    
    async def detect_logical_fallacies(self, content: str) -> List[LogicalFallacy]:
        """檢測邏輯謬誤"""
        try:
            fallacy_prompt = f"""
            請檢測以下論證中的邏輯謬誤：

            論證內容：{content}

            請識別是否存在以下邏輯謬誤：
            - ad_hominem: 人身攻擊
            - straw_man: 稻草人謬誤
            - false_dichotomy: 假二分法
            - slippery_slope: 滑坡謬誤
            - circular_reasoning: 循環論證
            - appeal_to_authority: 訴諸權威
            - hasty_generalization: 草率概括
            - red_herring: 轉移話題

            請以JSON列表格式回應檢測到的謬誤：
            ["ad_hominem", "straw_man"] 或 ["none"] 如果沒有謬誤
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": fallacy_prompt}],
                max_tokens=200,
                temperature=0.2
            )
            
            try:
                fallacy_names = json.loads(response)
                fallacies = []
                
                for name in fallacy_names:
                    try:
                        fallacy = LogicalFallacy(name)
                        fallacies.append(fallacy)
                    except ValueError:
                        continue
                
                return fallacies if fallacies else [LogicalFallacy.NONE]
                
            except json.JSONDecodeError:
                return [LogicalFallacy.NONE]
                
        except Exception as e:
            logger.error(f"Error detecting logical fallacies: {e}")
            return [LogicalFallacy.NONE]


class ArgumentAnalysisEngine:
    """論證分析引擎"""
    
    def __init__(self):
        self.structure_analyzer = ArgumentStructureAnalyzer()
        self.evidence_evaluator = EvidenceEvaluator()
        self.rebuttal_analyzer = RebuttalAnalyzer()
        self.strength_calculator = StrengthCalculator()
        
        # 分析歷史
        self.analysis_history: Dict[str, ArgumentStrengthReport] = {}
        
        logger.info("Argument analysis engine initialized")
    
    async def analyze_argument(
        self,
        argument_id: str,
        content: str,
        speaker: str,
        timestamp: Optional[datetime] = None
    ) -> ArgumentStrengthReport:
        """完整分析論證強度"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # 1. 結構分析
            structure = await self.structure_analyzer.analyze_structure(content)
            
            # 2. 證據評估
            evidence_items = await self.evidence_evaluator.evaluate_evidence(content)
            
            # 3. 邏輯謬誤檢測
            logical_fallacies = await self.strength_calculator.detect_logical_fallacies(content)
            
            # 4. 強度計算
            overall_strength, confidence_level, suggestions = await self.strength_calculator.calculate_strength(
                structure, evidence_items, logical_fallacies
            )
            
            # 5. 生成報告
            report = ArgumentStrengthReport(
                argument_id=argument_id,
                content=content,
                speaker=speaker,
                timestamp=timestamp,
                structure=structure,
                evidence_items=evidence_items,
                logical_fallacies=logical_fallacies,
                logical_soundness_score=1.0 - (len([f for f in logical_fallacies if f != LogicalFallacy.NONE]) * 0.2),
                overall_strength=overall_strength,
                confidence_level=confidence_level,
                improvement_suggestions=suggestions
            )
            
            # 存儲分析結果
            self.analysis_history[argument_id] = report
            
            # 記錄分析指標
            record_metric("argument_analysis_completed", 1, {
                "speaker": speaker,
                "strength": str(round(overall_strength, 2)),
                "confidence": str(round(confidence_level, 2)),
                "fallacies_count": str(len([f for f in logical_fallacies if f != LogicalFallacy.NONE]))
            })
            
            logger.info(f"Completed argument analysis for {argument_id}, strength: {overall_strength:.2f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error analyzing argument {argument_id}: {e}")
            # 返回默認報告
            return self._create_default_report(argument_id, content, speaker, timestamp or datetime.now())
    
    def _create_default_report(
        self,
        argument_id: str,
        content: str,
        speaker: str,
        timestamp: datetime
    ) -> ArgumentStrengthReport:
        """創建默認分析報告"""
        default_structure = ArgumentStructure(
            id=str(uuid.uuid4()),
            clarity_score=0.5,
            completeness_score=0.5,
            logical_flow_score=0.5
        )
        
        return ArgumentStrengthReport(
            argument_id=argument_id,
            content=content,
            speaker=speaker,
            timestamp=timestamp,
            structure=default_structure,
            logical_fallacies=[LogicalFallacy.NONE],
            logical_soundness_score=0.5,
            overall_strength=0.5,
            confidence_level=0.5,
            improvement_suggestions=["分析過程中出現錯誤，建議重新分析"]
        )
    
    async def compare_arguments(
        self,
        argument_ids: List[str]
    ) -> Dict[str, Any]:
        """比較多個論證的強度"""
        try:
            reports = []
            for arg_id in argument_ids:
                if arg_id in self.analysis_history:
                    reports.append(self.analysis_history[arg_id])
            
            if not reports:
                return {"error": "No analysis reports found for given arguments"}
            
            # 排序論證
            sorted_reports = sorted(reports, key=lambda x: x.overall_strength, reverse=True)
            
            # 統計分析
            strengths = [r.overall_strength for r in reports]
            avg_strength = sum(strengths) / len(strengths)
            
            # 識別最強和最弱論證
            strongest = sorted_reports[0]
            weakest = sorted_reports[-1]
            
            return {
                "total_arguments": len(reports),
                "average_strength": avg_strength,
                "strength_range": {
                    "min": min(strengths),
                    "max": max(strengths)
                },
                "strongest_argument": {
                    "id": strongest.argument_id,
                    "speaker": strongest.speaker,
                    "strength": strongest.overall_strength,
                    "key_strengths": strongest.improvement_suggestions[:2] if strongest.overall_strength > 0.7 else []
                },
                "weakest_argument": {
                    "id": weakest.argument_id,
                    "speaker": weakest.speaker,
                    "strength": weakest.overall_strength,
                    "improvement_areas": weakest.improvement_suggestions[:3]
                },
                "comparison_insights": self._generate_comparison_insights(reports)
            }
            
        except Exception as e:
            logger.error(f"Error comparing arguments: {e}")
            return {"error": str(e)}
    
    def _generate_comparison_insights(self, reports: List[ArgumentStrengthReport]) -> List[str]:
        """生成比較洞察"""
        insights = []
        
        try:
            # 分析證據使用模式
            evidence_counts = [len(r.evidence_items) for r in reports]
            avg_evidence = sum(evidence_counts) / len(evidence_counts) if evidence_counts else 0
            
            if avg_evidence < 1:
                insights.append("整體論證缺乏足夠的證據支持")
            elif avg_evidence > 3:
                insights.append("論證普遍具有豐富的證據支持")
            
            # 分析邏輯謬誤模式
            fallacy_counts = [len([f for f in r.logical_fallacies if f != LogicalFallacy.NONE]) for r in reports]
            total_fallacies = sum(fallacy_counts)
            
            if total_fallacies > len(reports):
                insights.append("論證中存在較多邏輯謬誤，需要改進邏輯推理")
            
            # 分析發言者表現
            speaker_performance = {}
            for report in reports:
                if report.speaker not in speaker_performance:
                    speaker_performance[report.speaker] = []
                speaker_performance[report.speaker].append(report.overall_strength)
            
            for speaker, strengths in speaker_performance.items():
                avg_strength = sum(strengths) / len(strengths)
                if avg_strength > 0.8:
                    insights.append(f"{speaker}的論證質量consistently較高")
                elif avg_strength < 0.4:
                    insights.append(f"{speaker}的論證需要在結構和證據方面加強")
            
            return insights[:5]  # 限制洞察數量
            
        except Exception as e:
            logger.error(f"Error generating comparison insights: {e}")
            return ["無法生成比較洞察"]
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析摘要"""
        try:
            if not self.analysis_history:
                return {"message": "No analysis history available"}
            
            reports = list(self.analysis_history.values())
            
            # 基本統計
            total_analyses = len(reports)
            avg_strength = sum(r.overall_strength for r in reports) / total_analyses
            avg_confidence = sum(r.confidence_level for r in reports) / total_analyses
            
            # 強度分布
            strength_distribution = {
                "high": len([r for r in reports if r.overall_strength >= 0.7]),
                "medium": len([r for r in reports if 0.4 <= r.overall_strength < 0.7]),
                "low": len([r for r in reports if r.overall_strength < 0.4])
            }
            
            # 常見問題
            all_fallacies = []
            for report in reports:
                all_fallacies.extend([f for f in report.logical_fallacies if f != LogicalFallacy.NONE])
            
            fallacy_counts = {}
            for fallacy in all_fallacies:
                fallacy_counts[fallacy.value] = fallacy_counts.get(fallacy.value, 0) + 1
            
            common_fallacies = sorted(fallacy_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "total_analyses": total_analyses,
                "average_strength": avg_strength,
                "average_confidence": avg_confidence,
                "strength_distribution": strength_distribution,
                "common_fallacies": [{"type": f[0], "count": f[1]} for f in common_fallacies],
                "analysis_period": {
                    "start": min(r.timestamp for r in reports).isoformat(),
                    "end": max(r.timestamp for r in reports).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {"error": str(e)}


# 全局論證分析引擎實例
argument_analysis_engine = None

def get_argument_analysis_engine() -> ArgumentAnalysisEngine:
    """獲取論證分析引擎實例"""
    global argument_analysis_engine
    if argument_analysis_engine is None:
        argument_analysis_engine = ArgumentAnalysisEngine()
    return argument_analysis_engine