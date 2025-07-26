"""
Deep Debate System Implementation
Task 2.3.1: Multi-round Deep Debate System

Features:
- Argument chain tracking
- Context management
- Dynamic issue focusing
- Deep argument analysis
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


class ArgumentType(Enum):
    """論證類型"""
    PREMISE = "premise"           # 前提
    CONCLUSION = "conclusion"     # 結論
    EVIDENCE = "evidence"         # 證據
    REBUTTAL = "rebuttal"        # 反駁
    COUNTER_ARGUMENT = "counter_argument"  # 反論證
    CLARIFICATION = "clarification"        # 澄清
    SYNTHESIS = "synthesis"       # 綜合


class IssueStatus(Enum):
    """議題狀態"""
    EMERGING = "emerging"         # 新興
    ACTIVE = "active"            # 活躍
    CONTESTED = "contested"      # 爭議中
    RESOLVED = "resolved"        # 已解決
    ABANDONED = "abandoned"      # 已放棄


@dataclass
class ArgumentNode:
    """論證節點"""
    id: str
    content: str
    speaker: str
    argument_type: ArgumentType
    timestamp: datetime
    
    # 關係追蹤
    parent_id: Optional[str] = None      # 父論證ID
    children_ids: List[str] = field(default_factory=list)  # 子論證ID列表
    references: List[str] = field(default_factory=list)    # 引用的論證ID
    
    # 分析數據
    strength_score: float = 0.0          # 論證強度分數
    relevance_score: float = 0.0         # 相關性分數
    novelty_score: float = 0.0           # 新穎性分數
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child_id: str):
        """添加子論證"""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
    
    def add_reference(self, ref_id: str):
        """添加引用"""
        if ref_id not in self.references:
            self.references.append(ref_id)


@dataclass
class ArgumentChain:
    """論證鏈"""
    id: str
    root_argument_id: str
    nodes: List[str] = field(default_factory=list)  # 論證節點ID列表
    depth: int = 0
    total_strength: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_node(self, node_id: str):
        """添加節點到鏈中"""
        if node_id not in self.nodes:
            self.nodes.append(node_id)
            self.depth = len(self.nodes)
            self.last_updated = datetime.now()


@dataclass
class DebateIssue:
    """辯論議題"""
    id: str
    title: str
    description: str
    status: IssueStatus
    
    # 相關論證
    supporting_arguments: List[str] = field(default_factory=list)
    opposing_arguments: List[str] = field(default_factory=list)
    
    # 統計數據
    engagement_level: float = 0.0        # 參與度
    controversy_level: float = 0.0       # 爭議度
    resolution_confidence: float = 0.0   # 解決信心度
    
    # 時間追蹤
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_supporting_argument(self, arg_id: str):
        """添加支持論證"""
        if arg_id not in self.supporting_arguments:
            self.supporting_arguments.append(arg_id)
            self.last_activity = datetime.now()
    
    def add_opposing_argument(self, arg_id: str):
        """添加反對論證"""
        if arg_id not in self.opposing_arguments:
            self.opposing_arguments.append(arg_id)
            self.last_activity = datetime.now()


@dataclass
class ContextSnapshot:
    """上下文快照"""
    id: str
    round_number: int
    timestamp: datetime
    
    # 論證狀態
    active_arguments: List[str] = field(default_factory=list)
    resolved_issues: List[str] = field(default_factory=list)
    emerging_themes: List[str] = field(default_factory=list)
    
    # 參與者狀態
    participant_positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 辯論動態
    momentum_shift: Optional[str] = None  # 動量轉移方向
    focus_areas: List[str] = field(default_factory=list)  # 焦點領域


class ArgumentChainTracker:
    """論證鏈追蹤器"""
    
    def __init__(self):
        self.arguments: Dict[str, ArgumentNode] = {}
        self.chains: Dict[str, ArgumentChain] = {}
        self.openrouter_client = get_openrouter_client()
    
    async def add_argument(
        self,
        content: str,
        speaker: str,
        argument_type: ArgumentType = ArgumentType.PREMISE,
        parent_id: Optional[str] = None,
        references: Optional[List[str]] = None
    ) -> ArgumentNode:
        """添加新論證"""
        arg_id = str(uuid.uuid4())
        
        # 創建論證節點
        argument = ArgumentNode(
            id=arg_id,
            content=content,
            speaker=speaker,
            argument_type=argument_type,
            timestamp=datetime.now(),
            parent_id=parent_id,
            references=references or []
        )
        
        # 分析論證
        await self._analyze_argument(argument)
        
        # 存儲論證
        self.arguments[arg_id] = argument
        
        # 更新父子關係
        if parent_id and parent_id in self.arguments:
            self.arguments[parent_id].add_child(arg_id)
        
        # 更新論證鏈
        await self._update_argument_chains(argument)
        
        # 記錄指標
        record_metric("deep_debate_arguments_added", 1, {
            "type": argument_type.value,
            "speaker": speaker,
            "has_parent": str(parent_id is not None)
        })
        
        logger.info(f"Added argument {arg_id} of type {argument_type.value}")
        
        return argument
    
    async def _analyze_argument(self, argument: ArgumentNode):
        """分析論證內容"""
        try:
            # 構建分析提示
            analysis_prompt = f"""
            請分析以下論證的質量和特徵：

            論證內容：{argument.content}
            論證類型：{argument.argument_type.value}
            發言者：{argument.speaker}

            請從以下維度評分（0-1分）：
            1. 論證強度 (strength_score)
            2. 相關性 (relevance_score)  
            3. 新穎性 (novelty_score)

            請以JSON格式回應：
            {{
                "strength_score": 0.8,
                "relevance_score": 0.9,
                "novelty_score": 0.7,
                "key_points": ["要點1", "要點2"],
                "logical_structure": "論證結構描述"
            }}
            """
            
            # 調用AI分析
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # 解析響應
            try:
                analysis_result = json.loads(response)
                argument.strength_score = analysis_result.get("strength_score", 0.5)
                argument.relevance_score = analysis_result.get("relevance_score", 0.5)
                argument.novelty_score = analysis_result.get("novelty_score", 0.5)
                argument.metadata.update({
                    "key_points": analysis_result.get("key_points", []),
                    "logical_structure": analysis_result.get("logical_structure", "")
                })
            except json.JSONDecodeError:
                # 如果解析失敗，使用默認值
                argument.strength_score = 0.5
                argument.relevance_score = 0.5
                argument.novelty_score = 0.5
                
        except Exception as e:
            logger.error(f"Error analyzing argument {argument.id}: {e}")
            # 使用默認分數
            argument.strength_score = 0.5
            argument.relevance_score = 0.5
            argument.novelty_score = 0.5
    
    async def _update_argument_chains(self, argument: ArgumentNode):
        """更新論證鏈"""
        if argument.parent_id:
            # 找到父論證所在的鏈
            parent_chain = None
            for chain in self.chains.values():
                if argument.parent_id in chain.nodes:
                    parent_chain = chain
                    break
            
            if parent_chain:
                # 添加到現有鏈
                parent_chain.add_node(argument.id)
                parent_chain.total_strength += argument.strength_score
            else:
                # 創建新鏈
                chain_id = str(uuid.uuid4())
                new_chain = ArgumentChain(
                    id=chain_id,
                    root_argument_id=argument.parent_id,
                    nodes=[argument.parent_id, argument.id],
                    depth=2,
                    total_strength=argument.strength_score
                )
                self.chains[chain_id] = new_chain
        else:
            # 創建新的根鏈
            chain_id = str(uuid.uuid4())
            new_chain = ArgumentChain(
                id=chain_id,
                root_argument_id=argument.id,
                nodes=[argument.id],
                depth=1,
                total_strength=argument.strength_score
            )
            self.chains[chain_id] = new_chain
    
    def get_argument_chain(self, argument_id: str) -> Optional[ArgumentChain]:
        """獲取論證所在的鏈"""
        for chain in self.chains.values():
            if argument_id in chain.nodes:
                return chain
        return None
    
    def get_strongest_chains(self, limit: int = 5) -> List[ArgumentChain]:
        """獲取最強的論證鏈"""
        return sorted(
            self.chains.values(),
            key=lambda x: x.total_strength,
            reverse=True
        )[:limit]
    
    def get_deepest_chains(self, limit: int = 5) -> List[ArgumentChain]:
        """獲取最深的論證鏈"""
        return sorted(
            self.chains.values(),
            key=lambda x: x.depth,
            reverse=True
        )[:limit]


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.snapshots: Dict[int, ContextSnapshot] = {}
        self.current_context: Optional[ContextSnapshot] = None
        self.openrouter_client = get_openrouter_client()
    
    async def create_snapshot(
        self,
        round_number: int,
        arguments: List[ArgumentNode],
        issues: List[DebateIssue]
    ) -> ContextSnapshot:
        """創建上下文快照"""
        snapshot_id = str(uuid.uuid4())
        
        # 分析當前狀態
        active_arguments = [arg.id for arg in arguments if arg.timestamp > datetime.now().replace(hour=0, minute=0, second=0)]
        resolved_issues = [issue.id for issue in issues if issue.status == IssueStatus.RESOLVED]
        
        # 識別新興主題
        emerging_themes = await self._identify_emerging_themes(arguments)
        
        # 分析參與者立場
        participant_positions = await self._analyze_participant_positions(arguments)
        
        # 檢測動量轉移
        momentum_shift = await self._detect_momentum_shift(arguments)
        
        # 創建快照
        snapshot = ContextSnapshot(
            id=snapshot_id,
            round_number=round_number,
            timestamp=datetime.now(),
            active_arguments=active_arguments,
            resolved_issues=resolved_issues,
            emerging_themes=emerging_themes,
            participant_positions=participant_positions,
            momentum_shift=momentum_shift
        )
        
        # 存儲快照
        self.snapshots[round_number] = snapshot
        self.current_context = snapshot
        
        logger.info(f"Created context snapshot for round {round_number}")
        
        return snapshot
    
    async def _identify_emerging_themes(self, arguments: List[ArgumentNode]) -> List[str]:
        """識別新興主題"""
        try:
            # 收集最近的論證內容
            recent_args = [arg for arg in arguments if arg.timestamp > datetime.now().replace(hour=datetime.now().hour-1)]
            if not recent_args:
                return []
            
            # 構建主題識別提示
            content_summary = "\n".join([f"- {arg.content[:100]}..." for arg in recent_args[-10:]])
            
            theme_prompt = f"""
            基於以下最近的辯論論證，識別正在出現的新主題或議題：

            {content_summary}

            請識別3-5個新興主題，以JSON列表格式回應：
            ["主題1", "主題2", "主題3"]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": theme_prompt}],
                max_tokens=200,
                temperature=0.5
            )
            
            try:
                themes = json.loads(response)
                return themes if isinstance(themes, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Error identifying emerging themes: {e}")
            return []
    
    async def _analyze_participant_positions(self, arguments: List[ArgumentNode]) -> Dict[str, Dict[str, Any]]:
        """分析參與者立場"""
        positions = {}
        
        # 按發言者分組論證
        speaker_args = {}
        for arg in arguments:
            if arg.speaker not in speaker_args:
                speaker_args[arg.speaker] = []
            speaker_args[arg.speaker].append(arg)
        
        # 分析每個參與者的立場
        for speaker, args in speaker_args.items():
            total_strength = sum(arg.strength_score for arg in args)
            avg_strength = total_strength / len(args) if args else 0
            
            # 分析論證類型分布
            type_counts = {}
            for arg in args:
                arg_type = arg.argument_type.value
                type_counts[arg_type] = type_counts.get(arg_type, 0) + 1
            
            positions[speaker] = {
                "total_arguments": len(args),
                "average_strength": avg_strength,
                "total_strength": total_strength,
                "argument_types": type_counts,
                "last_activity": max(arg.timestamp for arg in args) if args else datetime.now()
            }
        
        return positions
    
    async def _detect_momentum_shift(self, arguments: List[ArgumentNode]) -> Optional[str]:
        """檢測辯論動量轉移"""
        if len(arguments) < 4:
            return None
        
        # 分析最近幾輪的論證強度變化
        recent_args = sorted(arguments, key=lambda x: x.timestamp)[-6:]
        
        # 按發言者分組
        speaker_trends = {}
        for arg in recent_args:
            if arg.speaker not in speaker_trends:
                speaker_trends[arg.speaker] = []
            speaker_trends[arg.speaker].append(arg.strength_score)
        
        # 檢測趨勢
        for speaker, scores in speaker_trends.items():
            if len(scores) >= 3:
                # 簡單的趨勢檢測：比較前半部分和後半部分的平均值
                mid = len(scores) // 2
                early_avg = sum(scores[:mid]) / mid if mid > 0 else 0
                late_avg = sum(scores[mid:]) / (len(scores) - mid) if len(scores) - mid > 0 else 0
                
                if late_avg > early_avg + 0.2:  # 顯著提升
                    return f"momentum_to_{speaker}"
        
        return None
    
    def get_context_evolution(self) -> List[ContextSnapshot]:
        """獲取上下文演進歷史"""
        return sorted(self.snapshots.values(), key=lambda x: x.round_number)
    
    def get_current_focus_areas(self) -> List[str]:
        """獲取當前焦點領域"""
        if self.current_context:
            return self.current_context.focus_areas
        return []


class IssueAnalyzer:
    """議題分析器"""
    
    def __init__(self):
        self.issues: Dict[str, DebateIssue] = {}
        self.openrouter_client = get_openrouter_client()
    
    async def identify_issues(
        self,
        arguments: List[ArgumentNode],
        context: Optional[ContextSnapshot] = None
    ) -> List[DebateIssue]:
        """識別辯論議題"""
        try:
            # 構建議題識別提示
            arg_summary = "\n".join([
                f"[{arg.speaker}] {arg.content[:150]}..."
                for arg in arguments[-10:]  # 最近10個論證
            ])
            
            issue_prompt = f"""
            基於以下辯論論證，識別主要的爭議議題：

            {arg_summary}

            請識別3-5個核心議題，每個議題包含：
            - title: 議題標題
            - description: 議題描述
            - controversy_level: 爭議程度 (0-1)

            以JSON格式回應：
            [
                {{
                    "title": "議題標題",
                    "description": "議題描述",
                    "controversy_level": 0.8
                }},
                ...
            ]
            """
            
            response = await self.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": issue_prompt}],
                max_tokens=800,
                temperature=0.4
            )
            
            try:
                issue_data = json.loads(response)
                issues = []
                
                for item in issue_data:
                    issue_id = str(uuid.uuid4())
                    issue = DebateIssue(
                        id=issue_id,
                        title=item.get("title", "未知議題"),
                        description=item.get("description", ""),
                        status=IssueStatus.ACTIVE,
                        controversy_level=item.get("controversy_level", 0.5)
                    )
                    
                    # 分析相關論證
                    await self._analyze_issue_arguments(issue, arguments)
                    
                    self.issues[issue_id] = issue
                    issues.append(issue)
                
                return issues
                
            except json.JSONDecodeError:
                logger.error("Failed to parse issue identification response")
                return []
                
        except Exception as e:
            logger.error(f"Error identifying issues: {e}")
            return []
    
    async def _analyze_issue_arguments(self, issue: DebateIssue, arguments: List[ArgumentNode]):
        """分析議題相關論證"""
        # 簡化實現：基於關鍵詞匹配
        issue_keywords = issue.title.lower().split() + issue.description.lower().split()
        
        for arg in arguments:
            arg_content = arg.content.lower()
            
            # 計算相關性分數
            relevance_score = sum(1 for keyword in issue_keywords if keyword in arg_content)
            
            if relevance_score > 0:
                # 根據論證類型分類
                if arg.argument_type in [ArgumentType.PREMISE, ArgumentType.EVIDENCE]:
                    issue.add_supporting_argument(arg.id)
                elif arg.argument_type in [ArgumentType.REBUTTAL, ArgumentType.COUNTER_ARGUMENT]:
                    issue.add_opposing_argument(arg.id)
    
    def update_issue_status(self, issue_id: str, new_status: IssueStatus):
        """更新議題狀態"""
        if issue_id in self.issues:
            self.issues[issue_id].status = new_status
            self.issues[issue_id].last_activity = datetime.now()
    
    def get_active_issues(self) -> List[DebateIssue]:
        """獲取活躍議題"""
        return [issue for issue in self.issues.values() if issue.status == IssueStatus.ACTIVE]
    
    def get_most_controversial_issues(self, limit: int = 3) -> List[DebateIssue]:
        """獲取最具爭議的議題"""
        return sorted(
            self.issues.values(),
            key=lambda x: x.controversy_level,
            reverse=True
        )[:limit]


class DeepDebateEngine:
    """深度辯論引擎"""
    
    def __init__(self):
        self.chain_tracker = ArgumentChainTracker()
        self.context_manager = ContextManager()
        self.issue_analyzer = IssueAnalyzer()
        
        # 辯論狀態
        self.current_round = 0
        self.debate_history: List[ArgumentNode] = []
        
        logger.info("Deep debate engine initialized")
    
    async def process_debate_message(
        self,
        content: str,
        speaker: str,
        round_number: int,
        message_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """處理辯論消息"""
        try:
            # 分析論證類型
            argument_type = await self._classify_argument_type(content, message_context)
            
            # 識別父論證
            parent_id = await self._identify_parent_argument(content, self.debate_history)
            
            # 添加論證到鏈中
            argument = await self.chain_tracker.add_argument(
                content=content,
                speaker=speaker,
                argument_type=argument_type,
                parent_id=parent_id
            )
            
            # 更新辯論歷史
            self.debate_history.append(argument)
            self.current_round = round_number
            
            # 創建上下文快照
            context_snapshot = await self.context_manager.create_snapshot(
                round_number=round_number,
                arguments=self.debate_history,
                issues=list(self.issue_analyzer.issues.values())
            )
            
            # 識別新議題
            new_issues = await self.issue_analyzer.identify_issues(
                arguments=self.debate_history,
                context=context_snapshot
            )
            
            # 記錄處理指標
            record_metric("deep_debate_messages_processed", 1, {
                "speaker": speaker,
                "round": str(round_number),
                "argument_type": argument_type.value
            })
            
            return {
                "argument_id": argument.id,
                "argument_type": argument_type.value,
                "strength_score": argument.strength_score,
                "relevance_score": argument.relevance_score,
                "novelty_score": argument.novelty_score,
                "parent_id": parent_id,
                "chain_info": self._get_chain_info(argument.id),
                "context_snapshot": {
                    "emerging_themes": context_snapshot.emerging_themes,
                    "momentum_shift": context_snapshot.momentum_shift,
                    "focus_areas": context_snapshot.focus_areas
                },
                "new_issues": [{"id": issue.id, "title": issue.title} for issue in new_issues]
            }
            
        except Exception as e:
            logger.error(f"Error processing debate message: {e}")
            return {"error": str(e)}
    
    async def _classify_argument_type(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ArgumentType:
        """分類論證類型"""
        try:
            classification_prompt = f"""
            請分析以下論證的類型：

            論證內容：{content}

            請從以下類型中選擇最合適的一個：
            - premise: 前提論證
            - conclusion: 結論論證
            - evidence: 證據支持
            - rebuttal: 反駁論證
            - counter_argument: 反論證
            - clarification: 澄清說明
            - synthesis: 綜合論證

            只回應類型名稱，不要其他內容。
            """
            
            response = await self.chain_tracker.openrouter_client.chat_completion(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=50,
                temperature=0.2
            )
            
            # 解析響應
            response = response.strip().lower()
            for arg_type in ArgumentType:
                if arg_type.value in response:
                    return arg_type
            
            # 默認返回前提類型
            return ArgumentType.PREMISE
            
        except Exception as e:
            logger.error(f"Error classifying argument type: {e}")
            return ArgumentType.PREMISE
    
    async def _identify_parent_argument(
        self,
        content: str,
        history: List[ArgumentNode]
    ) -> Optional[str]:
        """識別父論證"""
        if not history:
            return None
        
        try:
            # 簡化實現：查找最相關的最近論證
            recent_args = history[-5:]  # 最近5個論證
            
            best_match = None
            best_score = 0.0
            
            for arg in recent_args:
                # 簡單的相似度計算（基於共同詞彙）
                content_words = set(content.lower().split())
                arg_words = set(arg.content.lower().split())
                
                if content_words and arg_words:
                    similarity = len(content_words & arg_words) / len(content_words | arg_words)
                    
                    if similarity > best_score and similarity > 0.2:  # 閾值
                        best_score = similarity
                        best_match = arg.id
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error identifying parent argument: {e}")
            return None
    
    def _get_chain_info(self, argument_id: str) -> Dict[str, Any]:
        """獲取論證鏈信息"""
        chain = self.chain_tracker.get_argument_chain(argument_id)
        if chain:
            return {
                "chain_id": chain.id,
                "depth": chain.depth,
                "total_strength": chain.total_strength,
                "position_in_chain": chain.nodes.index(argument_id) + 1 if argument_id in chain.nodes else 0
            }
        return {}
    
    def get_debate_analysis(self) -> Dict[str, Any]:
        """獲取辯論分析報告"""
        try:
            # 獲取最強論證鏈
            strongest_chains = self.chain_tracker.get_strongest_chains(3)
            
            # 獲取最深論證鏈
            deepest_chains = self.chain_tracker.get_deepest_chains(3)
            
            # 獲取活躍議題
            active_issues = self.issue_analyzer.get_active_issues()
            
            # 獲取上下文演進
            context_evolution = self.context_manager.get_context_evolution()
            
            return {
                "total_arguments": len(self.debate_history),
                "total_chains": len(self.chain_tracker.chains),
                "total_issues": len(self.issue_analyzer.issues),
                "current_round": self.current_round,
                "strongest_chains": [
                    {
                        "id": chain.id,
                        "depth": chain.depth,
                        "strength": chain.total_strength,
                        "root_argument": chain.root_argument_id
                    }
                    for chain in strongest_chains
                ],
                "deepest_chains": [
                    {
                        "id": chain.id,
                        "depth": chain.depth,
                        "strength": chain.total_strength,
                        "root_argument": chain.root_argument_id
                    }
                    for chain in deepest_chains
                ],
                "active_issues": [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "controversy_level": issue.controversy_level,
                        "supporting_args": len(issue.supporting_arguments),
                        "opposing_args": len(issue.opposing_arguments)
                    }
                    for issue in active_issues
                ],
                "context_snapshots": len(context_evolution),
                "emerging_themes": self.context_manager.current_context.emerging_themes if self.context_manager.current_context else []
            }
            
        except Exception as e:
            logger.error(f"Error generating debate analysis: {e}")
            return {"error": str(e)}


# 全局深度辯論引擎實例
deep_debate_engine = None

def get_deep_debate_engine() -> DeepDebateEngine:
    """獲取深度辯論引擎實例"""
    global deep_debate_engine
    if deep_debate_engine is None:
        deep_debate_engine = DeepDebateEngine()
    return deep_debate_engine