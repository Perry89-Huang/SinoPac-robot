"""
持倉異常警告說明工具
解釋 SinoPac-close 的單邊持倉警告
"""
from tabulate import tabulate

def explain_alert():
    """解釋持倉異常警告"""
    
    print("\n" + "="*100)
    print("⚠️  持倉異常警告說明")
    print("="*100)
    
    print("\n📋 您收到的警告訊息：")
    print("-"*100)
    print("   ⚠️ 檢測到單邊持倉異常: CSFB6 Action.Buy x10 @ 34.15")
    print("-"*100)
    
    print("\n💡 這是什麼意思？")
    print("-"*100)
    print("   SinoPac-close 是一個「組合單平倉機器人」，專門用來平倉：")
    print("   • 買近月 + 賣遠月")
    print("   • 賣近月 + 買遠月")
    print()
    print("   這種「一買一賣配對」的組合單才是正常的。")
    print()
    print("   但是現在檢測到：")
    print("   🔴 只有 CSFB6（華新期貨02）買進 10 口")
    print("   🔴 沒有對應的華新期貨01賣出部位")
    print("   🔴 這是「單邊持倉」= 不正常的情況")
    
    print("\n🔍 實際持倉狀況：")
    print("-"*100)
    
    position_data = [
        ['CSFA6', '華新期貨01', '買進', 6, '33.83', '+37.50', '✅ 正常'],
        ['CSFB6', '華新期貨02', '買進', 4, '34.15', '-50.00', '⚠️ 單邊（之前是 10 口）']
    ]
    headers = ['合約代碼', '名稱', '方向', '口數', '成本', '損益', '狀態']
    print(tabulate(position_data, headers=headers, tablefmt='grid'))
    
    print("\n📊 分析：")
    print("-"*100)
    print("   1️⃣  您之前平倉過華新期貨，從 10 口減少到 4 口")
    print("   2️⃣  但是 CSFB6 和 CSFA6 的口數不匹配：")
    print("      • CSFA6 買進 6 口")
    print("      • CSFB6 買進 4 口")
    print("   3️⃣  理論上組合單應該是：")
    print("      • CSFA6 買進 N 口 + CSFB6 賣出 N 口")
    print("      • 或 CSFA6 賣出 N 口 + CSFB6 買進 N 口")
    print()
    print("   ❌ 但現在兩個都是「買進」= 不是組合單")
    
    print("\n⚠️  為什麼會持續警告？")
    print("-"*100)
    print("   因為 SinoPac-close 每次收到 BidAsk（報價）時都會檢查：")
    print("   1. 是否有兩個月份的期貨（近月 + 遠月）")
    print("   2. 方向是否相反（一買一賣）")
    print("   3. 如果只有單邊，就發出警告")
    print()
    print("   只要持倉狀況沒改變，警告就會一直出現！")
    
    print("\n✅ 解決方案：")
    print("-"*100)
    print()
    print("   方案 1️⃣ : 手動平倉所有華新期貨")
    print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   • 賣出 CSFA6 6 口")
    print("   • 賣出 CSFB6 4 口")
    print("   • 完全清空華新持倉，警告就會消失")
    print()
    print("   方案 2️⃣ : 使用 manage_simulation_positions.py 一鍵清空")
    print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   • 執行選項 7「重置所有持倉」")
    print("   • 選擇市價單（保證成交）")
    print("   • 清空所有持倉，警告自然消失")
    print()
    print("   方案 3️⃣ : 暫時忽略警告")
    print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   • 如果不影響其他交易，可以暫時不處理")
    print("   • 但建議定期清理單邊持倉")
    
    print("\n🎯 建議做法：")
    print("-"*100)
    print("   由於您目前有 296 口持倉（已達 98.7%），建議：")
    print()
    print("   1️⃣  先執行 manage_simulation_positions.py")
    print("   2️⃣  選擇選項 7「重置所有持倉」")
    print("   3️⃣  確認輸入 YES")
    print("   4️⃣  選擇市價單（選項 2）")
    print("   5️⃣  等待 3 秒讓訂單成交")
    print("   6️⃣  重新載入確認持倉清空")
    print()
    print("   這樣可以：")
    print("   ✅ 清空所有單邊持倉")
    print("   ✅ 消除持倉異常警告")
    print("   ✅ 釋放持倉空間（目前只剩 4 口可用）")
    
    print("\n💬 技術說明：")
    print("-"*100)
    print("   在 SinoPac-close.py 第 677-684 行：")
    print()
    print("   ```python")
    print("   # 檢測單邊持倉（只有近月或只有遠月，但沒有配對）")
    print("   if len(listPosition_OneFut) == 1:")
    print("       pos = listPosition_OneFut[0]")
    print("       if objTrade.getTradeQty(pos.code) == 0:")
    print("           alert_msg = f'⚠️ 檢測到單邊持倉異常...'")
    print("           logger.warning(alert_msg)")
    print("           notifier.notify_position_alert(alert_msg)")
    print("   ```")
    print()
    print("   只要 listPosition_OneFut 只有 1 個（沒有配對），就會警告。")
    
    print("="*100)
    
    print("\n" + "="*100)
    print("📝 快速指令")
    print("="*100)
    print()
    print("清空所有持倉（推薦）：")
    print("┌" + "─"*98 + "┐")
    print("│ python manage_simulation_positions.py                                                           │")
    print("│ → 選擇 7                                                                                        │")
    print("│ → 輸入 YES                                                                                      │")
    print("│ → 選擇 2 (市價單)                                                                              │")
    print("└" + "─"*98 + "┘")
    print("="*100 + "\n")


if __name__ == "__main__":
    explain_alert()
