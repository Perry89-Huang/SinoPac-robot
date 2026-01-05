"""
快速查看真實持倉 - 使用與 SinoPac-new.py 相同的登入方式
"""
import shioaji as sj
from tabulate import tabulate
from typing import List, Dict
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# ========== 設定 ==========
g_bolTestMode = False  # False = 正式環境

# 從環境變數讀取
API_KEY = os.getenv("SINOPAC_API_KEY", "")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
CA_PATH = os.getenv("SINOPAC_CA_PATH", "C:/ekey/551/J120420374/S/Sinopac.pfx")
CA_PASSWORD = os.getenv("SINOPAC_CA_PASSWORD", "J120420374")

def get_positions_summary(api) -> Dict:
    """取得持倉彙總（依商品代碼分組）"""
    try:
        all_positions = api.list_positions(api.futopt_account)
        
        if not all_positions:
            return {}
        
        # 依商品代碼前綴分組
        grouped = {}
        for pos in all_positions:
            prefix = pos.code[:2]  # 取前兩碼，如 'HS', 'DH', 'CD'
            
            if prefix not in grouped:
                try:
                    contract_name = api.Contracts.Futures[pos.code].name
                except:
                    contract_name = "N/A"
                
                grouped[prefix] = {
                    'name': contract_name,
                    'quantity': 0,
                    'pnl': 0.0,
                    'positions': []
                }
            
            grouped[prefix]['quantity'] += int(pos.quantity)
            grouped[prefix]['pnl'] += float(pos.pnl)
            grouped[prefix]['positions'].append(pos)
        
        return grouped
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return {}


def display_quick_summary(grouped: Dict):
    """快速顯示彙總表格"""
    if not grouped:
        print("\n✓ 目前無持倉\n")
        return
    
    print("\n" + "="*100)
    print(f"📊 持倉彙總 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    summary_data = []
    total_qty = 0
    total_pnl = 0.0
    
    for prefix in sorted(grouped.keys()):
        data = grouped[prefix]
        total_qty += data['quantity']
        total_pnl += data['pnl']
        
        summary_data.append([
            prefix,
            data['name'],
            data['quantity'],
            f"{data['pnl']:+,.2f}",
            '✅' if data['pnl'] > 0 else '⚠️' if data['pnl'] < 0 else '➖'
        ])
    
    # 顯示表格
    headers = ['代碼', '商品名稱', '口數', '損益', '狀態']
    table = tabulate(summary_data, headers=headers, tablefmt='grid', stralign='center', numalign='right')
    print(table)
    
    # 顯示總計
    print("\n" + "-"*100)
    print(f"📈 總計：{len(grouped)} 種商品 | {total_qty} 口 | 損益: {total_pnl:+,.2f} 元")
    print("="*100 + "\n")


def display_detailed_positions(grouped: Dict):
    """顯示詳細持倉"""
    if not grouped:
        return
    
    print("\n" + "="*100)
    print(f"📋 持倉明細")
    print("="*100)
    
    all_positions = []
    idx = 1
    
    for prefix in sorted(grouped.keys()):
        data = grouped[prefix]
        for pos in data['positions']:
            direction_str = '買進' if str(pos.direction) == 'Action.Buy' else '賣出'
            
            if pos.price != 0:
                pnl_percent = (pos.pnl / (pos.price * abs(pos.quantity))) * 100
            else:
                pnl_percent = 0
            
            all_positions.append([
                idx,
                pos.code,
                data['name'],
                direction_str,
                int(pos.quantity),
                f"{float(pos.price):.2f}",
                f"{float(pos.last_price):.2f}",
                f"{float(pos.pnl):+,.2f}",
                f"{pnl_percent:+.2f}%"
            ])
            idx += 1
    
    headers = ['序號', '商品代碼', '名稱', '方向', '口數', '成本價', '現價', '損益', '損益%']
    table = tabulate(all_positions, headers=headers, tablefmt='simple')
    print(table)
    print("="*100 + "\n")


def main():
    print("\n" + "="*100)
    print("🔍 快速查看持倉 - 連接正式帳戶")
    print("="*100)
    
    # 驗證 API Key
    if not API_KEY or not SECRET_KEY or API_KEY == "YOUR_API_KEY":
        print("\n❌ 錯誤：尚未設定 API Key")
        print("請設定環境變數：")
        print("  SINOPAC_API_KEY=您的API_KEY")
        print("  SINOPAC_SECRET_KEY=您的SECRET_KEY")
        return
    
    # 登入
    print("\n正在登入正式環境...")
    api = sj.Shioaji(simulation=g_bolTestMode)
    
    try:
        accounts = api.login(
            api_key=API_KEY,
            secret_key=SECRET_KEY,
            contracts_cb=lambda security_type: print(f"  ✓ {security_type} 合約下載完成")
        )
        print(f"\n✅ 登入成功")
        
        # 啟動憑證
        if not g_bolTestMode and os.path.exists(CA_PATH):
            try:
                api.activate_ca(ca_path=CA_PATH, ca_passwd=CA_PASSWORD)
                print("✅ 憑證啟動成功")
            except Exception as e:
                print(f"⚠️  憑證啟動失敗: {e}")
        
        # 取得持倉資料
        print("\n正在取得持倉資料...")
        grouped = get_positions_summary(api)
        
        # 顯示彙總
        display_quick_summary(grouped)
        
        # 詢問是否顯示明細
        if grouped:
            show_detail = input("是否顯示詳細明細? (y/n): ").strip().lower()
            if show_detail == 'y':
                display_detailed_positions(grouped)
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            api.logout()
            print("\n✅ 已登出")
        except:
            pass


if __name__ == "__main__":
    main()
