"""
通知功能使用範例

此腳本展示如何在您的程式中使用通知管理器
"""

from notification_manager import notifier

# ============================================================
# 範例 1: 程式生命週期通知
# ============================================================

def example_program_lifecycle():
    """程式啟動和停止通知"""
    print("\n=== 範例 1: 程式生命週期通知 ===\n")
    
    # 程式啟動時
    notifier.notify_program_start("我的交易程式")
    print("✓ 已發送程式啟動通知")
    
    # 程式停止時（正常停止）
    notifier.notify_program_stop("我的交易程式", "正常結束")
    print("✓ 已發送程式停止通知")
    
    # 程式異常停止
    notifier.notify_program_stop("我的交易程式", "發生錯誤: 連線逾時")
    print("✓ 已發送異常停止通知")


# ============================================================
# 範例 2: 交易執行通知
# ============================================================

def example_trading_notifications():
    """下單成功和失敗通知"""
    print("\n=== 範例 2: 交易執行通知 ===\n")
    
    # 下單成功
    notifier.notify_order_success(
        contract_code="HSFL2",
        action="買進",
        price=125.5,
        quantity=2
    )
    print("✓ 已發送下單成功通知")
    
    # 下單失敗
    notifier.notify_order_failed(
        contract_code="HSFL2",
        action="賣出",
        error="餘額不足"
    )
    print("✓ 已發送下單失敗通知")
    
    # 組合單失敗（特殊情況）
    notifier.notify_combo_order_failed(
        near_code="HSFL2",
        far_code="HSFA3"
    )
    print("✓ 已發送組合單失敗通知")


# ============================================================
# 範例 3: 持倉監控通知
# ============================================================

def example_position_monitoring():
    """持倉限制和異常通知"""
    print("\n=== 範例 3: 持倉監控通知 ===\n")
    
    # 達到總持倉上限
    notifier.notify_position_limit_reached(
        limit_type="總持倉上限",
        current=30,
        limit=30
    )
    print("✓ 已發送總持倉上限通知")
    
    # 達到單一標的上限
    notifier.notify_position_limit_reached(
        limit_type="單一標的上限 (長榮航)",
        current=5,
        limit=5
    )
    print("✓ 已發送單一標的上限通知")
    
    # 持倉異常警告
    notifier.notify_position_alert(
        "檢測到單邊持倉: HSFL2 買進 x2 未配對遠月"
    )
    print("✓ 已發送持倉異常警告")


# ============================================================
# 範例 4: 連線監控通知
# ============================================================

def example_connection_monitoring():
    """連線狀態變化通知"""
    print("\n=== 範例 4: 連線監控通知 ===\n")
    
    # 連線中斷
    notifier.notify_connection_lost()
    print("✓ 已發送連線中斷通知")
    
    # 重新連線成功
    notifier.notify_reconnect_success()
    print("✓ 已發送重連成功通知")
    
    # 重新連線失敗
    notifier.notify_reconnect_failed()
    print("✓ 已發送重連失敗通知")


# ============================================================
# 範例 5: 每日摘要通知
# ============================================================

def example_daily_summary():
    """每日交易摘要通知"""
    print("\n=== 範例 5: 每日摘要通知 ===\n")
    
    summary = {
        "date": "2025-01-17",
        "total_trades": 15,
        "successful_trades": 13,
        "failed_trades": 2,
        "total_profit": 2500,
        "total_positions": 8
    }
    
    notifier.notify_daily_summary(summary)
    print("✓ 已發送每日摘要通知")


# ============================================================
# 範例 6: 在實際交易函數中使用
# ============================================================

def example_real_world_usage():
    """實際交易場景中的通知整合"""
    print("\n=== 範例 6: 實際交易場景 ===\n")
    
    # 模擬下單流程
    try:
        # 1. 檢查持倉限制
        current_position = 28
        max_position = 30
        
        if current_position >= max_position:
            notifier.notify_position_limit_reached(
                limit_type="總持倉上限",
                current=current_position,
                limit=max_position
            )
            print("✓ 達到持倉限制，已發送通知")
            return
        
        # 2. 執行下單（模擬）
        order_success = True  # 假設下單成功
        
        if order_success:
            notifier.notify_order_success(
                contract_code="HSFL2",
                action="買進",
                price=123.5,
                quantity=2
            )
            print("✓ 下單成功，已發送通知")
        else:
            notifier.notify_order_failed(
                contract_code="HSFL2",
                action="買進",
                error="市場已關閉"
            )
            print("✓ 下單失敗，已發送通知")
            
    except Exception as e:
        # 3. 異常處理
        notifier.notify_program_stop(
            program_name="交易程式",
            reason=f"發生異常: {str(e)}"
        )
        print(f"✓ 程式異常，已發送通知: {e}")


# ============================================================
# 範例 7: 條件式通知（避免通知轟炸）
# ============================================================

def example_conditional_notification():
    """智能通知 - 避免重複通知"""
    print("\n=== 範例 7: 智能通知策略 ===\n")
    
    # 使用全域變數記錄上次通知時間
    from datetime import datetime, timedelta
    
    last_notification = {}
    
    def smart_notify(event_type, cooldown_minutes=5):
        """帶冷卻時間的智能通知"""
        now = datetime.now()
        
        # 檢查冷卻時間
        if event_type in last_notification:
            time_since_last = now - last_notification[event_type]
            if time_since_last < timedelta(minutes=cooldown_minutes):
                print(f"  ⏳ {event_type} 冷卻中，跳過通知")
                return False
        
        # 發送通知並更新時間
        last_notification[event_type] = now
        return True
    
    # 模擬多次連線檢查
    for i in range(3):
        if smart_notify("connection_check"):
            notifier.notify_connection_lost()
            print(f"  ✓ 第 {i+1} 次連線中斷通知已發送")
        else:
            print(f"  ⏭️  第 {i+1} 次連線中斷跳過（冷卻中）")


# ============================================================
# 主程式
# ============================================================

def main():
    print("=" * 70)
    print("通知功能使用範例")
    print("=" * 70)
    
    # 檢查通知設定
    print("\n📋 當前通知設定:")
    print(f"  Email: {'✅ 已設定' if notifier.email_enabled else '❌ 未設定'}")
    print(f"  Line:  {'✅ 已設定' if notifier.line_enabled else '❌ 未設定'}")
    
    if not notifier.email_enabled and not notifier.line_enabled:
        print("\n⚠️  未設定任何通知通道，通知將不會發送")
        print("請參考 '通知設定說明.md' 完成設定\n")
    
    # 執行範例（註解掉避免發送過多通知）
    # 取消註解以測試
    
    # example_program_lifecycle()
    # example_trading_notifications()
    # example_position_monitoring()
    # example_connection_monitoring()
    # example_daily_summary()
    # example_real_world_usage()
    # example_conditional_notification()
    
    print("\n" + "=" * 70)
    print("範例程式結束")
    print("=" * 70)
    print()
    print("💡 提示：")
    print("  - 取消註解上方的範例函數來測試不同的通知類型")
    print("  - 每個範例都展示了通知功能的具體使用場景")
    print("  - 在實際程式中，請根據需求選擇適合的通知方法")
    print()


if __name__ == "__main__":
    main()
