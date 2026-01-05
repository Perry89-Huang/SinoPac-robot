"""
简单诊断：直接查看期货合约对象
"""
import shioaji as sj

API_KEY = "GCoNeVLvBoACiPdECEiZ1nMyB1TJWRNrxN9EBgmjY6ts"
SECRET_KEY = "G4RSPDjtZEx7BM46e2ekfxB4n5YR1au2RpSbEfvcj9dK"

print("登入中...")
api = sj.Shioaji(simulation=False)
api.login(api_key=API_KEY, secret_key=SECRET_KEY, contracts_timeout=10000)
print("登入成功\n")

# 方法1：查看 Futures 对象结构
print("=" * 80)
print("方法1：查看 api.Contracts.Futures 对象")
print("=" * 80)
print(f"类型: {type(api.Contracts.Futures)}")
print(f"属性: {dir(api.Contracts.Futures)[:20]}")  # 只显示前20个

# 方法2：尝试不同的访问方式
print("\n" + "=" * 80)
print("方法2：尝试访问台指期货（TXF）")
print("=" * 80)

test_codes = ['TXFA1', 'TXFA2', 'TXF202501', 'TXF202502', 'MTXA1', 'MTXA2']

for code in test_codes:
    try:
        contract = api.Contracts.Futures.get(code)
        if contract:
            print(f"✓ {code:15} -> {contract.code} | {contract.name} | 交割月: {contract.delivery_month}")
        else:
            print(f"✗ {code:15} -> None")
    except Exception as e:
        print(f"✗ {code:15} -> Error: {e}")

# 方法3：查看 TXF 类别
print("\n" + "=" * 80)
print("方法3：直接查看 api.Contracts.Futures.TXF")
print("=" * 80)

try:
    if hasattr(api.Contracts.Futures, 'TXF'):
        txf_contracts = api.Contracts.Futures.TXF
        print(f"类型: {type(txf_contracts)}")
        print(f"TXF 合约对象: {txf_contracts}")
        print(f"\n前5个 TXF 合约：")
        count = 0
        for contract in txf_contracts:
            if count < 5:
                print(f"  {contract.code:15} | {contract.symbol:20} | {contract.name:25} | 交割: {contract.delivery_month}")
                count += 1
    else:
        print("找不到 TXF 属性")
except Exception as e:
    print(f"错误: {e}")

# 方法4：使用字典方式访问
print("\n" + "=" * 80)
print("方法4：使用字典方式 api.Contracts.Futures[code]")
print("=" * 80)

for code in test_codes:
    try:
        contract = api.Contracts.Futures[code]
        print(f"✓ {code:15} -> {contract.code} | {contract.name}")
    except Exception as e:
        print(f"✗ {code:15} -> {type(e).__name__}")

api.logout()
print("\n完成！")
