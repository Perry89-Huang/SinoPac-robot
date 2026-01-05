# Shioaji API 設定指南

## ⚠️ 重要：登入方式已改變

從 Shioaji 1.0 版本開始，登入方式已經改變：

### ❌ 舊版（已不支援）
```python
api.login("帳號", "密碼")  # 不再使用
```

### ✅ 新版（正確方式）
```python
api.login(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY"
)
```

## 📝 申請步驟

### 1. 申請 API Key

1. 前往 [永豐證券 API 管理頁面](https://www.sinotrade.com.tw/newweb/PythonAPIKey/)
2. 點擊「新增 API KEY」
3. 使用手機或電子郵件進行雙因素驗證
4. 設定以下項目：
   - **過期時間**：建議設定較長時間
   - **權限**：
     - ✅ Market / Data（市場數據）
     - ✅ Account（帳戶查詢）
     - ✅ Trading（交易功能）
   - **生產環境**：如果要在正式環境交易，需勾選
   - **允許的 IP**：建議限制 IP 提高安全性
   - **可使用帳號**：選擇您的期貨帳號

5. 完成後會獲得：
   - **API Key**：類似帳號的識別碼
   - **Secret Key**：類似密碼，只會顯示一次，請妥善保存！

### 2. 下載憑證

1. 在 API 管理頁面點擊「下載憑證」
2. 將 `.pfx` 檔案放到安全的位置
3. 記住憑證密碼

### 3. 更新程式碼

在 `SinoPac-new.py` 和 `SinoPac-close.py` 中：

```python
# 更新這些值
API_KEY = "YOUR_API_KEY"        # 填入您的 API Key
SECRET_KEY = "YOUR_SECRET_KEY"  # 填入您的 Secret Key
CA_PATH = "C:/path/to/your/certificate.pfx"  # 憑證路徑
CA_PASSWORD = "您的憑證密碼"
```

## 🔒 安全建議

### ⚠️ 不要將 API Key 硬編碼在程式中！

建議使用環境變數或配置文件：

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SINOPAC_API_KEY")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY")
```

然後在 `.env` 文件中：
```
SINOPAC_API_KEY=your_api_key_here
SINOPAC_SECRET_KEY=your_secret_key_here
```

並將 `.env` 加入 `.gitignore`：
```
.env
*.pfx
*.log
config.ini
```

## 🧪 測試模式

在開發測試時，建議先使用模擬模式：

```python
api = sj.Shioaji(simulation=True)  # 模擬模式
```

## 📋 檢查清單

- [ ] 已申請 API Key 和 Secret Key
- [ ] 已下載憑證檔案
- [ ] 已更新程式碼中的 API Key
- [ ] 已更新程式碼中的 Secret Key
- [ ] 已更新憑證路徑
- [ ] 已完成 API 使用簽署（Terms of Service）
- [ ] 已通過模擬環境測試
- [ ] 已將敏感資訊加入 .gitignore

## ❓ 常見問題

### Q: ValueError: Invalid character 'l'
**A:** 這是因為使用了舊版登入方式。請更新為新版 API Key 登入。

### Q: 如何測試 API Key 是否正確？
**A:** 使用以下測試程式：

```python
import shioaji as sj

api = sj.Shioaji(simulation=True)
try:
    accounts = api.login(
        api_key="YOUR_API_KEY",
        secret_key="YOUR_SECRET_KEY"
    )
    print("✓ 登入成功！", accounts)
except Exception as e:
    print("✗ 登入失敗：", e)
```

### Q: activate_ca 需要 person_id 嗎？
**A:** 新版不需要。只需要：
```python
api.activate_ca(
    ca_path="憑證路徑",
    ca_passwd="憑證密碼"
)
```

## 📚 相關文件

- [Shioaji 官方文檔](https://sinotrade.github.io/)
- [Token & Certificate](https://sinotrade.github.io/tutor/prepare/token/)
- [Login 教學](https://sinotrade.github.io/tutor/login/)
- [永豐證券 API 管理](https://www.sinotrade.com.tw/newweb/PythonAPIKey/)

## 🔄 已修復的問題

1. ✅ 修復日誌路徑的轉義序列警告（`\_` → `/`）
2. ✅ 更新為新版 API Key 登入方式
3. ✅ 移除 activate_ca 中的 person_id 參數
4. ✅ 添加錯誤處理和提示訊息
5. ✅ 添加 .gitignore 保護敏感資訊
