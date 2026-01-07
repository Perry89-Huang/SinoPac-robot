import shioaji as sj
import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()
print("✓ 已載入 .env 設定檔\n")

# 從環境變數讀取設定
API_KEY = os.getenv("SINOPAC_API_KEY", "")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
CA_PATH = os.getenv("SINOPAC_CA_PATH", "")
CA_PASSWORD = os.getenv("SINOPAC_CA_PASSWORD", "")

# 檢查設定
if not API_KEY or not SECRET_KEY:
    print("❌ 錯誤：未設定 API_KEY 或 SECRET_KEY")
    print("請在 .env 檔案中設定 SINOPAC_API_KEY 和 SINOPAC_SECRET_KEY")
    exit(1)

print("開始測試登入...")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
print(f"憑證路徑: {CA_PATH}\n")

# 使用模擬模式測試
api = sj.Shioaji(simulation=True)

try:
    # 新版登入方式 (Shioaji >= 1.0)
    print("正在登入模擬帳號...")
    accounts = api.login(
        api_key=API_KEY,
        secret_key=SECRET_KEY,
        contracts_cb=lambda security_type: print(f"  {security_type} 合約下載完成")
    )
    print("\n✓ 模擬模式登入成功！")
    print(f"帳戶數量: {len(accounts)}")
    for acc in accounts:
        print(f"  - {acc}")
    
    # 測試憑證啟動
    if CA_PATH and os.path.exists(CA_PATH):
        print("\n正在測試憑證啟動...")
        try:
            api.activate_ca(
                ca_path=CA_PATH,
                ca_passwd=CA_PASSWORD,
            )
            print("✓ 憑證啟動成功")
        except Exception as e:
            print(f"✗ 憑證啟動失敗: {e}")
            print("請檢查憑證路徑和密碼是否正確")
    else:
        print(f"\n⚠️  憑證檔案不存在: {CA_PATH}")
        print("跳過憑證測試")
    
    # 登出
    api.logout()
    print("\n✓ 測試完成，已登出")
    
except Exception as e:
    print(f"\n✗ 登入失敗: {e}")
    print("\n可能的原因：")
    print("1. API Key 或 Secret Key 格式錯誤")
    print("2. API Key 權限未啟用")
    print("3. 網路連線問題")
    print("4. 電腦時間不正確")
    
print("\n" + "="*50)
print("如果模擬模式成功，可以將 simulation 改為 False 測試正式環境")
print("特別注意以下易混淆字符：")
print("  - 小寫 'l' (L) vs 大寫 'I' (i) vs 數字 '1'")
print("  - 數字 '0' vs 大寫 'O'")
print("="*50)
