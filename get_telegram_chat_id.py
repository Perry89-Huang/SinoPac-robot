"""
快速獲取 Telegram Chat ID

使用方法：
1. 確保已經與您的機器人發送過至少一則訊息
2. 執行此腳本
"""

import requests
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ 錯誤：找不到 TELEGRAM_BOT_TOKEN")
    print("\n請確認 .env 檔案中已設定：")
    print("TELEGRAM_BOT_TOKEN=your_bot_token")
    exit(1)

print("=" * 70)
print("🔍 正在獲取 Telegram Chat ID...")
print("=" * 70)
print()

try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ API 錯誤: {data.get('description', '未知錯誤')}")
        print("\n請確認：")
        print("1. Bot Token 是否正確")
        print("2. 網路連線是否正常")
        exit(1)
    
    results = data.get('result', [])
    
    if not results:
        print("⚠️  找不到任何訊息")
        print("\n請依照以下步驟：")
        print("1. 在 Telegram 搜尋您的機器人")
        print("2. 點擊「開始」或發送任意訊息（例如：Hello）")
        print("3. 重新執行此腳本")
        exit(0)
    
    # 收集所有唯一的 Chat ID
    chat_ids = set()
    chat_info = {}
    
    for result in results:
        if 'message' in result:
            chat = result['message']['chat']
            chat_id = chat['id']
            chat_ids.add(chat_id)
            
            if chat_id not in chat_info:
                chat_info[chat_id] = {
                    'type': chat['type'],
                    'title': chat.get('title', chat.get('first_name', 'Unknown'))
                }
    
    print(f"✅ 找到 {len(chat_ids)} 個對話\n")
    
    for chat_id in sorted(chat_ids):
        info = chat_info[chat_id]
        chat_type = info['type']
        title = info['title']
        
        print(f"Chat ID: {chat_id}")
        print(f"  類型: {chat_type}")
        print(f"  名稱: {title}")
        
        if chat_type == 'private':
            print(f"  👤 個人對話")
            print(f"\n✅ 請將此 Chat ID 複製到 .env 檔案：")
            print(f"   TELEGRAM_CHAT_ID={chat_id}")
        elif chat_type == 'group' or chat_type == 'supergroup':
            print(f"  👥 群組對話")
            print(f"\n✅ 如要使用群組通知，請將此 Chat ID 複製到 .env：")
            print(f"   TELEGRAM_CHAT_ID={chat_id}")
        
        print()
    
    print("=" * 70)
    print("💡 提示：")
    print("  - 個人對話的 Chat ID 通常是正數")
    print("  - 群組對話的 Chat ID 通常是負數")
    print("  - 複製 Chat ID 後，重新執行 test_notification.py 測試")
    print("=" * 70)
    
except requests.exceptions.RequestException as e:
    print(f"❌ 網路錯誤: {e}")
    print("\n請檢查網路連線")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
