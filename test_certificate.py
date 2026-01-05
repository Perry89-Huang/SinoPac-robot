"""
測試憑證檔案和密碼
"""
import os
from pathlib import Path

# 憑證設定
CA_PATH = "C:/ekey/551/J120420374/S/Sinopac.pfx"

print("=" * 70)
print("憑證測試工具")
print("=" * 70)

# 1. 檢查檔案是否存在
print(f"\n1. 檢查憑證檔案...")
if os.path.exists(CA_PATH):
    print(f"   ✓ 檔案存在: {CA_PATH}")
    file_size = os.path.getsize(CA_PATH)
    print(f"   檔案大小: {file_size:,} bytes")
else:
    print(f"   ✗ 檔案不存在: {CA_PATH}")
    print("\n請確認：")
    print("   1. 憑證路徑是否正確")
    print("   2. 是否已下載憑證")
    exit(1)

# 2. 測試常見的憑證密碼
print(f"\n2. 測試憑證密碼...")
print("   提示：憑證密碼可能是：")
print("   • 身分證字號")
print("   • 出生年月日（如：19800101）")
print("   • 申請時設定的密碼")
print("   • 與網銀密碼相同")

# 提供密碼測試
test_passwords = []

print("\n請輸入要測試的憑證密碼（按 Enter 跳過）：")
while True:
    passwd = input(f"  密碼 {len(test_passwords)+1} (直接按 Enter 結束): ").strip()
    if not passwd:
        break
    test_passwords.append(passwd)

if not test_passwords:
    print("\n未輸入任何密碼，使用預設測試...")
    test_passwords = ["celia5818"]  # 目前程式中的密碼

# 測試密碼
import shioaji as sj

api = sj.Shioaji(simulation=True)  # 使用測試模式

# 先登入（測試帳號）
try:
    print("\n3. 登入測試環境...")
    api.login(
        api_key="PAPIUSER07",
        secret_key="2317"
    )
    print("   ✓ 測試環境登入成功")
except Exception as e:
    print(f"   ✗ 登入失敗: {e}")
    exit(1)

# 測試憑證密碼
print("\n4. 測試憑證密碼...")
success = False
correct_password = None

for i, passwd in enumerate(test_passwords, 1):
    print(f"\n   測試密碼 {i}: {'*' * len(passwd)}")
    try:
        api.activate_ca(
            ca_path=CA_PATH,
            ca_passwd=passwd,
        )
        print(f"   ✓ 成功！正確的憑證密碼: {passwd}")
        success = True
        correct_password = passwd
        break
    except ValueError as e:
        if "Ca Password Incorrect" in str(e):
            print(f"   ✗ 密碼錯誤")
        else:
            print(f"   ✗ 錯誤: {e}")
    except Exception as e:
        print(f"   ✗ 未預期的錯誤: {e}")

print("\n" + "=" * 70)
if success:
    print("✓ 憑證測試成功！")
    print(f"\n正確的憑證密碼: {correct_password}")
    print("\n請更新 SinoPac-new.py 中的 CA_PASSWORD：")
    print(f'  CA_PASSWORD = "{correct_password}"')
else:
    print("✗ 所有密碼測試都失敗")
    print("\n建議：")
    print("1. 聯繫永豐證券客服確認憑證密碼")
    print("2. 重新申請並下載憑證")
    print("3. 檢查憑證是否過期")
print("=" * 70)
