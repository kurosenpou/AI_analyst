"""
Consensus Building Mechanism Implementation
Task 2.3.3: Consensus Building Mechanism

Features:
- Common ground discovery
- Disagreement resolution
- Solution generation
- Compromise identification
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json

from .openrouter_client import get_openrouter_client
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class AgreementLevel(Enum):
    """同意程度"""
    FULL_AGREEMENT = "full_agreement"           # 完全同意
    PARTIAL_AGREEMENT = "partial_agreement"     # 部分同意
    NEUTRAL = "neutral"                         # 中立
    PARTIAL_DISAGREEMENT = "partial_disagreement"  # 部分不同意
    FULL_DISAGREEMENT = "full_disagreement"     # 完全不同意


class DisagreementType(Enum):
    """分歧類型"""
    FACTUAL = "factual"                 # 事實分歧
    DEFINITIONAL = "definitional"       # 定義分歧
    METHODOLOGICAL = "methodological"   # 方法論分歧
    VALUE_BASED = "value_based"         # 價值觀分歧
    PRIORITY = "priority"               # 優先級分歧
    SCOPE = "scope"                     # 範圍分歧
    TEMPORAL = "temporal"               # 時間分歧


class SolutionType(Enum):
    """解決方案類型"""
    COMPROMISE = "compromise"           # 妥協方案
    SYNTHESIS = "synthesis"             # 綜合方案
    ALTERNATIVE = "alternative"         # 替代方案
    SEQUENTIAL = "sequential"           # 順序方案
    CONDITIONAL = "conditional"         # 條件方案
    HYBRID = "hybrid"                   # 混合方案


@dataclass
class CommonGround:
    """共同點"""
    id: str
    title: str
    description: str
    
    # 支持者
    supporters: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    
    # 強度評估
    consensus_strength: float = 0.0     # 共識強度
    evidence_quality: float = 0.0       # 證據質量
    stability_score: float = 0.0        # 穩定性分數
    
    # 時間追蹤
    identified_at: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_supporter(self, supporter: str):
        """添加支持者"""
        if supporter not in self.supporters:
            self.supporters.append(supporter)
            self.last_reinforced = datetime.now()
    
    def add_evidence(self, evidence: str):
        """添加支持證據"""
        if evidence not in self.supporting_evidence:
            self.supporting_evidence.append(evidence)
            self.last_reinforced = datetime.now()


@dataclass
class Disagreement:
    """分歧"""
    id: str
    title: str
    description: str
    disagreement_type: DisagreementType
    
    # 分歧雙方
    position_a: Dict[str, Any] = field(default_factory=dict)  # 立場A
    position_b: Dict[str, Any] = field(default_factory=dict)  # 立場B
    
    # 分析數據
    intensity_level: float = 0.0        # 分歧強度
    resolution_difficulty: float = 0.0  # 解決難度
    impact_scope: float = 0.0           # 影響範圍
    
    # 解決狀態
    resolution_attempts: List[str] = field(default_factory=list)
    potential_bridges: List[str] = field(default_factory=list)  # 潛在橋樑
    
    # 時間追蹤
    identified_at: datetime = field(default_factory=datetime.now)
    last_escalated: Optional[datetime] = None
    
    def add_resolution_attempt(self, attempt: str):
        """添加解決嘗試"""
        self.resolution_attempts.append(attempt)
    
    def add_potential_bridge(self, bridge: str):
        """添加潛在橋樑"""
        if bridge not in self.potential_bridges:
            self.potential_bridges.append(bridge)


@dataclass
class Solution:
    """解決方案"""
    id: str
    title: str
    description: str
    solution_type: SolutionType
    
    # 目標分歧
    target_disagreements: List[str] = field(default_factory=list)
    
    # 方案內容
    key_components: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    
    # 評估分數
    feasibility_score: float = 0.0      # 可行性
    acceptance_likelihood: float = 0.0   # 接受可能性
    effectiveness_score: float = 0.0     # 有效性
    
    # 利益相關者分析
    beneficiaries: List[str] = field(default_factory=list)
    potential_objectors: List[str] = field(default_factory=list)
    
    # 時間追蹤
    proposed_at: datetime = field(default_factory=datetime.now)
    
    def add_component(self, component: str):
        """添加關鍵組件"""
        if component not in self.key_components:
            self.key_components.append(component)
    
    def add_implementation_step(self, step: str):
        """添加實施步驟"""
        if step not in self.implementation_steps:
            self.implementation_steps.append(step)


@dataclass
class ConsensusReport:
    """共識報告"""
    debate_id: str
    topic: str
    participants: List[str]
    
    # 共識分析
    common_grounds: List[CommonGround] = field(default_factory=list)
    disagreements: List[Disagreement] = field(default_factory=list)
    solutions: List[Solution] = field(default_factory=list)
    
    # 整體評估
    overall_consensus_level: float = 0.0    # 整體共識水平
    polarization_index: float = 0.0         # 極化指數
    resolution_potential: float = 0.0       # 解決潛力
    
    # 建議
    next_steps: List[str] = field(default_factory=list)
    facilitation_recommendations: List[str] = field(default_factory=list)
    
    # 生成時間
    generated_at: datetime = field(default_factory=datetime.now)


class CommonGroundFinder:
    """共同點發現器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def find_common_ground(
        self,
        arguments: List[Dict[str, Any]],
        participants: List[str]
    ) -> List[CommonGround]:
        """發現共同點"""
        try:
            # 構建共同點識別提示
            arguments_text = self._format_arguments_for_analysis(arguments)
            
            common_ground_prompt = f"""
            請分析以下辯論論證，識別參與者之間的共同點：

            參與者：{', '.join(participants)}

            論證內容：
            {arguments_text}

            請識別3-5個主要的共同點，每個共同點包含：
            - title: 共同點標題
            - description: 詳細描述
            - supporters: 支持這個觀點的參與者列表
            - supporting_evidence: 支持證據
            - consensus_strength: 共識強度 (0-1)

            請以JSON格式回應：
            [
                {{
                    "title": "共同點標題",
                    "description": "詳細描述",
                    "supporters": ["participant1", "participant2"],
                    "supporting_evidence": ["證據1", "證據2"],
                    "consensus_strength": 0.8
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": common_ground_prompt}],
                max_tokens=1200,
                temperature=0.4
            )
            
            try:
                common_ground_data = json.loads(response)
                common_grounds = []
                
                for item in common_ground_data:
                    cg_id = str(uuid.uuid4())
                    
                    common_ground = CommonGround(
                        id=cg_id,
                        title=item.get("title", "未知共同點"),
                        description=item.get("description", ""),
                        supporters=item.get("supporters", []),
                        supporting_evidence=item.get("supporting_evidence", []),
                        consensus_strength=item.get("consensus_strength", 0.5)
                    )
                    
                    # 計算證據質量和穩定性
                    common_ground.evidence_quality = self._assess_evidence_quality(
                        common_ground.supporting_evidence
                    )
                    common_ground.stability_score = self._assess_stability(
                        common_ground.supporters, participants
                    )
                    
                    common_grounds.append(common_ground)
                
                # 記錄發現指標
                record_metric("common_grounds_found", len(common_grounds), {
                    "participants_count": str(len(participants)),
                    "avg_consensus_strength": str(sum(cg.consensus_strength for cg in common_grounds) / len(common_grounds)) if common_grounds else "0"
                })
                
                return common_grounds
                
            except json.JSONDecodeError:
                logger.error("Failed to parse common ground response")
                return []
                
        except Exception as e:
            logger.error(f"Error finding common ground: {e}")
            return []
    
    def _format_arguments_for_analysis(self, arguments: List[Dict[str, Any]]) -> str:
        """格式化論證用於分析"""
        formatted = []
        for arg in arguments:
            speaker = arg.get("speaker", "Unknown")
            content = arg.get("content", "")
            formatted.append(f"[{speaker}] {content}")
        return "\n\n".join(formatted)
    
    def _assess_evidence_quality(self, evidence_list: List[str]) -> float:
        """評估證據質量"""
        if not evidence_list:
            return 0.0
        
        # 簡化評估：基於證據數量和多樣性
        quality_score = min(1.0, len(evidence_list) * 0.2)  # 每個證據0.2分
        
        # 檢查證據多樣性（簡化實現）
        unique_words = set()
        for evidence in evidence_list:
            unique_words.update(evidence.lower().split())
        
        diversity_bonus = min(0.3, len(unique_words) * 0.01)
        
        return min(1.0, quality_score + diversity_bonus)
    
    def _assess_stability(self, supporters: List[str], all_participants: List[str]) -> float:
        """評估穩定性"""
        if not all_participants:
            return 0.0
        
        # 基於支持者比例
        support_ratio = len(supporters) / len(all_participants)
        
        # 如果超過一半參與者支持，穩定性較高
        if support_ratio > 0.5:
            return 0.7 + (support_ratio - 0.5) * 0.6
        else:
            return support_ratio * 1.4  # 線性增長到0.7


class DisagreementAnalyzer:
    """分歧分析器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def analyze_disagreements(
        self,
        arguments: List[Dict[str, Any]],
        participants: List[str]
    ) -> List[Disagreement]:
        """分析分歧"""
        try:
            # 構建分歧分析提示
            arguments_text = self._format_arguments_for_analysis(arguments)
            
            disagreement_prompt = f"""
            請分析以下辯論中的主要分歧：

            參與者：{', '.join(participants)}

            論證內容：
            {arguments_text}

            請識別3-5個主要分歧，每個分歧包含：
            - title: 分歧標題
            - description: 分歧描述
            - disagreement_type: 分歧類型 (factual, definitional, methodological, value_based, priority, scope, temporal)
            - position_a: 立場A的描述和支持者
            - position_b: 立場B的描述和支持者
            - intensity_level: 分歧強度 (0-1)
            - resolution_difficulty: 解決難度 (0-1)

            請以JSON格式回應：
            [
                {{
                    "title": "分歧標題",
                    "description": "分歧描述",
                    "disagreement_type": "factual",
                    "position_a": {{
                        "description": "立場A描述",
                        "supporters": ["participant1"]
                    }},
                    "position_b": {{
                        "description": "立場B描述", 
                        "supporters": ["participant2"]
                    }},
                    "intensity_level": 0.8,
                    "resolution_difficulty": 0.6
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": disagreement_prompt}],
                max_tokens=1500,
                temperature=0.4
            )
            
            try:
                disagreement_data = json.loads(response)
                disagreements = []
                
                for item in disagreement_data:
                    disagreement_id = str(uuid.uuid4())
                    
                    # 解析分歧類型
                    disagreement_type = DisagreementType.FACTUAL  # 默認
                    try:
                        disagreement_type = DisagreementType(item.get("disagreement_type", "factual"))
                    except ValueError:
                        pass
                    
                    disagreement = Disagreement(
                        id=disagreement_id,
                        title=item.get("title", "未知分歧"),
                        description=item.get("description", ""),
                        disagreement_type=disagreement_type,
                        position_a=item.get("position_a", {}),
                        position_b=item.get("position_b", {}),
                        intensity_level=item.get("intensity_level", 0.5),
                        resolution_difficulty=item.get("resolution_difficulty", 0.5)
                    )
                    
                    # 計算影響範圍
                    disagreement.impact_scope = self._calculate_impact_scope(
                        disagreement.position_a, disagreement.position_b, participants
                    )
                    
                    # 識別潛在橋樑
                    potential_bridges = await self._identify_potential_bridges(disagreement)
                    disagreement.potential_bridges = potential_bridges
                    
                    disagreements.append(disagreement)
                
                # 記錄分析指標
                record_metric("disagreements_analyzed", len(disagreements), {
                    "avg_intensity": str(sum(d.intensity_level for d in disagreements) / len(disagreements)) if disagreements else "0",
                    "avg_difficulty": str(sum(d.resolution_difficulty for d in disagreements) / len(disagreements)) if disagreements else "0"
                })
                
                return disagreements
                
            except json.JSONDecodeError:
                logger.error("Failed to parse disagreement analysis response")
                return []
                
        except Exception as e:
            logger.error(f"Error analyzing disagreements: {e}")
            return []
    
    def _format_arguments_for_analysis(self, arguments: List[Dict[str, Any]]) -> str:
        """格式化論證用於分析"""
        formatted = []
        for arg in arguments:
            speaker = arg.get("speaker", "Unknown")
            content = arg.get("content", "")
            formatted.append(f"[{speaker}] {content}")
        return "\n\n".join(formatted)
    
    def _calculate_impact_scope(
        self,
        position_a: Dict[str, Any],
        position_b: Dict[str, Any],
        all_participants: List[str]
    ) -> float:
        """計算影響範圍"""
        try:
            supporters_a = position_a.get("supporters", [])
            supporters_b = position_b.get("supporters", [])
            
            total_involved = len(set(supporters_a + supporters_b))
            
            if not all_participants:
                return 0.5
            
            return total_involved / len(all_participants)
            
        except Exception:
            return 0.5
    
    async def _identify_potential_bridges(self, disagreement: Disagreement) -> List[str]:
        """識別潛在橋樑"""
        try:
            bridge_prompt = f"""
            基於以下分歧，請識別可能的橋樑或中間立場：

            分歧：{disagreement.title}
            描述：{disagreement.description}
            立場A：{disagreement.position_a.get('description', '')}
            立場B：{disagreement.position_b.get('description', '')}

            請識別2-3個可能的橋樑或妥協點，以JSON列表格式回應：
            ["橋樑1", "橋樑2", "橋樑3"]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": bridge_prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            try:
                bridges = json.loads(response)
                return bridges if isinstance(bridges, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Error identifying potential bridges: {e}")
            return []


class SolutionGenerator:
    """解決方案生成器"""
    
    def __init__(self):
        self.openrouter_client = get_openrouter_client()
    
    async def generate_solutions(
        self,
        disagreements: List[Disagreement],
        common_grounds: List[CommonGround],
        context: Dict[str, Any]
    ) -> List[Solution]:
        """生成解決方案"""
        solutions = []
        
        try:
            for disagreement in disagreements:
                # 為每個分歧生成解決方案
                disagreement_solutions = await self._generate_solutions_for_disagreement(
                    disagreement, common_grounds, context
                )
                solutions.extend(disagreement_solutions)
            
            # 生成綜合解決方案
            if len(disagreements) > 1:
                comprehensive_solution = await self._generate_comprehensive_solution(
                    disagreements, common_grounds, context
                )
                if comprehensive_solution:
                    solutions.append(comprehensive_solution)
            
            # 評估和排序解決方案
            for solution in solutions:
                await self._evaluate_solution(solution, context)
            
            # 按有效性排序
            solutions.sort(key=lambda x: x.effectiveness_score, reverse=True)
            
            # 記錄生成指標
            record_metric("solutions_generated", len(solutions), {
                "disagreements_count": str(len(disagreements)),
                "avg_feasibility": str(sum(s.feasibility_score for s in solutions) / len(solutions)) if solutions else "0"
            })
            
            return solutions[:5]  # 返回前5個最佳方案
            
        except Exception as e:
            logger.error(f"Error generating solutions: {e}")
            return []
    
    async def _generate_solutions_for_disagreement(
        self,
        disagreement: Disagreement,
        common_grounds: List[CommonGround],
        context: Dict[str, Any]
    ) -> List[Solution]:
        """為特定分歧生成解決方案"""
        try:
            # 構建解決方案生成提示
            common_ground_text = "\n".join([
                f"- {cg.title}: {cg.description}"
                for cg in common_grounds[:3]  # 使用前3個共同點
            ])
            
            solution_prompt = f"""
            請為以下分歧生成2-3個解決方案：

            分歧：{disagreement.title}
            描述：{disagreement.description}
            類型：{disagreement.disagreement_type.value}
            立場A：{disagreement.position_a.get('description', '')}
            立場B：{disagreement.position_b.get('description', '')}

            可利用的共同點：
            {common_ground_text}

            請生成不同類型的解決方案，每個方案包含：
            - title: 方案標題
            - description: 方案描述
            - solution_type: 方案類型 (compromise, synthesis, alternative, sequential, conditional, hybrid)
            - key_components: 關鍵組件
            - implementation_steps: 實施步驟
            - success_criteria: 成功標準

            請以JSON格式回應：
            [
                {{
                    "title": "方案標題",
                    "description": "方案描述",
                    "solution_type": "compromise",
                    "key_components": ["組件1", "組件2"],
                    "implementation_steps": ["步驟1", "步驟2"],
                    "success_criteria": ["標準1", "標準2"]
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": solution_prompt}],
                max_tokens=1200,
                temperature=0.6
            )
            
            try:
                solution_data = json.loads(response)
                solutions = []
                
                for item in solution_data:
                    solution_id = str(uuid.uuid4())
                    
                    # 解析方案類型
                    solution_type = SolutionType.COMPROMISE  # 默認
                    try:
                        solution_type = SolutionType(item.get("solution_type", "compromise"))
                    except ValueError:
                        pass
                    
                    solution = Solution(
                        id=solution_id,
                        title=item.get("title", "未知方案"),
                        description=item.get("description", ""),
                        solution_type=solution_type,
                        target_disagreements=[disagreement.id],
                        key_components=item.get("key_components", []),
                        implementation_steps=item.get("implementation_steps", []),
                        success_criteria=item.get("success_criteria", [])
                    )
                    
                    solutions.append(solution)
                
                return solutions
                
            except json.JSONDecodeError:
                logger.error("Failed to parse solution generation response")
                return []
                
        except Exception as e:
            logger.error(f"Error generating solutions for disagreement: {e}")
            return []
    
    async def _generate_comprehensive_solution(
        self,
        disagreements: List[Disagreement],
        common_grounds: List[CommonGround],
        context: Dict[str, Any]
    ) -> Optional[Solution]:
        """生成綜合解決方案"""
        try:
            # 構建綜合方案提示
            disagreements_summary = "\n".join([
                f"- {d.title}: {d.description}"
                for d in disagreements[:3]  # 使用前3個分歧
            ])
            
            comprehensive_prompt = f"""
            請基於以下多個分歧生成一個綜合解決方案：

            主要分歧：
            {disagreements_summary}

            請生成一個能夠同時處理多個分歧的綜合方案，包含：
            - title: 綜合方案標題
            - description: 方案描述
            - key_components: 關鍵組件
            - implementation_steps: 分階段實施步驟
            - success_criteria: 成功標準

            請以JSON格式回應：
            {{
                "title": "綜合方案標題",
                "description": "方案描述",
                "key_components": ["組件1", "組件2"],
                "implementation_steps": ["階段1", "階段2"],
                "success_criteria": ["標準1", "標準2"]
            }}
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": comprehensive_prompt}],
                max_tokens=800,
                temperature=0.5
            )
            
            try:
                solution_data = json.loads(response)
                solution_id = str(uuid.uuid4())
                
                solution = Solution(
                    id=solution_id,
                    title=solution_data.get("title", "綜合解決方案"),
                    description=solution_data.get("description", ""),
                    solution_type=SolutionType.SYNTHESIS,
                    target_disagreements=[d.id for d in disagreements],
                    key_components=solution_data.get("key_components", []),
                    implementation_steps=solution_data.get("implementation_steps", []),
                    success_criteria=solution_data.get("success_criteria", [])
                )
                
                return solution
                
            except json.JSONDecodeError:
                logger.error("Failed to parse comprehensive solution response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating comprehensive solution: {e}")
            return None
    
    async def _evaluate_solution(self, solution: Solution, context: Dict[str, Any]):
        """評估解決方案"""
        try:
            # 簡化評估實現
            
            # 可行性評估（基於組件數量和複雜度）
            component_count = len(solution.key_components)
            step_count = len(solution.implementation_steps)
            
            # 組件越多，可行性可能越低
            feasibility = max(0.3, 1.0 - (component_count * 0.1) - (step_count * 0.05))
            solution.feasibility_score = min(1.0, feasibility)
            
            # 接受可能性（基於方案類型）
            type_acceptance = {
                SolutionType.COMPROMISE: 0.8,
                SolutionType.SYNTHESIS: 0.7,
                SolutionType.ALTERNATIVE: 0.6,
                SolutionType.SEQUENTIAL: 0.7,
                SolutionType.CONDITIONAL: 0.5,
                SolutionType.HYBRID: 0.6
            }
            solution.acceptance_likelihood = type_acceptance.get(solution.solution_type, 0.5)
            
            # 有效性評估（基於成功標準數量）
            criteria_count = len(solution.success_criteria)
            effectiveness = min(1.0, 0.4 + (criteria_count * 0.15))
            solution.effectiveness_score = effectiveness
            
        except Exception as e:
            logger.error(f"Error evaluating solution: {e}")
            # 設置默認分數
            solution.feasibility_score = 0.5
            solution.acceptance_likelihood = 0.5
            solution.effectiveness_score = 0.5


class ConsensusEngine:
    """共識建構引擎"""
    
    def __init__(self):
        self.common_ground_finder = CommonGroundFinder()
        self.disagreement_analyzer = DisagreementAnalyzer()
        self.solution_generator = SolutionGenerator()
        
        # 分析歷史
        self.consensus_history: Dict[str, ConsensusReport] = {}
        
        logger.info("Consensus building engine initialized")
    
    async def build_consensus(
        self,
        debate_id: str,
        topic: str,
        participants: List[str],
        arguments: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ConsensusReport:
        """建構共識"""
        try:
            if context is None:
                context = {}
            
            # 1. 發現共同點
            common_grounds = await self.common_ground_finder.find_common_ground(
                arguments, participants
            )
            
            # 2. 分析分歧
            disagreements = await self.disagreement_analyzer.analyze_disagreements(
                arguments, participants
            )
            
            # 3. 生成解決方案
            solutions = await self.solution_generator.generate_solutions(
                disagreements, common_grounds, context
            )
            
            # 4. 計算整體指標
            overall_consensus_level = self._calculate_overall_consensus(
                common_grounds, disagreements, participants
            )
            
            polarization_index = self._calculate_polarization_index(
                disagreements, participants
            )
            
            resolution_potential = self._calculate_resolution_potential(
                solutions, disagreements
            )
            
            # 5. 生成建議
            next_steps = await self._generate_next_steps(
                common_grounds, disagreements, solutions
            )
            
            facilitation_recommendations = await self._generate_facilitation_recommendations(
                disagreements, overall_consensus_level
            )
            
            # 6. 創建報告
            report = ConsensusReport(
                debate_id=debate_id,
                topic=topic,
                participants=participants,
                common_grounds=common_grounds,
                disagreements=disagreements,
                solutions=solutions,
                overall_consensus_level=overall_consensus_level,
                polarization_index=polarization_index,
                resolution_potential=resolution_potential,
                next_steps=next_steps,
                facilitation_recommendations=facilitation_recommendations
            )
            
            # 存儲報告
            self.consensus_history[debate_id] = report
            
            # 記錄共識建構指標
            record_metric("consensus_reports_generated", 1, {
                "debate_id": debate_id[:8],
                "participants_count": str(len(participants)),
                "consensus_level": str(round(overall_consensus_level, 2)),
                "disagreements_count": str(len(disagreements)),
                "solutions_count": str(len(solutions))
            })
            
            logger.info(f"Generated consensus report for debate {debate_id}, consensus level: {overall_consensus_level:.2f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error building consensus for debate {debate_id}: {e}")
            # 返回默認報告
            return self._create_default_report(debate_id, topic, participants)
    
    def _calculate_overall_consensus(
        self,
        common_grounds: List[CommonGround],
        disagreements: List[Disagreement],
        participants: List[str]
    ) -> float:
        """計算整體共識水平"""
        try:
            if not participants:
                return 0.0
            
            # 共同點貢獻
            if common_grounds:
                consensus_contribution = sum(cg.consensus_strength for cg in common_grounds) / len(common_grounds)
            else:
                consensus_contribution = 0.0
            
            # 分歧懲罰
            if disagreements:
                disagreement_penalty = sum(d.intensity_level for d in disagreements) / len(disagreements)
            else:
                disagreement_penalty = 0.0
            
            # 整體共識 = 共同點貢獻 - 分歧懲罰
            overall_consensus = max(0.0, consensus_contribution - (disagreement_penalty * 0.5))
            
            return min(1.0, overall_consensus)
            
        except Exception as e:
            logger.error(f"Error calculating overall consensus: {e}")
            return 0.5
    
    def _calculate_polarization_index(
        self,
        disagreements: List[Disagreement],
        participants: List[str]
    ) -> float:
        """計算極化指數"""
        try:
            if not disagreements or not participants:
                return 0.0
            
            # 基於分歧強度和參與者分布
            total_intensity = sum(d.intensity_level for d in disagreements)
            avg_intensity = total_intensity / len(disagreements)
            
            # 檢查參與者分布的均勻性
            participant_involvement = 0.0
            for disagreement in disagreements:
                supporters_a = disagreement.position_a.get("supporters", [])
                supporters_b = disagreement.position_b.get("supporters", [])
                
                if supporters_a and supporters_b:
                    # 如果雙方都有支持者，極化程度較高
                    participant_involvement += 1.0
            
            if disagreements:
                involvement_ratio = participant_involvement / len(disagreements)
            else:
                involvement_ratio = 0.0
            
            # 極化指數 = 平均強度 * 參與度
            polarization = avg_intensity * involvement_ratio
            
            return min(1.0, polarization)
            
        except Exception as e:
            logger.error(f"Error calculating polarization index: {e}")
            return 0.5
    
    def _calculate_resolution_potential(
        self,
        solutions: List[Solution],
        disagreements: List[Disagreement]
    ) -> float:
        """計算解決潛力"""
        try:
            if not solutions or not disagreements:
                return 0.0
            
            # 基於解決方案的平均有效性和可行性
            total_effectiveness = sum(s.effectiveness_score for s in solutions)
            total_feasibility = sum(s.feasibility_score for s in solutions)
            
            avg_effectiveness = total_effectiveness / len(solutions)
            avg_feasibility = total_feasibility / len(solutions)
            
            # 解決潛力 = (有效性 + 可行性) / 2
            resolution_potential = (avg_effectiveness + avg_feasibility) / 2
            
            return min(1.0, resolution_potential)
            
        except Exception as e:
            logger.error(f"Error calculating resolution potential: {e}")
            return 0.5
    
    async def _generate_next_steps(
        self,
        common_grounds: List[CommonGround],
        disagreements: List[Disagreement],
        solutions: List[Solution]
    ) -> List[str]:
        """生成下一步建議"""
        try:
            next_steps = []
            
            # 基於共同點的建議
            if common_grounds:
                strong_grounds = [cg for cg in common_grounds if cg.consensus_strength > 0.7]
                if strong_grounds:
                    next_steps.append(f"基於強共識點'{strong_grounds[0].title}'深化討論")
            
            # 基於分歧的建議
            if disagreements:
                high_priority_disagreements = sorted(
                    disagreements,
                    key=lambda x: x.intensity_level * x.impact_scope,
                    reverse=True
                )[:2]
                
                for disagreement in high_priority_disagreements:
                    if disagreement.potential_bridges:
                        next_steps.append(f"探索'{disagreement.title}'的潛在橋樑：{disagreement.potential_bridges[0]}")
            
            # 基於解決方案的建議
            if solutions:
                best_solution = max(solutions, key=lambda x: x.effectiveness_score)
                if best_solution.implementation_steps:
                    next_steps.append(f"考慮實施'{best_solution.title}'的第一步：{best_solution.implementation_steps[0]}")
            
            # 通用建議
            if not next_steps:
                next_steps.extend([
                    "繼續尋找更多共同點",
                    "深入分析核心分歧的根源",
                    "邀請中立方提供新的視角"
                ])
            
            return next_steps[:5]  # 限制建議數量
            
        except Exception as e:
            logger.error(f"Error generating next steps: {e}")
            return ["建議繼續對話以尋求共識"]
    
    async def _generate_facilitation_recommendations(
        self,
        disagreements: List[Disagreement],
        consensus_level: float
    ) -> List[str]:
        """生成促進建議"""
        try:
            recommendations = []
            
            # 基於共識水平的建議
            if consensus_level < 0.3:
                recommendations.extend([
                    "建議暫停辯論，先建立基本的對話規則",
                    "邀請中立的調解者參與討論",
                    "重新定義討論的核心問題"
                ])
            elif consensus_level < 0.6:
                recommendations.extend([
                    "專注於尋找更多共同點",
                    "使用結構化的對話技巧",
                    "鼓勵參與者表達潛在的擔憂"
                ])
            else:
                recommendations.extend([
                    "準備進入解決方案討論階段",
                    "開始制定具體的行動計劃",
                    "建立後續跟進機制"
                ])
            
            # 基於分歧類型的建議
            disagreement_types = [d.disagreement_type for d in disagreements]
            
            if DisagreementType.FACTUAL in disagreement_types:
                recommendations.append("提供更多客觀事實和數據支持")
            
            if DisagreementType.VALUE_BASED in disagreement_types:
                recommendations.append("探討不同價值觀背後的共同關切")
            
            if DisagreementType.DEFINITIONAL in disagreement_types:
                recommendations.append("首先就關鍵概念達成共同定義")
            
            return recommendations[:5]  # 限制建議數量
            
        except Exception as e:
            logger.error(f"Error generating facilitation recommendations: {e}")
            return ["建議使用專業的對話促進技巧"]
    
    def _create_default_report(
        self,
        debate_id: str,
        topic: str,
        participants: List[str]
    ) -> ConsensusReport:
        """創建默認報告"""
        return ConsensusReport(
            debate_id=debate_id,
            topic=topic,
            participants=participants,
            overall_consensus_level=0.5,
            polarization_index=0.5,
            resolution_potential=0.5,
            next_steps=["建議重新分析辯論內容"],
            facilitation_recommendations=["建議尋求專業協助"]
        )
    
    def get_consensus_history(self) -> List[ConsensusReport]:
        """獲取共識歷史"""
        return list(self.consensus_history.values())
    
    def get_consensus_summary(self) -> Dict[str, Any]:
        """獲取共識摘要"""
        try:
            if not self.consensus_history:
                return {"message": "No consensus history available"}
            
            reports = list(self.consensus_history.values())
            
            # 基本統計
            total_reports = len(reports)
            avg_consensus = sum(r.overall_consensus_level for r in reports) / total_reports
            avg_polarization = sum(r.polarization_index for r in reports) / total_reports
            avg_resolution_potential = sum(r.resolution_potential for r in reports) / total_reports
            
            # 成功案例
            high_consensus_reports = [r for r in reports if r.overall_consensus_level > 0.7]
            
            return {
                "total_reports": total_reports,
                "average_consensus_level": avg_consensus,
                "average_polarization_index": avg_polarization,
                "average_resolution_potential": avg_resolution_potential,
                "high_consensus_cases": len(high_consensus_reports),
                "success_rate": len(high_consensus_reports) / total_reports if total_reports > 0 else 0,
                "analysis_period": {
                    "start": min(r.generated_at for r in reports).isoformat(),
                    "end": max(r.generated_at for r in reports).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating consensus summary: {e}")
            return {"error": str(e)}


# 全局共識建構引擎實例
consensus_engine = None

def get_consensus_engine() -> ConsensusEngine:
    """獲取共識建構引擎實例"""
    global consensus_engine
    if consensus_engine is None:
        consensus_engine = ConsensusEngine()
    return consensus_engine