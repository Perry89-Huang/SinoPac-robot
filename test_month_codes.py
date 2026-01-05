# -*- coding: utf-8 -*-
"""測試月份代碼自動計算功能"""

from datetime import datetime, timedelta

def get_third_wednesday(year, month):
    """計算指定月份的第3個星期三（個股期貨結算日）"""
    # 找到該月第一天
    first_day = datetime(year, month, 1)
    # 找到第一個星期三（weekday: 0=Monday, 2=Wednesday）
    days_until_wednesday = (2 - first_day.weekday()) % 7
    first_wednesday = first_day + timedelta(days=days_until_wednesday)
    # 第3個星期三 = 第1個星期三 + 14天
    third_wednesday = first_wednesday + timedelta(days=14)
    return third_wednesday

def get_future_month_codes():
    """
    根據結算日自動選擇期貨月份代碼
    
    規則：
    - 結算日：每月第3個星期三
    - 平時：選擇本月和下個月
    - 結算日前2天：跳過本月，選擇下個月和下下個月
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # 計算本月第3個星期三（結算日）
    settlement_date = get_third_wednesday(current_year, current_month)
    days_until_settlement = (settlement_date - now).days
    
    # 如果距離結算日不到2天，跳過本月
    if days_until_settlement <= 2:
        # 選擇下個月和下下個月
        near_offset = 1
        far_offset = 2
        status = "⚠️  接近結算日"
    else:
        # 選擇本月和下個月
        near_offset = 0
        far_offset = 1
        status = "✅ 正常交易期"
    
    month_map = {1:'A',2:'B',3:'C',4:'D',5:'E',6:'F',
                 7:'G',8:'H',9:'I',10:'J',11:'K',12:'L'}
    
    # 計算近月
    near_month = ((current_month - 1 + near_offset) % 12) + 1
    near_year = current_year + (current_month + near_offset - 1) // 12
    
    # 計算遠月
    far_month = ((current_month - 1 + far_offset) % 12) + 1
    far_year = current_year + (current_month + far_offset - 1) // 12
    
    near_code = f'F{month_map[near_month]}{str(near_year)[-1]}'
    far_code = f'F{month_map[far_month]}{str(far_year)[-1]}'
    
    print("=" * 60)
    print("📊 個股期貨月份代碼自動計算")
    print("=" * 60)
    print(f"📅 當前日期: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📆 本月結算日: {settlement_date.strftime('%Y-%m-%d')} (星期三)")
    print(f"⏰ 距離結算: {days_until_settlement} 天")
    print(f"🔔 狀態: {status}")
    print("-" * 60)
    print(f"📈 選擇月份:")
    print(f"   近月: {near_code} = {near_year}年{near_month}月 ({month_map[near_month]})")
    print(f"   遠月: {far_code} = {far_year}年{far_month}月 ({month_map[far_month]})")
    print("=" * 60)
    
    return near_code, far_code

if __name__ == "__main__":
    # 測試當前日期
    print("\n🧪 測試1: 當前日期")
    NEAR_MON, FAR_MON = get_future_month_codes()
    
    # 測試結算日前1天的情況
    print("\n\n🧪 測試2: 模擬結算日前1天")
    print("-" * 60)
    test_date = get_third_wednesday(2025, 12) - timedelta(days=1)
    print(f"模擬日期: {test_date.strftime('%Y-%m-%d')}")
    print("預期：應該跳過12月，選擇1月和2月")
    print("-" * 60)
    
    # 測試結算日後的情況
    print("\n\n🧪 測試3: 模擬結算日後3天")
    print("-" * 60)
    test_date = get_third_wednesday(2025, 12) + timedelta(days=3)
    print(f"模擬日期: {test_date.strftime('%Y-%m-%d')}")
    print("預期：應該選擇本月和下個月")
    print("-" * 60)
    
    # 顯示未來幾個月的結算日
    print("\n\n📅 未來6個月結算日表：")
    print("=" * 60)
    now = datetime.now()
    for i in range(6):
        target_month = (now.month + i - 1) % 12 + 1
        target_year = now.year + (now.month + i - 1) // 12
        settlement = get_third_wednesday(target_year, target_month)
        print(f"{target_year}年{target_month:02d}月: {settlement.strftime('%Y-%m-%d')} (星期{settlement.weekday()+1})")
    print("=" * 60)
