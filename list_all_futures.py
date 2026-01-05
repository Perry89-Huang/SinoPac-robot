"""
列出所有可用的期貨合約
"""
import shioaji as sj
from datetime import datetime

API_KEY = "GCoNeVLvBoACiPdECEiZ1nMyB1TJWRNrxN9EBgmjY6ts"
SECRET_KEY = "G4RSPDjtZEx7BM46e2ekfxB4n5YR1au2RpSbEfvcj9dK"

print("登入中...")
api = sj.Shioaji(simulation=False)
api.login(api_key=API_KEY, secret_key=SECRET_KEY)

print("\n" + "=" * 80)
print(f"可用的期貨合約列表（{datetime.now().strftime('%Y-%m-%d')}）")
print("=" * 80)

# 取得所有期貨合約
futures_list = []
for key in dir(api.Contracts.Futures):
    if not key.startswith('_'):
        try:
            contract = getattr(api.Contracts.Futures, key)
            if hasattr(contract, 'code'):
                futures_list.append(contract)
        except:
            pass

# 按代碼分類
categories = {}
for contract in futures_list:
    prefix = contract.code[:3] if len(contract.code) >= 3 else contract.code
    if prefix not in categories:
        categories[prefix] = []
    categories[prefix].append(contract)

# 顯示結果
count = 0
for prefix in sorted(categories.keys()):
    contracts = categories[prefix][:5]  # 只顯示前5個
    if contracts:
        print(f"\n{prefix}系列：")
        for c in contracts:
            print(f"  {c.code:12s} - {c.name:20s} 交割月:{c.delivery_month}")
            count += 1

print("\n" + "=" * 80)
print(f"共找到 {count} 個合約（部分顯示）")
print("\n建議的配置：")
print("  # 找到第一個 TXF 合約的交割月份")
print("  NEAR_MON = '第一個月份'  # 例如：'202501'")
print("  FAR_MON = '第二個月份'   # 例如：'202502'")
print("=" * 80)

api.logout()
