"""
Debate Engine Test Script
測試辯論引擎功能的腳本
"""

import asyncio
import json
import time
from services.debate_engine import get_debate_engine, DebateStatus, DebatePhase
from services.model_pool import get_model_pool
from services.monitoring import get_monitoring_system

async def test_debate_engine():
    """測試辯論引擎的完整流程"""
    print("🎯 開始測試辯論引擎...")
    
    # 獲取辯論引擎實例
    engine = get_debate_engine()
    print("✅ 辯論引擎初始化成功")
    
    # 測試數據
    test_topic = "是否應該在公司中全面採用AI自動化客服系統"
    test_business_data = """
    公司背景：
    - 電商平台，日均客服諮詢量5000+
    - 目前人工客服團隊50人，成本每月50萬
    - 客戶滿意度78%，平均回應時間3分鐘
    
    AI方案：
    - 初期投資80萬，每月維護成本5萬
    - 預計處理70%常見問題，24小時服務
    - 人工客服可減少至20人
    """
    
    try:
        # 1. 創建辯論會話
        print("\n📝 創建辯論會話...")
        session = await engine.create_debate_session(
            topic=test_topic,
            business_data=test_business_data,
            context="需要考慮成本效益、客戶體驗、員工影響等多個角度",
            max_rounds=3,
            assignment_strategy="default"
        )
        
        print(f"✅ 會話創建成功，ID: {session.session_id}")
        print(f"   主題: {session.topic}")
        print(f"   狀態: {session.status.value}")
        print(f"   最大輪數: {session.max_rounds}")
        
        # 顯示模型分配
        print("\n🤖 模型分配：")
        for role, config in session.model_assignments.items():
            print(f"   {role.value}: {config.name} ({config.id})")
        
        # 2. 開始辯論
        print(f"\n🚀 開始辯論會話 {session.session_id}...")
        session = await engine.start_debate(session.session_id)
        print(f"✅ 辯論已開始，當前階段: {session.current_phase.value}")
        
        # 3. 監控辯論進度
        print("\n📊 監控辯論進度...")
        max_iterations = 20  # 防止無限循環
        iteration = 0
        
        while (session.status == DebateStatus.ACTIVE and 
               session.current_phase != DebatePhase.COMPLETED and 
               iteration < max_iterations):
            
            iteration += 1
            print(f"\n--- 迭代 {iteration} ---")
            print(f"狀態: {session.status.value}")
            print(f"階段: {session.current_phase.value}")
            print(f"輪次: {session.current_round}/{session.max_rounds}")
            print(f"消息數: {len(session.all_messages)}")
            
            if session.all_messages:
                last_message = session.all_messages[-1]
                print(f"最新發言: {last_message.speaker.value}")
                print(f"內容預覽: {last_message.content[:100]}...")
            
            # 繼續辯論
            try:
                session = await engine.continue_debate(session.session_id)
            except Exception as e:
                print(f"⚠️ 辯論繼續時出錯: {e}")
                break
            
            # 短暫延遲
            await asyncio.sleep(1)
        
        # 4. 檢查最終結果
        print(f"\n🏁 辯論結束")
        print(f"最終狀態: {session.status.value}")
        print(f"最終階段: {session.current_phase.value}")
        print(f"總輪數: {len(session.rounds)}")
        print(f"總消息數: {len(session.all_messages)}")
        print(f"持續時間: {session.duration:.1f}秒" if session.duration else "N/A")
        
        # 5. 顯示辯論內容
        print("\n📚 辯論內容摘要：")
        for i, round in enumerate(session.rounds, 1):
            print(f"\n第{i}輪 ({round.phase.value}):")
            for msg in round.messages:
                speaker_name = {
                    "debater_a": "正方",
                    "debater_b": "反方",
                    "judge": "裁判"
                }.get(msg.speaker.value, msg.speaker.value)
                
                print(f"  【{speaker_name}】: {msg.content[:150]}...")
                if msg.response_time:
                    print(f"    (回應時間: {msg.response_time:.2f}秒)")
        
        # 6. 顯示裁判判決
        if session.judgment:
            print(f"\n⚖️ 裁判判決：")
            print(session.judgment.content)
        
        # 7. 顯示最終報告
        if session.final_report:
            print(f"\n📋 最終報告：")
            print(session.final_report[:500] + "..." if len(session.final_report) > 500 else session.final_report)
        
        # 8. 統計信息
        print(f"\n📈 統計信息：")
        print(f"   總Token數: {session.total_tokens}")
        print(f"   估計成本: ${session.total_cost:.4f}")
        print(f"   錯誤次數: {session.error_count}")
        
        return session.session_id
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_multiple_sessions():
    """測試多個並發辯論會話"""
    print("\n🔄 測試多個並發辯論會話...")
    
    engine = get_debate_engine()
    
    # 創建多個會話
    topics = [
        "是否應該實施遠程工作政策",
        "是否應該投資開發移動APP",
        "是否應該擴展海外市場"
    ]
    
    sessions = []
    for i, topic in enumerate(topics):
        try:
            session = await engine.create_debate_session(
                topic=topic,
                business_data=f"業務場景{i+1}的相關數據...",
                max_rounds=2
            )
            sessions.append(session)
            print(f"✅ 創建會話 {i+1}: {session.session_id[:8]}...")
        except Exception as e:
            print(f"❌ 創建會話 {i+1} 失敗: {e}")
    
    print(f"✅ 共創建 {len(sessions)} 個會話")
    
    # 列出所有會話
    all_sessions = engine.list_active_sessions()
    print(f"📋 活躍會話總數: {len(all_sessions)}")
    
    return sessions


async def test_monitoring_integration():
    """測試監控系統集成"""
    print("\n📊 測試監控系統集成...")
    
    monitoring = get_monitoring_system()
    
    # 顯示當前指標
    try:
        summary = monitoring.get_metrics_summary()
        print(f"✅ 監控系統狀態: 運行中")
        print(f"   註冊的指標數: {summary.get('total_metrics', 0)}")
        print(f"   活躍警報數: {summary.get('active_alerts', 0)}")
        
        # 顯示一些指標
        print("\n📈 已註冊的指標:")
        metrics_info = summary.get('metrics', {})
        for metric_name, info in list(metrics_info.items())[:5]:  # 顯示前5個
            latest = info.get('latest_value', 'N/A')
            print(f"   {metric_name}: {latest}")
    
    except Exception as e:
        print(f"⚠️ 無法獲取監控摘要: {e}")
        print("✅ 監控系統已初始化")


def main():
    """主測試函數"""
    print("=" * 50)
    print("🎯 辯論引擎測試腳本")
    print("=" * 50)
    
    try:
        # 運行測試
        session_id = asyncio.run(test_debate_engine())
        
        if session_id:
            print(f"\n✅ 主要測試完成，會話ID: {session_id}")
            
            # 運行額外測試
            asyncio.run(test_multiple_sessions())
            asyncio.run(test_monitoring_integration())
        
        print("\n" + "=" * 50)
        print("🎉 所有測試完成！")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試運行失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
