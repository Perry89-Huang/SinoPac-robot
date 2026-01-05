"""
模擬持倉管理工具
用於查看、分析和管理模擬環境中的持倉
"""
import shioaji as sj
from tabulate import tabulate
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

# 設定
API_KEY = os.getenv("SINOPAC_API_KEY", "")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
MAX_TOTAL_POSITION = 300

class SimulationPositionManager:
    """模擬持倉管理器"""
    
    def __init__(self):
        self.api = None
        self.positions = []
        
    def login(self):
        """登入模擬環境"""
        print("\n正在登入模擬環境...")
        self.api = sj.Shioaji(simulation=True)
        
        try:
            if API_KEY and SECRET_KEY and API_KEY != "YOUR_API_KEY":
                accounts = self.api.login(
                    api_key=API_KEY,
                    secret_key=SECRET_KEY,
                    contracts_cb=lambda security_type: None
                )
            else:
                accounts = self.api.login("PAPIUSER07", "2317")
            
            print("✅ 登入成功")
            return True
        except Exception as e:
            print(f"❌ 登入失敗: {e}")
            return False
    
    def load_positions(self):
        """載入持倉資料"""
        try:
            all_positions = self.api.list_positions(self.api.futopt_account)
            self.positions = all_positions if all_positions else []
            return True
        except Exception as e:
            print(f"❌ 載入持倉失敗: {e}")
            return False
    
    def display_summary(self):
        """顯示持倉彙總"""
        if not self.positions:
            print("\n✓ 目前無持倉\n")
            return
        
        print("\n" + "="*120)
        print(f"📊 模擬環境持倉彙總 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*120)
        
        # 依商品分組
        grouped = {}
        total_qty = 0
        total_pnl = 0.0
        
        for pos in self.positions:
            prefix = pos.code[:2]
            qty = abs(pos.quantity)
            total_qty += qty
            total_pnl += float(pos.pnl)
            
            if prefix not in grouped:
                try:
                    name = self.api.Contracts.Futures[pos.code].name
                except:
                    name = pos.code
                grouped[prefix] = {
                    'name': name,
                    'quantity': 0,
                    'pnl': 0.0,
                    'positions': []
                }
            
            grouped[prefix]['quantity'] += qty
            grouped[prefix]['pnl'] += float(pos.pnl)
            grouped[prefix]['positions'].append(pos)
        
        # 顯示彙總表格
        summary_data = []
        for prefix in sorted(grouped.keys()):
            data = grouped[prefix]
            summary_data.append([
                prefix,
                data['name'],
                data['quantity'],
                f"{(data['quantity']/MAX_TOTAL_POSITION)*100:.1f}%",
                f"{data['pnl']:+,.2f}",
                '✅' if data['pnl'] > 0 else '⚠️' if data['pnl'] < 0 else '➖'
            ])
        
        headers = ['代碼', '商品名稱', '口數', '佔比', '損益', '狀態']
        table = tabulate(summary_data, headers=headers, tablefmt='grid', stralign='center', numalign='right')
        print(table)
        
        # 顯示總計
        print("\n" + "="*120)
        print(f"📈 總計")
        print(f"   商品種類: {len(grouped)} 種")
        print(f"   總持倉: {total_qty} 口 / {MAX_TOTAL_POSITION} 口")
        print(f"   使用率: {(total_qty/MAX_TOTAL_POSITION)*100:.1f}%")
        print(f"   剩餘可用: {MAX_TOTAL_POSITION - total_qty} 口")
        print(f"   總損益: {total_pnl:+,.2f} 元")
        
        if total_qty >= MAX_TOTAL_POSITION:
            print(f"   ⚠️  已達或超過上限！")
        elif total_qty >= MAX_TOTAL_POSITION * 0.9:
            print(f"   ⚠️  接近上限（90%以上）")
        else:
            print(f"   ✅ 仍有額度")
        
        print("="*120)
    
    def display_details(self):
        """顯示持倉明細"""
        if not self.positions:
            return
        
        print("\n" + "="*120)
        print("📋 持仓明细")
        print("="*120)
        
        detail_data = []
        for idx, pos in enumerate(self.positions, 1):
            try:
                name = self.api.Contracts.Futures[pos.code].name
            except:
                name = pos.code
            
            direction = '买进' if str(pos.direction) == 'Action.Buy' else '卖出'
            
            if pos.price != 0:
                pnl_percent = (pos.pnl / (pos.price * abs(pos.quantity))) * 100
            else:
                pnl_percent = 0
            
            detail_data.append([
                idx,
                pos.code,
                name,
                direction,
                int(pos.quantity),
                f"{float(pos.price):.2f}",
                f"{float(pos.last_price):.2f}",
                f"{float(pos.pnl):+,.2f}",
                f"{pnl_percent:+.2f}%"
            ])
        
        headers = ['#', '代码', '名称', '方向', '口数', '成本价', '现价', '损益', '损益%']
        table = tabulate(detail_data, headers=headers, tablefmt='simple')
        print(table)
        print("="*120)
    
    def export_to_file(self):
        """匯出持倉到檔案"""
        if not self.positions:
            print("\n⚠️  無持倉可匯出")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"positions_simulation_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write(f"模擬環境持倉報表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")
            
            # 彙總
            grouped = {}
            total_qty = 0
            total_pnl = 0.0
            
            for pos in self.positions:
                prefix = pos.code[:2]
                qty = abs(pos.quantity)
                total_qty += qty
                total_pnl += float(pos.pnl)
                
                if prefix not in grouped:
                    try:
                        name = self.api.Contracts.Futures[pos.code].name
                    except:
                        name = pos.code
                    grouped[prefix] = {
                        'name': name,
                        'quantity': 0,
                        'pnl': 0.0
                    }
                
                grouped[prefix]['quantity'] += qty
                grouped[prefix]['pnl'] += float(pos.pnl)
            
            f.write("【彙總表】\n")
            f.write("-"*100 + "\n")
            for prefix in sorted(grouped.keys()):
                data = grouped[prefix]
                f.write(f"{prefix:4s} {data['name']:12s} {data['quantity']:5d} 口 "
                       f"({(data['quantity']/MAX_TOTAL_POSITION)*100:5.1f}%) "
                       f"損益: {data['pnl']:+12,.2f}\n")
            
            f.write("-"*100 + "\n")
            f.write(f"總計: {total_qty} 口 / {MAX_TOTAL_POSITION} 口 ({(total_qty/MAX_TOTAL_POSITION)*100:.1f}%) "
                   f"| 損益: {total_pnl:+,.2f}\n")
            f.write("="*100 + "\n\n")
            
            # 明細
            f.write("【明細表】\n")
            f.write("-"*100 + "\n")
            for idx, pos in enumerate(self.positions, 1):
                try:
                    name = self.api.Contracts.Futures[pos.code].name
                except:
                    name = pos.code
                
                direction = '買' if str(pos.direction) == 'Action.Buy' else '賣'
                f.write(f"{idx:3d}. {pos.code:10s} {name:12s} {direction} "
                       f"{int(pos.quantity):3d}口 成本:{float(pos.price):7.2f} "
                       f"現價:{float(pos.last_price):7.2f} 損益:{float(pos.pnl):+10,.2f}\n")
            
            f.write("="*100 + "\n")
        
        print(f"\n✅ 已匯出到: {filename}")
    
    def get_top_positions(self, n=5):
        """获取持仓最多的商品"""
        if not self.positions:
            return []
        
        grouped = {}
        for pos in self.positions:
            prefix = pos.code[:2]
            if prefix not in grouped:
                try:
                    name = self.api.Contracts.Futures[pos.code].name
                except:
                    name = pos.code
                grouped[prefix] = {'name': name, 'quantity': 0}
            grouped[prefix]['quantity'] += abs(pos.quantity)
        
        sorted_items = sorted(grouped.items(), key=lambda x: x[1]['quantity'], reverse=True)
        return sorted_items[:n]
    
    def reset_all_positions(self):
        """重置（清空）所有持倉"""
        if not self.positions:
            print("\n✓ 目前無持倉，無需重置")
            return True
        
        print("\n" + "="*120)
        print("⚠️  警告：重置所有持倉")
        print("="*120)
        print(f"即將平倉 {len(self.positions)} 筆持倉，總共 {sum(abs(p.quantity) for p in self.positions)} 口")
        print("\n確定要執行嗎？這個操作無法復原！")
        confirm = input("請輸入 'YES' 確認執行重置: ").strip()
        
        if confirm != 'YES':
            print("❌ 已取消重置操作")
            return False
        
        # 詢問使用限價或市價
        print("\n請選擇平倉方式：")
        print("1. 限價單（LMT）- 使用現價，可能無法立即成交")
        print("2. 市價單（MKT）- 保證成交但價格可能不理想")
        price_choice = input("請選擇 (1/2，預設為2): ").strip()
        
        use_market_price = (price_choice != '1')
        
        print(f"\n開始執行平倉（{'市價單' if use_market_price else '限價單'}）...")
        success_count = 0
        fail_count = 0
        
        for idx, pos in enumerate(self.positions, 1):
            try:
                # 取得合約
                contract = self.api.Contracts.Futures[pos.code]
                
                # 判斷平倉方向（與持倉相反）
                if str(pos.direction) == 'Action.Buy':
                    close_action = sj.constant.Action.Sell
                    action_name = '賣出平倉'
                else:
                    close_action = sj.constant.Action.Buy
                    action_name = '買進平倉'
                
                # 建立平倉單
                if use_market_price:
                    # 市價單
                    order = self.api.Order(
                        price=float(pos.last_price),  # 市價單仍需填價格但會忽略
                        quantity=abs(int(pos.quantity)),
                        action=close_action,
                        price_type=sj.constant.StockPriceType.MKT,  # 市價單
                        order_type=sj.constant.OrderType.ROD,  # 當日有效
                        octype=sj.constant.FuturesOCType.Cover,  # 平倉
                        account=self.api.futopt_account
                    )
                else:
                    # 限價單
                    order = self.api.Order(
                        price=float(pos.last_price),  # 使用現價
                        quantity=abs(int(pos.quantity)),
                        action=close_action,
                        price_type=sj.constant.StockPriceType.LMT,  # 限價單
                        order_type=sj.constant.OrderType.ROD,  # 當日有效
                        octype=sj.constant.FuturesOCType.Cover,  # 平倉
                        account=self.api.futopt_account
                    )
                
                # 下單
                trade = self.api.place_order(contract, order)
                
                try:
                    name = self.api.Contracts.Futures[pos.code].name
                except:
                    name = pos.code
                
                print(f"  [{idx}/{len(self.positions)}] ✅ {pos.code} ({name}) "
                      f"{action_name} {abs(int(pos.quantity))} 口")
                success_count += 1
                
            except Exception as e:
                print(f"  [{idx}/{len(self.positions)}] ❌ {pos.code} 平倉失敗: {e}")
                fail_count += 1
        
        print("\n" + "="*120)
        print(f"📊 平倉結果")
        print(f"   成功下單: {success_count} 筆")
        print(f"   失敗: {fail_count} 筆")
        print("="*120)
        
        # 等待成交
        if success_count > 0:
            print("\n⏳ 等待委託單成交（3秒）...")
            import time
            time.sleep(3)
        
        # 重新載入持倉
        print("\n正在重新載入持倉...")
        self.load_positions()
        
        if not self.positions:
            print("✅ 所有持倉已清空！")
            return True
        else:
            remaining_qty = sum(abs(p.quantity) for p in self.positions)
            print(f"⚠️  仍有 {len(self.positions)} 筆持倉未平倉（{remaining_qty} 口）")
            print("\n💡 提示：")
            print("   • 委託單可能尚未成交，請等待後再次執行重置")
            print("   • 或選擇使用市價單來確保成交")
            print("   • 可用選項 2 查看剩餘持倉明細")
            return False
    
    def logout(self):
        print("\n正在重新載入持倉...")
        self.load_positions()
        
        if not self.positions:
            print("✅ 所有持倉已清空！")
            return True
        else:
            print(f"⚠️  仍有 {len(self.positions)} 筆持倉未平倉")
            return False
    
    def logout(self):
        """登出"""
        try:
            self.api.logout()
            print("\n✅ 已登出")
        except:
            pass


def main():
    """主程序"""
    print("\n" + "="*120)
    print("🎮 模拟持仓管理工具")
    print("="*120)
    
    manager = SimulationPositionManager()
    
    if not manager.login():
        return
    
    if not manager.load_positions():
        manager.logout()
        return
    
    # 主選單
    while True:
        print("\n" + "="*120)
        print("📋 功能選單")
        print("="*120)
        print("1. 顯示持倉彙總")
        print("2. 顯示持倉明細")
        print("3. 同時顯示彙總+明細")
        print("4. 匯出持倉報表到檔案")
        print("5. 顯示 TOP 5 持倉商品")
        print("6. 重新載入持倉（重新整理）")
        print("7. ⚠️  重置所有持倉（清空全部）")
        print("0. 離開")
        print("="*120)
        
        choice = input("\n請選擇功能 (0-7): ").strip()
        
        if choice == '1':
            manager.display_summary()
        elif choice == '2':
            manager.display_details()
        elif choice == '3':
            manager.display_summary()
            manager.display_details()
        elif choice == '4':
            manager.export_to_file()
        elif choice == '5':
            top_positions = manager.get_top_positions(5)
            print("\n" + "="*120)
            print("🏆 TOP 5 持倉商品")
            print("="*120)
            for idx, (code, data) in enumerate(top_positions, 1):
                print(f"  {idx}. {code} ({data['name']}): {data['quantity']} 口")
            print("="*120)
        elif choice == '6':
            print("\n正在重新整理持倉資料...")
            manager.load_positions()
            print("✅ 重新整理完成")
        elif choice == '7':
            manager.reset_all_positions()
        elif choice == '0':
            print("\n👋 再見！")
            break
        else:
            print("\n❌ 無效選擇，請重新輸入")
    
    manager.logout()


if __name__ == "__main__":
    main()
