"""
資料庫系統示範 - 不需要 API 的測試
展示資料庫的基本功能
"""
import sys
from database_manager import init_database
import pandas as pd
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("資料庫系統功能示範")
print("="*80)

# 初始化資料庫
print("\n📦 初始化資料庫...")
db = init_database()

# 顯示初始狀態
print("\n📊 資料庫初始狀態:")
stats = db.get_database_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

# 建立測試資料
print("\n✨ 建立測試資料...")

test_stocks = {
    '2330': {'name': '台積電', 'dividend': 11.0, 'price': 600.0},
    '2317': {'name': '鴻海', 'dividend': 5.0, 'price': 100.0},
    '2454': {'name': '聯發科', 'dividend': 32.0, 'price': 1000.0},
    '2881': {'name': '富邦金', 'dividend': 3.0, 'price': 60.0},
    '2882': {'name': '國泰金', 'dividend': 3.5, 'price': 50.0},
}

# 1. 儲存股票資訊
print("   1. 儲存股票基本資訊...")
stock_info = pd.DataFrame([
    {
        'stock_id': stock_id,
        'stock_name': info['name'],
        'industry_category': '電子' if stock_id in ['2330', '2317', '2454'] else '金融',
        'type': 'twse'
    }
    for stock_id, info in test_stocks.items()
])
db.save_stock_info(stock_info)
print(f"   ✅ 已儲存 {len(test_stocks)} 檔股票資訊")

# 2. 儲存股利資料
print("   2. 儲存股利資料...")
for stock_id, info in test_stocks.items():
    dividend_df = pd.DataFrame({
        'AnnouncementDate': ['2024-03-15'],
        'CashDividend': [info['dividend']],
        'StockDividend': [0.0],
        'CashEarningsDistribution': [info['dividend']]
    })
    db.save_dividend_data(stock_id, dividend_df)
print(f"   ✅ 已儲存 {len(test_stocks)} 檔股利資料")

# 3. 儲存股價資料（最近 7 天）
print("   3. 儲存股價資料（最近 7 天）...")
for stock_id, info in test_stocks.items():
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
             for i in range(7)]
    # 模擬價格波動
    base_price = info['price']
    prices = [base_price * (1 + (i % 3 - 1) * 0.01) for i in range(7)]
    
    price_df = pd.DataFrame({
        'date': dates,
        'open': [p * 0.99 for p in prices],
        'max': [p * 1.02 for p in prices],
        'min': [p * 0.98 for p in prices],
        'close': prices,
        'Trading_Volume': [10000000] * 7
    })
    db.save_daily_price(stock_id, price_df)
print(f"   ✅ 已儲存 {len(test_stocks) * 7} 筆股價資料")

# 4. 儲存 KD 指標
print("   4. 儲存 KD 指標...")
for stock_id in test_stocks.keys():
    # 日 KD
    db.save_kd_indicators(stock_id, 'daily', 75.5, 68.3)
    # 週 KD
    db.save_kd_indicators(stock_id, 'weekly', 82.1, 79.6)
print(f"   ✅ 已儲存 {len(test_stocks) * 2} 組 KD 指標")

# 顯示更新後狀態
print("\n📊 資料庫更新後狀態:")
stats = db.get_database_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

# 5. 測試資料讀取
print("\n🔍 測試資料讀取功能:")

print("\n   1️⃣ 讀取台積電 (2330) 股利資料:")
dividend_data = db.get_dividend_data('2330', start_date='2024-01-01')
if not dividend_data.empty:
    print(f"      股利: {dividend_data.iloc[0]['CashEarningsDistribution']}")
    print(f"      日期: {dividend_data.iloc[0]['AnnouncementDate']}")

print("\n   2️⃣ 讀取台積電 (2330) 最新股價:")
latest_price = db.get_latest_price('2330')
print(f"      最新收盤價: {latest_price:.2f}")

print("\n   3️⃣ 讀取台積電 (2330) 日 KD 指標:")
daily_kd = db.get_kd_indicators('2330', 'daily')
if daily_kd:
    print(f"      K: {daily_kd['k']:.2f}, D: {daily_kd['d']:.2f}")

print("\n   4️⃣ 檢查資料新舊:")
for stock_id in ['2330', '2317']:
    is_fresh = db.is_dividend_data_fresh(stock_id, max_age_days=7)
    print(f"      {stock_id} 股利資料: {'✅ 最新' if is_fresh else '❌ 過期'}")

# 6. 測試高殖利率篩選
print("\n💎 篩選殖利率 > 5% 的股票:")
print(f"{'股票代碼':<8} {'股票名稱':<10} {'股價':<8} {'股利':<8} {'殖利率':<8}")
print("-" * 50)

for stock_id, info in test_stocks.items():
    price = db.get_latest_price(stock_id)
    dividend_data = db.get_dividend_data(stock_id)
    
    if not dividend_data.empty and price:
        dividend = dividend_data.iloc[0]['CashEarningsDistribution']
        dividend_yield = (dividend / price) * 100
        
        if dividend_yield > 5:
            print(f"{stock_id:<8} {info['name']:<10} {price:<8.2f} {dividend:<8.2f} {dividend_yield:<8.2f}%")

# 7. API 使用統計
print("\n📈 API 請求統計（示範）:")
# 記錄一些示範請求
for stock_id in test_stocks.keys():
    db.log_api_request('dividend', stock_id, True)
    db.log_api_request('price', stock_id, True)

api_stats = db.get_api_request_stats(hours=24)
print(f"   總請求數: {api_stats['total_requests']}")
print(f"   成功請求: {api_stats['successful_requests']}")
print(f"   查詢股票數: {api_stats['unique_stocks']}")

# 關閉資料庫
print("\n💾 關閉資料庫連接...")
db.close()

print("\n" + "="*80)
print("✅ 示範完成！")
print("="*80)
print("\n說明：")
print("1. 此示範不需要 FinMind API，使用模擬資料")
print("2. 展示了資料庫的基本儲存和讀取功能")
print("3. 實際使用時，資料會從 FinMind API 自動下載")
print("\n下一步：")
print("1. 等待 API 恢復後執行：python sync_data.py --stock 2330")
print("2. 成功後執行：python sync_data.py --mode candidates")
print("3. 開始查詢：python find_high_dividend_stocks.py")
