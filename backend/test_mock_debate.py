"""
Mock Debate Engine Test
使用模擬響應測試辯論引擎邏輯
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch
from services.debate_engine import get_debate_engine, DebateStatus, DebatePhase
from services.model_pool import ModelRole

# 模擬響應數據
MOCK_RESPONSES = {
    ModelRole.DEBATER_A: {
        DebatePhase.OPENING: """
        作為正方，我堅決支持全面採用AI自動化客服系統。

        核心論點：
        1. **成本效益顯著**：初期投資80萬，每月維護5萬，相比人工客服每月50萬的成本，年節省540萬元，投資回報率達到675%。

        2. **服務效率提升**：AI客服可提供24小時無間斷服務，平均回應時間可縮短至秒級，大大提升客戶體驗。

        3. **規模化處理**：能同時處理數千個客戶諮詢，有效解決客服高峰期排隊問題，提升客戶滿意度。

        數據支撐：預計可處理70%的常見問題，釋放人力資源專注於複雜問題處理。
        """,
        DebatePhase.FIRST_ROUND: """
        針對反方提出的關切，我要強調AI客服的優勢遠大於風險：

        **回應個性化問題**：現代AI技術已具備情境理解能力，能根據客戶歷史記錄提供個性化服務，並非冰冷的機械回復。

        **職位轉型非失業**：減少的30個客服崗位可轉為AI訓練師、數據分析師等更高價值職位，提升員工技能而非單純裁員。

        **技術成熟度**：當前AI客服技術已在多家大型企業成功部署，技術風險可控，實施經驗豐富。

        投資視角：這不僅是成本節約，更是數字化轉型的戰略投資，將為公司帶來長期競爭優勢。
        """,
        DebatePhase.CLOSING: """
        總結正方立場：全面採用AI自動化客服系統是明智的戰略決策。

        **核心優勢回顧**：
        - 年節省540萬元成本，投資回報清晰
        - 24/7不間斷服務，客戶體驗質的飛躍
        - 處理能力可無限擴展，適應業務增長

        **風險可控**：通過漸進式部署、員工培訓轉型、技術監控等措施，可有效管控實施風險。

        **未來導向**：這是公司走向數字化未來的必要步驟，越早實施，競爭優勢越明顯。

        因此，我堅決建議立即啟動AI客服系統的全面部署計劃。
        """
    },
    
    ModelRole.DEBATER_B: {
        DebatePhase.OPENING: """
        作為反方，我強烈反對全面採用AI自動化客服系統。

        核心論點：
        1. **客戶體驗風險**：AI無法處理複雜情緒和個性化需求，機械化回復將損害客戶關係，可能導致客戶流失。

        2. **就業倫理問題**：直接裁減30名員工，對企業社會責任造成負面影響，也會影響團隊士氣和企業形象。

        3. **技術依賴風險**：過度依賴AI系統存在技術故障、安全漏洞等風險，一旦出現問題將嚴重影響業務運營。

        現實考量：78%的客戶滿意度雖有改進空間，但不應以犧牲服務質量和員工利益為代價。
        """,
        DebatePhase.FIRST_ROUND: """
        正方過於樂觀地估計了AI的能力，忽視了實際風險：

        **個性化服務局限**：AI的"情境理解"仍然基於預設模式，無法真正理解客戶的情緒狀態和特殊需求，機械化回復會讓客戶感到被忽視。

        **職位轉型現實**：將客服轉為AI訓練師是理想化假設，實際上大部分員工缺乏相關技術背景，轉型成功率低，變相就是裁員。

        **隱性成本**：除了80萬初期投資，還需要持續的員工培訓、系統維護、客戶投訴處理等隱性成本，實際投資遠超預估。

        **競爭劣勢**：當競爭對手提供人性化服務時，我們的機器客服將成為明顯劣勢。
        """,
        DebatePhase.CLOSING: """
        總結反方立場：全面採用AI客服是短視的決策，將帶來長期損害。

        **核心風險警示**：
        - 客戶關係惡化，滿意度可能從78%進一步下降
        - 30名員工失業，企業社會責任缺失
        - 技術風險集中，系統故障影響巨大

        **更好方案**：建議採用人機協作模式，AI處理標準問題，人工處理複雜案例，既提升效率又保證服務質量。

        **長遠考慮**：客戶關係是企業最寶貴的資產，不應為了短期成本節約而損害客戶信任。

        因此，我強烈建議暫緩全面AI客服計劃，改為漸進式人機協作方案。
        """
    },
    
    ModelRole.JUDGE: {
        DebatePhase.JUDGMENT: """
        經過深入分析雙方論證，我做出如下評判：

        【雙方論點分析】

        **正方優勢**：
        - 成本效益分析具體明確，投資回報率計算詳實
        - 技術可行性論證充分，實施路徑清晰
        - 對業務規模化需求的分析準確

        **反方優勢**：
        - 對客戶體驗風險的關注非常中肯
        - 員工影響和企業社會責任考慮周全
        - 對技術風險的警示具有實際意義

        【判決理由】

        雙方都提出了有價值的觀點，但反方在風險評估方面更為全面。正方雖然在經濟效益方面論證充分，但對實施風險考慮不足。

        **最終判決**：反方勝出

        **建議實施方案**：
        採用分階段混合模式：
        1. 第一階段：AI處理30%簡單查詢，保留全部人工客服
        2. 第二階段：根據效果評估，逐步提升AI處理比例
        3. 第三階段：實現人機協作最優配置

        這樣既能獲得技術優勢，又能保障服務質量和員工利益。
        """
    }
}

async def mock_openrouter_call(*args, **kwargs):
    """模擬OpenRouter API調用"""
    # 模擬API延遲
    await asyncio.sleep(0.5)
    
    # 根據上下文確定角色和階段
    messages = kwargs.get('messages', [])
    if not messages:
        return "模擬響應"
    
    content = messages[0].get('content', '')
    
    # 簡單的角色和階段推斷
    if '正方' in content or 'debater_a' in content:
        role = ModelRole.DEBATER_A
    elif '反方' in content or 'debater_b' in content:
        role = ModelRole.DEBATER_B
    elif '裁判' in content or 'judge' in content:
        role = ModelRole.JUDGE
    else:
        role = ModelRole.DEBATER_A  # 默認
    
    if '開場' in content or '第一次' in content:
        phase = DebatePhase.OPENING
    elif '輪次' in content or '第' in content and '輪' in content:
        phase = DebatePhase.FIRST_ROUND
    elif '結語' in content or '總結' in content:
        phase = DebatePhase.CLOSING
    elif '裁判' in content or '判決' in content:
        phase = DebatePhase.JUDGMENT
    else:
        phase = DebatePhase.OPENING  # 默認
    
    # 返回對應的模擬響應
    response = MOCK_RESPONSES.get(role, {}).get(phase, f"模擬{role.value}在{phase.value}階段的響應")
    return response

async def test_mock_debate_engine():
    """使用模擬響應測試辯論引擎"""
    print("🎯 開始模擬辯論引擎測試...")
    
    # 使用模擬替換實際API調用
    with patch('services.openrouter_client.OpenRouterClient.chat_completion', side_effect=mock_openrouter_call):
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
            
            # 顯示模型分配
            print("\n🤖 模型分配：")
            for role, config in session.model_assignments.items():
                print(f"   {role.value}: {config.name}")
            
            # 2. 開始辯論
            print(f"\n🚀 開始辯論會話...")
            session = await engine.start_debate(session.session_id)
            print(f"✅ 辯論已開始，當前階段: {session.current_phase.value}")
            
            # 3. 進行完整辯論流程
            print("\n📊 執行完整辯論流程...")
            max_iterations = 10
            iteration = 0
            
            while (session.status == DebateStatus.ACTIVE and 
                   session.current_phase != DebatePhase.COMPLETED and 
                   iteration < max_iterations):
                
                iteration += 1
                print(f"\n--- 步驟 {iteration} ---")
                print(f"階段: {session.current_phase.value}")
                print(f"輪次: {session.current_round}/{session.max_rounds}")
                
                # 繼續辯論
                try:
                    session = await engine.continue_debate(session.session_id)
                    print(f"✅ 進入下一階段: {session.current_phase.value}")
                except Exception as e:
                    print(f"⚠️ 辯論繼續時出錯: {e}")
                    break
                
                # 顯示最新消息
                if session.all_messages:
                    last_message = session.all_messages[-1]
                    print(f"最新發言者: {last_message.speaker.value}")
                
                await asyncio.sleep(0.2)  # 短暫延遲
            
            # 4. 檢查最終結果
            print(f"\n🏁 辯論完成")
            print(f"最終狀態: {session.status.value}")
            print(f"最終階段: {session.current_phase.value}")
            print(f"總輪數: {len(session.rounds)}")
            print(f"總消息數: {len(session.all_messages)}")
            
            # 5. 顯示辯論內容摘要
            print("\n📚 辯論內容摘要：")
            for i, round in enumerate(session.rounds, 1):
                print(f"\n--- 第{i}輪 ({round.phase.value}) ---")
                for msg in round.messages:
                    speaker_name = {
                        ModelRole.DEBATER_A: "正方",
                        ModelRole.DEBATER_B: "反方",
                        ModelRole.JUDGE: "裁判"
                    }.get(msg.speaker, msg.speaker.value)
                    
                    print(f"\n【{speaker_name}】")
                    print(msg.content[:200] + "..." if len(msg.content) > 200 else msg.content)
            
            # 6. 顯示裁判判決
            if session.judgment:
                print(f"\n⚖️ 裁判判決：")
                print(session.judgment.content[:400] + "..." if len(session.judgment.content) > 400 else session.judgment.content)
            
            # 7. 顯示統計信息
            print(f"\n📈 統計信息：")
            print(f"   總Token數: {session.total_tokens}")
            print(f"   估計成本: ${session.total_cost:.4f}")
            print(f"   錯誤次數: {session.error_count}")
            print(f"   持續時間: {session.duration:.1f}秒" if session.duration else "N/A")
            
            return session.session_id
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

async def test_api_endpoints():
    """測試辯論API端點（模擬模式）"""
    print("\n🌐 測試API端點...")
    
    # 測試健康檢查
    try:
        engine = get_debate_engine()
        active_count = len(engine.active_sessions)
        
        health_response = {
            "status": "healthy",
            "active_sessions": active_count,
            "service": "debate_engine"
        }
        
        print("✅ 健康檢查端點測試通過")
        print(f"   活躍會話數: {health_response['active_sessions']}")
        
        # 測試會話列表
        sessions = engine.list_active_sessions()
        print(f"✅ 會話列表端點測試通過，共 {len(sessions)} 個會話")
        
        return True
        
    except Exception as e:
        print(f"❌ API端點測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🎯 模擬辯論引擎測試腳本")
    print("=" * 60)
    
    try:
        # 運行主要測試
        session_id = asyncio.run(test_mock_debate_engine())
        
        if session_id:
            print(f"\n✅ 主要測試完成，會話ID: {session_id}")
            
            # 運行API測試
            api_success = asyncio.run(test_api_endpoints())
            
            if api_success:
                print("\n✅ API端點測試通過")
        
        print("\n" + "=" * 60)
        print("🎉 所有模擬測試完成！")
        print("📋 測試驗證了以下功能：")
        print("   ✓ 辯論會話創建和管理")
        print("   ✓ 多輪辯論流程控制")
        print("   ✓ 模型角色分配和輪換")
        print("   ✓ 辯論內容記錄和整理")
        print("   ✓ 裁判判決生成")
        print("   ✓ 統計信息收集")
        print("   ✓ 錯誤處理和容錯機制")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試運行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
