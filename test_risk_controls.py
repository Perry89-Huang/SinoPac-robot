# -*- coding: utf-8 -*-
"""測試風險控制功能"""

import sys

print("=" * 70)
print("🧪 交易系統風險控制測試")
print("=" * 70)

# 測試1: 檢查持倉限制參數
print("\n📊 測試1: 持倉限制參數")
print("-" * 70)

try:
    # 檢查 new.py
    with open('SinoPac-new.py', 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    if 'MAX_POSITION_PER_CONTRACT' in new_content:
        print("✓ SinoPac-new.py 已設定 MAX_POSITION_PER_CONTRACT")
    else:
        print("✗ SinoPac-new.py 未設定 MAX_POSITION_PER_CONTRACT")
    
    if 'MAX_TOTAL_POSITION' in new_content:
        print("✓ SinoPac-new.py 已設定 MAX_TOTAL_POSITION")
    else:
        print("✗ SinoPac-new.py 未設定 MAX_TOTAL_POSITION")
    
    if 'MAX_SINGLE_ORDER' in new_content:
        print("✓ SinoPac-new.py 已設定 MAX_SINGLE_ORDER")
    else:
        print("✗ SinoPac-new.py 未設定 MAX_SINGLE_ORDER")
    
    # 檢查 close.py
    with open('SinoPac-close.py', 'r', encoding='utf-8') as f:
        close_content = f.read()
    
    if 'MAX_CLOSE_QUANTITY' in close_content:
        print("✓ SinoPac-close.py 已設定 MAX_CLOSE_QUANTITY")
    else:
        print("✗ SinoPac-close.py 未設定 MAX_CLOSE_QUANTITY")
        
except Exception as e:
    print(f"✗ 測試失敗: {e}")

# 測試2: 檢查斷線重連機制
print("\n🔌 測試2: 斷線重連機制")
print("-" * 70)

try:
    if 'def check_connection()' in new_content:
        print("✓ SinoPac-new.py 已實作 check_connection()")
    else:
        print("✗ SinoPac-new.py 未實作 check_connection()")
    
    if 'def reconnect()' in new_content:
        print("✓ SinoPac-new.py 已實作 reconnect()")
    else:
        print("✗ SinoPac-new.py 未實作 reconnect()")
    
    if 'connection_check_interval' in new_content:
        print("✓ SinoPac-new.py 已設定定期檢查")
    else:
        print("✗ SinoPac-new.py 未設定定期檢查")
    
    if 'def check_connection()' in close_content:
        print("✓ SinoPac-close.py 已實作 check_connection()")
    else:
        print("✗ SinoPac-close.py 未實作 check_connection()")
    
    if 'def reconnect()' in close_content:
        print("✓ SinoPac-close.py 已實作 reconnect()")
    else:
        print("✗ SinoPac-close.py 未實作 reconnect()")
        
except Exception as e:
    print(f"✗ 測試失敗: {e}")

# 測試3: 檢查日誌系統
print("\n📝 測試3: 增強型日誌系統")
print("-" * 70)

try:
    log_patterns_new = [
        'logs/trading_',
        'logs/errors.log',
        'logs/orders_',
        'rotation="00:00"',
        'retention="30 days"',
        'retention="90 days"',
    ]
    
    for pattern in log_patterns_new:
        if pattern in new_content:
            print(f"✓ SinoPac-new.py 包含 {pattern}")
        else:
            print(f"✗ SinoPac-new.py 缺少 {pattern}")
    
    log_patterns_close = [
        'logs/closing_',
        'logs/errors.log',
        'logs/closings_',
    ]
    
    for pattern in log_patterns_close:
        if pattern in close_content:
            print(f"✓ SinoPac-close.py 包含 {pattern}")
        else:
            print(f"✗ SinoPac-close.py 缺少 {pattern}")
            
except Exception as e:
    print(f"✗ 測試失敗: {e}")

# 測試4: 檢查logs目錄
print("\n📁 測試4: 日誌目錄結構")
print("-" * 70)

import os

if os.path.exists('logs'):
    print("✓ logs 目錄已存在")
    log_files = os.listdir('logs')
    if log_files:
        print(f"  發現 {len(log_files)} 個日誌檔案:")
        for f in log_files[:5]:  # 只顯示前5個
            print(f"    - {f}")
        if len(log_files) > 5:
            print(f"    ... 還有 {len(log_files)-5} 個檔案")
    else:
        print("  ⚠️  目錄為空（正常，尚未執行程式）")
else:
    print("⚠️  logs 目錄不存在（將在程式啟動時自動創建）")

if os.path.exists('PerryLogs'):
    print("✓ PerryLogs 目錄已存在（兼容舊版）")
else:
    print("⚠️  PerryLogs 目錄不存在（將在程式啟動時自動創建）")

# 測試5: 功能統計
print("\n📊 測試5: 功能實作統計")
print("-" * 70)

features = {
    "持倉限制 (new)": all([
        'MAX_POSITION_PER_CONTRACT' in new_content,
        'MAX_TOTAL_POSITION' in new_content,
        'MAX_SINGLE_ORDER' in new_content,
    ]),
    "持倉限制 (close)": 'MAX_CLOSE_QUANTITY' in close_content,
    "斷線重連 (new)": all([
        'def check_connection()' in new_content,
        'def reconnect()' in new_content,
    ]),
    "斷線重連 (close)": all([
        'def check_connection()' in close_content,
        'def reconnect()' in close_content,
    ]),
    "增強日誌 (new)": all([
        'logs/trading_' in new_content,
        'logs/errors.log' in new_content,
        'logs/orders_' in new_content,
    ]),
    "增強日誌 (close)": all([
        'logs/closing_' in close_content,
        'logs/errors.log' in close_content,
        'logs/closings_' in close_content,
    ]),
}

total = len(features)
passed = sum(features.values())

print(f"\n功能實作完成度: {passed}/{total} ({passed/total*100:.1f}%)\n")

for feature, status in features.items():
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {feature}")

# 總結
print("\n" + "=" * 70)
print("📋 測試總結")
print("=" * 70)

if passed == total:
    print("🎉 所有功能測試通過！")
    print("\n建議下一步：")
    print("  1. 執行程式確認日誌系統正常運作")
    print("  2. 測試持倉限制是否生效（設定小數值測試）")
    print("  3. 模擬斷線情況測試重連機制")
    print("  4. 檢查日誌檔案是否正確產生和輪換")
else:
    print(f"⚠️  部分功能未通過測試 ({total-passed}/{total})")
    print("\n未通過的功能:")
    for feature, status in features.items():
        if not status:
            print(f"  ❌ {feature}")

print("\n" + "=" * 70)
