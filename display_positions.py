"""
顯示模擬庫存的漂亮表格
用於查看當前持倉狀況
"""
import shioaji as sj
from tabulate import tabulate
from typing import List, Dict
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class PositionDisplay:
    """庫存顯示類別"""
    
    def __init__(self, api):
        self.api = api
        
    def get_positions_data(self) -> List[Dict]:
        """取得持倉資料並整理成表格格式"""
        positions = []
        
        try:
            # 取得所有持倉
            all_positions = self.api.list_positions(self.api.futopt_account)
            
            if not all_positions:
                print("\n目前無持倉")
                return []
            
            # 整理每筆持倉資料
            for idx, pos in enumerate(all_positions, 1):
                # 取得商品名稱
                try:
                    contract_name = self.api.Contracts.Futures[pos.code].name
                except:
                    contract_name = "N/A"
                
                # 計算損益百分比
                if pos.price != 0:
                    pnl_percent = (pos.pnl / (pos.price * abs(pos.quantity))) * 100
                else:
                    pnl_percent = 0
                
                position_data = {
                    '序號': idx,
                    '商品代碼': pos.code,
                    '商品名稱': contract_name,
                    '方向': '買進' if str(pos.direction) == 'Action.Buy' else '賣出',
                    '數量': int(pos.quantity),
                    '成本價': f"{float(pos.price):.2f}",
                    '現價': f"{float(pos.last_price):.2f}",
                    '損益': f"{float(pos.pnl):+.2f}",
                    '損益%': f"{pnl_percent:+.2f}%"
                }
                positions.append(position_data)
                
        except Exception as e:
            print(f"取得持倉資料時發生錯誤: {e}")
            return []
        
        return positions
    
    def display_positions(self):
        """以漂亮的表格顯示持倉"""
        print("\n" + "="*100)
        print(f"📊 持倉一覽表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        positions = self.get_positions_data()
        
        if not positions:
            return
        
        # 使用 tabulate 生成表格
        headers = positions[0].keys()
        rows = [pos.values() for pos in positions]
        
        table = tabulate(rows, headers=headers, tablefmt='grid', stralign='center', numalign='center')
        print(table)
        
        # 計算總損益
        total_pnl = sum(float(pos['損益']) for pos in positions)
        total_quantity = sum(pos['數量'] for pos in positions)
        
        print("\n" + "="*100)
        print(f"📈 統計資訊")
        print(f"   總持倉口數: {total_quantity} 口")
        print(f"   總損益: {total_pnl:+,.2f} 元")
        
        if total_pnl > 0:
            print(f"   狀態: ✅ 獲利中")
        elif total_pnl < 0:
            print(f"   狀態: ⚠️  虧損中")
        else:
            print(f"   狀態: ➖ 持平")
        
        print("="*100 + "\n")
    
    def display_margin_info(self):
        """顯示保證金資訊"""
        try:
            margin_info = self.api.margin(self.api.futopt_account)
            
            print("\n" + "="*100)
            print("💰 保證金資訊")
            print("="*100)
            
            info_data = [
                ['可用保證金', f"{getattr(margin_info, 'available_margin', 0):,.2f}", '元'],
                ['權益總值', f"{getattr(margin_info, 'equity', 0):,.2f}", '元'],
                ['未平倉損益', f"{getattr(margin_info, 'open_position_profit_loss', 0):+,.2f}", '元'],
            ]
            
            table = tabulate(info_data, headers=['項目', '金額', '單位'], tablefmt='grid')
            print(table)
            print("="*100 + "\n")
            
        except Exception as e:
            print(f"取得保證金資訊時發生錯誤: {e}\n")
    
    def display_by_product(self):
        """依商品分組顯示"""
        print("\n" + "="*100)
        print(f"📋 依商品分組顯示 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        positions = self.get_positions_data()
        
        if not positions:
            return
        
        # 依商品代碼前兩碼分組
        grouped = {}
        for pos in positions:
            code_prefix = pos['商品代碼'][:2]
            if code_prefix not in grouped:
                grouped[code_prefix] = []
            grouped[code_prefix].append(pos)
        
        # 顯示各組
        for prefix, group in grouped.items():
            print(f"\n📌 {prefix} 系列")
            print("-" * 100)
            
            headers = group[0].keys()
            rows = [pos.values() for pos in group]
            
            table = tabulate(rows, headers=headers, tablefmt='simple', stralign='center', numalign='center')
            print(table)
            
            # 小計
            group_pnl = sum(float(pos['損益']) for pos in group)
            print(f"\n   小計損益: {group_pnl:+,.2f} 元")
        
        print("\n" + "="*100 + "\n")


def main():
    """主程式"""
    print("\n" + "="*100)
    print("🚀 模擬庫存顯示程式")
    print("="*100)
    
    # 登入 Shioaji（模擬模式）
    print("\n正在登入模擬帳戶...")
    api = sj.Shioaji(simulation=True)
    
    try:
        # 從環境變數讀取帳密
        api_key = os.getenv('SHIOAJI_API_KEY', 'PAPIUSER07')
        api_secret = os.getenv('SHIOAJI_SECRET_KEY', '2317')
        
        accounts = api.login(api_key, api_secret)
        print("✅ 登入成功！")
        
        # 建立顯示物件
        display = PositionDisplay(api)
        
        # 顯示選單
        while True:
            print("\n" + "="*100)
            print("📋 選單")
            print("="*100)
            print("1. 顯示持倉明細")
            print("2. 顯示保證金資訊")
            print("3. 依商品分組顯示")
            print("4. 全部顯示")
            print("0. 離開")
            print("="*100)
            
            choice = input("\n請選擇功能 (0-4): ").strip()
            
            if choice == '1':
                display.display_positions()
            elif choice == '2':
                display.display_margin_info()
            elif choice == '3':
                display.display_by_product()
            elif choice == '4':
                display.display_positions()
                display.display_margin_info()
                display.display_by_product()
            elif choice == '0':
                print("\n👋 再見！")
                break
            else:
                print("\n❌ 無效的選擇，請重新輸入")
    
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
    
    finally:
        # 登出
        try:
            api.logout()
            print("\n✅ 已登出")
        except:
            pass


if __name__ == "__main__":
    main()
