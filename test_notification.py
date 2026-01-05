"""
測試通知功能腳本
執行此腳本以驗證 Email 和 Line Notify 設定是否正確
"""

from notification_manager import notifier
import time

def main():
    print("=" * 70)
    print("通知功能測試腳本")
    print("=" * 70)
    print()
    
    # 顯示當前設定狀態
    print("📋 當前通知設定:")
    print(f"  Email: {'✅ 已設定' if notifier.email_enabled else '❌ 未設定'}")
    print(f"  Telegram: {'✅ 已設定' if notifier.telegram_enabled else '❌ 未設定'}")
    print()
    
    if not notifier.email_enabled and not notifier.telegram_enabled:
        print("⚠️  警告: 未設定任何通知管道")
        print()
        print("請依照以下步驟設定：")
        print("1. 複製 .env.example 為 .env")
        print("2. 編輯 .env 並填入 Email 或 Telegram 設定")
        print("3. 參考 '通知設定說明.md' 獲取詳細教學")
        print()
        return
    
    print("開始測試通知發送...")
    print()
    
    # 測試 1: 程式啟動通知
    print("📤 測試 1/7: 程式啟動通知")
    notifier.notify_program_start("測試機器人")
    time.sleep(2)
    
    # 測試 2: 下單成功通知
    print("📤 測試 2/7: 下單成功通知")
    notifier.notify_order_success(
        contract_code="HSFL2",
        action="買進",
        price=123.5,
        quantity=2
    )
    time.sleep(2)
    
    # 測試 3: 下單失敗通知
    print("📤 測試 3/7: 下單失敗通知")
    notifier.notify_order_failed(
        contract_code="HSFL2",
        action="賣出",
        error="市場已關閉"
    )
    time.sleep(2)
    
    # 測試 4: 持倉限制通知
    print("📤 測試 4/7: 持倉限制通知")
    notifier.notify_position_limit_reached(
        limit_type="總持倉上限",
        current=30,
        limit=30
    )
    time.sleep(2)
    
    # 測試 5: 連線中斷通知
    print("📤 測試 5/7: 連線中斷通知")
    notifier.notify_connection_lost()
    time.sleep(2)
    
    # 測試 6: 重新連線成功通知
    print("📤 測試 6/7: 重新連線成功通知")
    notifier.notify_reconnect_success()
    time.sleep(2)
    
    # 測試 7: 程式停止通知
    print("📤 測試 7/7: 程式停止通知")
    notifier.notify_program_stop("測試機器人", "測試完成")
    time.sleep(2)
    
    print()
    print("=" * 70)
    print("✅ 測試完成！")
    print("=" * 70)
    print()
    print("請檢查：")
    if notifier.email_enabled:
        print(f"  📧 Email 信箱: 是否收到 7 封測試郵件")
    if notifier.telegram_enabled:
        print(f"  📢 Telegram: 是否收到 7 則測試訊息")
    print()
    print("如果沒有收到通知，請檢查：")
    print("  1. .env 檔案設定是否正確")
    print("  2. 網路連線是否正常")
    print("  3. 查看 PerryLogs/notification.log 日誌")
    print()
    print("詳細設定說明請參考: 通知設定說明.md")
    print()

if __name__ == "__main__":
    main()
