"""
查詢可用的期貨合約代碼
"""
import shioaji as sj
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 使用您的 API Key登入
API_KEY = "GCoNeVLvBoACiPdECEiZ1nMyB1TJWRNrxN9EBgmjY6ts"
SECRET_KEY = "G4RSPDjtZEx7BM46e2ekfxB4n5YR1au2RpSbEfvcj9dK"

print("正在登入...")
api = sj.Shioaji(simulation=False)
api.login(api_key=API_KEY, secret_key=SECRET_KEY)
print("登入成功\n")

# 查詢特定股票期貨
test_codes = ['HS', 'HC', 'CS', 'CD', 'CH', 'IR', 'DH', 'NV', 'CK', 'CZ', 'CC']

print("=" * 80)
print("查詢期貨合約代碼")
print("=" * 80)

for code in test_codes:
    print(f"\n{code} 相關合約：")
    found = False
    count = 0
    
    # 直接嘗試常見的月份代碼
    months = ['202501', '202502', '202503', '202504', '202505', '202506']
    for mon in months:
        try:
            contract_code = code + mon
            contract = api.Contracts.Futures.get(contract_code)
            if contract:
                print(f"  {contract.code} - {contract.name} (交割月: {contract.delivery_month})")
                found = True
                count += 1
                if count >= 3:  # 只顯示前3個
                    break
        except:
            pass
    
    if not found:
        print(f"  找不到任何 {code} 相關的期貨合約")

print("\n" + "=" * 80)
print("可用的月份代碼格式說明：")
print("=" * 80)
print("期貨月份代碼通常格式如下：")
print("  - 2502 = 2025年2月")
print("  - 2503 = 2025年3月")
print("  - 202502 = 2025年2月（完整格式）")
print("\n範例：")
print("  NEAR_MON = '202501'  # 2025年1月")
print("  FAR_MON = '202502'   # 2025年2月")
print("=" * 80)

api.logout()
