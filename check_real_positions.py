"""
查看真實持倉的漂亮表格
連接實際帳戶，顯示目前所有持倉
"""
import shioaji as sj
from tabulate import tabulate
from typing import List, Dict
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def get_positions_table(api) -> List[Dict]:
    """取得持倉資料並整理成表格格式"""
    positions = []
    
    try:
        # 取得所有持倉
        all_positions = api.list_positions(api.futopt_account)
        
        if not all_positions:
            print("\n✓ 目前無持倉")
            return []
        
        # 整理每筆持倉資料
        for idx, pos in enumerate(all_positions, 1):
            # 取得商品名稱
            try:
                contract_name = api.Contracts.Futures[pos.code].name
            except:
                contract_name = "N/A"
            
            # 計算損益百分比
            if pos.price != 0:
                pnl_percent = (pos.pnl / (pos.price * abs(pos.quantity))) * 100
            else:
                pnl_percent = 0
            
            # 判斷方向
            direction_str = '買進' if str(pos.direction) == 'Action.Buy' else '賣出'
            
            position_data = {
                '序號': idx,
                '商品代碼': pos.code,
                '商品名稱': contract_name,
                '方向': direction_str,
                '數量': int(pos.quantity),
                '成本價': f"{float(pos.price):.2f}",
                '現價': f"{float(pos.last_price):.2f}",
                '損益': f"{float(pos.pnl):+,.2f}",
                '損益%': f"{pnl_percent:+.2f}%"
            }
            positions.append(position_data)
            
    except Exception as e:
        print(f"❌ 取得持倉資料時發生錯誤: {e}")
        return []
    
    return positions


def display_positions_by_prefix(positions: List[Dict]):
    """依商品代碼前綴分組顯示（如 HS, DH 等）"""
    if not positions:
        return
    
    print("\n" + "="*120)
    print(f"📋 依商品分組統計 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    
    # 依商品代碼前兩碼分組
    grouped = {}
    for pos in positions:
        code_prefix = pos['商品代碼'][:2]  # 取前兩碼，如 'HS', 'DH', 'CD'
        if code_prefix not in grouped:
            grouped[code_prefix] = []
        grouped[code_prefix].append(pos)
    
    # 準備彙總表格
    summary_data = []
    total_qty = 0
    total_pnl = 0.0
    
    for prefix in sorted(grouped.keys()):
        group = grouped[prefix]
        group_qty = sum(p['數量'] for p in group)
        group_pnl = sum(float(p['損益'].replace('+', '').replace(',', '')) for p in group)
        
        total_qty += group_qty
        total_pnl += group_pnl
        
        # 取第一筆的商品名稱
        sample_name = group[0]['商品名稱']
        
        summary_data.append({
            '商品代碼': prefix,
            '商品名稱': sample_name,
            '持倉口數': group_qty,
            '損益': f"{group_pnl:+,.2f}",
            '狀態': '✅' if group_pnl > 0 else '⚠️' if group_pnl < 0 else '➖'
        })
    
    # 顯示彙總表格
    headers = summary_data[0].keys()
    rows = [item.values() for item in summary_data]
    table = tabulate(rows, headers=headers, tablefmt='grid', stralign='center', numalign='center')
    print(table)
    
    # 顯示總計
    print("\n" + "="*120)
    print(f"📊 總計")
    print(f"   商品種類: {len(grouped)} 種")
    print(f"   總持倉口數: {total_qty} 口")
    print(f"   總損益: {total_pnl:+,.2f} 元")
    
    if total_pnl > 0:
        print(f"   整體狀態: ✅ 獲利中")
    elif total_pnl < 0:
        print(f"   整體狀態: ⚠️  虧損中")
    else:
        print(f"   整體狀態: ➖ 持平")
    
    print("="*120)


def display_positions_detail(positions: List[Dict]):
    """顯示持倉明細表格"""
    if not positions:
        return
    
    print("\n" + "="*120)
    print(f"📊 持倉明細表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    
    # 使用 tabulate 生成漂亮的表格
    headers = positions[0].keys()
    rows = [pos.values() for pos in positions]
    
    table = tabulate(rows, headers=headers, tablefmt='grid', stralign='center', numalign='center')
    print(table)
    
    # 計算總損益
    total_pnl = sum(float(pos['損益'].replace('+', '').replace(',', '')) for pos in positions)
    total_quantity = sum(pos['數量'] for pos in positions)
    
    print("\n" + "="*120)
    print(f"📈 統計資訊")
    print(f"   總持倉口數: {total_quantity} 口")
    print(f"   總損益: {total_pnl:+,.2f} 元")
    
    if total_pnl > 0:
        print(f"   狀態: ✅ 獲利中")
    elif total_pnl < 0:
        print(f"   狀態: ⚠️  虧損中")
    else:
        print(f"   狀態: ➖ 持平")
    
    print("="*120)


def display_margin_info(api):
    """顯示保證金資訊"""
    try:
        margin_info = api.margin(api.futopt_account)
        
        print("\n" + "="*120)
        print("💰 保證金資訊")
        print("="*120)
        
        info_data = [
            ['可用保證金', f"{getattr(margin_info, 'available_margin', 0):,.2f}", '元'],
            ['權益總值', f"{getattr(margin_info, 'equity', 0):,.2f}", '元'],
            ['未平倉損益', f"{getattr(margin_info, 'open_position_profit_loss', 0):+,.2f}", '元'],
            ['佔用保證金', f"{getattr(margin_info, 'margin_call', 0):,.2f}", '元'],
        ]
        
        table = tabulate(info_data, headers=['項目', '金額', '單位'], tablefmt='grid', stralign='left', numalign='right')
        print(table)
        print("="*120)
        
    except Exception as e:
        print(f"\n❌ 取得保證金資訊時發生錯誤: {e}")


def main():
    """主程式"""
    print("\n" + "="*120)
    print("🔍 真實持倉查詢工具")
    print("="*120)
    
    # 讀取環境變數
    API_KEY = os.getenv("SINOPAC_API_KEY", "")
    SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
    
    # 詢問使用模擬還是正式環境
    print("\n請選擇環境：")
    print("1. 模擬環境 (simulation=True)")
    print("2. 正式環境 (simulation=False)")
    
    choice = input("\n請選擇 (1/2): ").strip()
    
    if choice == '1':
        simulation = True
        print("\n✓ 使用模擬環境")
    elif choice == '2':
        simulation = False
        print("\n✓ 使用正式環境")
    else:
        print("\n❌ 無效選擇，預設使用模擬環境")
        simulation = True
    
    # 登入
    print("\n正在登入...")
    api = sj.Shioaji(simulation=simulation)
    
    try:
        if API_KEY and SECRET_KEY and API_KEY != "YOUR_API_KEY":
            # 使用 API Key 登入
            accounts = api.login(
                api_key=API_KEY,
                secret_key=SECRET_KEY,
                contracts_cb=lambda security_type: print(f"  {security_type} 合約下載完成")
            )
        else:
            # 使用測試帳號（僅模擬環境）
            if simulation:
                accounts = api.login("PAPIUSER07", "2317")
            else:
                print("\n❌ 正式環境需要設定 API Key 和 Secret Key")
                print("請在 .env 檔案或環境變數中設定：")
                print("  SINOPAC_API_KEY=您的API_KEY")
                print("  SINOPAC_SECRET_KEY=您的SECRET_KEY")
                return
        
        print(f"\n✅ 登入成功！")
        print(f"帳戶數量: {len(accounts)}")
        
        # 取得持倉資料
        positions = get_positions_table(api)
        
        if positions:
            # 顯示各種報表
            display_positions_detail(positions)  # 明細表
            display_positions_by_prefix(positions)  # 分組統計
            display_margin_info(api)  # 保證金
        else:
            print("\n✓ 目前無持倉")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 登出
        try:
            api.logout()
            print("\n✅ 已登出")
        except:
            pass


if __name__ == "__main__":
    main()
