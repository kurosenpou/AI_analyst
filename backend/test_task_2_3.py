"""
Task 2.3 Integration Test
測試所有Task 2.3功能的集成和基本功能
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_deep_debate_engine():
    """測試深度辯論引擎"""
    print("\n=== 測試深度辯論引擎 ===")
    
    try:
        from services.deep_debate import get_deep_debate_engine
        
        engine = get_deep_debate_engine()
        
        # 模擬辯論消息
        test_message = "我認為人工智能將會極大地改善人類的生活質量，通過自動化繁重的工作和提供更好的醫療診斷。"
        
        result = await engine.process_debate_message(
            content=test_message,
            speaker="debater_a",
            round_number=1,
            message_context={"topic": "AI對人類的影響"}
        )
        
        print(f"✅ 深度辯論分析完成")
        print(f"   - 論證ID: {result.get('argument_id', 'N/A')}")
        print(f"   - 論證類型: {result.get('argument_type', 'N/A')}")
        print(f"   - 強度分數: {result.get('strength_score', 0):.3f}")
        
        # 獲取分析摘要
        analysis = engine.get_debate_analysis()
        print(f"   - 總論證數: {analysis.get('total_arguments', 0)}")
        print(f"   - 論證鏈數: {analysis.get('total_chains', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 深度辯論引擎測試失敗: {e}")
        return False


async def test_argument_analysis_engine():
    """測試論證分析引擎"""
    print("\n=== 測試論證分析引擎 ===")
    
    try:
        from services.argument_analysis import get_argument_analysis_engine
        
        engine = get_argument_analysis_engine()
        
        # 測試論證分析
        test_argument = "根據最新的研究數據，人工智能在醫療診斷方面的準確率已經超過了90%，這證明了AI技術的可靠性。"
        
        report = await engine.analyze_argument(
            argument_id="test_arg_1",
            content=test_argument,
            speaker="test_speaker",
            timestamp=datetime.now()
        )
        
        print(f"✅ 論證分析完成")
        print(f"   - 整體強度: {report.overall_strength:.3f}")
        print(f"   - 信心度: {report.confidence_level:.3f}")
        print(f"   - 邏輯健全性: {report.logical_soundness_score:.3f}")
        print(f"   - 證據數量: {len(report.evidence_items)}")
        print(f"   - 邏輯謬誤: {[f.value for f in report.logical_fallacies if f.value != 'none']}")
        
        # 獲取分析摘要
        summary = engine.get_analysis_summary()
        print(f"   - 總分析數: {summary.get('total_analyses', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 論證分析引擎測試失敗: {e}")
        return False


async def test_consensus_engine():
    """測試共識建構引擎"""
    print("\n=== 測試共識建構引擎 ===")
    
    try:
        from services.consensus_builder import get_consensus_engine
        
        engine = get_consensus_engine()
        
        # 模擬辯論論證
        test_arguments = [
            {
                "content": "AI技術確實能提高效率，這是大家都認同的。",
                "speaker": "debater_a",
                "timestamp": datetime.now().isoformat()
            },
            {
                "content": "我同意AI能提高效率，但我們也要考慮就業問題。",
                "speaker": "debater_b", 
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        participants = ["debater_a", "debater_b"]
        
        report = await engine.build_consensus(
            debate_id="test_debate_1",
            topic="AI對社會的影響",
            participants=participants,
            arguments=test_arguments,
            context={"test": True}
        )
        
        print(f"✅ 共識分析完成")
        print(f"   - 整體共識水平: {report.overall_consensus_level:.3f}")
        print(f"   - 極化指數: {report.polarization_index:.3f}")
        print(f"   - 解決潛力: {report.resolution_potential:.3f}")
        print(f"   - 共同點數量: {len(report.common_grounds)}")
        print(f"   - 分歧數量: {len(report.disagreements)}")
        print(f"   - 解決方案數量: {len(report.solutions)}")
        
        # 獲取共識摘要
        summary = engine.get_consensus_summary()
        print(f"   - 總報告數: {summary.get('total_reports', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 共識建構引擎測試失敗: {e}")
        return False


async def test_advanced_judge_engine():
    """測試高級裁判引擎"""
    print("\n=== 測試高級裁判引擎 ===")
    
    try:
        from services.advanced_judge import get_advanced_judge_engine
        
        engine = get_advanced_judge_engine()
        
        # 模擬辯論內容
        debate_content = """
        [debater_a] AI技術將會創造更多就業機會，因為它會催生新的行業和職位。
        [debater_b] 但是AI也會取代很多現有的工作，導致大量失業。
        [debater_a] 歷史上每次技術革命都是如此，最終都創造了更多機會。
        [debater_b] 這次不同，AI的影響範圍更廣，速度更快。
        """
        
        participant_arguments = {
            "debater_a": [
                "AI技術將會創造更多就業機會，因為它會催生新的行業和職位。",
                "歷史上每次技術革命都是如此，最終都創造了更多機會。"
            ],
            "debater_b": [
                "但是AI也會取代很多現有的工作，導致大量失業。",
                "這次不同，AI的影響範圍更廣，速度更快。"
            ]
        }
        
        judgment = await engine.conduct_advanced_judgment(
            debate_id="test_judgment_1",
            topic="AI對就業的影響",
            participants=["debater_a", "debater_b"],
            debate_content=debate_content,
            participant_arguments=participant_arguments,
            context={"test": True}
        )
        
        print(f"✅ 高級判決完成")
        print(f"   - 獲勝者: {judgment.winner or '平局'}")
        print(f"   - 獲勝優勢: {judgment.winning_margin:.3f}")
        print(f"   - 整體質量: {judgment.overall_quality:.3f}")
        print(f"   - 判決信心度: {judgment.judgment_confidence:.3f}")
        print(f"   - 檢測到的偏見: {len(judgment.detected_biases)}")
        print(f"   - 視角評估數: {len(judgment.perspective_evaluations)}")
        print(f"   - 評估時間: {judgment.evaluation_time:.2f}秒")
        
        # 獲取判決摘要
        summary = engine.get_judgment_summary()
        print(f"   - 總判決數: {summary.get('total_judgments', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 高級裁判引擎測試失敗: {e}")
        return False


async def test_integration():
    """測試集成功能"""
    print("\n=== 測試集成功能 ===")
    
    try:
        from services.debate_engine import get_debate_engine
        
        engine = get_debate_engine()
        
        # 檢查所有Task 2.3組件是否已集成
        components = [
            ("deep_debate_engine", hasattr(engine, 'deep_debate_engine')),
            ("argument_analysis_engine", hasattr(engine, 'argument_analysis_engine')),
            ("consensus_engine", hasattr(engine, 'consensus_engine')),
            ("advanced_judge_engine", hasattr(engine, 'advanced_judge_engine'))
        ]
        
        print("✅ 組件集成檢查:")
        for name, integrated in components:
            status = "✅" if integrated else "❌"
            print(f"   {status} {name}: {'已集成' if integrated else '未集成'}")
        
        # 檢查新方法是否可用
        methods = [
            ("get_deep_debate_analysis", hasattr(engine, 'get_deep_debate_analysis')),
            ("get_argument_strength_comparison", hasattr(engine, 'get_argument_strength_comparison')),
            ("get_consensus_insights", hasattr(engine, 'get_consensus_insights')),
            ("get_advanced_judgment_details", hasattr(engine, 'get_advanced_judgment_details'))
        ]
        
        print("\n✅ 新方法可用性檢查:")
        for name, available in methods:
            status = "✅" if available else "❌"
            print(f"   {status} {name}: {'可用' if available else '不可用'}")
        
        all_integrated = all(integrated for _, integrated in components)
        all_methods_available = all(available for _, available in methods)
        
        return all_integrated and all_methods_available
        
    except Exception as e:
        print(f"❌ 集成測試失敗: {e}")
        return False


async def main():
    """主測試函數"""
    print("🚀 開始Task 2.3集成測試")
    print("=" * 50)
    
    # 運行所有測試
    tests = [
        ("深度辯論引擎", test_deep_debate_engine),
        ("論證分析引擎", test_argument_analysis_engine),
        ("共識建構引擎", test_consensus_engine),
        ("高級裁判引擎", test_advanced_judge_engine),
        ("集成功能", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}測試出現異常: {e}")
            results.append((test_name, False))
    
    # 輸出測試結果摘要
    print("\n" + "=" * 50)
    print("📊 測試結果摘要")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有Task 2.3功能測試通過！")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查相關組件")
        return False


if __name__ == "__main__":
    # 運行測試
    success = asyncio.run(main())
    
    # 設置退出碼
    sys.exit(0 if success else 1)