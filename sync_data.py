"""
資料同步程式
從 FinMind API 下載資料並儲存到本地資料庫
"""
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List
from dotenv import load_dotenv
from FinMind.data import DataLoader
from database_manager import init_database

# 設定輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

# 載入環境變數
load_dotenv()


class DataSyncManager:
    """資料同步管理器"""
    
    def __init__(self, db_path: str = 'stock_data.db'):
        """
        初始化同步管理器
        
        Args:
            db_path: 資料庫路徑
        """
        self.db = init_database(db_path)
        
        # 初始化 FinMind
        finmind_token = os.getenv('FINMIND_API_TOKEN')
        if finmind_token:
            self.dl = DataLoader()
            self.dl.login_by_token(api_token=finmind_token)
            self.has_token = True
            print("✅ FinMind API Token 已啟用")
        else:
            self.dl = DataLoader()
            self.has_token = False
            print("⚠️ 未設定 FinMind API Token（使用免費額度）")
        
        # API 請求延遲（秒）
        self.request_delay = 0.5 if self.has_token else 1.0
        
        # 統計資訊
        self.stats = {
            'stocks_processed': 0,
            'dividend_updated': 0,
            'price_updated': 0,
            'errors': 0,
            'api_errors': 0
        }
    
    def sync_stock_list(self) -> bool:
        """
        同步股票清單
        
        Returns:
            True 表示成功，False 表示失敗
        """
        print("\n" + "="*80)
        print("📥 同步股票清單")
        print("="*80)
        
        try:
            stock_info = self.dl.taiwan_stock_info()
            
            # 只保留一般股票（排除 ETF 等）
            stock_info = stock_info[stock_info['type'] == 'twse']
            stock_list = [s for s in stock_info['stock_id'].tolist() 
                         if s.isdigit() and len(s) == 4]
            
            print(f"✅ 取得 {len(stock_list)} 檔台股資訊")
            
            # 儲存到資料庫
            self.db.save_stock_info(stock_info)
            print(f"✅ 股票清單已儲存到資料庫")
            
            self.db.log_api_request('stock_list', '', True)
            return True
            
        except KeyError as e:
            if "'data'" in str(e):
                print("❌ API 請求達到上限")
                self.stats['api_errors'] += 1
            else:
                print(f"❌ 取得股票清單失敗: {e}")
                self.stats['errors'] += 1
            self.db.log_api_request('stock_list', '', False)
            return False
        except Exception as e:
            print(f"❌ 取得股票清單失敗: {e}")
            self.stats['errors'] += 1
            self.db.log_api_request('stock_list', '', False)
            return False
    
    def sync_dividend_data(self, stock_id: str, start_date: str = None) -> bool:
        """
        同步單支股票的股利資料
        
        Args:
            stock_id: 股票代碼
            start_date: 起始日期
        
        Returns:
            True 表示成功，False 表示失敗
        """
        try:
            if start_date is None:
                # 預設查詢最近 3 年
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
            
            dividend_data = self.dl.taiwan_stock_dividend(
                stock_id=stock_id,
                start_date=start_date
            )
            
            if not dividend_data.empty:
                self.db.save_dividend_data(stock_id, dividend_data)
                self.stats['dividend_updated'] += 1
                self.db.log_api_request('dividend', stock_id, True)
                return True
            else:
                # 即使沒有股利資料也記錄為成功（避免重複查詢）
                self.db._log_sync(stock_id, 'dividend', 'success', 'no data')
                self.db.log_api_request('dividend', stock_id, True)
                return True
                
        except KeyError as e:
            if "'data'" in str(e):
                self.stats['api_errors'] += 1
            else:
                self.stats['errors'] += 1
            self.db.log_api_request('dividend', stock_id, False)
            return False
        except Exception as e:
            self.stats['errors'] += 1
            self.db.log_api_request('dividend', stock_id, False)
            return False
    
    def sync_price_data(self, stock_id: str, days: int = 365) -> bool:
        """
        同步單支股票的股價資料
        
        Args:
            stock_id: 股票代碼
            days: 查詢天數
        
        Returns:
            True 表示成功，False 表示失敗
        """
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            price_data = self.dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not price_data.empty:
                self.db.save_daily_price(stock_id, price_data)
                self.stats['price_updated'] += 1
                self.db.log_api_request('price', stock_id, True)
                return True
            else:
                self.db._log_sync(stock_id, 'price', 'success', 'no data')
                self.db.log_api_request('price', stock_id, True)
                return True
                
        except KeyError as e:
            if "'data'" in str(e):
                self.stats['api_errors'] += 1
            else:
                self.stats['errors'] += 1
            self.db.log_api_request('price', stock_id, False)
            return False
        except Exception as e:
            self.stats['errors'] += 1
            self.db.log_api_request('price', stock_id, False)
            return False
    
    def sync_stock_data(self, stock_id: str, force: bool = False) -> bool:
        """
        同步單支股票的所有資料（股利+股價）
        
        Args:
            stock_id: 股票代碼
            force: 是否強制更新（忽略資料新舊）
        
        Returns:
            True 表示成功，False 表示失敗
        """
        success = True
        
        # 檢查是否需要更新
        if not force:
            needs_update = self.db.batch_update_needed(stock_id)
            if not any(needs_update.values()):
                print(f"   ⏩ {stock_id}: 資料已是最新，跳過")
                return True
        
        # 同步股利資料
        if force or (not force and needs_update.get('dividend', True)):
            if not self.sync_dividend_data(stock_id):
                success = False
            time.sleep(self.request_delay)
        
        # 同步股價資料
        if force or (not force and needs_update.get('price', True)):
            if not self.sync_price_data(stock_id):
                success = False
            time.sleep(self.request_delay)
        
        self.stats['stocks_processed'] += 1
        return success
    
    def sync_all_stocks(self, stock_list: List[str] = None, 
                       max_stocks: int = None, force: bool = False):
        """
        同步所有股票資料
        
        Args:
            stock_list: 指定股票清單（可選，預設為資料庫中所有股票）
            max_stocks: 最多同步幾檔（可選，用於測試）
            force: 是否強制更新
        """
        print("\n" + "="*80)
        print("🔄 批次同步股票資料")
        print("="*80)
        
        # 取得股票清單
        if stock_list is None:
            stock_list = self.db.get_all_stock_ids()
        
        if not stock_list:
            print("❌ 沒有股票清單，請先執行 sync_stock_list()")
            return
        
        # 檢查資料庫，篩選出需要下載的股票
        if not force:
            print("🔍 檢查資料庫，篩選需要更新的股票...")
            
            # 取得需要更新股利資料的股票
            dividend_needs_update = set(self.db.get_stocks_need_update('dividend', max_age_days=30))
            # 取得需要更新股價資料的股票
            price_needs_update = set(self.db.get_stocks_need_update('price', max_age_days=7))
            # 合併需要更新的股票
            needs_update = dividend_needs_update | price_needs_update
            
            # 只保留需要更新的股票
            original_count = len(stock_list)
            stock_list = [s for s in stock_list if s in needs_update]
            
            print(f"✅ 原始清單: {original_count} 檔")
            print(f"✅ 需要更新: {len(stock_list)} 檔")
            print(f"   - 需要股利資料: {len(dividend_needs_update)} 檔")
            print(f"   - 需要股價資料: {len(price_needs_update)} 檔")
            print(f"✅ 已跳過: {original_count - len(stock_list)} 檔（資料已是最新）")
            
            if not stock_list:
                print("\n✅ 所有股票資料都已是最新，無需更新！")
                return
        
        # 限制數量
        if max_stocks:
            stock_list = stock_list[:max_stocks]
            print(f"📊 同步前 {max_stocks} 檔股票（測試模式）")
        
        total = len(stock_list)
        print(f"\n📊 準備同步 {total} 檔股票")
        print(f"⏱️  預估時間: {total * self.request_delay * 2 / 60:.1f} 分鐘")
        
        if not force:
            print("💡 模式：智慧更新（只更新過期資料）")
        else:
            print("💡 模式：強制更新（更新所有資料）")
        
        print()
        
        start_time = time.time()
        
        for i, stock_id in enumerate(stock_list, 1):
            # 顯示進度
            if i % 10 == 0 or i == total:
                elapsed = time.time() - start_time
                speed = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / speed if speed > 0 else 0
                
                print(f"📊 進度: {i}/{total} ({i/total*100:.1f}%) | "
                      f"成功: {self.stats['dividend_updated']} 股利 + "
                      f"{self.stats['price_updated']} 股價 | "
                      f"錯誤: {self.stats['errors']} | "
                      f"API限制: {self.stats['api_errors']} | "
                      f"預計剩餘: {eta/60:.1f}分")
            
            # 同步資料
            result = self.sync_stock_data(stock_id, force=force)
            
            # 如果遇到 API 限制，停止同步
            if self.stats['api_errors'] > 5:
                print("\n⚠️ API 請求次數過多，暫停同步")
                print("💡 建議等待幾分鐘後再繼續")
                break
        
        # 顯示統計
        elapsed = time.time() - start_time
        print("\n" + "="*80)
        print("📊 同步完成統計")
        print("="*80)
        print(f"處理股票數: {self.stats['stocks_processed']}")
        print(f"股利更新: {self.stats['dividend_updated']}")
        print(f"股價更新: {self.stats['price_updated']}")
        print(f"錯誤次數: {self.stats['errors']}")
        print(f"API 限制: {self.stats['api_errors']}")
        print(f"總耗時: {elapsed/60:.1f} 分鐘")
        
        # 顯示資料庫統計
        db_stats = self.db.get_database_stats()
        print(f"\n資料庫統計:")
        print(f"  股票數: {db_stats['total_stocks']}")
        print(f"  股利記錄: {db_stats['dividend_records']}")
        print(f"  股價記錄: {db_stats['price_records']}")
        print(f"  資料庫大小: {db_stats['db_size_mb']:.2f} MB")
    
    def sync_high_dividend_candidates(self):
        """同步高殖利率候選股票（優先股票清單）"""
        print("\n" + "="*80)
        print("🎯 同步高殖利率候選股票")
        print("="*80)
        
        # 高殖利率候選清單
        candidate_stocks = [
            # 之前找到的高殖利率股票
            '8422', '2062', '6754', '9943', '6670', '2707', '6671', '3557',
            # 金融股
            '2880', '2881', '2882', '2883', '2884', '2885', '2886', '2887', 
            '2888', '2889', '2890', '2891', '2892',
            # 電信股
            '2412', '3045',
            # 傳產股
            '1101', '1102', '1301', '1303', '2002', '2105', '2201',
            # 其他高息股
            '2912', '2609', '2615'
        ]
        
        print(f"📊 候選股票總數: {len(candidate_stocks)}")
        
        self.sync_all_stocks(stock_list=candidate_stocks, force=False)
    
    def close(self):
        """關閉資料庫連接"""
        self.db.close()


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FinMind 資料同步工具')
    parser.add_argument('--mode', choices=['list', 'candidates', 'all', 'test'], 
                       default='candidates',
                       help='同步模式：list=更新股票清單, candidates=高息候選股, all=全部股票, test=測試(前10檔)')
    parser.add_argument('--force', action='store_true', 
                       help='強制更新所有資料（忽略資料新舊）')
    parser.add_argument('--stock', type=str, 
                       help='指定單一股票代碼')
    
    args = parser.parse_args()
    
    print("="*80)
    print("FinMind 資料同步工具")
    print("="*80)
    
    sync_manager = DataSyncManager()
    
    try:
        if args.stock:
            # 同步單一股票
            print(f"\n🎯 同步單一股票: {args.stock}")
            sync_manager.sync_stock_data(args.stock, force=args.force)
        
        elif args.mode == 'list':
            # 只更新股票清單
            sync_manager.sync_stock_list()
        
        elif args.mode == 'candidates':
            # 同步高殖利率候選股
            sync_manager.sync_high_dividend_candidates()
        
        elif args.mode == 'all':
            # 同步所有股票
            if args.force:
                print("\n⚠️ 警告：強制模式會重新下載所有資料，需要數小時且可能達到 API 限制")
                confirm = input("確定要繼續嗎？(yes/no): ")
                if confirm.lower() != 'yes':
                    print("❌ 已取消")
                    return
            else:
                print("\n💡 智慧模式：只會下載尚未下載或過期的股票資料")
            
            # 先更新股票清單
            if sync_manager.sync_stock_list():
                sync_manager.sync_all_stocks(force=args.force)
        
        elif args.mode == 'test':
            # 測試模式：只同步前 10 檔
            print("\n🧪 測試模式：同步前 10 檔股票")
            if sync_manager.sync_stock_list():
                stock_list = sync_manager.db.get_all_stock_ids()[:10]
                sync_manager.sync_all_stocks(stock_list=stock_list, force=args.force)
        
        print("\n✅ 同步完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 使用者中斷同步")
    
    finally:
        sync_manager.close()


if __name__ == "__main__":
    main()
