"""
示範：查詢高殖利率股票並顯示KD指標
使用固定的高殖利率股票清單
"""
import os
import datetime
import pandas as pd
from FinMind.data import DataLoader
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def calculate_kd(df: pd.DataFrame, period: int = 9):
    """計算 KD 指標"""
    try:
        if df.empty or len(df) < period:
            return None, None
        
        # 計算 RSV
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        
        # 計算 K 值和 D 值
        k = rsv.ewm(alpha=1/3, adjust=False).mean()
        d = k.ewm(alpha=1/3, adjust=False).mean()
        
        latest_k = k.iloc[-1] if not k.empty else None
        latest_d = d.iloc[-1] if not d.empty else None
        
        return latest_k, latest_d
    except Exception as e:
        return None, None

def get_stock_data_with_kd(dl, stock_id: str):
    """取得股票資料並計算KD"""
    try:
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        
        # 取得日線資料
        daily_data = dl.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if daily_data.empty:
            return None
        
        # 取得最新股價
        current_price = daily_data.iloc[-1]['close']
        
        # 計算日KD
        daily_k, daily_d = calculate_kd(daily_data)
        
        # 轉換為週線資料
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data.set_index('date', inplace=True)
        
        weekly_data = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'Trading_Volume': 'sum'
        }).dropna()
        
        # 計算週KD
        weekly_k, weekly_d = calculate_kd(weekly_data)
        
        # 取得股利資料
        dividend_data = dl.taiwan_stock_dividend(
            stock_id=stock_id,
            start_date='2023-01-01'
        )
        
        cash_dividend = None
        dividend_yield = None
        year = None
        
        if not dividend_data.empty:
            latest_dividend = dividend_data.iloc[-1]
            cash_dividend = latest_dividend['CashEarningsDistribution']
            if current_price > 0:
                dividend_yield = (cash_dividend / current_price) * 100
            year = latest_dividend['AnnouncementDate'][:4]
        
        return {
            'stock_id': stock_id,
            'current_price': current_price,
            'cash_dividend': cash_dividend,
            'dividend_yield': dividend_yield,
            'year': year,
            'daily_k': daily_k,
            'daily_d': daily_d,
            'weekly_k': weekly_k,
            'weekly_d': weekly_d
        }
    except Exception as e:
        print(f"處理 {stock_id} 時發生錯誤: {e}")
        return None

def main():
    print("=" * 100)
    print("示範：殖利率大於 5% 的股票 (含 KD 指標)")
    print("=" * 100)
    
    # 初始化 FinMind (使用API token如果有的話)
    finmind_token = os.getenv('FINMIND_API_TOKEN')
    dl = DataLoader() if not finmind_token else DataLoader(token=finmind_token)
    
    # 使用部分知名的高殖利率候選股票
    stock_list = [
        '2882', '2886', '2885', '2891',  # 金融股
        '2412', '3045',  # 電信股
        '1101', '1102', '1301', '1303',  # 水泥、塑化
        '2002', '2201',  # 食品、紡織
        '2609', '2615',  # 航運
        '2912',  # 統一超
    ]
    
    print(f"\n正在查詢 {len(stock_list)} 檔股票...")
    print("(僅示範部分股票，完整查詢請使用 find_high_dividend_stocks.py)\n")
    
    results = []
    
    for i, stock_id in enumerate(stock_list, 1):
        print(f"[{i}/{len(stock_list)}] 查詢 {stock_id}...", end=" ")
        
        data = get_stock_data_with_kd(dl, stock_id)
        
        if data and data['dividend_yield'] and data['dividend_yield'] > 5:
            results.append(data)
            print(f"✅ 殖利率 {data['dividend_yield']:.2f}%")
        else:
            if data and data['dividend_yield']:
                print(f"殖利率 {data['dividend_yield']:.2f}%")
            else:
                print("無資料")
    
    # 顯示結果
    print("\n" + "=" * 100)
    print(f"找到 {len(results)} 檔殖利率大於 5% 的股票：")
    print("=" * 100)
    
    if results:
        results.sort(key=lambda x: x['dividend_yield'], reverse=True)
        
        print(f"\n{'股票':<6} {'股價':<8} {'股利':<8} {'殖利率':<8} {'日K':<8} {'日D':<8} {'周K':<8} {'周D':<8} {'年度':<6}")
        print("-" * 100)
        
        for stock in results:
            daily_k = f"{stock['daily_k']:.2f}" if stock['daily_k'] is not None else "N/A"
            daily_d = f"{stock['daily_d']:.2f}" if stock['daily_d'] is not None else "N/A"
            weekly_k = f"{stock['weekly_k']:.2f}" if stock['weekly_k'] is not None else "N/A"
            weekly_d = f"{stock['weekly_d']:.2f}" if stock['weekly_d'] is not None else "N/A"
            
            print(f"{stock['stock_id']:<6} {stock['current_price']:<8.2f} {stock['cash_dividend']:<8.2f} "
                  f"{stock['dividend_yield']:<7.2f}% {daily_k:<8} {daily_d:<8} {weekly_k:<8} {weekly_d:<8} {stock['year']:<6}")
    else:
        print("未找到符合條件的股票")

if __name__ == "__main__":
    main()
