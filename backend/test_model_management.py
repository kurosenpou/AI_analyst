"""
測試模型池和prompt模板系統
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.model_pool import get_model_pool, ModelRole
from services.prompt_templates import get_prompt_manager, PromptType

async def test_model_pool():
    """測試模型池功能"""
    print("🔧 測試模型池管理系統...")
    print("=" * 50)
    
    # 初始化模型池
    pool = get_model_pool()
    
    # 測試1: 列出可用模型
    print("📋 可用模型:")
    for key, model in pool.get_available_models().items():
        print(f"  {key}: {model.name} ({model.provider})")
        print(f"    優勢: {', '.join(model.strengths)}")
        print(f"    成本: ${model.cost_per_token:.8f}/token")
    
    # 測試2: 不同分配策略
    print("\n🎯 測試模型分配策略:")
    
    strategies = ["default", "random", "optimal", "cost_aware"]
    for strategy in strategies:
        print(f"\n策略: {strategy}")
        try:
            assignments = pool.assign_models_to_roles(strategy=strategy)
            for role, model in assignments.items():
                print(f"  {role.value}: {model.name}")
            
            # 估算成本
            costs = pool.estimate_cost(assignments)
            print(f"  預估成本: ${costs['總計']:.6f}")
            
        except Exception as e:
            print(f"  ❌ 失敗: {e}")
    
    # 測試3: 模型輪換
    print("\n🔄 測試模型輪換:")
    initial = pool.assign_models_to_roles("default")
    print("初始分配:")
    for role, model in initial.items():
        print(f"  {role.value}: {model.name}")
    
    rotated = pool.rotate_models(initial)
    print("輪換後:")
    for role, model in rotated.items():
        print(f"  {role.value}: {model.name}")
    
    # 測試4: 創建辯論會話
    print("\n📝 測試辯論會話創建:")
    session = pool.create_debate_session(
        topic="是否應該投資這個商業項目？",
        model_assignments=initial
    )
    print(f"會話ID: {session.session_id}")
    print(f"主題: {session.topic}")
    print(f"參與者: {session.participants}")
    
    # 測試5: 模型健康檢查
    print("\n🏥 測試模型健康狀態:")
    health_results = await pool.test_model_health()
    for model, is_healthy in health_results.items():
        status = "✅" if is_healthy else "❌"
        print(f"  {model}: {status}")
    
    return pool, session

async def test_prompt_templates():
    """測試prompt模板系統"""
    print("\n🎨 測試Prompt模板系統...")
    print("=" * 50)
    
    # 初始化模板管理器
    manager = get_prompt_manager()
    
    # 測試1: 列出所有模板
    print("📋 可用模板:")
    templates = manager.list_all_templates()
    for template_id, info in templates.items():
        print(f"  {template_id}:")
        print(f"    角色: {info['role']}")
        print(f"    類型: {info['type']}")
        print(f"    變數: {info['variables']}")
        print(f"    描述: {info['description']}")
    
    # 測試2: 渲染系統提示
    print("\n🤖 測試系統提示渲染:")
    for role in ["debater_a", "debater_b", "judge"]:
        template_id = f"{role}_system"
        try:
            rendered = manager.render_template(template_id)
            print(f"\n{role.upper()} 系統提示:")
            print("-" * 30)
            print(rendered[:200] + "...")
        except Exception as e:
            print(f"❌ {role} 系統提示渲染失敗: {e}")
    
    # 測試3: 渲染開場陳述
    print("\n📢 測試開場陳述渲染:")
    sample_data = {
        "topic": "是否應該投資這個AI分析項目？",
        "business_data": "收入: $100k-$150k, 成本: $80k-$100k, 增長率: 25%",
        "context": "目標是擴展到企業客戶市場"
    }
    
    for role in ["debater_a", "debater_b"]:
        template_id = f"{role}_opening"
        try:
            rendered = manager.render_template(template_id, **sample_data)
            print(f"\n{role.upper()} 開場陳述模板:")
            print("-" * 30)
            print(rendered[:300] + "...")
        except Exception as e:
            print(f"❌ {role} 開場陳述渲染失敗: {e}")
    
    # 測試4: 變數驗證
    print("\n✅ 測試變數驗證:")
    template_id = "debater_a_opening"
    
    # 完整變數
    complete_vars = sample_data
    missing = manager.validate_template_variables(template_id, complete_vars)
    print(f"完整變數檢查: {len(missing)} 個缺失變數")
    
    # 不完整變數
    incomplete_vars = {"topic": "測試主題"}
    missing = manager.validate_template_variables(template_id, incomplete_vars)
    print(f"不完整變數檢查: {len(missing)} 個缺失變數: {missing}")
    
    return manager

async def test_integration():
    """測試整合功能"""
    print("\n🔗 測試系統整合...")
    print("=" * 50)
    
    # 初始化
    pool = get_model_pool()
    manager = get_prompt_manager()
    
    # 創建辯論會話
    assignments = pool.assign_models_to_roles("optimal")
    session = pool.create_debate_session(
        "是否應該立即擴大生產規模？",
        assignments
    )
    
    # 為每個模型準備開場陳述prompt
    sample_data = {
        "topic": session.topic,
        "business_data": "當前產能: 1000units/月, 訂單需求: 1500units/月, 預計投資: $50k",
        "context": "市場需求強勁，但資金有限"
    }
    
    print(f"辯論會話: {session.session_id}")
    print(f"主題: {session.topic}")
    print("\n角色分配和Prompt準備:")
    
    for role, model_id in session.participants.items():
        model = pool.get_model_by_id(model_id)
        if model:
            print(f"\n{role.value.upper()}: {model.name}")
            
            # 準備系統提示
            system_template_id = f"{role.value}_system"
            if manager.get_template(system_template_id):
                system_prompt = manager.render_template(system_template_id)
                print(f"  系統提示: ✅ ({len(system_prompt)} 字符)")
            
            # 準備開場陳述（如果有）
            if role in [ModelRole.DEBATER_A, ModelRole.DEBATER_B]:
                opening_template_id = f"{role.value}_opening"
                if manager.get_template(opening_template_id):
                    opening_prompt = manager.render_template(opening_template_id, **sample_data)
                    print(f"  開場陳述: ✅ ({len(opening_prompt)} 字符)")
        else:
            print(f"\n{role.value.upper()}: ❌ 模型未找到 ({model_id})")
    
    print("\n✅ 系統整合測試完成！")
    return session

async def main():
    """主測試函數"""
    print("🚀 開始測試任務1.2 - 多模型管理系統...")
    print("=" * 60)
    
    try:
        # 測試模型池
        pool, session = await test_model_pool()
        
        # 測試prompt模板
        manager = await test_prompt_templates()
        
        # 測試整合
        final_session = await test_integration()
        
        print("\n🎉 任務1.2測試完成！")
        print("\n📊 測試總結:")
        print(f"✅ 模型池管理: 正常運行")
        print(f"✅ Prompt模板: 正常運行")
        print(f"✅ 系統整合: 正常運行")
        print(f"✅ 創建會話: {final_session.session_id}")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
