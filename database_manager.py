"""
資料庫管理模組
用於儲存和讀取 FinMind 下載的台股資料，避免重複 API 請求
"""
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

class StockDatabase:
    """台股資料庫管理類別"""
    
    def __init__(self, db_path: str = 'stock_data.db'):
        """
        初始化資料庫連接
        
        Args:
            db_path: 資料庫檔案路徑
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """建立資料庫連接"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        """建立所有需要的資料表"""
        
        # 1. 股票資訊表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                stock_id TEXT PRIMARY KEY,
                stock_name TEXT,
                industry_category TEXT,
                market TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. 股利資料表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividend_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                announcement_date DATE,
                cash_dividend REAL,
                stock_dividend REAL,
                cash_earnings_distribution REAL,
                year TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_id, announcement_date)
            )
        ''')
        
        # 3. 每日股價表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_id, date)
            )
        ''')
        
        # 4. KD 指標快取表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kd_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                period_type TEXT,  -- 'daily' or 'weekly'
                date DATE,
                k_value REAL,
                d_value REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_id, period_type, date)
            )
        ''')
        
        # 5. API 請求記錄表（用於追蹤 API 使用量）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_type TEXT,
                stock_id TEXT,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER
            )
        ''')
        
        # 6. 資料更新記錄表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT,
                stock_id TEXT,
                last_sync TIMESTAMP,
                status TEXT,
                message TEXT
            )
        ''')
        
        # 建立索引以加速查詢
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dividend_stock ON dividend_data(stock_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_stock ON daily_price(stock_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_date ON daily_price(date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_kd_stock ON kd_indicators(stock_id)')
        
        self.conn.commit()
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
    
    # ==================== 股票資訊相關 ====================
    
    def save_stock_info(self, stock_list: pd.DataFrame):
        """
        儲存股票基本資訊
        
        Args:
            stock_list: 包含 stock_id, stock_name 等欄位的 DataFrame
        """
        for _, row in stock_list.iterrows():
            self.cursor.execute('''
                INSERT OR REPLACE INTO stock_info 
                (stock_id, stock_name, industry_category, market, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row.get('stock_id', ''),
                row.get('stock_name', ''),
                row.get('industry_category', ''),
                row.get('type', ''),
                datetime.now()
            ))
        self.conn.commit()
    
    def get_all_stock_ids(self) -> List[str]:
        """取得所有股票代碼"""
        self.cursor.execute('SELECT stock_id FROM stock_info')
        return [row[0] for row in self.cursor.fetchall()]
    
    # ==================== 股利資料相關 ====================
    
    def save_dividend_data(self, stock_id: str, dividend_df: pd.DataFrame):
        """
        儲存股利資料
        
        Args:
            stock_id: 股票代碼
            dividend_df: 股利資料 DataFrame
        """
        if dividend_df.empty:
            return
        
        for _, row in dividend_df.iterrows():
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO dividend_data 
                    (stock_id, announcement_date, cash_dividend, stock_dividend, 
                     cash_earnings_distribution, year, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_id,
                    row.get('AnnouncementDate', ''),
                    float(row.get('CashDividend', 0)),
                    float(row.get('StockDividend', 0)),
                    float(row.get('CashEarningsDistribution', 0)),
                    str(row.get('AnnouncementDate', ''))[:4],
                    datetime.now()
                ))
            except Exception as e:
                print(f"儲存 {stock_id} 股利資料失敗: {e}")
        
        self.conn.commit()
        self._log_sync(stock_id, 'dividend', 'success')
    
    def get_dividend_data(self, stock_id: str, start_date: str = None) -> pd.DataFrame:
        """
        從資料庫讀取股利資料
        
        Args:
            stock_id: 股票代碼
            start_date: 起始日期 (可選)
        
        Returns:
            DataFrame 包含股利資料
        """
        if start_date:
            query = '''
                SELECT announcement_date as AnnouncementDate, 
                       cash_dividend as CashDividend,
                       stock_dividend as StockDividend,
                       cash_earnings_distribution as CashEarningsDistribution,
                       year
                FROM dividend_data 
                WHERE stock_id = ? AND announcement_date >= ?
                ORDER BY announcement_date
            '''
            self.cursor.execute(query, (stock_id, start_date))
        else:
            query = '''
                SELECT announcement_date as AnnouncementDate, 
                       cash_dividend as CashDividend,
                       stock_dividend as StockDividend,
                       cash_earnings_distribution as CashEarningsDistribution,
                       year
                FROM dividend_data 
                WHERE stock_id = ?
                ORDER BY announcement_date
            '''
            self.cursor.execute(query, (stock_id,))
        
        rows = self.cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        
        columns = ['AnnouncementDate', 'CashDividend', 'StockDividend', 
                   'CashEarningsDistribution', 'year']
        return pd.DataFrame(rows, columns=columns)
    
    def is_dividend_data_fresh(self, stock_id: str, max_age_days: int = 7) -> bool:
        """
        檢查股利資料是否夠新
        
        Args:
            stock_id: 股票代碼
            max_age_days: 資料有效天數
        
        Returns:
            True 如果資料夠新，False 需要更新
        """
        self.cursor.execute('''
            SELECT MAX(updated_at) FROM dividend_data WHERE stock_id = ?
        ''', (stock_id,))
        result = self.cursor.fetchone()
        
        if not result[0]:
            return False
        
        last_update = datetime.fromisoformat(result[0])
        age = (datetime.now() - last_update).days
        return age < max_age_days
    
    # ==================== 股價資料相關 ====================
    
    def save_daily_price(self, stock_id: str, price_df: pd.DataFrame):
        """
        儲存每日股價資料
        
        Args:
            stock_id: 股票代碼
            price_df: 股價資料 DataFrame
        """
        if price_df.empty:
            return
        
        for _, row in price_df.iterrows():
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO daily_price 
                    (stock_id, date, open, high, low, close, volume, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_id,
                    row.get('date', ''),
                    float(row.get('open', 0)),
                    float(row.get('max', 0)),
                    float(row.get('min', 0)),
                    float(row.get('close', 0)),
                    int(row.get('Trading_Volume', 0)),
                    datetime.now()
                ))
            except Exception as e:
                print(f"儲存 {stock_id} 股價資料失敗: {e}")
        
        self.conn.commit()
        self._log_sync(stock_id, 'price', 'success')
    
    def get_daily_price(self, stock_id: str, start_date: str = None, 
                        end_date: str = None) -> pd.DataFrame:
        """
        從資料庫讀取每日股價
        
        Args:
            stock_id: 股票代碼
            start_date: 起始日期 (可選)
            end_date: 結束日期 (可選)
        
        Returns:
            DataFrame 包含股價資料
        """
        query = '''
            SELECT date, open, high as max, low as min, close, volume as Trading_Volume
            FROM daily_price 
            WHERE stock_id = ?
        '''
        params = [stock_id]
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY date'
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        columns = ['date', 'open', 'max', 'min', 'close', 'Trading_Volume']
        return pd.DataFrame(rows, columns=columns)
    
    def get_latest_price(self, stock_id: str) -> Optional[float]:
        """
        取得最新收盤價
        
        Args:
            stock_id: 股票代碼
        
        Returns:
            最新收盤價，如果沒有資料則返回 None
        """
        self.cursor.execute('''
            SELECT close FROM daily_price 
            WHERE stock_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        ''', (stock_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def is_price_data_fresh(self, stock_id: str, max_age_days: int = 1) -> bool:
        """
        檢查股價資料是否夠新
        
        Args:
            stock_id: 股票代碼
            max_age_days: 資料有效天數
        
        Returns:
            True 如果資料夠新，False 需要更新
        """
        self.cursor.execute('''
            SELECT MAX(date) FROM daily_price WHERE stock_id = ?
        ''', (stock_id,))
        result = self.cursor.fetchone()
        
        if not result[0]:
            return False
        
        last_date = datetime.strptime(result[0], '%Y-%m-%d').date()
        today = datetime.now().date()
        age = (today - last_date).days
        return age <= max_age_days
    
    # ==================== KD 指標相關 ====================
    
    def save_kd_indicators(self, stock_id: str, period_type: str, 
                          k_value: float, d_value: float, date: str = None):
        """
        儲存 KD 指標
        
        Args:
            stock_id: 股票代碼
            period_type: 'daily' or 'weekly'
            k_value: K 值
            d_value: D 值
            date: 日期 (可選，預設為今天)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO kd_indicators 
            (stock_id, period_type, date, k_value, d_value, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (stock_id, period_type, date, k_value, d_value, datetime.now()))
        
        self.conn.commit()
    
    def get_kd_indicators(self, stock_id: str, period_type: str) -> Optional[Dict]:
        """
        從資料庫讀取 KD 指標
        
        Args:
            stock_id: 股票代碼
            period_type: 'daily' or 'weekly'
        
        Returns:
            字典包含 k_value, d_value，如果沒有則返回 None
        """
        self.cursor.execute('''
            SELECT k_value, d_value FROM kd_indicators 
            WHERE stock_id = ? AND period_type = ?
            ORDER BY date DESC 
            LIMIT 1
        ''', (stock_id, period_type))
        
        result = self.cursor.fetchone()
        if result:
            return {'k': result[0], 'd': result[1]}
        return None
    
    # ==================== API 請求記錄 ====================
    
    def log_api_request(self, request_type: str, stock_id: str, success: bool):
        """記錄 API 請求"""
        self.cursor.execute('''
            INSERT INTO api_requests (request_type, stock_id, request_time, success)
            VALUES (?, ?, ?, ?)
        ''', (request_type, stock_id, datetime.now(), 1 if success else 0))
        self.conn.commit()
    
    def get_api_request_stats(self, hours: int = 24) -> Dict:
        """
        取得 API 請求統計
        
        Args:
            hours: 統計過去幾小時
        
        Returns:
            字典包含統計資訊
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(success) as successful_requests,
                COUNT(DISTINCT stock_id) as unique_stocks
            FROM api_requests
            WHERE request_time >= ?
        ''', (cutoff_time,))
        
        result = self.cursor.fetchone()
        return {
            'total_requests': result[0],
            'successful_requests': result[1],
            'unique_stocks': result[2],
            'period_hours': hours
        }
    
    # ==================== 資料同步記錄 ====================
    
    def _log_sync(self, stock_id: str, data_type: str, status: str, message: str = ''):
        """記錄資料同步狀態"""
        self.cursor.execute('''
            INSERT INTO data_sync_log (data_type, stock_id, last_sync, status, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (data_type, stock_id, datetime.now(), status, message))
        self.conn.commit()
    
    def get_stocks_need_update(self, data_type: str, max_age_days: int = 7) -> List[str]:
        """
        取得需要更新的股票清單
        
        Args:
            data_type: 'dividend' or 'price'
            max_age_days: 資料有效天數
        
        Returns:
            需要更新的股票代碼清單
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # 取得所有股票
        all_stocks = self.get_all_stock_ids()
        
        # 取得已有最新資料的股票
        self.cursor.execute('''
            SELECT DISTINCT stock_id 
            FROM data_sync_log 
            WHERE data_type = ? AND last_sync >= ? AND status = 'success'
        ''', (data_type, cutoff_date))
        
        updated_stocks = set(row[0] for row in self.cursor.fetchall())
        
        # 需要更新的 = 全部 - 已更新
        return [s for s in all_stocks if s not in updated_stocks]
    
    # ==================== 批次操作 ====================
    
    def batch_update_needed(self, stock_id: str) -> Dict[str, bool]:
        """
        檢查股票是否需要更新各類資料
        
        Args:
            stock_id: 股票代碼
        
        Returns:
            字典指示各類資料是否需要更新
        """
        return {
            'dividend': not self.is_dividend_data_fresh(stock_id, max_age_days=7),
            'price': not self.is_price_data_fresh(stock_id, max_age_days=1)
        }
    
    def get_database_stats(self) -> Dict:
        """取得資料庫統計資訊"""
        stats = {}
        
        # 股票數量
        self.cursor.execute('SELECT COUNT(*) FROM stock_info')
        stats['total_stocks'] = self.cursor.fetchone()[0]
        
        # 股利資料筆數
        self.cursor.execute('SELECT COUNT(*) FROM dividend_data')
        stats['dividend_records'] = self.cursor.fetchone()[0]
        
        # 股價資料筆數
        self.cursor.execute('SELECT COUNT(*) FROM daily_price')
        stats['price_records'] = self.cursor.fetchone()[0]
        
        # KD 指標筆數
        self.cursor.execute('SELECT COUNT(*) FROM kd_indicators')
        stats['kd_records'] = self.cursor.fetchone()[0]
        
        # 資料庫大小
        stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
        
        return stats


# ==================== 便利函數 ====================

def init_database(db_path: str = 'stock_data.db') -> StockDatabase:
    """
    初始化資料庫連接
    
    Args:
        db_path: 資料庫檔案路徑
    
    Returns:
        StockDatabase 實例
    """
    return StockDatabase(db_path)


if __name__ == "__main__":
    # 測試資料庫功能
    print("初始化資料庫...")
    db = init_database()
    
    print("\n資料庫統計:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    db.close()
    print("\n✅ 資料庫初始化完成！")
