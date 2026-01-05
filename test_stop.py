"""
測試改進的停止機制
按 Ctrl+C 或輸入 'quit' 停止程式
"""
import shioaji as sj
import signal
import sys
import threading

API_KEY = "GCoNeVLvBoACiPdECEiZ1nMyB1TJWRNrxN9EBgmjY6ts"
SECRET_KEY = "G4RSPDjtZEx7BM46e2ekfxB4n5YR1au2RpSbEfvcj9dK"

# 全域變數
running = True
api = None

def signal_handler(sig, frame):
    global running
    print("\n\n⚠️  收到停止信號...")
    running = False
    if api:
        try:
            api.logout()
            print("✓ 已登出")
        except:
            pass
    print("程式已停止")
    sys.exit(0)

# 註冊信號
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, signal_handler)

# 登入
print("正在登入...")
api = sj.Shioaji(simulation=False)
api.login(api_key=API_KEY, secret_key=SECRET_KEY)
print("✓ 登入成功")

print("\n測試停止機制...")
print("方法1: 按 Ctrl+C")
print("方法2: 關閉終端視窗")
print("方法3: 執行 stop_program.ps1\n")

# 使用輪詢而不是 Event().wait()
import time
print("程式運行中...\n")
try:
    while running:
        time.sleep(1)
        print(".", end="", flush=True)
except KeyboardInterrupt:
    signal_handler(None, None)
