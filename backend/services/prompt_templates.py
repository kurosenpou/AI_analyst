"""
Prompt Template System for AI Debate
Manages prompts for different roles and debate scenarios
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from services.model_pool import ModelRole

class PromptType(Enum):
    """Prompt類型"""
    SYSTEM = "system"           # 系統提示
    OPENING = "opening"         # 開場陳述
    REBUTTAL = "rebuttal"       # 反駁
    CLOSING = "closing"         # 總結陳詞
    JUDGMENT = "judgment"       # 裁判評決

@dataclass
class PromptTemplate:
    """Prompt模板"""
    template_id: str
    role: ModelRole
    prompt_type: PromptType
    template: str
    variables: List[str]        # 模板中的變數
    description: str

class PromptTemplateManager:
    """
    Prompt模板管理器
    為不同角色和場景提供合適的prompt模板
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """初始化所有prompt模板"""
        
        # ================== 系統提示模板 ==================
        
        # 辯論者A系統提示
        self.templates["debater_a_system"] = PromptTemplate(
            template_id="debater_a_system",
            role=ModelRole.DEBATER_A,
            prompt_type=PromptType.SYSTEM,
            template="""你是一位專業的商業分析辯論專家，在這次辯論中擔任「正方」角色。

你的特點：
- 邏輯清晰，論證嚴謹
- 善於從數據中挖掘支持論點的證據
- 能夠預見並回應反方可能的攻擊點
- 保持專業和建設性的辯論態度

辯論規則：
1. 基於提供的商業數據進行分析
2. 提出明確的論點並用數據支撐
3. 尊重對手，但堅持自己的立場
4. 每次發言控制在200-300字內
5. 避免人身攻擊，專注於事實和邏輯

你的目標是說服裁判接受你的觀點。""",
            variables=[],
            description="辯論者A的系統角色設定"
        )
        
        # 辯論者B系統提示
        self.templates["debater_b_system"] = PromptTemplate(
            template_id="debater_b_system",
            role=ModelRole.DEBATER_B,
            prompt_type=PromptType.SYSTEM,
            template="""你是一位資深的商業顧問，在這次辯論中擔任「反方」角色。

你的特點：
- 批判性思維強，善於發現問題
- 從風險管理角度分析商業決策
- 能夠質疑表面數據，深入挖掘潛在問題
- 以務實和謹慎的態度進行辯論

辯論規則：
1. 基於提供的商業數據進行分析
2. 指出對方論點的薄弱環節
3. 提出合理的質疑和替代方案
4. 每次發言控制在200-300字內
5. 保持專業態度，避免情緒化表達

你的目標是通過合理質疑來幫助找到最佳的商業決策。""",
            variables=[],
            description="辯論者B的系統角色設定"
        )
        
        # 裁判系統提示
        self.templates["judge_system"] = PromptTemplate(
            template_id="judge_system",
            role=ModelRole.JUDGE,
            prompt_type=PromptType.SYSTEM,
            template="""你是一位經驗豐富的商業決策專家，擔任本次辯論的「裁判」。

你的職責：
- 客觀評估雙方的論點和證據
- 關注邏輯性、數據支撐和實用性
- 識別每一方的優點和不足
- 最終做出基於事實的判斷

評判標準：
1. 論點的邏輯性和一致性
2. 數據使用的準確性和相關性
3. 對商業風險的考慮程度
4. 解決方案的可行性
5. 論證的說服力

注意事項：
- 保持中立，不偏向任何一方
- 基於事實和邏輯進行評判
- 提供建設性的反饋
- 最終判決要有明確的理由說明""",
            variables=[],
            description="裁判的系統角色設定"
        )
        
        # ================== 開場陳述模板 ==================
        
        # 辯論者A開場
        self.templates["debater_a_opening"] = PromptTemplate(
            template_id="debater_a_opening",
            role=ModelRole.DEBATER_A,
            prompt_type=PromptType.OPENING,
            template="""基於以下商業數據和背景信息，請以正方立場進行開場陳述：

**辯論主題**: {topic}
**商業數據**: 
{business_data}

**額外背景**: {context}

請結構化地陳述你的觀點：
1. 明確表達你的核心立場
2. 列出3-4個主要支持論點
3. 用數據證明你的觀點
4. 簡要說明預期的商業價值

開場陳述應該有說服力且專業。""",
            variables=["topic", "business_data", "context"],
            description="辯論者A的開場陳述模板"
        )
        
        # 辯論者B開場
        self.templates["debater_b_opening"] = PromptTemplate(
            template_id="debater_b_opening",
            role=ModelRole.DEBATER_B,
            prompt_type=PromptType.OPENING,
            template="""基於以下商業數據和背景信息，請以反方立場進行開場陳述：

**辯論主題**: {topic}
**商業數據**: 
{business_data}

**額外背景**: {context}

請從批判角度陳述你的觀點：
1. 明確表達你的質疑立場
2. 指出數據中的潛在問題或局限性
3. 列出3-4個主要風險點
4. 提出更謹慎或替代的方案

開場陳述應該基於事實，有理有據。""",
            variables=["topic", "business_data", "context"],
            description="辯論者B的開場陳述模板"
        )
        
        # ================== 反駁模板 ==================
        
        # 通用反駁模板
        self.templates["general_rebuttal"] = PromptTemplate(
            template_id="general_rebuttal",
            role=ModelRole.DEBATER_A,  # 可用於任何辯論者
            prompt_type=PromptType.REBUTTAL,
            template="""請針對對方的以下觀點進行反駁：

**對方觀點**: 
{opponent_argument}

**當前辯論上下文**: 
{debate_context}

**可用數據**: 
{available_data}

反駁要求：
1. 指出對方論點的具體問題
2. 提供反駁的事實依據
3. 強化自己的立場
4. 保持邏輯一致性

請專業且有力地進行反駁。""",
            variables=["opponent_argument", "debate_context", "available_data"],
            description="通用反駁模板"
        )
        
        # ================== 裁判評決模板 ==================
        
        # 輪次評決
        self.templates["round_judgment"] = PromptTemplate(
            template_id="round_judgment",
            role=ModelRole.JUDGE,
            prompt_type=PromptType.JUDGMENT,
            template="""請對本輪辯論進行評判：

**辯論主題**: {topic}

**正方觀點**: 
{debater_a_arguments}

**反方觀點**: 
{debater_b_arguments}

**商業數據背景**: 
{business_data}

評判要求：
1. 客觀分析雙方論點的優劣
2. 評估數據使用的準確性
3. 考慮商業可行性和風險
4. 指出本輪的勝出方並說明理由
5. 為下一輪提供辯論方向建議

請提供公正、專業的評判。""",
            variables=["topic", "debater_a_arguments", "debater_b_arguments", "business_data"],
            description="輪次評判模板"
        )
        
        # 最終評決
        self.templates["final_judgment"] = PromptTemplate(
            template_id="final_judgment",
            role=ModelRole.JUDGE,
            prompt_type=PromptType.JUDGMENT,
            template="""請對整場辯論進行最終評決：

**辯論主題**: {topic}

**完整辯論記錄**: 
{full_debate_history}

**商業數據**: 
{business_data}

最終評決要求：
1. 綜合評估整場辯論的質量
2. 分析雙方論點的說服力
3. 評價數據分析的深度和準確性
4. 宣布最終勝出方
5. 提供商業建議和決策建議
6. 總結關鍵洞察和學習點

請提供全面、權威的最終評決。""",
            variables=["topic", "full_debate_history", "business_data"],
            description="最終評決模板"
        )
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """獲取指定的prompt模板"""
        return self.templates.get(template_id)
    
    def get_templates_by_role(self, role: ModelRole) -> List[PromptTemplate]:
        """獲取指定角色的所有模板"""
        return [t for t in self.templates.values() if t.role == role]
    
    def get_templates_by_type(self, prompt_type: PromptType) -> List[PromptTemplate]:
        """獲取指定類型的所有模板"""
        return [t for t in self.templates.values() if t.prompt_type == prompt_type]
    
    def render_template(self, template_id: str, **kwargs) -> str:
        """
        渲染模板，替換變數
        
        Args:
            template_id: 模板ID
            **kwargs: 模板變數的值
            
        Returns:
            渲染後的prompt文本
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"模板 {template_id} 缺少必需的變數: {missing_var}")
    
    def validate_template_variables(self, template_id: str, variables: Dict[str, Any]) -> List[str]:
        """
        驗證模板變數是否完整
        
        Returns:
            缺失的變數列表
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        missing = []
        for var in template.variables:
            if var not in variables:
                missing.append(var)
        
        return missing
    
    def create_custom_template(
        self,
        template_id: str,
        role: ModelRole,
        prompt_type: PromptType,
        template: str,
        variables: List[str],
        description: str
    ) -> PromptTemplate:
        """創建自定義模板"""
        
        custom_template = PromptTemplate(
            template_id=template_id,
            role=role,
            prompt_type=prompt_type,
            template=template,
            variables=variables,
            description=description
        )
        
        self.templates[template_id] = custom_template
        return custom_template
    
    def list_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """列出所有模板的基本信息"""
        result = {}
        for template_id, template in self.templates.items():
            result[template_id] = {
                "role": template.role.value,
                "type": template.prompt_type.value,
                "variables": template.variables,
                "description": template.description
            }
        return result

# 全局模板管理器實例
prompt_manager = None

def get_prompt_manager() -> PromptTemplateManager:
    """獲取或創建全局prompt模板管理器實例"""
    global prompt_manager
    if prompt_manager is None:
        prompt_manager = PromptTemplateManager()
    return prompt_manager
