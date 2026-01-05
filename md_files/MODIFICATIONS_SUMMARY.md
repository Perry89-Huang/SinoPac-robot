# SinoPac 程序修改总结

## 已完成的修改（SinoPac-new.py 和 SinoPac-close.py）

### ✅ 1. 登入方式更新
- 从旧版 `api.login(person_id, password)` 更新为新版 `api.login(api_key, secret_key)`
- 添加 API Key 验证逻辑
- 添加 Base58 格式验证

### ✅ 2. 错误处理改进
- 登入失败时提供详细错误信息
- 憑證启动失败时的完整错误处理
- 不再因憑證错误而中止程序（允许继续执行）

### ✅ 3. 路径问题修复
- 修复日志路径 `PerryLogs\_New_{time}.log` → `PerryLogs/New_{time}.log`
- 修复日志路径 `PerryLogs\Close_{time}.log` → `PerryLogs/Close_{time}.log`

### ✅ 4. 月份代码格式
- 从 `FL2`, `FA3` 更正为 `A6`, `B6`（根据实际可用合约）
- A6 = 六个月后合约
- B6 = 七个月后合约

### ✅ 5. 停止机制改进
- 添加信号处理（SIGINT, SIGBREAK）
- 使用轮询 `while running` 代替 `Event().wait()`
- 支持 Ctrl+C 优雅停止
- 添加 `stop_program.ps1` 强制停止脚本

### ✅ 6. 配置改进
- GROUP 设置更清晰
- 添加股票期货组选项（GROUP=3）
- 修正拼写错误：`Fales` → `False`

### ✅ 7. 合约载入验证
- 添加合约存在性检查
- 详细的合约载入日志
- 失败时提供清晰的错误提示

## 主要文件

### SinoPac-new.py
建倉機器人 - 監聽期貨報價，當價差符合條件時自動建倉

### SinoPac-close.py
平倉機器人 - 監聽現有倉位，當利潤達標時自動平倉

### 輔助工具
- `check_contracts.py` - 查詢可用合約
- `diagnose_contracts.py` - 診斷合約訪問問題
- `list_all_futures.py` - 列出所有期貨合約
- `test_certificate.py` - 測試憑證密碼
- `test_stop.py` - 測試停止機制
- `stop_program.ps1` - 強制停止程序

## 使用方法

### 運行建倉機器人
```powershell
python d:\PerryCoding\Python\SinoPac\SinoPac-new.py
```

### 運行平倉機器人
```powershell
python d:\PerryCoding\Python\SinoPac\SinoPac-close.py
```

### 停止程序
方法 1: 按 Ctrl+C
方法 2: 執行 `.\stop_program.ps1`
方法 3: `Get-Process python | Stop-Process -Force`

## 配置說明

### 修改 GROUP 設定
```python
GROUP = 1  # 台指期貨（TXF）
GROUP = 2  # 小型台指（MTX）
GROUP = 3  # 股票期貨（HS, HC, CS, 等）
```

### 修改交易模式
```python
g_bolOrderOn = False  # 僅觀察模式
g_bolOrderOn = True   # 自動下單模式
```

## 注意事項

⚠️ **API Key 安全**
- 不要將 API Key 上傳到 Git
- 已添加 `.gitignore` 保護敏感信息

⚠️ **測試建議**
- 先使用 `simulation=True` 測試
- 先設定 `g_bolOrderOn=False` 觀察模式
- 確認策略無誤後再啟用自動交易

⚠️ **市場時間**
- 期貨交易時間：08:45-13:45（日盤）
- 期貨交易時間：15:00-05:00（夜盤）
- 非交易時間無法下單

## 問題排查

### 找不到合約
- 檢查 NEAR_MON 和 FAR_MON 設定
- 執行 `check_contracts.py` 查詢可用合約
- 確認合約是否已過期

### 無法停止程序
- 執行 `.\stop_program.ps1`
- 或直接關閉終端視窗

### 登入失敗
- 確認 API Key 和 Secret Key 正確
- 檢查 API 權限設定
- 確認網路連線正常

### 憑證錯誤
- 確認憑證密碼正確
- 檢查憑證文件是否存在
- 確認憑證未過期
