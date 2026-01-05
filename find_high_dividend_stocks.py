"""
尋找殖利率大於 5% 的股票，並計算 KD 指標

注意：Shioaji API 不提供殖利率資料，此腳本示範兩種方法：
1. 整合第三方資料源（如 FinMind、TEJ 等）
2. 手動輸入股票清單進行篩選

建議使用 FinMind API 取得殖利率資料

資料庫模式：
- 優先從本地資料庫讀取資料（快速，不消耗 API 配額）
- 資料不存在或過期時才呼叫 API
- 使用 sync_data.py 預先下載資料到資料庫
"""
import shioaji as sj
import os
import sys
import datetime
import pandas as pd
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from database_manager import init_database

# 設定輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

# 載入 .env 檔案
load_dotenv()

def login_shioaji():
    """登入 Shioaji"""
    api = sj.Shioaji(simulation=False)
    
    try:
        api.login(
            api_key=os.getenv('SINOPAC_API_KEY'),
            secret_key=os.getenv('SINOPAC_SECRET_KEY')
        )
        print("✅ Shioaji 登入成功")
        return api
    except Exception as e:
        print(f"❌ 登入失敗: {e}")
        return None

def get_stock_price_from_shioaji(api, stock_code: str) -> float:
    """從 Shioaji 取得股票目前價格"""
    try:
        contract = api.Contracts.Stocks[stock_code]
        snapshot = api.snapshots([contract])
        if snapshot and len(snapshot) > 0:
            return snapshot[0].close
    except Exception as e:
        print(f"從 Shioaji 取得 {stock_code} 價格失敗: {e}")
    return None

def get_stock_price_from_finmind(dl, stock_code: str, db=None) -> float:
    """從 FinMind 取得股票最新收盤價（優先使用資料庫）"""
    try:
        # 優先從資料庫讀取
        if db:
            latest_price = db.get_latest_price(stock_code)
            if latest_price:
                # 檢查資料是否夠新（1天內）
                if db.is_price_data_fresh(stock_code, max_age_days=1):
                    return latest_price
        
        # 資料庫沒有或過期，從 API 取得
        import datetime
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        price_data = dl.taiwan_stock_daily(
            stock_id=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        
        if not price_data.empty:
            latest_price = price_data.iloc[-1]['close']
            # 儲存到資料庫
            if db:
                db.save_daily_price(stock_code, price_data)
            return latest_price
    except Exception as e:
        pass  # 靜默錯誤，避免干擾輸出
    return None

def calculate_kd(df: pd.DataFrame, period: int = 9) -> Tuple[float, float]:
    """
    計算 KD 指標
    
    Args:
        df: 包含 high, low, close 欄位的 DataFrame
        period: 計算週期，預設 9 日
    
    Returns:
        (K值, D值) 的 tuple，如果無法計算則返回 (None, None)
    """
    try:
        if df.empty or len(df) < period:
            return (None, None)
        
        # 計算 RSV (Raw Stochastic Value)
        df = df.copy()
        df['low_min'] = df['low'].rolling(window=period, min_periods=period).min()
        df['high_max'] = df['high'].rolling(window=period, min_periods=period).max()
        
        df['rsv'] = 100 * (df['close'] - df['low_min']) / (df['high_max'] - df['low_min'])
        df['rsv'] = df['rsv'].fillna(50)  # 初始值設為50
        
        # 計算 K 值（使用加權移動平均）
        k_values = [50]  # K 初始值
        for rsv in df['rsv'].iloc[1:]:
            k = k_values[-1] * 2/3 + rsv * 1/3
            k_values.append(k)
        
        df['k'] = k_values
        
        # 計算 D 值（K 值的加權移動平均）
        d_values = [50]  # D 初始值
        for k in df['k'].iloc[1:]:
            d = d_values[-1] * 2/3 + k * 1/3
            d_values.append(d)
        
        df['d'] = d_values
        
        # 返回最新的 K 和 D 值
        latest_k = df['k'].iloc[-1]
        latest_d = df['d'].iloc[-1]
        
        return (latest_k, latest_d)
        
    except Exception as e:
        return (None, None)

def get_kd_indicators(dl, stock_id: str, db=None) -> Dict:
    """
    取得股票的 KD 指標
    
    Args:
        dl: FinMind DataLoader 實例
        stock_id: 股票代碼
        db: 資料庫管理器（可選）
    
    Returns:
        包含 daily_k, daily_d, weekly_k, weekly_d 的字典
    """
    try:
        import datetime
        
        # 計算日期範圍（需要足夠的歷史數據）
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        
        # 優先從資料庫讀取
        price_data = None
        if db:
            price_data = db.get_daily_price(stock_id, start_date=start_date, end_date=end_date)
        
        # 資料庫沒有，從 API 取得
        if price_data is None or price_data.empty:
            price_data = dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # 儲存到資料庫
            if db and not price_data.empty:
                db.save_daily_price(stock_id, price_data)
        
        if price_data.empty:
            return {'daily_k': None, 'daily_d': None, 'weekly_k': None, 'weekly_d': None}
        
        # 確保欄位名稱正確（FinMind 使用 max/min，資料庫使用 high/low）
        if 'max' in price_data.columns:
            price_data = price_data.rename(columns={'max': 'high', 'min': 'low'})
        
        # 計算日 KD
        daily_k, daily_d = calculate_kd(price_data, period=9)
        
        # 計算周 KD（將日數據轉換為周數據）
        weekly_data = price_data.copy()
        weekly_data['date'] = pd.to_datetime(weekly_data['date'])
        weekly_data.set_index('date', inplace=True)
        
        # 轉換為周數據
        weekly_price = weekly_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        weekly_k, weekly_d = calculate_kd(weekly_price, period=9)
        
        return {
            'daily_k': daily_k,
            'daily_d': daily_d,
            'weekly_k': weekly_k,
            'weekly_d': weekly_d
        }
        
    except Exception as e:
        # 返回空值而不是拋出錯誤
        return {'daily_k': None, 'daily_d': None, 'weekly_k': None, 'weekly_d': None}

def calculate_dividend_yield(dividend_per_share: float, current_price: float) -> float:
    """計算殖利率 (%)"""
    if current_price > 0:
        return (dividend_per_share / current_price) * 100
    return 0

def check_finmind_api_status(dl) -> bool:
    """
    檢查 FinMind API 是否正常
    返回 True 表示正常，False 表示達到限制或錯誤
    """
    try:
        # 嘗試查詢一檔測試股票
        import datetime
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        test_data = dl.taiwan_stock_daily(
            stock_id='2330',
            start_date=end_date,
            end_date=end_date
        )
        return True
    except KeyError as e:
        if "'data'" in str(e):
            print("\n⚠️ FinMind API 已達到請求上限")
            print("💡 可能的解決方案：")
            print("   1. 等待幾分鐘後重試（通常每分鐘有請求限制）")
            print("   2. 等到隔天再試（可能有每日請求限制）")
            print("   3. 升級 FinMind 方案以獲得更高配額")
            print("   4. 考慮使用較小的股票清單")
            return False
    except Exception as e:
        print(f"\n❌ FinMind API 錯誤: {e}")
        return False

def method_1_with_finmind():
    """
    方法 1：使用 FinMind API 取得殖利率資料
    需要先安裝: pip install FinMind
    
    資料庫模式：
    - 優先從本地資料庫讀取（快速，不消耗 API）
    - 資料不存在時才呼叫 API
    - 建議先執行 sync_data.py 預先下載資料
    """
    print("\n" + "="*80)
    print("方法 1：使用 FinMind API 取得殖利率資料（資料庫模式）")
    print("="*80)
    
    # 初始化資料庫
    db = None
    use_database = os.getenv('USE_DATABASE', 'True').lower() == 'true'
    
    if use_database:
        try:
            db = init_database()
            db_stats = db.get_database_stats()
            print(f"\n💾 資料庫模式已啟用")
            print(f"   股票數: {db_stats['total_stocks']}")
            print(f"   股利記錄: {db_stats['dividend_records']}")
            print(f"   股價記錄: {db_stats['price_records']}")
            print(f"   資料庫大小: {db_stats['db_size_mb']:.2f} MB")
            
            if db_stats['total_stocks'] == 0:
                print("\n⚠️ 資料庫為空，建議先執行：python sync_data.py --mode candidates")
        except Exception as e:
            print(f"\n⚠️ 資料庫初始化失敗: {e}")
            print("   將改用純 API 模式")
            db = None
    else:
        print("\n📡 純 API 模式（不使用資料庫）")
    
    try:
        from FinMind.data import DataLoader
        
        # 初始化 FinMind (使用 API token 提升使用量)
        finmind_token = os.getenv('FINMIND_API_TOKEN')
        if finmind_token:
            dl = DataLoader()
            dl.login_by_token(api_token=finmind_token)
            print("✅ FinMind API Token 已啟用（提升使用量）")
        else:
            dl = DataLoader()
            print("⚠️ 未設定 FinMind API Token（使用免費額度）")
        
        # 檢查是否啟用 Shioaji 登入
        enable_login = os.getenv('ENABLE_SHIOAJI_LOGIN', 'False').lower() == 'true'
        api = None
        
        if enable_login:
            print("\n🔑 啟用 Shioaji 登入模式（即時股價）")
            api = login_shioaji()
            if not api:
                print("⚠️ 登入失敗，將改用 FinMind 歷史股價")
        else:
            print("\n📊 使用歷史資料模式（FinMind 股價），不登入 Shioaji")
        
        # 如果沒有資料庫，檢查 API 狀態
        if not db:
            print("\n🔍 檢查 FinMind API 狀態...")
            if not check_finmind_api_status(dl):
                print("\n❌ 由於 API 限制，無法繼續執行查詢")
                print("💡 建議：使用資料庫模式並先執行 sync_data.py 下載資料")
                return []
            print("✅ API 狀態正常")
        
        # 取得所有台股清單
        print("\n📥 正在取得所有台股清單...")
        
        # 智慧模式：優先從資料庫獲取股票清單
        if db:
            db_stock_list = db.get_all_stock_ids()
            if db_stock_list:
                stock_list = db_stock_list
                print(f"✅ 從資料庫取得 {len(stock_list)} 檔台股清單")
            else:
                print("⚠️ 資料庫中無股票清單，從 API 取得...")
                stock_list = None
        else:
            stock_list = None
        
        # 資料庫沒有清單，從 API 取得
        if stock_list is None:
            try:
                stock_info = dl.taiwan_stock_info()
                # 只取一般股票（排除 ETF 等），股票代號通常是 4 位數字
                stock_list = stock_info[stock_info['type'] == 'twse']['stock_id'].tolist()
                # 過濾掉非純數字的代碼（如 ETF、特別股等）
                stock_list = [s for s in stock_list if s.isdigit() and len(s) == 4]
                print(f"✅ 從 API 取得 {len(stock_list)} 檔台股")
                
                # 儲存到資料庫
                if db:
                    db.save_stock_info(stock_info)
                    print("✅ 股票清單已儲存到資料庫")
            except Exception as e:
                print(f"❌ 取得台股清單失敗: {e}")
                print("改用擴展清單（包含高殖利率候選股票）...")
                # 擴展清單包含較多金融股、傳產股等高殖利率候選
            stock_list = [
                # 之前找到的高殖利率股票
                '8422', '2062', '6754', '9943', '6670', '2707', '6671', '3557',
                # 金融股
                '2880', '2881', '2882', '2883', '2884', '2885', '2886', '2887', '2888', '2889', '2890', '2891', '2892',
                '5880', '2809', '2812', '2834', '2836', '2838', '2845', '2849', '2850', '2851', '2852', '2855',
                # 電信三雄
                '2412', '3045', '4904',
                # 傳產股
                '1101', '1102', '1103', '1301', '1303', '1326', '1402', '1476', '1590',
                '2002', '2105', '2201', '2301', '2303', '2308', '2317', '2327', '2330',
                '2454', '2603', '2609', '2610', '2615', '2801', '2912', '3008',
                # 其他高股息候選
                '9910', '9911', '9912', '9914', '9917', '9918', '9919', '9921', '9924', '9925', '9926', '9927', '9928', '9929', '9930', '9931', '9933', '9934', '9935', '9937', '9938', '9939', '9940', '9941', '9942', '9943', '9944', '9945', '9946', '9949', '9950', '9951', '9955', '9956', '9958'
            ]
        
        print("\n🔍 智慧查詢模式：")
        if db:
            # 檢查哪些股票需要更新資料
            stocks_need_dividend = set(db.get_stocks_need_update('dividend', max_age_days=30))
            stocks_need_price = set(db.get_stocks_need_update('price', max_age_days=7))
            
            # 交集：清單中需要更新的股票
            stocks_to_query = [s for s in stock_list if s in (stocks_need_dividend | stocks_need_price)]
            stocks_from_db = [s for s in stock_list if s not in stocks_to_query]
            
            print(f"   📊 總股票數: {len(stock_list)}")
            print(f"   ✅ 從資料庫讀取: {len(stocks_from_db)} 檔（資料已是最新）")
            print(f"   📥 需要查詢API: {len(stocks_to_query)} 檔")
            print(f"      - 需要股利資料: {len([s for s in stock_list if s in stocks_need_dividend])} 檔")
            print(f"      - 需要股價資料: {len([s for s in stock_list if s in stocks_need_price])} 檔")
            
            if stocks_to_query:
                print(f"\n⏱️  預估 API 呼叫次數: ~{len(stocks_to_query) * 2} 次（股利+股價）")
        else:
            stocks_to_query = stock_list
            print(f"   📡 純 API 模式: 需查詢 {len(stock_list)} 檔股票")
        
        print("\n正在查詢股票殖利率...")
        high_dividend_stocks = []
        processed_count = 0
        total_count = len(stock_list)
        db_hit_count = 0  # 從資料庫讀取的次數
        api_call_count = 0  # API 呼叫次數
        skipped_count = 0  # 跳過的次數（資料完整且最新）
        
        for stock_id in stock_list:
            processed_count += 1
            try:
                # 智慧模式：檢查是否需要查詢
                need_dividend_update = db is None or not db.is_dividend_data_fresh(stock_id, max_age_days=30)
                need_price_update = db is None or not db.is_price_data_fresh(stock_id, max_age_days=7)
                
                # 從資料庫讀取股利資料
                dividend_data = None
                if db:
                    dividend_data = db.get_dividend_data(stock_id, start_date='2022-01-01')
                    if not dividend_data.empty and not need_dividend_update:
                        db_hit_count += 1
                
                # 需要更新股利資料
                if need_dividend_update and (dividend_data is None or dividend_data.empty):
                    dividend_data = dl.taiwan_stock_dividend(
                        stock_id=stock_id,
                        start_date='2022-01-01'
                    )
                    api_call_count += 1
                    # 儲存到資料庫
                    if db and not dividend_data.empty:
                        db.save_dividend_data(stock_id, dividend_data)
                
                if not dividend_data.empty:
                    # 取得最新的股利資料
                    latest_dividend = dividend_data.iloc[-1]
                    cash_dividend = latest_dividend['CashEarningsDistribution']  # 現金股利
                    
                    # 取得股價（優先使用 Shioaji 即時股價，否則使用 FinMind 或資料庫）
                    if api:
                        current_price = get_stock_price_from_shioaji(api, stock_id)
                    else:
                        current_price = get_stock_price_from_finmind(dl, stock_id, db=db)
                    
                    if current_price and cash_dividend > 0:
                        dividend_yield = calculate_dividend_yield(cash_dividend, current_price)
                        
                        if dividend_yield > 5:
                            # 取得 KD 指標
                            kd_data = get_kd_indicators(dl, stock_id, db=db)
                            
                            high_dividend_stocks.append({
                                'stock_id': stock_id,
                                'current_price': current_price,
                                'cash_dividend': cash_dividend,
                                'dividend_yield': dividend_yield,
                                'year': latest_dividend['AnnouncementDate'][:4],
                                'daily_k': kd_data['daily_k'],
                                'daily_d': kd_data['daily_d'],
                                'weekly_k': kd_data['weekly_k'],
                                'weekly_d': kd_data['weekly_d']
                            })
                            print(f"✅ [{processed_count}/{total_count}] {stock_id}: 殖利率 {dividend_yield:.2f}% ⭐")
                        else:
                            # 顯示前 10 檔測試用
                            if processed_count <= 10:
                                print(f"   [{processed_count}/{total_count}] {stock_id}: 股價={current_price:.2f}, 股利={cash_dividend:.2f}, 殖利率={dividend_yield:.2f}%")
                    else:
                        if processed_count <= 10:
                            print(f"   [{processed_count}/{total_count}] {stock_id}: 無法取得股價或股利=0 (股價={current_price}, 股利={cash_dividend})")
                else:
                    if processed_count <= 10:
                        print(f"   [{processed_count}/{total_count}] {stock_id}: 無股利資料")
                            
            except KeyboardInterrupt:
                print("\n⚠️ 使用者中斷查詢")
                break
            except Exception as e:
                # 顯示錯誤以便調試
                if processed_count <= 10:
                    print(f"   ⚠️ [{processed_count}/{total_count}] {stock_id}: 錯誤 - {e}")
            
            # 每 50 檔顯示進度
            if processed_count % 50 == 0:
                if db:
                    saved_pct = (db_hit_count / (db_hit_count + api_call_count) * 100) if (db_hit_count + api_call_count) > 0 else 0
                    print(f"📊 進度: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%) - "
                          f"已找到 {len(high_dividend_stocks)} 檔 | "
                          f"DB命中: {db_hit_count} | API呼叫: {api_call_count} | "
                          f"節省: {saved_pct:.1f}%")
                else:
                    print(f"📊 進度: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%) - "
                          f"已找到 {len(high_dividend_stocks)} 檔高殖利率股票")
        
        # 顯示結果
        print("\n" + "="*100)
        print(f"找到 {len(high_dividend_stocks)} 檔殖利率大於 5% 的股票：")
        print("="*100)
        
        if db:
            print(f"\n💾 資料來源統計:")
            print(f"   從資料庫讀取: {db_hit_count} 次")
            print(f"   API 呼叫: {api_call_count} 次")
            print(f"   節省 API 請求: {db_hit_count / (db_hit_count + api_call_count) * 100:.1f}%")
        
        if high_dividend_stocks:
            # 依殖利率排序
            high_dividend_stocks.sort(key=lambda x: x['dividend_yield'], reverse=True)
            
            print(f"\n{'股票':<6} {'股價':<8} {'股利':<8} {'殖利率':<8} {'日K':<8} {'日D':<8} {'周K':<8} {'周D':<8} {'年度':<6}")
            print("-" * 100)
            for stock in high_dividend_stocks:
                daily_k = f"{stock['daily_k']:.2f}" if stock['daily_k'] is not None else "N/A"
                daily_d = f"{stock['daily_d']:.2f}" if stock['daily_d'] is not None else "N/A"
                weekly_k = f"{stock['weekly_k']:.2f}" if stock['weekly_k'] is not None else "N/A"
                weekly_d = f"{stock['weekly_d']:.2f}" if stock['weekly_d'] is not None else "N/A"
                
                print(f"{stock['stock_id']:<6} {stock['current_price']:<8.2f} {stock['cash_dividend']:<8.2f} "
                      f"{stock['dividend_yield']:<7.2f}% {daily_k:<8} {daily_d:<8} {weekly_k:<8} {weekly_d:<8} {stock['year']:<6}")
        else:
            print("未找到符合條件的股票")
        
        # 關閉資料庫連接
        if db:
            db.close()
            print("\n💾 資料庫已關閉")
            
    except ImportError:
        print("❌ 未安裝 FinMind，請執行以下指令安裝：")
        print("   pip install FinMind")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    finally:
        # 確保資料庫關閉
        if db:
            db.close()

def method_2_manual():
    """
    方法 2：手動輸入股利資料進行篩選
    適合已知特定股票的股利資訊
    """
    print("\n" + "="*80)
    print("方法 2：手動輸入股利資料")
    print("="*80)
    
    # 手動輸入的股利資料（股票代碼: 現金股利）
    # 請根據最新的除息公告更新
    manual_dividend_data = {
        '2330': 11.0,   # 台積電 (範例)
        '2317': 5.5,    # 鴻海 (範例)
        '2882': 1.7,    # 國泰金 (範例)
        '1301': 2.0,    # 台塑 (範例)
        '2454': 8.0,    # 聯發科 (範例)
    }
    
    # 檢查是否啟用 Shioaji 登入
    enable_login = os.getenv('ENABLE_SHIOAJI_LOGIN', 'False').lower() == 'true'
    api = None
    
    if enable_login:
        print("\n🔑 啟用 Shioaji 登入模式（即時股價）")
        api = login_shioaji()
        if not api:
            print("⚠️ 登入失敗，將改用 FinMind 歷史股價")
    else:
        print("\n📊 使用歷史資料模式（FinMind 股價），不登入 Shioaji")
    
    # 初始化 FinMind（如果需要）
    dl = None
    if not api:
        try:
            from FinMind.data import DataLoader
            dl = DataLoader()
        except ImportError:
            print("❌ 未安裝 FinMind，請執行: pip install FinMind")
            return
    
    print("\n正在計算殖利率...")
    high_dividend_stocks = []
    
    for stock_id, cash_dividend in manual_dividend_data.items():
        try:
            # 取得股價（優先使用 Shioaji 即時股價，否則使用 FinMind 歷史股價）
            if api:
                current_price = get_stock_price_from_shioaji(api, stock_id)
            else:
                current_price = get_stock_price_from_finmind(dl, stock_id)
            
            if current_price and cash_dividend > 0:
                dividend_yield = calculate_dividend_yield(cash_dividend, current_price)
                
                if dividend_yield > 7:
                    high_dividend_stocks.append({
                        'stock_id': stock_id,
                        'current_price': current_price,
                        'cash_dividend': cash_dividend,
                        'dividend_yield': dividend_yield
                    })
                    print(f"✅ {stock_id}: 殖利率 {dividend_yield:.2f}%")
                else:
                    print(f"   {stock_id}: 殖利率 {dividend_yield:.2f}% (未達標)")
                    
        except Exception as e:
            print(f"❌ 處理 {stock_id} 時發生錯誤: {e}")
    
    # 顯示結果
    print("\n" + "="*80)
    print(f"找到 {len(high_dividend_stocks)} 檔殖利率大於 7% 的股票：")
    print("="*80)
    
    if high_dividend_stocks:
        high_dividend_stocks.sort(key=lambda x: x['dividend_yield'], reverse=True)
        
        print(f"\n{'股票代碼':<10} {'目前股價':<10} {'現金股利':<10} {'殖利率':<10}")
        print("-" * 80)
        for stock in high_dividend_stocks:
            print(f"{stock['stock_id']:<10} {stock['current_price']:<10.2f} "
                  f"{stock['cash_dividend']:<10.2f} {stock['dividend_yield']:<10.2f}%")
    else:
        print("未找到符合條件的股票")

def main():
    """主程式"""
    print("=" * 80)
    print("尋找殖利率大於 5% 的股票 (含 KD 指標)")
    print("=" * 80)
    
    # 直接執行方法 1
    method_1_with_finmind()

if __name__ == "__main__":
    main()
