"""
Debate Quality Assessment System
辯論質量評估系統
Features: 論證強度分析、一致性評估、說服力測量
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import math

from .openrouter_client import get_openrouter_client
from .monitoring import record_metric, trigger_custom_alert, AlertLevel

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """質量評估維度"""
    ARGUMENT_STRENGTH = "argument_strength"       # 論證強度
    LOGICAL_COHERENCE = "logical_coherence"      # 邏輯一致性
    EVIDENCE_QUALITY = "evidence_quality"        # 證據質量
    PERSUASIVENESS = "persuasiveness"            # 說服力
    CLARITY = "clarity"                          # 清晰度
    RELEVANCE = "relevance"                      # 相關性
    ORIGINALITY = "originality"                  # 原創性
    EMOTIONAL_APPEAL = "emotional_appeal"        # 情感感染力


class DebateRole(Enum):
    """辯論角色"""
    OPENING_STATEMENT = "opening_statement"      # 開場陳述
    REBUTTAL = "rebuttal"                       # 反駁
    COUNTER_REBUTTAL = "counter_rebuttal"       # 反反駁
    CLOSING_STATEMENT = "closing_statement"     # 結束陳述


@dataclass
class QualityScore:
    """質量評分"""
    dimension: QualityDimension
    score: float                 # 0-1之間的評分
    confidence: float           # 評分置信度
    reasoning: str              # 評分理由
    evidence: List[str]         # 支持證據


@dataclass
class ArgumentAnalysis:
    """論證分析結果"""
    content: str
    role: DebateRole
    speaker: str
    
    # 基礎統計
    word_count: int
    sentence_count: int
    reading_level: float
    
    # 質量評分
    quality_scores: Dict[QualityDimension, QualityScore] = field(default_factory=dict)
    
    # 結構分析
    main_claims: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    logical_fallacies: List[str] = field(default_factory=list)
    
    # 語言特徵
    sentiment_score: float = 0.0
    emotional_markers: List[str] = field(default_factory=list)
    rhetorical_devices: List[str] = field(default_factory=list)
    
    # 綜合評價
    overall_quality: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class DebateQualityReport:
    """辯論質量報告"""
    debate_id: str
    topic: str
    participants: Dict[str, str]
    
    # 個體分析
    argument_analyses: List[ArgumentAnalysis] = field(default_factory=list)
    
    # 整體評估
    debate_flow_score: float = 0.0
    engagement_level: float = 0.0
    depth_of_discussion: float = 0.0
    balance_score: float = 0.0
    
    # 比較分析
    participant_rankings: Dict[str, float] = field(default_factory=dict)
    winning_arguments: List[str] = field(default_factory=list)
    debate_highlights: List[str] = field(default_factory=list)
    
    # 改進建議
    debate_improvements: List[str] = field(default_factory=list)
    moderator_notes: List[str] = field(default_factory=list)
    
    generated_at: datetime = field(default_factory=datetime.now)


class DebateQualityAssessor:
    """
    辯論質量評估器
    
    負責：
    1. 分析論證結構和質量
    2. 評估邏輯一致性
    3. 測量說服力和影響力
    4. 生成改進建議
    """
    
    def __init__(self):
        self.client = get_openrouter_client()
        
        # 評估模型配置
        self.assessment_model = "anthropic/claude-3-5-sonnet-20241022"
        
        # 停用詞列表（簡化版）
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # 論證模式
        self.argument_patterns = {
            'claim': r'(?:I believe|I argue|My position is|It is clear that|The evidence shows)',
            'evidence': r'(?:According to|Research shows|Studies indicate|Data reveals|Statistics show)',
            'reasoning': r'(?:Therefore|Thus|Consequently|As a result|This means that)',
            'counterpoint': r'(?:However|Nevertheless|On the other hand|Critics argue|Some may say)',
            'refutation': r'(?:This is wrong because|This fails to consider|The flaw in this argument)'
        }
        
        # 邏輯謬誤模式
        self.fallacy_patterns = {
            'ad_hominem': r'(?:you are|your character|personally attack)',
            'straw_man': r'(?:you claim|you say|your position).*(?:but that\'s not)',
            'false_dilemma': r'(?:either.*or|only two options|must choose)',
            'slippery_slope': r'(?:will lead to|inevitably result|chain reaction)',
            'appeal_to_authority': r'(?:expert says|authority claims|famous person)'
        }
        
        # 修辭手法模式
        self.rhetorical_patterns = {
            'metaphor': r'(?:like|as if|similar to|metaphorically)',
            'repetition': r'(.+)\1',
            'question': r'\?',
            'emphasis': r'(?:very|extremely|absolutely|definitely|clearly)',
            'analogy': r'(?:analogous to|similar to|parallel to|comparable to)'
        }
        
        logger.info("Debate quality assessor initialized")
    
    def _simple_tokenize_sentences(self, text: str) -> List[str]:
        """簡單的句子分割"""
        # 基於標點符號分割句子
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _simple_tokenize_words(self, text: str) -> List[str]:
        """簡單的詞語分割"""
        # 移除標點符號並分割單詞
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.lower().split()
        return [word for word in words if word not in self.stop_words]
    
    def _calculate_reading_level(self, text: str) -> float:
        """計算閱讀難度（簡化版）"""
        sentences = self._simple_tokenize_sentences(text)
        words = self._simple_tokenize_words(text)
        
        if not sentences or not words:
            return 5.0
        
        avg_sentence_length = len(words) / len(sentences)
        # 簡化的可讀性評分
        reading_level = max(1, min(20, avg_sentence_length / 2))
        return reading_level
    
    def _calculate_sentiment(self, text: str) -> float:
        """簡單的情感分析"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'benefit']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'problem', 'issue', 'concern']
        
        words = self._simple_tokenize_words(text)
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words
    
    async def analyze_argument(
        self,
        content: str,
        role: DebateRole,
        speaker: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ArgumentAnalysis:
        """分析單個論證"""
        
        logger.info(f"Analyzing argument from {speaker} in role {role.value}")
        
        # 基礎統計分析
        analysis = ArgumentAnalysis(
            content=content,
            role=role,
            speaker=speaker,
            word_count=len(self._simple_tokenize_words(content)),
            sentence_count=len(self._simple_tokenize_sentences(content)),
            reading_level=self._calculate_reading_level(content)
        )
        
        # 並行執行多個分析任務
        tasks = [
            self._analyze_argument_structure(content, analysis),
            self._assess_logical_coherence(content, analysis),
            self._evaluate_evidence_quality(content, analysis),
            self._measure_persuasiveness(content, analysis, context),
            self._analyze_clarity(content, analysis),
            self._assess_relevance(content, analysis, context),
            self._detect_logical_fallacies(content, analysis),
            self._analyze_language_features(content, analysis)
        ]
        
        await asyncio.gather(*tasks)
        
        # 計算綜合質量評分
        await self._calculate_overall_quality(analysis)
        
        # 生成改進建議
        await self._generate_improvement_suggestions(analysis)
        
        logger.info(f"Argument analysis completed, overall quality: {analysis.overall_quality:.3f}")
        
        return analysis
    
    async def _analyze_argument_structure(self, content: str, analysis: ArgumentAnalysis):
        """分析論證結構"""
        
        prompt = f"""
        分析以下論證的結構，識別主要論點、支持證據和推理邏輯：
        
        論證內容：
        {content}
        
        請提供：
        1. 主要論點（claims）
        2. 支持證據（evidence）
        3. 推理邏輯（reasoning）
        4. 論證強度評分（0-1）
        
        請以JSON格式返回結果。
        """
        
        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.assessment_model,
                max_tokens=1000,
                temperature=0.3
            )
            
            result = json.loads(response)
            
            analysis.main_claims = result.get('claims', [])
            analysis.supporting_evidence = result.get('evidence', [])
            
            # 記錄論證強度評分
            strength_score = result.get('argument_strength', 0.5)
            analysis.quality_scores[QualityDimension.ARGUMENT_STRENGTH] = QualityScore(
                dimension=QualityDimension.ARGUMENT_STRENGTH,
                score=strength_score,
                confidence=0.8,
                reasoning=result.get('strength_reasoning', ''),
                evidence=result.get('strength_evidence', [])
            )
            
        except Exception as e:
            logger.error(f"Error analyzing argument structure: {e}")
            # 回退到規則基礎分析
            await self._fallback_structure_analysis(content, analysis)
    
    async def _fallback_structure_analysis(self, content: str, analysis: ArgumentAnalysis):
        """結構分析的回退方法"""
        sentences = self._simple_tokenize_sentences(content)
        
        claims = []
        evidence = []
        
        for sentence in sentences:
            if any(pattern in sentence.lower() for pattern in ['i believe', 'i argue', 'my position']):
                claims.append(sentence)
            elif any(pattern in sentence.lower() for pattern in ['according to', 'research shows', 'data']):
                evidence.append(sentence)
        
        analysis.main_claims = claims
        analysis.supporting_evidence = evidence
        
        # 簡單的強度評分
        strength = min(1.0, (len(claims) * 0.3 + len(evidence) * 0.4) / len(sentences)) if sentences else 0.5
        analysis.quality_scores[QualityDimension.ARGUMENT_STRENGTH] = QualityScore(
            dimension=QualityDimension.ARGUMENT_STRENGTH,
            score=strength,
            confidence=0.6,
            reasoning="基於規則的分析",
            evidence=[]
        )
    
    async def _assess_logical_coherence(self, content: str, analysis: ArgumentAnalysis):
        """評估邏輯一致性"""
        
        prompt = f"""
        評估以下論證的邏輯一致性：
        
        論證內容：
        {content}
        
        評估標準：
        1. 前後邏輯是否一致
        2. 結論是否從前提自然推出
        3. 是否存在邏輯跳躍
        4. 推理鏈是否完整
        
        請提供：
        1. 邏輯一致性評分（0-1）
        2. 邏輯問題描述
        3. 改進建議
        
        請以JSON格式返回。
        """
        
        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.assessment_model,
                max_tokens=800,
                temperature=0.2
            )
            
            result = json.loads(response)
            
            coherence_score = result.get('coherence_score', 0.5)
            analysis.quality_scores[QualityDimension.LOGICAL_COHERENCE] = QualityScore(
                dimension=QualityDimension.LOGICAL_COHERENCE,
                score=coherence_score,
                confidence=0.85,
                reasoning=result.get('coherence_reasoning', ''),
                evidence=result.get('logical_issues', [])
            )
            
        except Exception as e:
            logger.error(f"Error assessing logical coherence: {e}")
            # 簡單的一致性檢查
            sentences = self._simple_tokenize_sentences(content)
            contradiction_words = ['however', 'but', 'although', 'despite']
            contradictions = sum(1 for sent in sentences for word in contradiction_words if word in sent.lower())
            
            coherence = max(0.3, 1.0 - (contradictions / len(sentences))) if sentences else 0.5
            analysis.quality_scores[QualityDimension.LOGICAL_COHERENCE] = QualityScore(
                dimension=QualityDimension.LOGICAL_COHERENCE,
                score=coherence,
                confidence=0.5,
                reasoning="基於矛盾詞頻率的簡單評估",
                evidence=[]
            )
    
    async def _evaluate_evidence_quality(self, content: str, analysis: ArgumentAnalysis):
        """評估證據質量"""
        
        # 檢測證據類型和來源
        evidence_markers = {
            'research': r'(?:study|research|investigation|experiment)',
            'statistics': r'(?:statistics|data|numbers|percentage|%)',
            'expert': r'(?:expert|professor|doctor|authority)',
            'example': r'(?:for example|for instance|case study)',
            'comparison': r'(?:compared to|in contrast|versus)'
        }
        
        evidence_types = []
        for evidence_type, pattern in evidence_markers.items():
            if re.search(pattern, content, re.IGNORECASE):
                evidence_types.append(evidence_type)
        
        # 評估證據質量
        base_score = 0.3
        type_bonus = len(evidence_types) * 0.15
        specificity_bonus = 0.2 if re.search(r'\d+', content) else 0  # 包含具體數據
        
        evidence_score = min(1.0, base_score + type_bonus + specificity_bonus)
        
        analysis.quality_scores[QualityDimension.EVIDENCE_QUALITY] = QualityScore(
            dimension=QualityDimension.EVIDENCE_QUALITY,
            score=evidence_score,
            confidence=0.7,
            reasoning=f"檢測到 {len(evidence_types)} 種證據類型: {', '.join(evidence_types)}",
            evidence=evidence_types
        )
    
    async def _measure_persuasiveness(self, content: str, analysis: ArgumentAnalysis, context: Optional[Dict]):
        """測量說服力"""
        
        prompt = f"""
        評估以下論證的說服力：
        
        論證內容：
        {content}
        
        評估維度：
        1. 情感感染力
        2. 邏輯說服力
        3. 可信度
        4. 影響力
        
        請提供：
        1. 說服力評分（0-1）
        2. 情感感染力評分（0-1）
        3. 說服技巧分析
        
        請以JSON格式返回。
        """
        
        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.assessment_model,
                max_tokens=600,
                temperature=0.4
            )
            
            result = json.loads(response)
            
            persuasiveness_score = result.get('persuasiveness_score', 0.5)
            emotional_score = result.get('emotional_score', 0.5)
            
            analysis.quality_scores[QualityDimension.PERSUASIVENESS] = QualityScore(
                dimension=QualityDimension.PERSUASIVENESS,
                score=persuasiveness_score,
                confidence=0.8,
                reasoning=result.get('persuasiveness_reasoning', ''),
                evidence=result.get('persuasive_techniques', [])
            )
            
            analysis.quality_scores[QualityDimension.EMOTIONAL_APPEAL] = QualityScore(
                dimension=QualityDimension.EMOTIONAL_APPEAL,
                score=emotional_score,
                confidence=0.8,
                reasoning=result.get('emotional_reasoning', ''),
                evidence=result.get('emotional_techniques', [])
            )
            
        except Exception as e:
            logger.error(f"Error measuring persuasiveness: {e}")
            # 回退到情感分析
            sentiment = self._calculate_sentiment(content)
            emotional_intensity = abs(sentiment)
            
            analysis.quality_scores[QualityDimension.PERSUASIVENESS] = QualityScore(
                dimension=QualityDimension.PERSUASIVENESS,
                score=emotional_intensity * 0.7 + 0.3,
                confidence=0.6,
                reasoning="基於情感強度的簡單評估",
                evidence=[]
            )
    
    async def _analyze_clarity(self, content: str, analysis: ArgumentAnalysis):
        """分析清晰度"""
        
        # 可讀性指標
        reading_level = self._calculate_reading_level(content)
        
        # 句子長度分析
        sentences = self._simple_tokenize_sentences(content)
        avg_sentence_length = analysis.word_count / analysis.sentence_count if analysis.sentence_count > 0 else 0
        
        # 清晰度評分
        readability_score = max(0.2, min(1.0, (15 - reading_level) / 15))  # 15以下為好
        length_penalty = max(0, (avg_sentence_length - 20) / 30)  # 超過20詞的句子扣分
        clarity_score = max(0.2, readability_score - length_penalty)
        
        analysis.quality_scores[QualityDimension.CLARITY] = QualityScore(
            dimension=QualityDimension.CLARITY,
            score=clarity_score,
            confidence=0.9,
            reasoning=f"閱讀難度: {reading_level:.1f}, 平均句長: {avg_sentence_length:.1f}詞",
            evidence=[f"閱讀難度級別: {reading_level:.1f}"]
        )
    
    async def _assess_relevance(self, content: str, analysis: ArgumentAnalysis, context: Optional[Dict]):
        """評估相關性"""
        
        if not context or 'topic' not in context:
            # 沒有上下文，給予中等分數
            relevance_score = 0.7
            reasoning = "無法評估相關性：缺少辯論主題上下文"
        else:
            topic = context['topic']
            
            prompt = f"""
            評估以下論證與辯論主題的相關性：
            
            辯論主題：{topic}
            論證內容：{content}
            
            評估標準：
            1. 是否直接回應主題
            2. 是否偏離核心議題
            3. 是否提供相關例證
            
            請提供相關性評分（0-1）和評估理由。
            請以JSON格式返回。
            """
            
            try:
                response = await self.client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.assessment_model,
                    max_tokens=400,
                    temperature=0.2
                )
                
                result = json.loads(response)
                relevance_score = result.get('relevance_score', 0.7)
                reasoning = result.get('reasoning', '')
                
            except Exception as e:
                logger.error(f"Error assessing relevance: {e}")
                relevance_score = 0.7
                reasoning = "評估過程中出現錯誤"
        
        analysis.quality_scores[QualityDimension.RELEVANCE] = QualityScore(
            dimension=QualityDimension.RELEVANCE,
            score=relevance_score,
            confidence=0.75,
            reasoning=reasoning,
            evidence=[]
        )
    
    async def _detect_logical_fallacies(self, content: str, analysis: ArgumentAnalysis):
        """檢測邏輯謬誤"""
        
        detected_fallacies = []
        
        for fallacy_name, pattern in self.fallacy_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                detected_fallacies.append(fallacy_name)
        
        analysis.logical_fallacies = detected_fallacies
        
        # 記錄到監控系統
        if detected_fallacies:
            record_metric("logical_fallacies_detected", len(detected_fallacies), {
                "fallacies": ",".join(detected_fallacies)
            })
    
    async def _analyze_language_features(self, content: str, analysis: ArgumentAnalysis):
        """分析語言特徵"""
        
        # 情感分析
        sentiment = self._calculate_sentiment(content)
        analysis.sentiment_score = sentiment
        
        # 檢測修辭手法
        rhetorical_devices = []
        for device_name, pattern in self.rhetorical_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                rhetorical_devices.append(device_name)
        
        analysis.rhetorical_devices = rhetorical_devices
        
        # 檢測情感標記詞
        emotional_words = ['passionate', 'concerned', 'worried', 'excited', 'disappointed', 'hopeful']
        found_emotional_markers = [word for word in emotional_words if word in content.lower()]
        analysis.emotional_markers = found_emotional_markers
    
    async def _calculate_overall_quality(self, analysis: ArgumentAnalysis):
        """計算綜合質量評分"""
        
        if not analysis.quality_scores:
            analysis.overall_quality = 0.5
            return
        
        # 權重配置
        weights = {
            QualityDimension.ARGUMENT_STRENGTH: 0.25,
            QualityDimension.LOGICAL_COHERENCE: 0.20,
            QualityDimension.EVIDENCE_QUALITY: 0.15,
            QualityDimension.PERSUASIVENESS: 0.15,
            QualityDimension.CLARITY: 0.10,
            QualityDimension.RELEVANCE: 0.10,
            QualityDimension.EMOTIONAL_APPEAL: 0.05
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for dimension, quality_score in analysis.quality_scores.items():
            weight = weights.get(dimension, 0.05)
            weighted_sum += quality_score.score * weight * quality_score.confidence
            total_weight += weight * quality_score.confidence
        
        analysis.overall_quality = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # 調整基於邏輯謬誤的懲罰
        fallacy_penalty = len(analysis.logical_fallacies) * 0.05
        analysis.overall_quality = max(0.1, analysis.overall_quality - fallacy_penalty)
    
    async def _generate_improvement_suggestions(self, analysis: ArgumentAnalysis):
        """生成改進建議"""
        
        suggestions = []
        
        # 基於質量評分生成建議
        for dimension, quality_score in analysis.quality_scores.items():
            if quality_score.score < 0.6:
                if dimension == QualityDimension.ARGUMENT_STRENGTH:
                    suggestions.append("加強主要論點的表述，提供更多支持證據")
                elif dimension == QualityDimension.LOGICAL_COHERENCE:
                    suggestions.append("改善邏輯連接，確保推理鏈條完整")
                elif dimension == QualityDimension.EVIDENCE_QUALITY:
                    suggestions.append("引用更具權威性和具體的證據")
                elif dimension == QualityDimension.CLARITY:
                    suggestions.append("簡化句子結構，提高表達清晰度")
                elif dimension == QualityDimension.RELEVANCE:
                    suggestions.append("確保論證緊密圍繞核心議題")
        
        # 基於邏輯謬誤生成建議
        if analysis.logical_fallacies:
            suggestions.append(f"避免邏輯謬誤：{', '.join(analysis.logical_fallacies)}")
        
        # 基於長度和結構生成建議
        if analysis.word_count < 50:
            suggestions.append("論證過於簡短，需要更詳細的論述")
        elif analysis.word_count > 300:
            suggestions.append("論證過於冗長，建議精簡表達")
        
        analysis.improvement_suggestions = suggestions
        
        # 識別優勢
        strengths = []
        for dimension, quality_score in analysis.quality_scores.items():
            if quality_score.score > 0.8:
                strengths.append(f"{dimension.value}表現優秀")
        
        analysis.strengths = strengths
    
    async def generate_debate_report(
        self,
        debate_id: str,
        topic: str,
        participants: Dict[str, str],
        arguments: List[Dict[str, Any]]
    ) -> DebateQualityReport:
        """生成完整的辯論質量報告"""
        
        logger.info(f"Generating debate quality report for debate {debate_id}")
        
        report = DebateQualityReport(
            debate_id=debate_id,
            topic=topic,
            participants=participants
        )
        
        # 分析所有論證
        analysis_tasks = []
        for arg in arguments:
            role = DebateRole(arg.get('role', 'opening_statement'))
            speaker = arg.get('speaker', 'unknown')
            content = arg.get('content', '')
            context = {'topic': topic, 'debate_id': debate_id}
            
            task = self.analyze_argument(content, role, speaker, context)
            analysis_tasks.append(task)
        
        report.argument_analyses = await asyncio.gather(*analysis_tasks)
        
        # 計算整體指標
        await self._calculate_debate_metrics(report)
        
        # 生成參與者排名
        await self._rank_participants(report)
        
        # 識別精彩論證
        await self._identify_highlights(report)
        
        # 生成整體改進建議
        await self._generate_debate_improvements(report)
        
        logger.info(f"Debate report generated with {len(report.argument_analyses)} argument analyses")
        
        return report
    
    async def _calculate_debate_metrics(self, report: DebateQualityReport):
        """計算辯論整體指標"""
        
        if not report.argument_analyses:
            return
        
        # 辯論流暢度評分
        quality_scores = [analysis.overall_quality for analysis in report.argument_analyses]
        report.debate_flow_score = sum(quality_scores) / len(quality_scores)
        
        # 參與度評分
        total_words = sum(analysis.word_count for analysis in report.argument_analyses)
        avg_words_per_turn = total_words / len(report.argument_analyses)
        report.engagement_level = min(1.0, avg_words_per_turn / 150)  # 150詞為參考基準
        
        # 討論深度評分
        evidence_counts = [len(analysis.supporting_evidence) for analysis in report.argument_analyses]
        avg_evidence = sum(evidence_counts) / len(evidence_counts) if evidence_counts else 0
        report.depth_of_discussion = min(1.0, avg_evidence / 3)  # 3個證據為參考基準
        
        # 平衡性評分
        participant_words = {}
        for analysis in report.argument_analyses:
            if analysis.speaker not in participant_words:
                participant_words[analysis.speaker] = 0
            participant_words[analysis.speaker] += analysis.word_count
        
        if len(participant_words) > 1:
            word_counts = list(participant_words.values())
            max_words = max(word_counts)
            min_words = min(word_counts)
            balance = 1.0 - ((max_words - min_words) / max_words) if max_words > 0 else 1.0
            report.balance_score = balance
        else:
            report.balance_score = 1.0
    
    async def _rank_participants(self, report: DebateQualityReport):
        """對參與者進行排名"""
        
        participant_scores = {}
        participant_counts = {}
        
        for analysis in report.argument_analyses:
            speaker = analysis.speaker
            if speaker not in participant_scores:
                participant_scores[speaker] = 0
                participant_counts[speaker] = 0
            
            participant_scores[speaker] += analysis.overall_quality
            participant_counts[speaker] += 1
        
        # 計算平均分
        for speaker in participant_scores:
            if participant_counts[speaker] > 0:
                participant_scores[speaker] /= participant_counts[speaker]
        
        report.participant_rankings = participant_scores
    
    async def _identify_highlights(self, report: DebateQualityReport):
        """識別辯論亮點"""
        
        highlights = []
        winning_arguments = []
        
        # 找出質量最高的論證
        best_analyses = sorted(
            report.argument_analyses,
            key=lambda x: x.overall_quality,
            reverse=True
        )[:3]
        
        for analysis in best_analyses:
            if analysis.overall_quality > 0.8:
                highlights.append(f"{analysis.speaker}的{analysis.role.value}表現出色 (質量: {analysis.overall_quality:.2f})")
                winning_arguments.append(analysis.content[:100] + "...")
        
        # 識別精彩的修辭手法使用
        for analysis in report.argument_analyses:
            if len(analysis.rhetorical_devices) >= 3:
                highlights.append(f"{analysis.speaker}巧妙運用了多種修辭手法：{', '.join(analysis.rhetorical_devices)}")
        
        report.debate_highlights = highlights
        report.winning_arguments = winning_arguments
    
    async def _generate_debate_improvements(self, report: DebateQualityReport):
        """生成辯論整體改進建議"""
        
        improvements = []
        
        # 基於整體指標生成建議
        if report.debate_flow_score < 0.6:
            improvements.append("整體辯論質量需要提升，建議參與者加強論證準備")
        
        if report.engagement_level < 0.5:
            improvements.append("參與度較低，建議增加論證的詳細程度和深度")
        
        if report.depth_of_discussion < 0.5:
            improvements.append("討論深度不足，建議提供更多具體證據和例證")
        
        if report.balance_score < 0.7:
            improvements.append("辯論參與不夠平衡，建議調整發言時間分配")
        
        # 基於常見問題生成建議
        fallacy_count = sum(len(analysis.logical_fallacies) for analysis in report.argument_analyses)
        if fallacy_count > 2:
            improvements.append("檢測到較多邏輯謬誤，建議參與者加強邏輯訓練")
        
        report.debate_improvements = improvements


# 全局質量評估器實例
quality_assessor = None

def get_quality_assessor() -> DebateQualityAssessor:
    """獲取辯論質量評估器實例"""
    global quality_assessor
    if quality_assessor is None:
        quality_assessor = DebateQualityAssessor()
    return quality_assessor
