"""
Debate Engine Core Implementation
實現三模型辯論系統的核心辯論引擎 - Enhanced with Task 2.2 Features
Features: 辯論流程控制、會話管理、角色輪換、質量評估、自適應調整
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json

from .model_pool import get_model_pool, ModelRole, ModelConfig
from .prompt_templates import get_prompt_manager
from .openrouter_client import get_openrouter_client
from .monitoring import record_metric, trigger_custom_alert, AlertLevel
from .circuit_breaker import CircuitBreakerOpenError

# Task 2.2 Imports
from .model_rotation import get_rotation_engine, ModelRotationEngine, RotationDecision
from .debate_quality import get_quality_assessor, DebateQualityAssessor, DebateRole
from .adaptive_rounds import get_round_manager, AdaptiveRoundManager, RoundDecision

# Task 2.3 Imports
from .deep_debate import get_deep_debate_engine, DeepDebateEngine
from .argument_analysis import get_argument_analysis_engine, ArgumentAnalysisEngine
from .consensus_builder import get_consensus_engine, ConsensusEngine
from .advanced_judge import get_advanced_judge_engine, AdvancedJudgeEngine

logger = logging.getLogger(__name__)


class DebatePhase(Enum):
    """辯論階段"""
    INITIALIZATION = "initialization"    # 初始化階段
    OPENING = "opening"                  # 開場陳述
    FIRST_ROUND = "first_round"         # 第一輪辯論
    REBUTTAL = "rebuttal"               # 反駁階段
    CROSS_EXAMINATION = "cross_examination"  # 交叉質詢
    CLOSING = "closing"                 # 結語
    JUDGMENT = "judgment"               # 裁判階段
    COMPLETED = "completed"             # 完成
    FAILED = "failed"                   # 失敗


class DebateStatus(Enum):
    """辯論狀態"""
    PENDING = "pending"        # 等待開始
    ACTIVE = "active"          # 進行中
    PAUSED = "paused"          # 暫停
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失敗
    CANCELLED = "cancelled"    # 已取消


@dataclass
class DebateMessage:
    """辯論消息"""
    id: str
    speaker: ModelRole
    model_id: str
    phase: DebatePhase
    content: str
    timestamp: datetime
    token_count: Optional[int] = None
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebateRound:
    """辯論輪次"""
    round_number: int
    phase: DebatePhase
    messages: List[DebateMessage] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    @property
    def is_complete(self) -> bool:
        """檢查輪次是否完成"""
        required_speakers = {ModelRole.DEBATER_A, ModelRole.DEBATER_B}
        actual_speakers = {msg.speaker for msg in self.messages}
        return required_speakers.issubset(actual_speakers)


@dataclass
class DebateSession:
    """辯論會話"""
    session_id: str
    topic: str
    business_data: str
    context: str
    
    # 模型配置
    model_assignments: Dict[ModelRole, ModelConfig]
    
    # 會話狀態
    status: DebateStatus = DebateStatus.PENDING
    current_phase: DebatePhase = DebatePhase.INITIALIZATION
    current_round: int = 0
    max_rounds: int = 5
    
    # 辯論內容
    rounds: List[DebateRound] = field(default_factory=list)
    judgment: Optional[DebateMessage] = None
    final_report: Optional[str] = None
    
    # 時間追蹤
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 統計信息
    total_tokens: int = 0
    total_cost: float = 0.0
    error_count: int = 0
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """計算辯論持續時間"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
    
    @property
    def all_messages(self) -> List[DebateMessage]:
        """獲取所有辯論消息"""
        messages = []
        for round in self.rounds:
            messages.extend(round.messages)
        if self.judgment:
            messages.append(self.judgment)
        return messages
    
    def get_messages_by_speaker(self, speaker: ModelRole) -> List[DebateMessage]:
        """獲取指定發言者的所有消息"""
        return [msg for msg in self.all_messages if msg.speaker == speaker]


class DebateEngine:
    """
    辯論引擎核心類
    
    負責管理整個辯論流程，包括：
    - 辯論會話的創建和管理
    - 辯論流程的控制和推進
    - 模型之間的協調和通信
    - 結果的收集和整理
    """
    
    def __init__(self):
        self.model_pool = get_model_pool()
        self.prompt_manager = get_prompt_manager()
        self.openrouter_client = get_openrouter_client()
        self.active_sessions: Dict[str, DebateSession] = {}
        
        # Task 2.2 Components
        self.rotation_engine = get_rotation_engine()
        self.quality_assessor = get_quality_assessor()
        self.round_manager = get_round_manager()
        
        # Task 2.3 Components
        self.deep_debate_engine = get_deep_debate_engine()
        self.argument_analysis_engine = get_argument_analysis_engine()
        self.consensus_engine = get_consensus_engine()
        self.advanced_judge_engine = get_advanced_judge_engine()
        
        logger.info("Enhanced debate engine initialized with Task 2.2 and Task 2.3 features")
    
    async def create_debate_session(
        self,
        topic: str,
        business_data: str,
        context: str = "",
        max_rounds: int = 5,
        assignment_strategy: str = "default"
    ) -> DebateSession:
        """
        創建新的辯論會話
        
        Args:
            topic: 辯論主題
            business_data: 業務數據
            context: 額外上下文
            max_rounds: 最大辯論輪數
            assignment_strategy: 模型分配策略
            
        Returns:
            創建的辯論會話
        """
        session_id = str(uuid.uuid4())
        
        # 分配模型角色
        model_assignments = self.model_pool.assign_models_to_roles(assignment_strategy)
        
        # 創建辯論會話
        session = DebateSession(
            session_id=session_id,
            topic=topic,
            business_data=business_data,
            context=context,
            model_assignments=model_assignments,
            max_rounds=max_rounds,
            metadata={
                "assignment_strategy": assignment_strategy,
                "created_by": "debate_engine"
            }
        )
        
        # 註冊會話
        self.active_sessions[session_id] = session
        
        # 記錄指標
        record_metric("debate_sessions_created", 1, {
            "strategy": assignment_strategy,
            "max_rounds": str(max_rounds)
        })
        
        logger.info(f"Created debate session {session_id} with topic: {topic}")
        
        return session
    
    async def start_debate(self, session_id: str) -> DebateSession:
        """
        開始辯論會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            更新後的辯論會話
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Debate session {session_id} not found")
        
        if session.status != DebateStatus.PENDING:
            raise ValueError(f"Debate session {session_id} is not in pending status")
        
        try:
            # 更新會話狀態
            session.status = DebateStatus.ACTIVE
            session.started_at = datetime.now()
            session.current_phase = DebatePhase.OPENING
            
            # 記錄開始指標
            record_metric("debate_sessions_started", 1, {
                "session_id": session_id[:8]  # 只記錄前8位以保護隱私
            })
            
            logger.info(f"Started debate session {session_id}")
            
            # 開始第一輪辯論
            await self._conduct_opening_statements(session)
            
            return session
            
        except Exception as e:
            session.status = DebateStatus.FAILED
            session.error_count += 1
            
            logger.error(f"Failed to start debate session {session_id}: {e}")
            record_metric("debate_sessions_failed", 1, {"reason": "start_failure"})
            
            raise
    
    async def continue_debate(self, session_id: str) -> DebateSession:
        """
        繼續進行辯論
        
        Args:
            session_id: 會話ID
            
        Returns:
            更新後的辯論會話
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Debate session {session_id} not found")
        
        if session.status != DebateStatus.ACTIVE:
            raise ValueError(f"Debate session {session_id} is not active")
        
        try:
            # 根據當前階段決定下一步行動
            if session.current_phase == DebatePhase.OPENING:
                await self._conduct_debate_rounds(session)
            elif session.current_phase == DebatePhase.FIRST_ROUND:
                await self._conduct_debate_rounds(session)
            elif session.current_phase == DebatePhase.REBUTTAL:
                await self._conduct_cross_examination(session)
            elif session.current_phase == DebatePhase.CROSS_EXAMINATION:
                await self._conduct_closing_statements(session)
            elif session.current_phase == DebatePhase.CLOSING:
                await self._conduct_judgment(session)
            elif session.current_phase == DebatePhase.JUDGMENT:
                await self._finalize_debate(session)
            
            return session
            
        except Exception as e:
            session.status = DebateStatus.FAILED
            session.error_count += 1
            
            logger.error(f"Failed to continue debate session {session_id}: {e}")
            record_metric("debate_sessions_failed", 1, {"reason": "continuation_failure"})
            
            raise
    
    async def _conduct_opening_statements(self, session: DebateSession):
        """進行開場陳述"""
        logger.info(f"Conducting opening statements for session {session.session_id}")
        
        # 創建第一輪
        round_1 = DebateRound(
            round_number=1,
            phase=DebatePhase.OPENING,
            start_time=datetime.now()
        )
        
        # 正方開場陳述（辯論者A）
        debater_a_message = await self._get_model_response(
            session,
            ModelRole.DEBATER_A,
            DebatePhase.OPENING,
            self._build_opening_prompt(session, ModelRole.DEBATER_A)
        )
        round_1.messages.append(debater_a_message)
        
        # 反方開場陳述（辯論者B）
        debater_b_message = await self._get_model_response(
            session,
            ModelRole.DEBATER_B,
            DebatePhase.OPENING,
            self._build_opening_prompt(session, ModelRole.DEBATER_B, debater_a_message.content)
        )
        round_1.messages.append(debater_b_message)
        
        # 完成輪次
        round_1.end_time = datetime.now()
        if round_1.start_time:
            round_1.duration = (round_1.end_time - round_1.start_time).total_seconds()
        session.rounds.append(round_1)
        
        # 更新狀態
        session.current_round = 1
        session.current_phase = DebatePhase.FIRST_ROUND
        
        logger.info(f"Completed opening statements for session {session.session_id}")
    
    async def _conduct_debate_rounds(self, session: DebateSession):
        """進行辯論輪次"""
        max_rounds = min(session.max_rounds, 5)  # 限制最大輪數
        
        for round_num in range(2, max_rounds + 1):
            if session.status != DebateStatus.ACTIVE:
                break
                
            logger.info(f"Conducting round {round_num} for session {session.session_id}")
            
            await self._conduct_single_round(session, round_num)
            
            # 檢查是否達到結束條件
            if await self._should_end_debate(session):
                break
        
        # 進入反駁階段
        session.current_phase = DebatePhase.REBUTTAL
    
    async def _conduct_single_round(self, session: DebateSession, round_number: int):
        """進行單輪辯論 - Enhanced with Task 2.2 and Task 2.3 features"""
        debate_round = DebateRound(
            round_number=round_number,
            phase=DebatePhase.FIRST_ROUND,
            start_time=datetime.now()
        )
        
        # 獲取之前的辯論歷史
        debate_history = self._build_debate_history(session)
        
        # Task 2.2: 檢查是否需要模型輪換
        await self._evaluate_model_rotation(session)
        
        # 辯論者A發言
        debater_a_message = await self._get_model_response(
            session,
            ModelRole.DEBATER_A,
            DebatePhase.FIRST_ROUND,
            self._build_round_prompt(session, ModelRole.DEBATER_A, debate_history, round_number)
        )
        debate_round.messages.append(debater_a_message)
        
        # Task 2.2: 記錄模型性能
        await self._record_model_performance(session, ModelRole.DEBATER_A, debater_a_message)
        
        # Task 2.3: 深度辯論分析
        await self._process_deep_debate_message(session, debater_a_message, round_number)
        
        # Task 2.3: 論證強度分析
        await self._analyze_argument_strength(session, debater_a_message)
        
        # 辯論者B回應
        debater_b_message = await self._get_model_response(
            session,
            ModelRole.DEBATER_B,
            DebatePhase.FIRST_ROUND,
            self._build_round_prompt(session, ModelRole.DEBATER_B, debate_history + [debater_a_message], round_number)
        )
        debate_round.messages.append(debater_b_message)
        
        # Task 2.2: 記錄模型性能
        await self._record_model_performance(session, ModelRole.DEBATER_B, debater_b_message)
        
        # Task 2.3: 深度辯論分析
        await self._process_deep_debate_message(session, debater_b_message, round_number)
        
        # Task 2.3: 論證強度分析
        await self._analyze_argument_strength(session, debater_b_message)
        
        # 完成輪次
        debate_round.end_time = datetime.now()
        if debate_round.start_time:
            debate_round.duration = (debate_round.end_time - debate_round.start_time).total_seconds()
        session.rounds.append(debate_round)
        session.current_round = round_number
        
        # Task 2.2: 質量評估和輪次調整
        await self._evaluate_round_quality_and_adjustment(session, debate_round)
        
        # 記錄輪次指標
        record_metric("debate_rounds_completed", 1, {
            "session_id": session.session_id[:8],
            "round_number": str(round_number)
        })
    
    async def _conduct_cross_examination(self, session: DebateSession):
        """進行交叉質詢"""
        logger.info(f"Conducting cross examination for session {session.session_id}")
        
        # 實現交叉質詢邏輯
        session.current_phase = DebatePhase.CROSS_EXAMINATION
        
        # 簡化實現：跳過交叉質詢，直接進入結語
        session.current_phase = DebatePhase.CLOSING
    
    async def _conduct_closing_statements(self, session: DebateSession):
        """進行結語陳述"""
        logger.info(f"Conducting closing statements for session {session.session_id}")
        
        # 創建結語輪次
        closing_round = DebateRound(
            round_number=session.current_round + 1,
            phase=DebatePhase.CLOSING,
            start_time=datetime.now()
        )
        
        debate_history = self._build_debate_history(session)
        
        # 辯論者A結語
        debater_a_closing = await self._get_model_response(
            session,
            ModelRole.DEBATER_A,
            DebatePhase.CLOSING,
            self._build_closing_prompt(session, ModelRole.DEBATER_A, debate_history)
        )
        closing_round.messages.append(debater_a_closing)
        
        # 辯論者B結語
        debater_b_closing = await self._get_model_response(
            session,
            ModelRole.DEBATER_B,
            DebatePhase.CLOSING,
            self._build_closing_prompt(session, ModelRole.DEBATER_B, debate_history + [debater_a_closing])
        )
        closing_round.messages.append(debater_b_closing)
        
        # 完成結語輪次
        closing_round.end_time = datetime.now()
        if closing_round.start_time:
            closing_round.duration = (closing_round.end_time - closing_round.start_time).total_seconds()
        session.rounds.append(closing_round)
        
        session.current_phase = DebatePhase.JUDGMENT
    
    async def _conduct_judgment(self, session: DebateSession):
        """進行裁判判決"""
        logger.info(f"Conducting judgment for session {session.session_id}")
        
        # 構建完整的辯論記錄
        full_debate_history = self._build_debate_history(session)
        
        # 獲取裁判判決
        judgment_message = await self._get_model_response(
            session,
            ModelRole.JUDGE,
            DebatePhase.JUDGMENT,
            self._build_judgment_prompt(session, full_debate_history)
        )
        
        session.judgment = judgment_message
        session.current_phase = DebatePhase.COMPLETED
        
        # 記錄判決指標
        record_metric("debate_judgments_completed", 1, {
            "session_id": session.session_id[:8]
        })
    
    async def _finalize_debate(self, session: DebateSession):
        """完成辯論並生成最終報告 - Enhanced with Task 2.3 features"""
        logger.info(f"Finalizing debate for session {session.session_id}")
        
        # Task 2.3: 進行高級判決
        await self._conduct_advanced_judgment(session)
        
        # Task 2.3: 建構共識報告
        await self._build_consensus_report(session)
        
        # 生成增強的最終報告
        session.final_report = await self._generate_enhanced_final_report(session)
        
        # 更新會話狀態
        session.status = DebateStatus.COMPLETED
        session.completed_at = datetime.now()
        
        # 記錄完成指標
        record_metric("debate_sessions_completed", 1, {
            "session_id": session.session_id[:8],
            "total_rounds": str(len(session.rounds)),
            "duration": str(int(session.duration or 0)),
            "advanced_features_used": "true"
        })
        
        logger.info(f"Debate session {session.session_id} completed successfully with advanced analysis")
    
    async def _get_model_response(
        self,
        session: DebateSession,
        role: ModelRole,
        phase: DebatePhase,
        prompt: str
    ) -> DebateMessage:
        """獲取模型響應"""
        model_config = session.model_assignments[role]
        
        # 構建消息
        messages = [{"role": "user", "content": prompt}]
        
        start_time = datetime.now()
        
        try:
            # 調用模型API
            response_content = await self.openrouter_client.chat_completion(
                model=model_config.id,
                messages=messages,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 創建辯論消息
            message = DebateMessage(
                id=str(uuid.uuid4()),
                speaker=role,
                model_id=model_config.id,
                phase=phase,
                content=response_content,
                timestamp=datetime.now(),
                response_time=response_time,
                metadata={
                    "model_name": model_config.name,
                    "session_id": session.session_id
                }
            )
            
            # 更新會話統計
            session.total_tokens += int(len(response_content.split()) * 1.3)  # 估算token數
            session.total_cost += 0.001  # 簡化成本估算
            
            # 記錄模型調用指標
            record_metric("debate_model_calls", 1, {
                "role": role.value,
                "model": model_config.name,
                "phase": phase.value
            })
            
            return message
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker open for {role.value}: {e}")
            session.error_count += 1
            
            # 使用備用響應
            fallback_content = f"[系統提示: {role.value}模型暫時不可用，正在嘗試恢復連接]"
            
            return DebateMessage(
                id=str(uuid.uuid4()),
                speaker=role,
                model_id=model_config.id,
                phase=phase,
                content=fallback_content,
                timestamp=datetime.now(),
                metadata={"error": "circuit_breaker_open", "fallback": True}
            )
            
        except Exception as e:
            logger.error(f"Failed to get response from {role.value}: {e}")
            session.error_count += 1
            
            record_metric("debate_model_errors", 1, {
                "role": role.value,
                "model": model_config.name,
                "error_type": type(e).__name__
            })
            
            raise
    
    def _build_opening_prompt(self, session: DebateSession, role: ModelRole, opponent_statement: str = "") -> str:
        """構建開場陳述提示"""
        return self.prompt_manager.render_template(
            "debater_a_opening" if role == ModelRole.DEBATER_A else "debater_b_opening",
            topic=session.topic,
            business_data=session.business_data,
            context=session.context,
            opponent_statement=opponent_statement
        )
    
    def _build_round_prompt(self, session: DebateSession, role: ModelRole, 
                           debate_history: List[DebateMessage], round_number: int) -> str:
        """構建輪次辯論提示"""
        history_text = self._format_debate_history(debate_history)
        
        # 獲取對手最近的論點
        opponent_argument = ""
        if debate_history:
            last_msg = debate_history[-1]
            opponent_argument = last_msg.content
        
        return self.prompt_manager.render_template(
            "general_rebuttal",
            opponent_argument=opponent_argument,
            debate_context=f"當前是第{round_number}輪辯論，主題: {session.topic}",
            available_data=session.business_data,
            topic=session.topic,
            business_data=session.business_data,
            context=session.context,
            round_number=round_number,
            debate_history=history_text,
            role=role.value
        )
    
    def _build_closing_prompt(self, session: DebateSession, role: ModelRole, 
                             debate_history: List[DebateMessage]) -> str:
        """構建結語提示"""
        history_text = self._format_debate_history(debate_history)
        
        return self.prompt_manager.render_template(
            "general_rebuttal",  # 使用通用模板
            topic=session.topic,
            business_data=session.business_data,
            debate_history=history_text,
            role=role.value,
            context="這是結語階段，請總結你的核心論點"
        )
    
    def _build_judgment_prompt(self, session: DebateSession, debate_history: List[DebateMessage]) -> str:
        """構建裁判提示"""
        history_text = self._format_debate_history(debate_history)
        
        return self.prompt_manager.render_template(
            "final_judgment",
            topic=session.topic,
            full_debate_history=history_text,
            business_data=session.business_data,
            context=session.context,
            debate_history=history_text
        )
    
    def _build_debate_history(self, session: DebateSession) -> List[DebateMessage]:
        """構建辯論歷史"""
        return session.all_messages
    
    def _format_debate_history(self, messages: List[DebateMessage]) -> str:
        """格式化辯論歷史為文字"""
        formatted = []
        for msg in messages:
            speaker_name = {
                ModelRole.DEBATER_A: "正方",
                ModelRole.DEBATER_B: "反方",
                ModelRole.JUDGE: "裁判"
            }.get(msg.speaker, msg.speaker.value)
            
            formatted.append(f"【{speaker_name}】{msg.content}")
        
        return "\n\n".join(formatted)
    
    async def _should_end_debate(self, session: DebateSession) -> bool:
        """判斷是否應該結束辯論"""
        # 簡化實現：達到最大輪數時結束
        return session.current_round >= session.max_rounds
    
    async def _generate_final_report(self, session: DebateSession) -> str:
        """生成最終辯論報告"""
        report_sections = []
        
        # 辯論摘要
        report_sections.append(f"# 辯論報告：{session.topic}")
        report_sections.append(f"**創建時間：** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**辯論時長：** {session.duration:.1f}秒" if session.duration else "")
        report_sections.append(f"**總輪數：** {len(session.rounds)}")
        
        # 參與模型
        report_sections.append("\n## 參與模型")
        for role, config in session.model_assignments.items():
            report_sections.append(f"- **{role.value}：** {config.name}")
        
        # 辯論過程
        report_sections.append("\n## 辯論過程")
        for round in session.rounds:
            report_sections.append(f"\n### 第{round.round_number}輪")
            for msg in round.messages:
                speaker_name = {
                    ModelRole.DEBATER_A: "正方",
                    ModelRole.DEBATER_B: "反方"
                }.get(msg.speaker, msg.speaker.value)
                report_sections.append(f"\n**{speaker_name}：**\n{msg.content}")
        
        # 裁判判決
        if session.judgment:
            report_sections.append("\n## 裁判判決")
            report_sections.append(session.judgment.content)
        
        # 統計信息
        report_sections.append("\n## 統計信息")
        report_sections.append(f"- 總Token數：{session.total_tokens}")
        report_sections.append(f"- 估計成本：${session.total_cost:.4f}")
        report_sections.append(f"- 錯誤次數：{session.error_count}")
        
        return "\n".join(report_sections)
    
    async def _generate_enhanced_final_report(self, session: DebateSession) -> str:
        """生成增強的最終辯論報告 - 包含Task 2.3功能"""
        report_sections = []
        
        # 基本辯論摘要
        report_sections.append(f"# 增強辯論報告：{session.topic}")
        report_sections.append(f"**創建時間：** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**辯論時長：** {session.duration:.1f}秒" if session.duration else "")
        report_sections.append(f"**總輪數：** {len(session.rounds)}")
        
        # 參與模型
        report_sections.append("\n## 參與模型")
        for role, config in session.model_assignments.items():
            report_sections.append(f"- **{role.value}：** {config.name}")
        
        # Task 2.3: 高級判決結果
        advanced_judgment = session.metadata.get("advanced_judgment", {})
        if advanced_judgment:
            report_sections.append("\n## 高級AI判決")
            if advanced_judgment.get("winner"):
                report_sections.append(f"**獲勝者：** {advanced_judgment['winner']}")
                report_sections.append(f"**獲勝優勢：** {advanced_judgment.get('winning_margin', 0):.3f}")
            else:
                report_sections.append("**結果：** 平局")
            
            report_sections.append(f"**整體質量：** {advanced_judgment.get('overall_quality', 0):.3f}")
            report_sections.append(f"**判決信心度：** {advanced_judgment.get('judgment_confidence', 0):.3f}")
            
            if advanced_judgment.get("detected_biases", 0) > 0:
                report_sections.append(f"**檢測到的偏見數量：** {advanced_judgment['detected_biases']}")
            
            if advanced_judgment.get("key_turning_points"):
                report_sections.append("\n**關鍵轉折點：**")
                for point in advanced_judgment["key_turning_points"]:
                    report_sections.append(f"- {point}")
        
        # Task 2.3: 共識分析
        consensus_report = session.metadata.get("consensus_report", {})
        if consensus_report:
            report_sections.append("\n## 共識分析")
            report_sections.append(f"**整體共識水平：** {consensus_report.get('overall_consensus_level', 0):.3f}")
            report_sections.append(f"**極化指數：** {consensus_report.get('polarization_index', 0):.3f}")
            report_sections.append(f"**解決潛力：** {consensus_report.get('resolution_potential', 0):.3f}")
            
            report_sections.append(f"**發現的共同點：** {consensus_report.get('common_grounds_count', 0)}個")
            report_sections.append(f"**主要分歧：** {consensus_report.get('disagreements_count', 0)}個")
            report_sections.append(f"**提出的解決方案：** {consensus_report.get('solutions_count', 0)}個")
            
            if consensus_report.get("next_steps"):
                report_sections.append("\n**建議的下一步：**")
                for step in consensus_report["next_steps"]:
                    report_sections.append(f"- {step}")
        
        # 辯論過程（包含論證強度分析）
        report_sections.append("\n## 辯論過程與論證分析")
        for round in session.rounds:
            report_sections.append(f"\n### 第{round.round_number}輪")
            for msg in round.messages:
                speaker_name = {
                    ModelRole.DEBATER_A: "正方",
                    ModelRole.DEBATER_B: "反方"
                }.get(msg.speaker, msg.speaker.value)
                
                report_sections.append(f"\n**{speaker_name}：**")
                report_sections.append(msg.content)
                
                # Task 2.3: 添加論證強度分析
                strength_analysis = msg.metadata.get("strength_analysis", {})
                if strength_analysis:
                    report_sections.append(f"\n*論證分析：*")
                    report_sections.append(f"- 整體強度：{strength_analysis.get('overall_strength', 0):.3f}")
                    report_sections.append(f"- 邏輯健全性：{strength_analysis.get('logical_soundness', 0):.3f}")
                    report_sections.append(f"- 證據數量：{strength_analysis.get('evidence_count', 0)}")
                    
                    if strength_analysis.get("logical_fallacies"):
                        fallacies = [f for f in strength_analysis["logical_fallacies"] if f != "none"]
                        if fallacies:
                            report_sections.append(f"- 邏輯謬誤：{', '.join(fallacies)}")
                    
                    if strength_analysis.get("improvement_suggestions"):
                        report_sections.append("- 改進建議：")
                        for suggestion in strength_analysis["improvement_suggestions"]:
                            report_sections.append(f"  • {suggestion}")
        
        # 裁判判決
        if session.judgment:
            report_sections.append("\n## 基礎裁判判決")
            report_sections.append(session.judgment.content)
        
        # Task 2.3: 深度辯論洞察
        deep_analysis = self.deep_debate_engine.get_debate_analysis()
        if deep_analysis and "error" not in deep_analysis:
            report_sections.append("\n## 深度辯論洞察")
            report_sections.append(f"**總論證數：** {deep_analysis.get('total_arguments', 0)}")
            report_sections.append(f"**論證鏈數：** {deep_analysis.get('total_chains', 0)}")
            report_sections.append(f"**識別議題數：** {deep_analysis.get('total_issues', 0)}")
            
            if deep_analysis.get("emerging_themes"):
                report_sections.append("\n**新興主題：**")
                for theme in deep_analysis["emerging_themes"]:
                    report_sections.append(f"- {theme}")
        
        # 統計信息
        report_sections.append("\n## 統計信息")
        report_sections.append(f"- 總Token數：{session.total_tokens}")
        report_sections.append(f"- 估計成本：${session.total_cost:.4f}")
        report_sections.append(f"- 錯誤次數：{session.error_count}")
        
        # Task 2.3功能使用統計
        report_sections.append(f"- 使用高級分析功能：是")
        if advanced_judgment:
            report_sections.append(f"- 高級判決評估時間：{advanced_judgment.get('evaluation_time', 0):.2f}秒")
        
        return "\n".join(report_sections)
    
    def get_session(self, session_id: str) -> Optional[DebateSession]:
        """獲取辯論會話"""
        return self.active_sessions.get(session_id)
    
    def list_active_sessions(self) -> List[DebateSession]:
        """列出所有活躍的辯論會話"""
        return list(self.active_sessions.values())
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """獲取會話摘要"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status.value,
            "current_phase": session.current_phase.value,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "created_at": session.created_at.isoformat(),
            "duration": session.duration,
            "total_messages": len(session.all_messages),
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
    
    # ===== Task 2.2 Enhanced Methods =====
    
    async def _evaluate_model_rotation(self, session: DebateSession):
        """評估是否需要進行模型輪換"""
        try:
            # 構建辯論上下文
            debate_context = {
                'topic': session.topic,
                'current_round': session.current_round,
                'total_rounds': session.max_rounds,
                'session_id': session.session_id,
                'time_since_last_rotation': 0  # 簡化實現
            }
            
            # 評估輪換需求
            rotation_decision = await self.rotation_engine.evaluate_rotation_need(
                session.model_assignments,
                debate_context
            )
            
            # 如果需要輪換，執行輪換
            if rotation_decision.should_rotate and rotation_decision.new_assignments:
                logger.info(f"Rotating models for session {session.session_id}: {rotation_decision.reason}")
                
                # 更新模型分配
                session.model_assignments = rotation_decision.new_assignments
                
                # 記錄輪換事件
                record_metric("model_rotation_performed", 1, {
                    "session_id": session.session_id[:8],
                    "reason": rotation_decision.reason,
                    "confidence": str(rotation_decision.confidence)
                })
                
        except Exception as e:
            logger.error(f"Error during model rotation evaluation: {e}")
    
    async def _record_model_performance(self, session: DebateSession, role: ModelRole, message: DebateMessage):
        """記錄模型性能數據"""
        try:
            model_config = session.model_assignments.get(role)
            if not model_config:
                return
            
            # 計算響應時間
            response_time = getattr(message, 'response_time', 1.0) or 1.0
            
            # 記錄基礎性能
            self.rotation_engine.record_model_performance(
                model_id=model_config.id,
                role=role,
                response_time=response_time,
                success=True  # 如果到這裡說明成功了
            )
            
            # 如果有質量評估，記錄質量數據
            # 這裡可以添加更詳細的質量評估邏輯
            
        except Exception as e:
            logger.error(f"Error recording model performance: {e}")
    
    async def _evaluate_round_quality_and_adjustment(self, session: DebateSession, debate_round: DebateRound):
        """評估輪次質量並決定是否調整"""
        try:
            # 準備輪次論證數據
            round_arguments = []
            for message in debate_round.messages:
                round_arguments.append({
                    'content': message.content,
                    'speaker': message.speaker.value,
                    'role': 'argument',  # 簡化角色分類
                    'timestamp': message.timestamp.isoformat()
                })
            
            # 構建辯論上下文
            debate_context = {
                'topic': session.topic,
                'session_id': session.session_id,
                'start_time': session.created_at.isoformat(),
                'participants': {role.value: config.name for role, config in session.model_assignments.items()}
            }
            
            # 評估輪次調整需求
            adjustment_decision = await self.round_manager.evaluate_round_adjustment(
                current_round=session.current_round,
                planned_total_rounds=session.max_rounds,
                round_arguments=round_arguments,
                debate_context=debate_context
            )
            
            # 處理調整決策
            await self._handle_round_adjustment_decision(session, adjustment_decision)
            
        except Exception as e:
            logger.error(f"Error during round quality evaluation: {e}")
    
    async def _handle_round_adjustment_decision(self, session: DebateSession, decision):
        """處理輪次調整決策"""
        try:
            if decision.decision == RoundDecision.EXTEND_ROUNDS:
                if decision.target_rounds:
                    old_max = session.max_rounds
                    session.max_rounds = min(decision.target_rounds, 10)  # 限制最大輪數
                    logger.info(f"Extended debate rounds from {old_max} to {session.max_rounds} for session {session.session_id}")
                    
                    record_metric("debate_rounds_extended", 1, {
                        "session_id": session.session_id[:8],
                        "from_rounds": str(old_max),
                        "to_rounds": str(session.max_rounds),
                        "reason": ",".join([r.value for r in decision.reasons])
                    })
            
            elif decision.decision == RoundDecision.REDUCE_ROUNDS:
                if decision.target_rounds:
                    old_max = session.max_rounds
                    session.max_rounds = max(decision.target_rounds, session.current_round + 1)
                    logger.info(f"Reduced debate rounds from {old_max} to {session.max_rounds} for session {session.session_id}")
                    
                    record_metric("debate_rounds_reduced", 1, {
                        "session_id": session.session_id[:8],
                        "from_rounds": str(old_max),
                        "to_rounds": str(session.max_rounds),
                        "reason": ",".join([r.value for r in decision.reasons])
                    })
            
            elif decision.decision == RoundDecision.TERMINATE_EARLY:
                logger.info(f"Terminating debate early for session {session.session_id}: {decision.reasons}")
                session.max_rounds = session.current_round
                # 可以設置標誌提前結束
                
                record_metric("debate_terminated_early", 1, {
                    "session_id": session.session_id[:8],
                    "at_round": str(session.current_round),
                    "reason": ",".join([r.value for r in decision.reasons])
                })
            
        except Exception as e:
            logger.error(f"Error handling round adjustment decision: {e}")
    
    async def get_debate_quality_report(self, session_id: str) -> Dict[str, Any]:
        """獲取辯論質量報告"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # 準備論證數據
            arguments = []
            for round_obj in session.rounds:
                for message in round_obj.messages:
                    arguments.append({
                        'content': message.content,
                        'speaker': message.speaker.value,
                        'role': 'argument',
                        'round': round_obj.round_number,
                        'timestamp': message.timestamp.isoformat()
                    })
            
            # 生成質量報告
            quality_report = await self.quality_assessor.generate_debate_report(
                debate_id=session.session_id,
                topic=session.topic,
                participants={role.value: config.name for role, config in session.model_assignments.items()},
                arguments=arguments
            )
            
            # 轉換為字典格式
            return {
                "debate_id": quality_report.debate_id,
                "topic": quality_report.topic,
                "participants": quality_report.participants,
                "debate_flow_score": quality_report.debate_flow_score,
                "engagement_level": quality_report.engagement_level,
                "depth_of_discussion": quality_report.depth_of_discussion,
                "balance_score": quality_report.balance_score,
                "participant_rankings": quality_report.participant_rankings,
                "winning_arguments": quality_report.winning_arguments,
                "debate_highlights": quality_report.debate_highlights,
                "debate_improvements": quality_report.debate_improvements,
                "generated_at": quality_report.generated_at.isoformat(),
                "total_arguments_analyzed": len(quality_report.argument_analyses)
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {"error": str(e)}
    
    def get_rotation_summary(self) -> Dict[str, Any]:
        """獲取模型輪換摘要"""
        try:
            return self.rotation_engine.get_performance_summary()
        except Exception as e:
            logger.error(f"Error getting rotation summary: {e}")
            return {"error": str(e)}
    
    def get_round_adjustment_summary(self) -> Dict[str, Any]:
        """獲取輪次調整摘要"""
        try:
            return self.round_manager.get_adjustment_summary()
        except Exception as e:
            logger.error(f"Error getting round adjustment summary: {e}")
            return {"error": str(e)}
    
    # ===== Task 2.3 Enhanced Methods =====
    
    async def _process_deep_debate_message(
        self,
        session: DebateSession,
        message: DebateMessage,
        round_number: int
    ):
        """處理深度辯論消息"""
        try:
            # 構建消息上下文
            message_context = {
                "session_id": session.session_id,
                "topic": session.topic,
                "phase": message.phase.value,
                "round": round_number
            }
            
            # 處理深度辯論分析
            analysis_result = await self.deep_debate_engine.process_debate_message(
                content=message.content,
                speaker=message.speaker.value,
                round_number=round_number,
                message_context=message_context
            )
            
            # 將分析結果存儲到消息元數據中
            if "error" not in analysis_result:
                message.metadata.update({
                    "deep_analysis": analysis_result,
                    "argument_chain_info": analysis_result.get("chain_info", {}),
                    "context_insights": analysis_result.get("context_snapshot", {})
                })
            
        except Exception as e:
            logger.error(f"Error processing deep debate message: {e}")
    
    async def _analyze_argument_strength(
        self,
        session: DebateSession,
        message: DebateMessage
    ):
        """分析論證強度"""
        try:
            # 進行論證強度分析
            strength_report = await self.argument_analysis_engine.analyze_argument(
                argument_id=message.id,
                content=message.content,
                speaker=message.speaker.value,
                timestamp=message.timestamp
            )
            
            # 將分析結果存儲到消息元數據中
            message.metadata.update({
                "strength_analysis": {
                    "overall_strength": strength_report.overall_strength,
                    "confidence_level": strength_report.confidence_level,
                    "logical_soundness": strength_report.logical_soundness_score,
                    "evidence_count": len(strength_report.evidence_items),
                    "logical_fallacies": [f.value for f in strength_report.logical_fallacies],
                    "improvement_suggestions": strength_report.improvement_suggestions[:3]
                }
            })
            
        except Exception as e:
            logger.error(f"Error analyzing argument strength: {e}")
    
    async def _conduct_advanced_judgment(self, session: DebateSession):
        """進行高級判決"""
        try:
            # 準備參與者論證
            participant_arguments = {}
            for message in session.all_messages:
                if message.speaker in [ModelRole.DEBATER_A, ModelRole.DEBATER_B]:
                    speaker_name = message.speaker.value
                    if speaker_name not in participant_arguments:
                        participant_arguments[speaker_name] = []
                    participant_arguments[speaker_name].append(message.content)
            
            # 構建辯論內容
            debate_content = self._format_debate_history(session.all_messages)
            
            # 構建上下文
            context = {
                "session_id": session.session_id,
                "topic": session.topic,
                "total_rounds": len(session.rounds),
                "debate_duration": session.duration,
                "phase": session.current_phase.value
            }
            
            # 進行高級判決
            advanced_judgment = await self.advanced_judge_engine.conduct_advanced_judgment(
                debate_id=session.session_id,
                topic=session.topic,
                participants=list(participant_arguments.keys()),
                debate_content=debate_content,
                participant_arguments=participant_arguments,
                context=context
            )
            
            # 將高級判決結果存儲到會話元數據中
            session.metadata.update({
                "advanced_judgment": {
                    "judgment_id": advanced_judgment.judgment_id,
                    "winner": advanced_judgment.winner,
                    "winning_margin": advanced_judgment.winning_margin,
                    "overall_quality": advanced_judgment.overall_quality,
                    "judgment_confidence": advanced_judgment.judgment_confidence,
                    "detected_biases": len(advanced_judgment.detected_biases),
                    "key_turning_points": advanced_judgment.key_turning_points[:3],
                    "evaluation_time": advanced_judgment.evaluation_time
                }
            })
            
            return advanced_judgment
            
        except Exception as e:
            logger.error(f"Error conducting advanced judgment: {e}")
            return None
    
    async def _build_consensus_report(self, session: DebateSession):
        """建構共識報告"""
        try:
            # 準備論證數據
            arguments = []
            participants = []
            
            for message in session.all_messages:
                if message.speaker in [ModelRole.DEBATER_A, ModelRole.DEBATER_B]:
                    speaker_name = message.speaker.value
                    if speaker_name not in participants:
                        participants.append(speaker_name)
                    
                    arguments.append({
                        "content": message.content,
                        "speaker": speaker_name,
                        "timestamp": message.timestamp.isoformat(),
                        "round": getattr(message, 'round_number', 0)
                    })
            
            # 構建上下文
            context = {
                "session_id": session.session_id,
                "debate_duration": session.duration,
                "total_rounds": len(session.rounds)
            }
            
            # 建構共識
            consensus_report = await self.consensus_engine.build_consensus(
                debate_id=session.session_id,
                topic=session.topic,
                participants=participants,
                arguments=arguments,
                context=context
            )
            
            # 將共識報告存儲到會話元數據中
            session.metadata.update({
                "consensus_report": {
                    "overall_consensus_level": consensus_report.overall_consensus_level,
                    "polarization_index": consensus_report.polarization_index,
                    "resolution_potential": consensus_report.resolution_potential,
                    "common_grounds_count": len(consensus_report.common_grounds),
                    "disagreements_count": len(consensus_report.disagreements),
                    "solutions_count": len(consensus_report.solutions),
                    "next_steps": consensus_report.next_steps[:3]
                }
            })
            
            return consensus_report
            
        except Exception as e:
            logger.error(f"Error building consensus report: {e}")
            return None
    
    async def get_deep_debate_analysis(self, session_id: str) -> Dict[str, Any]:
        """獲取深度辯論分析"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # 獲取深度辯論分析
            analysis = self.deep_debate_engine.get_debate_analysis()
            
            return {
                "session_id": session_id,
                "analysis": analysis,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting deep debate analysis: {e}")
            return {"error": str(e)}
    
    async def get_argument_strength_comparison(self, session_id: str) -> Dict[str, Any]:
        """獲取論證強度比較"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # 收集所有論證ID
            argument_ids = [msg.id for msg in session.all_messages
                          if msg.speaker in [ModelRole.DEBATER_A, ModelRole.DEBATER_B]]
            
            # 獲取論證比較
            comparison = await self.argument_analysis_engine.compare_arguments(argument_ids)
            
            return {
                "session_id": session_id,
                "comparison": comparison,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting argument strength comparison: {e}")
            return {"error": str(e)}
    
    async def get_consensus_insights(self, session_id: str) -> Dict[str, Any]:
        """獲取共識洞察"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # 建構共識報告（如果還沒有）
            if "consensus_report" not in session.metadata:
                await self._build_consensus_report(session)
            
            consensus_data = session.metadata.get("consensus_report", {})
            
            return {
                "session_id": session_id,
                "consensus_insights": consensus_data,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting consensus insights: {e}")
            return {"error": str(e)}
    
    async def get_advanced_judgment_details(self, session_id: str) -> Dict[str, Any]:
        """獲取高級判決詳情"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # 進行高級判決（如果還沒有）
            if "advanced_judgment" not in session.metadata:
                await self._conduct_advanced_judgment(session)
            
            judgment_data = session.metadata.get("advanced_judgment", {})
            
            return {
                "session_id": session_id,
                "advanced_judgment": judgment_data,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting advanced judgment details: {e}")
            return {"error": str(e)}


# 全局辯論引擎實例
debate_engine = None

def get_debate_engine() -> DebateEngine:
    """獲取辯論引擎實例"""
    global debate_engine
    if debate_engine is None:
        debate_engine = DebateEngine()
    return debate_engine
