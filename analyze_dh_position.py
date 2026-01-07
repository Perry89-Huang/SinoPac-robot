"""
分析鴻海期貨持倉結構
"""
from tabulate import tabulate

def analyze_dh_positions():
    """分析鴻海期貨的近月遠月配對情況"""
    
    print("\n" + "="*100)
    print("📊 鴻海期貨持倉分析")
    print("="*100)
    
    print("\n【持倉明細】")
    print("-"*100)
    
    position_data = [
        ['DHFA6', '鴻海期貨01', '近月 (1月)', '賣出', 21, 236.00, 235.5, '+525.00'],
        ['DHFB6', '鴻海期貨02', '遠月 (2月)', '買進', 103, 236.65, 236.5, '-750.00']
    ]
    
    headers = ['合約', '名稱', '類型', '方向', '口數', '成本', '現價', '損益']
    print(tabulate(position_data, headers=headers, tablefmt='grid'))
    
    print("\n" + "="*100)
    print("✅ 確認結果")
    print("="*100)
    
    print("\n是的！鴻海期貨確實是近月和遠月的配對：")
    print()
    print("  📌 FA6 = 2026年1月到期（近月合約）")
    print("     └─ DHFA6: 賣出 21 口")
    print()
    print("  📌 FB6 = 2026年2月到期（遠月合約）")
    print("     └─ DHFB6: 買進 103 口")
    
    print("\n" + "="*100)
    print("📊 配對分析")
    print("="*100)
    
    print("\n✅ 正常配對（組合單）：21 口")
    print("   • 賣出近月 DHFA6: 21 口")
    print("   • 買進遠月 DHFB6: 21 口")
    print("   → 這 21 口形成「賣近買遠」的價差組合單")
    
    print("\n⚠️  單邊部位：82 口")
    print("   • 買進遠月 DHFB6 剩餘: 82 口 (103 - 21)")
    print("   → 這 82 口是沒有配對的單邊買方部位")
    
    print("\n" + "="*100)
    print("💡 這是什麼意思？")
    print("="*100)
    
    print("\n【正常的組合單策略】")
    print("   賣近月 + 買遠月 = 價差套利")
    print("   • 預期近月跌得快，遠月跌得慢（或漲得快）")
    print("   • 風險較小，因為一買一賣互相對沖")
    print("   • 鴻海有 21 口是這種配對 ✅")
    
    print("\n【單邊部位的風險】")
    print("   只買進遠月 = 單向看多")
    print("   • 如果價格下跌，82 口全部虧損")
    print("   • 沒有對沖保護")
    print("   • 鴻海有 82 口是這種單邊 ⚠️")
    
    print("\n" + "="*100)
    print("🎯 為什麼會這樣？")
    print("="*100)
    
    print("\n可能的原因：")
    print("  1️⃣  原本下了價差組合單，但部分平倉時只平了一邊")
    print("  2️⃣  分批建倉，近月和遠月的口數沒有對齊")
    print("  3️⃣  近月到期或結算，系統自動平倉部分持倉")
    print("  4️⃣  手動交易時，買賣雙方口數不一致")
    
    print("\n" + "="*100)
    print("💊 建議處理方式")
    print("="*100)
    
    print("\n方案 1️⃣ : 補足配對（建立更多組合單）")
    print("   • 賣出近月 DHFA6 再 82 口")
    print("   • 這樣所有 103 口遠月都有配對")
    print("   • 形成完整的價差套利策略")
    print("   ⚠️  但要注意是否超過持倉上限（目前 296/300）")
    
    print("\n方案 2️⃣ : 平掉單邊部位")
    print("   • 賣出遠月 DHFB6 的 82 口")
    print("   • 只保留 21 口的配對組合")
    print("   • 降低單向風險")
    
    print("\n方案 3️⃣ : 全部平倉")
    print("   • 買進近月 DHFA6: 21 口（平掉賣出部位）")
    print("   • 賣出遠月 DHFB6: 103 口（平掉買進部位）")
    print("   • 完全清空鴻海持倉")
    print("   ✅ 推薦：使用 manage_simulation_positions.py 選項 7")
    
    print("\n" + "="*100)
    print("📈 損益分析")
    print("="*100)
    
    print("\n當前損益：")
    print("   • DHFA6 賣出 21 口: +525.00 元 ✅")
    print("   • DHFB6 買進 103 口: -750.00 元 ⚠️")
    print("   • 合計: -225.00 元")
    print()
    print("   配對的 21 口: (+525 - 750×21/103) ≈ +372 元 ✅")
    print("   單邊的 82 口: -750×82/103 ≈ -597 元 ⚠️")
    
    print("\n" + "="*100)
    print("✅ 結論")
    print("="*100)
    
    print("\n1. ✅ DH 鴻海確實有近月（FA6）和遠月（FB6）的配對")
    print("2. ✅ 21 口形成正常的組合單（賣近買遠）")
    print("3. ⚠️  82 口是單邊買方部位（沒有配對）")
    print("4. 💡 SinoPac-close 不會對這個發出警告（因為有兩個月份）")
    print("5. 💡 但這不是完整的組合單策略")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    analyze_dh_positions()
