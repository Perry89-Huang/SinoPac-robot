# Telegram Bot 通知設定教學

## 📱 為什麼選擇 Telegram Bot？

Telegram Bot 是 Line Notify 終止服務後的最佳替代方案：

✅ **完全免費** - 無使用限制  
✅ **即時推播** - 訊息秒到  
✅ **設定簡單** - 5分鐘完成  
✅ **功能強大** - 支援文字、圖片、檔案  
✅ **隱私安全** - 端對端加密  
✅ **跨平台** - 手機、電腦都能用

---

## 🚀 快速設定（5分鐘）

### 步驟 1：建立 Telegram Bot

1. **開啟 Telegram**（手機或電腦版都可以）

2. **搜尋 @BotFather**
   - 在搜尋欄輸入 `@BotFather`
   - 點擊官方認證的 BotFather（藍色勾勾）

3. **開始對話**
   - 點擊「開始」或發送 `/start`

4. **建立新機器人**
   - 發送指令：`/newbot`
   - BotFather 會引導您完成設定

5. **設定機器人名稱**
   ```
   BotFather: Alright, a new bot. How are we going to call it?
   您輸入: 交易系統通知機器人
   ```
   - 這是顯示名稱，可以用中文

6. **設定機器人用戶名**
   ```
   BotFather: Good. Now let's choose a username for your bot.
   您輸入: MyTradingBot_2025_bot
   ```
   - ⚠️ 必須以 `bot` 結尾
   - ⚠️ 只能用英文、數字、底線
   - 💡 建議加上年份避免重複

7. **獲取 Bot Token**
   ```
   Done! Congratulations on your new bot. You will find it at t.me/MyTradingBot_2025_bot.
   
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
   
   Keep your token secure and store it safely...
   ```
   - ✅ **複製這串 Token**（很重要！）
   - ⚠️ 不要分享給任何人

---

### 步驟 2：獲取 Chat ID

#### 方法 A：使用瀏覽器（推薦）

1. **與您的機器人開始對話**
   - 在 Telegram 搜尋您剛建立的機器人用戶名
   - 例如：`@MyTradingBot_2025_bot`
   - 點擊「開始」或發送任意訊息（例如：`Hello`）

2. **開啟瀏覽器**
   - 在網址列輸入以下網址（替換 `<YOUR_BOT_TOKEN>`）：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   
   完整範例：
   ```
   https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890/getUpdates
   ```

3. **查看結果**
   - 會看到一堆 JSON 資料
   - 找到 `"chat":{"id":123456789}`
   - **123456789 就是您的 Chat ID**（可能是負數，沒關係）

#### 方法 B：使用 Python 腳本

1. **建立測試腳本** `get_chat_id.py`：
```python
import requests

# 替換成您的 Bot Token
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)
data = response.json()

if data['result']:
    chat_id = data['result'][0]['message']['chat']['id']
    print(f"✓ 您的 Chat ID: {chat_id}")
else:
    print("⚠️  請先與機器人發送一則訊息")
```

2. **執行腳本**
```powershell
python get_chat_id.py
```

---

### 步驟 3：設定環境變數

1. **編輯 .env 檔案**
```env
# Telegram Bot 通知設定
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
TELEGRAM_CHAT_ID=123456789
```

2. **儲存檔案**

---

### 步驟 4：測試通知

```powershell
python test_notification.py
```

如果設定正確，您應該會在 Telegram 收到測試訊息！

---

## 🔧 進階設定

### 設定機器人頭像

1. 與 @BotFather 對話
2. 發送 `/setuserpic`
3. 選擇您的機器人
4. 上傳圖片

### 設定機器人描述

```
/setdescription
選擇機器人
輸入描述：這是我的交易系統通知機器人
```

### 設定指令清單

```
/setcommands
選擇機器人
輸入：
status - 查詢系統狀態
positions - 查詢持倉
help - 幫助
```

---

## 📊 通知範例

### 程式啟動通知
```
🕐 2025-12-27 09:00:00

ℹ️ [INFO] 程式啟動

🚀 建倉機器人 (SinoPac-new) 已啟動運行
```

### 下單成功通知
```
🕐 2025-12-27 09:30:15

ℹ️ [INFO] 下單成功

合約: HSFL2
動作: 買進
價格: 123.5
數量: 2 口
```

### 連線中斷警告
```
🕐 2025-12-27 14:20:30

⚠️ [WARNING] 連線中斷

⚠️ API 連線中斷，正在嘗試重新連線...
```

---

## ❓ 常見問題

### Q1: Bot Token 遺失了怎麼辦？

1. 與 @BotFather 對話
2. 發送 `/mybots`
3. 選擇您的機器人
4. 點擊「API Token」
5. 選擇「Revoke current token」生成新 Token

⚠️ 舊 Token 會失效，需要更新 `.env` 檔案

---

### Q2: 找不到 Chat ID？

**確認步驟：**
1. ✅ 已經與機器人發送訊息了嗎？
2. ✅ Bot Token 是否正確？
3. ✅ 網址中的 Token 有包含完整嗎？

**重新嘗試：**
```powershell
# 使用 PowerShell
$token = "YOUR_BOT_TOKEN"
$response = Invoke-RestMethod "https://api.telegram.org/bot$token/getUpdates"
$response.result[0].message.chat.id
```

---

### Q3: 收不到通知？

**檢查清單：**
1. ✅ Bot Token 和 Chat ID 是否正確
2. ✅ `.env` 檔案是否儲存
3. ✅ 網路連線是否正常
4. ✅ 機器人是否被封鎖（檢查 Telegram 設定）

**查看日誌：**
```powershell
Get-Content PerryLogs/notification.log -Tail 20
```

---

### Q4: 可以讓多人接收通知嗎？

**方法 1：建立群組**
1. 建立 Telegram 群組
2. 將機器人加入群組
3. 發送訊息到群組
4. 使用 getUpdates 獲取群組的 Chat ID（會是負數）
5. 更新 `.env` 中的 TELEGRAM_CHAT_ID

**方法 2：建立多個機器人**
- 為不同人建立不同的機器人
- 各自設定自己的環境變數

---

### Q5: Telegram 比 Email 好在哪？

| 功能 | Telegram | Email |
|------|----------|-------|
| 即時性 | ⚡ 秒到 | 📧 數分鐘 |
| 推播通知 | ✅ 原生支援 | ⚠️ 需設定 |
| 訊息格式 | ✅ HTML/Markdown | ✅ HTML |
| 檔案傳送 | ✅ 最大 50MB | ⚠️ 依服務商 |
| 免費額度 | ✅ 無限制 | ⚠️ 有限制 |
| 設定難度 | ⭐⭐ 簡單 | ⭐⭐⭐ 中等 |

💡 **建議：兩者都設定**，Telegram 作為主要通知，Email 作為備援！

---

## 🔐 安全建議

1. **保護 Bot Token**
   - ✅ 不要上傳到 GitHub
   - ✅ 不要分享給他人
   - ✅ 定期更換 Token

2. **限制機器人權限**
   - 使用 @BotFather 的 `/setprivacy` 設定隱私
   - 建議設為 `ENABLED`（只回應指令）

3. **監控異常登入**
   - 定期查看機器人的使用記錄
   - 發現異常立即撤銷 Token

---

## 📚 更多資源

- [Telegram Bot API 官方文檔](https://core.telegram.org/bots/api)
- [BotFather 指令清單](https://core.telegram.org/bots#6-botfather)
- [Telegram Bot 範例](https://core.telegram.org/bots/samples)

---

## ✨ 設定完成檢查清單

- [ ] 已建立 Telegram Bot
- [ ] 已獲取 Bot Token
- [ ] 已獲取 Chat ID
- [ ] 已更新 `.env` 檔案
- [ ] 已執行測試腳本
- [ ] 已收到測試訊息

**恭喜！您已成功設定 Telegram 通知！** 🎉

---

**有問題？** 查看 `PerryLogs/notification.log` 日誌檔案或參考「通知設定說明.md」
