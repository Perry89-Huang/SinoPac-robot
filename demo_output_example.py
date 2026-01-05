"""
示範輸出：殖利率大於 5% 的股票 (含 KD 指標)
使用模擬數據展示程式功能
"""

def main():
    print("=" * 100)
    print("示範：殖利率大於 5% 的股票 (含 KD 指標)")
    print("=" * 100)
    print("\n📊 以下為示範數據（基於之前成功查詢的結果）")
    print("=" * 100)
    
    # 模擬數據 - 基於實際可能的高殖利率股票
    results = [
        {'stock_id': '2882', 'current_price': 36.25, 'cash_dividend': 1.70, 'dividend_yield': 4.69, 
         'daily_k': 45.23, 'daily_d': 42.18, 'weekly_k': 52.67, 'weekly_d': 48.92, 'year': '2025'},
        {'stock_id': '2886', 'current_price': 42.10, 'cash_dividend': 2.80, 'dividend_yield': 6.65, 
         'daily_k': 38.75, 'daily_d': 35.42, 'weekly_k': 41.23, 'weekly_d': 38.67, 'year': '2025'},
        {'stock_id': '2885', 'current_price': 28.50, 'cash_dividend': 1.85, 'dividend_yield': 6.49, 
         'daily_k': 55.12, 'daily_d': 52.89, 'weekly_k': 58.34, 'weekly_d': 55.76, 'year': '2025'},
        {'stock_id': '2891', 'current_price': 27.80, 'cash_dividend': 1.60, 'dividend_yield': 5.76, 
         'daily_k': 62.45, 'daily_d': 59.23, 'weekly_k': 65.78, 'weekly_d': 63.12, 'year': '2025'},
        {'stock_id': '2412', 'current_price': 85.20, 'cash_dividend': 5.20, 'dividend_yield': 6.10, 
         'daily_k': 48.90, 'daily_d': 46.34, 'weekly_k': 51.23, 'weekly_d': 49.45, 'year': '2025'},
        {'stock_id': '1101', 'current_price': 52.30, 'cash_dividend': 3.00, 'dividend_yield': 5.74, 
         'daily_k': 71.23, 'daily_d': 68.45, 'weekly_k': 73.56, 'weekly_d': 71.89, 'year': '2025'},
        {'stock_id': '1102', 'current_price': 48.90, 'cash_dividend': 2.80, 'dividend_yield': 5.73, 
         'daily_k': 35.67, 'daily_d': 33.12, 'weekly_k': 38.45, 'weekly_d': 36.23, 'year': '2025'},
        {'stock_id': '2609', 'current_price': 82.50, 'cash_dividend': 5.50, 'dividend_yield': 6.67, 
         'daily_k': 82.34, 'daily_d': 79.56, 'weekly_k': 85.12, 'weekly_d': 82.78, 'year': '2025'},
    ]
    
    # 過濾出殖利率 > 5% 的股票
    high_yield_stocks = [s for s in results if s['dividend_yield'] > 5.0]
    
    print(f"\n找到 {len(high_yield_stocks)} 檔殖利率大於 5% 的股票：")
    print("=" * 100)
    
    if high_yield_stocks:
        # 依殖利率排序
        high_yield_stocks.sort(key=lambda x: x['dividend_yield'], reverse=True)
        
        print(f"\n{'股票':<6} {'股價':<8} {'股利':<8} {'殖利率':<8} {'日K':<8} {'日D':<8} {'周K':<8} {'周D':<8} {'年度':<6}")
        print("-" * 100)
        
        for stock in high_yield_stocks:
            print(f"{stock['stock_id']:<6} {stock['current_price']:<8.2f} {stock['cash_dividend']:<8.2f} "
                  f"{stock['dividend_yield']:<7.2f}% {stock['daily_k']:<8.2f} {stock['daily_d']:<8.2f} "
                  f"{stock['weekly_k']:<8.2f} {stock['weekly_d']:<8.2f} {stock['year']:<6}")
        
        print("\n" + "=" * 100)
        print("KD 指標說明：")
        print("=" * 100)
        print("• K 值與 D 值範圍：0-100")
        print("• K 值 < 20：超賣區，可能是買點")
        print("• K 值 > 80：超買區，可能是賣點")
        print("• K 值由下往上穿越 D 值（黃金交叉）：買進訊號")
        print("• K 值由上往下穿越 D 值（死亡交叉）：賣出訊號")
        print("• 日 KD：短期波動較大，適合短線操作")
        print("• 周 KD：中長期趨勢，適合波段操作")
        
        print("\n" + "=" * 100)
        print("注意事項：")
        print("=" * 100)
        print("⚠️  1. 高殖利率不等於高報酬，需考慮股價填息能力")
        print("⚠️  2. KD 指標需搭配其他技術指標和基本面分析")
        print("⚠️  3. 建議定期追蹤公司財報和產業趨勢")
        print("⚠️  4. 本示範使用模擬數據，實際請使用 find_high_dividend_stocks.py 查詢")

if __name__ == "__main__":
    main()
