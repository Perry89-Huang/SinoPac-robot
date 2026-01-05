import shioaji as sj

# 測試登入
print("開始測試登入...")

# 使用模擬模式測試
api = sj.Shioaji(simulation=True)

try:
    accounts = api.login(
        "PAPIUSER07",  # 測試帳號
        "2317"         # 測試密碼
    )
    print("✓ 模擬模式登入成功！")
    print(f"帳戶資訊: {accounts}")
except Exception as e:
    print(f"✗ 模擬模式登入失敗: {e}")

print("\n" + "="*50)
print("如果模擬模式成功，請檢查您的正式帳號密碼")
print("特別注意以下易混淆字符：")
print("  - 小寫 'l' (L) vs 大寫 'I' (i) vs 數字 '1'")
print("  - 數字 '0' vs 大寫 'O'")
print("="*50)
