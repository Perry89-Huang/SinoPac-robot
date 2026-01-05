# -*- coding: utf-8 -*-
"""
交易系統通知模組
支援 Email 和 Telegram Bot 通知

注意：Line Notify 已於 2025年3月31日終止服務
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class NotificationManager:
    """通知管理器 - 支援 Email 和 Telegram Bot"""
    
    def __init__(self):
        """初始化通知管理器"""
        # Email 設定
        self.email_enabled = False
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_to = os.getenv("EMAIL_TO", "")
        
        # Telegram Bot 設定
        self.telegram_enabled = False
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # 檢查並啟用通知
        self._check_config()
    
    def _check_config(self):
        """檢查並啟用可用的通知方式"""
        # 檢查 Email 設定
        if self.smtp_user and self.smtp_password and self.email_to:
            self.email_enabled = True
            print("✓ Email 通知已啟用")
            logger.info("Email 通知已啟用")
        else:
            print("⚠️  Email 通知未設定")
        
        # 檢查 Telegram Bot 設定
        if self.telegram_token and self.telegram_chat_id:
            self.telegram_enabled = True
            print("✓ Telegram 通知已啟用")
            logger.info("Telegram 通知已啟用")
        else:
            print("⚠️  Telegram 通知未設定")
        
        if not self.email_enabled and not self.telegram_enabled:
            print("💡 提示：設定環境變數以啟用通知功能")
            print("   - Email: SMTP_USER, SMTP_PASSWORD, EMAIL_TO")
            print("   - Telegram: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
    
    def send_email(self, subject: str, message: str) -> bool:
        """
        發送 Email 通知
        
        Args:
            subject: 郵件主旨
            message: 郵件內容
            
        Returns:
            bool: 是否發送成功
        """
        if not self.email_enabled:
            return False
        
        try:
            # 建立郵件
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.email_to
            msg['Subject'] = f"[交易系統] {subject}"
            
            # 加入時間戳記
            body = f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{message}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 發送郵件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email 通知已發送: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Email 發送失敗: {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        """
        發送 Telegram 通知
        
        Args:
            message: 訊息內容
            
        Returns:
            bool: 是否發送成功
        """
        if not self.telegram_enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # 加入時間戳記
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_message = f"🕐 {timestamp}\n\n{message}"
            
            data = {
                "chat_id": self.telegram_chat_id,
                "text": full_message,
                "parse_mode": "HTML"  # 支援 HTML 格式
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram 通知已發送")
                return True
            else:
                logger.error(f"Telegram 發送失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram 發送失敗: {e}")
            return False
    
    def notify(self, subject: str, message: str, level: str = "INFO"):
        """
        發送通知（Email + Telegram）
        
        Args:
            subject: 通知主旨
            message: 通知內容
            level: 通知等級 (INFO/WARNING/ERROR/CRITICAL)
        """
        # 根據等級添加圖示
        level_icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        icon = level_icons.get(level, "📢")
        
        # Email 通知（詳細）
        email_subject = f"[{level}] {subject}"
        self.send_email(email_subject, message)
        
        # Telegram 通知（簡短）
        telegram_message = f"{icon} <b>[{level}] {subject}</b>\n\n{message}"
        self.send_telegram(telegram_message)
    
    # ========== 快捷方法 ==========
    
    def notify_order_success(self, contract_code: str, action: str, price: float, quantity: int):
        """通知：下單成功"""
        subject = "下單成功"
        message = (
            f"✅ 下單成功\n\n"
            f"合約代碼：{contract_code}\n"
            f"動作：{action}\n"
            f"價格：{price}\n"
            f"數量：{quantity} 口"
        )
        self.notify(subject, message, "INFO")
    
    def notify_order_failed(self, contract_code: str, action: str, error: str):
        """通知：下單失敗"""
        subject = "下單失敗"
        message = (
            f"❌ 下單失敗\n\n"
            f"合約代碼：{contract_code}\n"
            f"動作：{action}\n"
            f"錯誤訊息：{error}"
        )
        self.notify(subject, message, "ERROR")
    
    def notify_position_alert(self, message: str):
        """通知：持倉異常"""
        subject = "持倉異常警告"
        full_message = f"⚠️ 持倉異常\n\n{message}"
        self.notify(subject, full_message, "WARNING")
    
    def notify_program_start(self, program_name: str):
        """通知：程式啟動"""
        subject = "程式啟動"
        message = f"🚀 {program_name} 已啟動運行"
        self.notify(subject, message, "INFO")
    
    def notify_program_stop(self, program_name: str, reason: str = "正常停止"):
        """通知：程式停止"""
        subject = "程式停止"
        message = f"🛑 {program_name} 已停止\n\n原因：{reason}"
        level = "WARNING" if "異常" in reason or "錯誤" in reason else "INFO"
        self.notify(subject, message, level)
    
    def notify_connection_lost(self):
        """通知：連線中斷"""
        subject = "連線中斷"
        message = "⚠️ API 連線中斷，正在嘗試重新連線..."
        self.notify(subject, message, "WARNING")
    
    def notify_reconnect_success(self):
        """通知：重新連線成功"""
        subject = "重新連線成功"
        message = "✅ API 重新連線成功"
        self.notify(subject, message, "INFO")
    
    def notify_reconnect_failed(self):
        """通知：重新連線失敗"""
        subject = "重新連線失敗"
        message = "🚨 無法重新連線，程式將停止運行"
        self.notify(subject, message, "CRITICAL")
    
    def notify_position_limit_reached(self, limit_type: str, current: int, limit: int):
        """通知：達到持倉上限"""
        subject = "持倉上限警告"
        message = (
            f"⚠️ 已達{limit_type}持倉上限\n\n"
            f"當前持倉：{current} 口\n"
            f"上限設定：{limit} 口"
        )
        self.notify(subject, message, "WARNING")
    
    def notify_combo_order_failed(self, near_code: str, far_code: str):
        """通知：組合單失敗"""
        subject = "組合單失敗"
        message = (
            f"⚠️ 組合單建倉失敗\n\n"
            f"近月合約：{near_code}\n"
            f"遠月合約：{far_code}\n\n"
            f"請檢查持倉狀況"
        )
        self.notify(subject, message, "WARNING")
    
    def notify_daily_summary(self, summary: dict):
        """通知：每日總結"""
        subject = "每日交易總結"
        message = (
            f"📊 每日交易總結\n\n"
            f"建倉次數：{summary.get('open_count', 0)}\n"
            f"平倉次數：{summary.get('close_count', 0)}\n"
            f"當日損益：{summary.get('pnl', 0):.2f}\n"
            f"持倉數量：{summary.get('position_count', 0)} 口"
        )
        self.notify(subject, message, "INFO")


# 全域通知管理器實例
notifier = NotificationManager()


if __name__ == "__main__":
    """測試通知功能"""
    print("\n" + "=" * 70)
    print("🧪 通知系統測試")
    print("=" * 70)
    
    # 測試連線狀態
    print(f"\nEmail 狀態: {'✅ 已啟用' if notifier.email_enabled else '❌ 未啟用'}")
    print(f"Telegram 狀態: {'✅ 已啟用' if notifier.telegram_enabled else '❌ 未啟用'}")
    
    if notifier.email_enabled or notifier.telegram_enabled:
        print("\n發送測試通知...")
        
        # 測試通知
        notifier.notify(
            subject="系統測試",
            message="這是一則測試通知，如果您收到此訊息，表示通知功能正常運作。",
            level="INFO"
        )
        
        print("✓ 測試通知已發送")
    else:
        print("\n⚠️  無可用的通知方式")
        print("\n如要啟用通知，請設定以下環境變數：")
        print("\n【Email 通知】")
        print("  SMTP_USER=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_app_password")
        print("  EMAIL_TO=recipient@example.com")
        print("\n【Telegram 通知】")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id")
        print("\n設定方法：")
        print("  1. 在 .env 檔案中添加上述變數")
        print("  2. 或在系統環境變數中設定")
    
    print("\n" + "=" * 70)
