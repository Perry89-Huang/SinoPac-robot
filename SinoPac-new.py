###                              建倉機器人
# Shioaji API: https://sinotrade.github.io

# ------- Dynamic Configuration

GROUP = 1

g_bolOrderOn = True
g_bolLogOn = False
g_bolTestMode = True  # 測試模式：True=不檢查餘額, False=正常檢查餘額

# ⚠️ 注意：股票期貨代碼可能已變更或合約不存在
# 建議使用主要的指數期貨（如：台指期TXF、小台MTX等）
# 或者先用 check_contracts.py 查詢可用的合約代碼

if GROUP==1:
    # 成交量排行 group
    # '長榮航','宏達電','華新  ','台積電','友達  ','欣興  ','鴻海  ','元太  ','國泰金','長榮  ','聯電  '
    FutureList = ['HS','HC','CS','CD','CH','IR','DH','NV','CK','CZ','CC']
elif GROUP==2:
    # Price 100~200 group
    # '景碩  ','南電  ','智原  ','智擎  ','技嘉  ','中美晶','可成  ', '奇鋐  ','穩懋  ','聯亞  ','臻鼎  ','微星  ','精材  '
    FutureList = ['IX','QS','IP','PC','GH','NO','GX', 'RA','NA','OT','LU','GI','QL']
elif GROUP == 3:
    # 股票期貨組
    FutureList = ['HS','HC','CS','CD','CH','IR','DH','NV','CK','CZ','CC']    


import shioaji as sj
import signal
import sys
from notification_manager import notifier

# 根据 Shioaji 官方文档：https://sinotrade.github.io/tutor/contract/
# 月份代碼格式：F + 月份代碼 (A=1月, B=2月, C=3月...L=12月) + 年份末位

def get_third_wednesday(year, month):
    """計算指定月份的第3個星期三（個股期貨結算日）"""
    from datetime import datetime, timedelta
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
    
    Returns:
        tuple: (near_code, far_code) 例如 ('FA6', 'FB6')
    """
    from datetime import datetime
    
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
    else:
        # 選擇本月和下個月
        near_offset = 0
        far_offset = 1
    
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
    
    print(f"📅 當前日期: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 本月結算日: {settlement_date.strftime('%Y-%m-%d')} (還有 {days_until_settlement} 天)")
    print(f"📈 自動選擇: {near_code} ({near_year}年{near_month}月) 和 {far_code} ({far_year}年{far_month}月)")
    
    return near_code, far_code

# 自動計算月份代碼
NEAR_MON, FAR_MON = get_future_month_codes()

FEE=25

# ========== 風險控制參數 ==========
MAX_POSITION_PER_CONTRACT = 50  # 每個標的最多50口
MAX_TOTAL_POSITION = 300  # 總持倉最多300口
MAX_SINGLE_ORDER = 30  # 單次下單最多30口

# 通知節流機制 - 避免達到上限時頻繁發送通知
last_limit_notification = {}  # 記錄每個上限類型的最後通知時間

print(f"\n⚙️  風險控制參數：")
print(f"  單一標的上限: {MAX_POSITION_PER_CONTRACT} 口")
print(f"  總持倉上限: {MAX_TOTAL_POSITION} 口")
print(f"  單次下單上限: {MAX_SINGLE_ORDER} 口")
print(f"  測試模式: {'✓ 開啟（不檢查餘額）' if g_bolTestMode else '✗ 關閉（正常檢查餘額）'}")
print(f"  Shioaji環境: {'模擬環境 (simulation=True)' if g_bolTestMode else '正式環境 (simulation=False)'}\n")


# ---- Formal Login (Shioaji 1.0+ 使用 API Key)
# 請到 https://www.sinotrade.com.tw/newweb/PythonAPIKey/ 申請 API Key

import os

# 載入 .env 檔案（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()  # 從 .env 檔案載入環境變數
    print("✓ 已載入 .env 設定檔")
except ImportError:
    print("⚠️  未安裝 python-dotenv，使用系統環境變數或預設值")
except Exception as e:
    print(f"⚠️  載入 .env 時發生錯誤: {e}")

# 從環境變數讀取 API Key（推薦方式）
API_KEY = os.getenv("SINOPAC_API_KEY", "")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
CA_PATH = os.getenv("SINOPAC_CA_PATH", "C:/ekey/551/J120420374/S/Sinopac.pfx")
CA_PASSWORD = os.getenv("SINOPAC_CA_PASSWORD", "J120420374")


# 驗證是否已填入真實的 Key
if not API_KEY or not SECRET_KEY or API_KEY == "YOUR_API_KEY" or SECRET_KEY == "YOUR_SECRET_KEY":
    print("=" * 70)
    print("❌ 錯誤：尚未設定 API Key 和 Secret Key！")
    print("=" * 70)
    print("\n請按照以下步驟操作：")
    print("\n1. 申請 API Key：")
    print("   前往 https://www.sinotrade.com.tw/newweb/PythonAPIKey/")
    print("   點擊「新增 API KEY」")
    print("\n2. 設定權限：")
    print("   ✓ Market / Data（市場數據）")
    print("   ✓ Account（帳戶查詢）")
    print("   ✓ Trading（交易功能）")
    print("   ✓ Production Environment（生產環境，若要正式交易）")
    print("\n3. 設定環境變數（推薦）：")
    print("   Windows PowerShell:")
    print("     $env:SINOPAC_API_KEY='您的API_KEY'")
    print("     $env:SINOPAC_SECRET_KEY='您的SECRET_KEY'")
    print("   或在系統環境變數中設定 SINOPAC_API_KEY 和 SINOPAC_SECRET_KEY")
    print("\n4. 或直接修改程式碼（不建議）：")
    print("   修改程式中的 API_KEY 和 SECRET_KEY 變數")
    print("\n⚠️  注意：Secret Key 只會在申請時顯示一次，請妥善保存！")
    print("=" * 70)
    raise ValueError("請先設定 API_KEY 和 SECRET_KEY")

# 驗證 Key 格式（Base58 不包含 0, O, I, l）
invalid_chars_api = set(API_KEY) & {'0', 'O', 'I', 'l'}
invalid_chars_secret = set(SECRET_KEY) & {'0', 'O', 'I', 'l'}

if invalid_chars_api or invalid_chars_secret:
    print("=" * 70)
    print("❌ 錯誤：API Key 或 Secret Key 包含無效字符！")
    print("=" * 70)
    if invalid_chars_api:
        print(f"API_KEY 中發現無效字符: {invalid_chars_api}")
    if invalid_chars_secret:
        print(f"SECRET_KEY 中發現無效字符: {invalid_chars_secret}")
    print("\n⚠️  Base58 編碼不包含以下字符（避免混淆）：")
    print("   - 數字 '0'（零）")
    print("   - 大寫 'O'（歐）")
    print("   - 大寫 'I'（艾）")
    print("   - 小寫 'l'（L）")
    print("\n請檢查您是否：")
    print("   1. 複製錯誤（建議重新複製 API Key）")
    print("   2. 誤把數字 0 看成字母 O")
    print("   3. 誤把數字 1 看成字母 I 或 l")
    print("=" * 70)
    raise ValueError("API Key 格式錯誤")

api = sj.Shioaji(simulation=g_bolTestMode)  # 根據測試模式自動切換

try:
    # 新版登入方式（Shioaji >= 1.0）
    print("正在登入...")
    accounts = api.login(
        api_key=API_KEY,
        secret_key=SECRET_KEY,
        contracts_cb=lambda security_type: print(f"  {security_type} 合約下載完成")
    )
    print(f"✓ 登入成功！")
    print(f"  帳戶數量: {len(accounts)}")
    for acc in accounts:
        print(f"  - {acc}")
    
    # 發送程式啟動通知
    notifier.notify_program_start("建倉機器人 (SinoPac-new)")
except Exception as e:
    print(f"\n✗ 登入失敗: {e}")
    print("\n請確認：")
    print("1. API Key 和 Secret Key 是否正確（重新複製試試）")
    print("2. API Key 權限已啟用（Market/Data、Account、Trading）")
    print("3. 生產環境權限已開啟（若使用正式環境 simulation=False）")
    print("4. 網路連線正常")
    print("5. 您的電腦時間是否正確（時間差過大會導致登入失敗）")
    raise

try:
    # 啟動憑證
    import os
    if not os.path.exists(CA_PATH):
        print(f"✗ 憑證檔案不存在: {CA_PATH}")
        print("請確認憑證路徑是否正確")
        raise FileNotFoundError(f"找不到憑證檔案: {CA_PATH}")
    
    print("正在啟動憑證...")
    api.activate_ca(
        ca_path=CA_PATH,
        ca_passwd=CA_PASSWORD,
    )
    print("✓ 憑證啟動成功")
except ValueError as e:
    error_msg = str(e)
    print(f"\n✗ 憑證啟動失敗: {error_msg}")
    print("\n" + "=" * 70)
    
    if "Ca Password Incorrect" in error_msg or "mac verify failure" in error_msg:
        print("❌ 憑證密碼錯誤！")
        print("=" * 70)
        print("\n可能的原因：")
        print("1. 憑證密碼輸入錯誤")
        print(f"   目前設定的密碼: '{CA_PASSWORD}'")
        print("\n2. 憑證檔案損壞或格式不正確")
        print(f"   憑證路徑: {CA_PATH}")
        print("\n解決方法：")
        print("• 確認憑證密碼是否正確（區分大小寫）")
        print("• 重新下載憑證檔案")
        print("• 檢查憑證是否過期")
        print("\n⚠️  提示：憑證密碼通常與您的身分證號或設定的密碼相同")
    else:
        print(f"未預期的錯誤: {error_msg}")
        print("=" * 70)
    
    # 不再 raise，讓程式繼續執行（某些功能可能不需要憑證）
    print("\n⚠️  警告：憑證未啟動，部分功能可能無法使用")
    print("如需交易功能，請修正憑證問題後重新執行\n")
except Exception as e:
    print(f"\n✗ 憑證啟動失敗: {e}")
    print(f"憑證路徑: {CA_PATH}")
    print("\n⚠️  警告：憑證未啟動，部分功能可能無法使用\n")


from datetime import datetime, timedelta
from shioaji import TickFOPv1, BidAskFOPv1, Exchange
import numpy as np
from threading import Event 
import pandas as pd

from loguru import logger
from dataclasses import dataclass
from typing import Optional, Dict, List
import math
from shioaji.constant import OrderState, Action, StockOrderCond
import time

# ========== 增強型日誌系統 ==========
# 創建logs目錄
import os
if not os.path.exists('logs'):
    os.makedirs('logs')
    print("✓ 創建 logs 目錄")

if not os.path.exists('PerryLogs'):
    os.makedirs('PerryLogs')

# Loguru 配置（主日誌）
logger.remove()  # 移除預設handler
logger.add(
    "logs/trading_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天午夜輪換
    retention="30 days",  # 保留30天
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    encoding="utf-8"
)

# 錯誤日誌（使用獨立檔案，避免與其他程式衝突）
logger.add(
    "logs/errors_new.log",
    rotation="10 MB",
    retention=None,  # 永久保存
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {file}:{line} | {message}",
    encoding="utf-8"
)

# 交易日誌（重要操作）
logger.add(
    "logs/orders_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",  # 保留90天
    level="INFO",
    filter=lambda record: "ORDER" in record["message"] or "建倉" in record["message"] or "平倉" in record["message"],
    format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    encoding="utf-8"
)

# 保留舊日誌（兼容性）
logger.add("PerryLogs/New_{time}.log", level="TRACE", rotation="200 MB")

print("✓ 日誌系統已配置")
print("  - 交易日誌: logs/trading_YYYY-MM-DD.log (保留30天)")
print("  - 錯誤日誌: logs/errors_new.log (永久保存)")
print("  - 訂單日誌: logs/orders_YYYY-MM-DD.log (保留90天)\n")

logger.info("=" * 60)
logger.info("程式啟動 - 建倉機器人")
logger.info("=" * 60)

#--------------------------------------------------------------
#                     Class Defined
#--------------------------------------------------------------

@dataclass
class StockPosition:
    code: str
    action: Action
    quantity: int
    price: int
    ordercond: StockOrderCond


class PositionAid:
    def __init__(self, api_: sj.Shioaji):
        self.api = api_
        self.api.set_order_callback(self.onOrderStatusChange)
        self.position: Dict[str, StockPosition] = {}
        self.balance_future: float = self.api.margin(self.api.futopt_account)['available_margin']
        
    def onOrderStatusChange(self, state: OrderState, data: Dict):
        pprint(f'onOrderStatusChange: {state} --> {data}')
        
        #reload status from server           
        self.balance_future = self.api.margin(self.api.futopt_account)['available_margin'] 
        objTrade.createFromServer()
        
        if state == OrderState.TFTOrder:
            pass
        elif state == OrderState.TFTDeal: #成交回傳訊息
            #FDEAL --> {'trade_id': '097740c2', 'seqno': '890065', 'ordno': 'tn05bD1Y', 'exchange_seq': 'b0003094', 'broker_id': 'F002000', 
            #           'account_id': '1641626', 'action': 'Buy', 'code': 'CCF', 'price': 44.1, 'quantity': 4, 'subaccount': '', 'security_type': 'FUT', 
            #           'delivery_month': '202301', 'strike_price': 0.0, 'option_right': 'Future', 'market_type': 'Day', 'combo': False, 'ts': 1670979776}
            
            #Update postion
            # option 1: calcualte and update position in client side -> updatePosition
            #self.updatePosition(data) # option 1 calcualte and update position in client side.
            # option 2: reload position from server -> createFromServer
            self.position = {}
            self.createFromServer()
        elif state == OrderState.FOrder: 
            '''
            FORDER --> {'operation': {'op_type': 'New', 'op_code': '00', 'op_msg': ''}, 
            'order': {'id': '6ec98f6c', 'seqno': '565196', 'ordno': 'tn0VL', 
            'account': {'account_type': 'F', 'person_id': '', 'broker_id': 'F002000', 'account_id': '1641626', 
            'signed': True}, 'action': 'Sell', 'price': 123.0, 'quantity': 1, 'order_type': 'ROD', 
            'price_type': 'LMT', 'market_type': 'Day', 'oc_type': 'Cover', 'subaccount': '', 'combo': False}, 
            'status': {'id': '6ec98f6c', 'exchange_ts': 1670983751, 'modified_price': 0.0, 'cancel_quantity': 0, 
            'order_quantity': 1, 'web_id': 'Z'}, 'contract': {'security_type': 'FUT', 'code': 'OTF', 
            'exchange': 'TIM', 'delivery_month': '202212', 'delivery_date': '', 'strike_price': 0.0, 
            'option_right': 'Future'}}
            '''
            
            
            #if data['operation']['op_type']=='New' :
            #    pass
            
            #計算已下單但未成交的數量
            ###### Study Order.UpdateStatus
            
    def createFromServer(self):
        """
        從 api list_position 損益建立 Position 資訊
        [FuturePosition(code='TX201370J2', direction=<Action.Buy: 'Buy'>, quantity=3, price=131.0000, last_price=126.0, pnl=-750.00)]
        """
        all_positions = self.api.list_positions(self.api.futopt_account)
        
        for pos in all_positions:
            position = StockPosition(
                code=pos.code,
                action=pos.direction,
                quantity=int(pos.quantity),
                price=float(pos.price) ,
                ordercond='',
            )
            self.position[position.code] = position

    def AdjustQty(self,strCode:str , intQty: int):
        self.position[strCode].quantity -= intQty
 

    def getAllPosition(self) -> List[StockPosition]:
        return list(self.position.values())
    
    def getPosition_OneFuture(self, strFuture) -> List[StockPosition]: #strFuture: 'HS' -> 'HSFL2', 'HSFA3'
        list1=[]
        for pos in self.getAllPosition():
            if pos.code[0:2]==strFuture:
                list1.append(pos)
        return list1
    
    def updatePosition(self, deal: Dict): #Perry: one option, may delete in future.
        code = deal["code"]
        action = deal["action"]
        order_cond = deal["order_cond"]
        quantity = int(deal["quantity"])
        price = float(deal["price"] )

        position = self.getPosition(code)
        if position == None:
            position = StockPosition(
                code=code,
                action=action,
                quantity=quantity,
                price=price,
                ordercond=order_cond,
            )
        else:
            if position.action == action:
                position.quantity += quantity
            else:
                position.quantity -= quantity
        self.position[code] = position
        logger.info(
            f"{code} {self.api.Contracts.Futures[code].name} {action} {price} 元 {quantity}張  -> {position}"
        )

    def getPosition(self, code: str) -> Optional[StockPosition]:
        """code: 股票代碼
        透過 股票代碼 取得 StockPosition 資訊
        沒有此檔股票 則回傳 = None
        """
        return self.position.get(code, None)
    
    def getStockList(self) -> list:  #['HS', 'HC']
        list1=[]
        for pos in self.getAllPosition():
            list1.append(pos.code[0:2])
        return list(set(list1)) # 'set' for removing duplicated item.

#================================== classs 2: clsTrade ===========================
note ='''
    [Trade(
    contract=Contract(security_type=<SecurityType.Future: 'FUT'>, exchange=<Exchange.TAIFEX: 'TAIFEX'>, code='CCFL2'), 
    order=Order(action=<Action.Buy: 'Buy'>, price=41.0, quantity=2, id='2103b318', seqno='430119', ordno='tn019', account=Account(account_type=<AccountType.Future: 'F'>, 
        person_id='J120420374', broker_id='F002000', account_id='1641626', signed=True), price_type=<StockPriceType.LMT: 'LMT'>, order_type=<FuturesOrderType.ROD: 'ROD'>, 
        octype=<FuturesOCType.Cover: 'Cover'>), status=OrderStatus(id='2103b318', 
    status=<Status.Submitted: 'Submitted'>, status_code='0000', web_id='I', order_datetime=datetime.datetime(2022, 12, 15, 8, 43, 9), modified_price=41.0, deals=[]))]
    
'''

@dataclass
class clsTrade:
    code: str
    action: Action
    price: int
    quantity: int
    status: str

class TradeAid:
    def __init__(self, api_: sj.Shioaji):
        self.api = api_
        self.trades: List[clsTrade] = []

    def createFromServer(self):
        #從 api.list_trades() 建立 Trade 資訊
        self.api.update_status()
        all_trades = self.api.list_trades()
  
        self.trades=[]
        for tra in all_trades:
            if tra.contract.security_type == 'FUT':
                trade = clsTrade(
                    code= tra.contract.code,
                    action= tra.order.action,
                    quantity= int(tra.order.quantity),
                    price= float(tra.order.price),
                    status= tra.status.status 
            )
            self.trades.append(trade)
            
    def getAllTrade(self) -> List[clsTrade]:
        return self.trades
    
    def getTrade_OneFuture(self, strFutureCode) -> List[clsTrade]: 
        #strFutureCode: 'HSFL2' -> ['HSFL2', 'HSFL2', 'HSFL2']
        list1=[]
        for tra in self.getAllTrade():
            if tra.code==strFutureCode:
                list1.append(tra)
        return list1    
    def getTradeQty(self,strCode)-> int:
        intQty=0
        for tra in self.getTrade_OneFuture(strCode):
            if tra.status in ['PendingSubmit', 'PreSubmitted', 'Submitted'] :
                if tra.action==Action.Buy :
                    intQty += tra.quantity
                elif tra.action==Action.Sell :
                    intQty -= tra.quantity
        return intQty
    
    def AddTrade(self, strCode:str, objAction:Action , floPrice:float, intCloseQty:int, strStatus: str):
        tra = clsTrade(strCode, objAction , floPrice, intCloseQty, strStatus)
        self.trades.append(tra)
        
    def GetFutureCost(self, floPrice):
         return FEE*2 + (floPrice * 2000* 0.00002)
        
#==============================================================
#                     Function Defined
#==============================================================
def SetDfValue(df: pd.core.frame.DataFrame, intFutIndex:int, strField:str, intMonth:int, floValue:float):
    df.iloc[intFutIndex, list(df.columns).index(strField)][intMonth]= float(floValue)

def GetDfValue(df: pd.core.frame.DataFrame, intFutIndex:int, strField:str, intMonth:int):
    floValue = df.iloc[intFutIndex, list(df.columns).index(strField)][intMonth] 
    return floValue
    
def is_trading_time():
    """檢查當前是否為交易時段
    
    Returns:
        bool: True=交易時段, False=非交易時段
    
    台灣期貨交易時段：
    - 日盤: 08:45-13:45
    - 夜盤: 15:00-05:00 (次日)
    """
    from datetime import datetime, time
    now = datetime.now().time()
    
    # 日盤: 08:45-13:45
    if time(8, 45) <= now <= time(13, 45):
        return True
    
    # 夜盤: 15:00-05:00 (次日)
    if now >= time(15, 0) or now <= time(5, 0):
        return True
    
    return False

def pprint(strMsg: str):
    if(g_bolLogOn):
        logger.debug(strMsg)
    else:
        print(strMsg)

def GetFutureCode(strCode:str): #strCode: 'HS' -> '宏達電'
    df=pd.read_excel('Stock_Code.xlsx')
    if len(df[df['FutureCode']==strCode]) >0:
        strName=df[ df['FutureCode']==strCode ]['Name'].values[0]
    elif (strCode=='NA'):
        #解決奇怪的現象
        strName='穩懋'
    else:
        strName=''
    return strName    


# Stock order
def PlaceOrder_Stock(contract_stock: sj.contracts.Stock, objAction: Action, floPrice:float, intQty:int ):
    order1 = api.Order(
        action = objAction,
        price=floPrice,
        quantity=intQty,
        price_type=sj.constant.StockPriceType.LMT,
        order_type=sj.constant.OrderType.ROD, 
        octype=sj.constant.FuturesOCType.Auto,
        account=api.stock_account
    )

    trade = api.place_order(contract_stock, order1)
    

# Futures order
# Return: status (ex: 'Submitted', 'PendingSubmit' ...)
def PlaceOrder_Future(contract_fut: sj.contracts.Future, objAction: Action, floPrice:float, intQty:int ): 
# =============================================================================
# PendingSubmit: 傳送中
# PreSubmitted: 預約單
# Submitted: 傳送成功
# Failed: 失敗
# Cancelled: 已刪除
# Filled: 完全成交
# Filling: 部分成交
# =============================================================================
    '''
    contract=Stock(exchange=<Exchange.TSE: 'TSE'>, code='2890', symbol='TSE2890', name='永豐金', category='17', unit=1000, limit_up=15.2, limit_down=12.5, reference=13.85, update_date='2021/09/24', day_trade=<DayTrade.Yes: 'Yes'>) 
    order=Order(action=<Action.Buy: 'Buy'>, price=13.8, quantity=1, id='ca6171d5', seqno='092803', ordno='00000', account=Account(account_type=<AccountType.Stock: 'S'>, person_id='PAPIUSER06', broker_id='9A95', account_id='0506701', signed=True), price_type=<StockPriceType.LMT: 'LMT'>, order_type=<FuturesOrderType.ROD: 'ROD'>) 
    status=OrderStatus(id='ca6171d5', status=<Status.PendingSubmit: 'PendingSubmit'>, status_code='0', order_datetime=datetime.datetime(2021, 9, 26, 17, 54, 14), deals=[])
    '''
    order1 = api.Order(
        action = objAction,
        price=floPrice,
        quantity=intQty,
        price_type=sj.constant.StockPriceType.LMT,
        order_type=sj.constant.OrderType.ROD, 
        octype=sj.constant.FuturesOCType.Auto,
        account=api.futopt_account
    )
    trade = api.place_order(contract_fut, order1)
    strStatus=''
    for t in trade:
        if t[0]== 'status':
            strStatus = (t[1].status)
    
    # 發送下單通知
    action_str = "買進" if objAction == Action.Buy else "賣出"
    if strStatus in ['PendingSubmit', 'Submitted']:
        notifier.notify_order_success(
            contract_code=contract_fut.code,
            action=action_str,
            price=floPrice,
            quantity=intQty
        )
    elif strStatus == 'Failed':
        notifier.notify_order_failed(
            contract_code=contract_fut.code,
            action=action_str,
            error=strStatus
        )
    
    return strStatus

# Futures Combo Order (組合單) - 確保兩邊同時成交
# 防止部分成交風險，建倉時同時買近月+賣遠月
def PlaceOrder_FutureCombo(contract1: sj.contracts.Future, action1: Action, price1: float,
                           contract2: sj.contracts.Future, action2: Action, price2: float,
                           intQty: int):
    """
    下組合單：同時下兩個期貨合約，確保兩邊同時成交
    用於建倉時避免單邊曝險
    
    參數:
        contract1: 第一個合約 (通常是遠月)
        action1: 第一個動作 (Sell)
        price1: 第一個價格
        contract2: 第二個合約 (通常是近月)
        action2: 第二個動作 (Buy)
        price2: 第二個價格
        intQty: 數量
    
    返回: (status1, status2, success)
    """
    try:
        # 計算價差 (近月 - 遠月)
        spread_price = price2 - price1
        
        order1 = api.Order(
            action=action1,
            price=price1,
            quantity=intQty,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            octype=sj.constant.FuturesOCType.Auto,
            account=api.futopt_account
        )
        
        order2 = api.Order(
            action=action2,
            price=price2,
            quantity=intQty,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            octype=sj.constant.FuturesOCType.Auto,
            account=api.futopt_account
        )
        
        pprint(f"\n★ 使用組合單建倉 - 確保兩邊同時成交")
        pprint(f"  遠月: {contract1.code} {action1} {price1} x{intQty}")
        pprint(f"  近月: {contract2.code} {action2} {price2} x{intQty}")
        pprint(f"  價差: {spread_price:.2f} 元 (逆價差套利)")
        
        # 同時下單
        trade1 = api.place_order(contract1, order1)
        trade2 = api.place_order(contract2, order2)
        
        # 獲取狀態
        status1 = ''
        status2 = ''
        
        for t in trade1:
            if t[0] == 'status':
                status1 = t[1].status
                
        for t in trade2:
            if t[0] == 'status':
                status2 = t[1].status
        
        success = (status1 == 'PendingSubmit' or status1 == 'Submitted') and \
                  (status2 == 'PendingSubmit' or status2 == 'Submitted')
        
        if success:
            pprint(f"  ✓ 組合單建倉成功: {status1} / {status2}")
            notifier.notify_order_success(
                contract_code=f"{contract1.code}/{contract2.code}",
                action="組合單建倉",
                price=spread_price,
                quantity=intQty
            )
        else:
            pprint(f"  ✗ 組合單建倉失敗: {status1} / {status2}")
            pprint(f"  ⚠️  警告: 可能出現單邊曝險，請手動檢查持倉")
            notifier.notify_combo_order_failed(
                near_code=contract2.code,
                far_code=contract1.code
            )
        
        return (status1, status2, success)
        
    except Exception as e:
        pprint(f"  ✗ 組合單建倉異常: {e}")
        return ('Failed', 'Failed', False)

# Cancel order
# api.cancel_order(trade)

# 修改order價格
# api.update_order(trade=trade, price=410)

# qty是指要減少的數量
# api.update_order(trade=trade, qty=1)


#==============================================================


#------- 1. Create objPos & objTrade
#------- 2.Create dfBidAsk  

# 建立 PositionAid
objPos = PositionAid(api) # 自動接手 SJ 主動回報 並處理 成交資訊
objPos.createFromServer() # 從 api list_position 損益建立 Position 資訊

# 建立 TradeAid
objTrade = TradeAid(api)
objTrade.createFromServer()

FutureNameList = ['']* len(FutureList)
contract_1 = ['']* len(FutureList)
contract_2 = ['']* len(FutureList)
lstBid_price =[0]* len(FutureList)
lstBid_volume =[0]* len(FutureList)
lstAsk_price =[0]* len(FutureList)
lstAsk_volume =[0]* len(FutureList)

lstMatchTime =['']* len(FutureList)

print("\n正在載入期貨合約...")
valid_indices = []  # 記錄有效的合約索引

for i in range(0, len(FutureList)):
    strCode = FutureList[i]
    
    try:
        # 檢查合約是否存在
        contract_near = api.Contracts.Futures.get(strCode + NEAR_MON)
        contract_far = api.Contracts.Futures.get(strCode + FAR_MON)
        
        if contract_near is None:
            print(f"  ⚠️  找不到合約: {strCode}{NEAR_MON}")
            continue
        if contract_far is None:
            print(f"  ⚠️  找不到合約: {strCode}{FAR_MON}")
            continue
            
        # 合約存在，載入資料
        FutureNameList[i] = GetFutureCode(strCode)[0:3]
        contract_1[i] = contract_near
        contract_2[i] = contract_far
        
        lstBid_price[i] = [0, 0]  #= [mon1, mon2]
        lstBid_volume[i] = [0, 0]
        lstAsk_price[i] = [0, 0]
        lstAsk_volume[i] = [0, 0]
        
        valid_indices.append(i)
        print(f"  ✓ {strCode} - {FutureNameList[i]} ({contract_near.code}, {contract_far.code})")
        
    except Exception as e:
        print(f"  ✗ 載入 {strCode} 時發生錯誤: {e}")
        continue

if not valid_indices:
    print("\n❌ 沒有找到任何有效的期貨合約！")
    print("請檢查：")
    print("1. NEAR_MON 和 FAR_MON 設定是否正確")
    print("2. 期貨代碼是否正確")
    print("3. 合約是否已過期")
    exit(1)

print(f"\n成功載入 {len(valid_indices)}/{len(FutureList)} 個期貨合約\n")

dictBidAsk = {'id': FutureList , 'name': FutureNameList, 'bid_price': lstBid_price , 'bid_volume': lstBid_volume , 'ask_price': lstAsk_price, 'ask_volume': lstAsk_volume}
dfBidAsk = pd.DataFrame(dictBidAsk)    
  

def MyStrategy_New(bidask:BidAskFOPv1):
    #pprint('.', end='')
    #global g_count
    #pprint('My=' + str(g_count))
    
    now = datetime.now()  # 2021-02-18 15:41:50.350467
    bid_price_0= bidask['bid_price'][0]
    bid_volume_0= bidask['bid_volume'][0]
    ask_price_0= bidask['ask_price'][0]
    ask_volume_0= bidask['ask_volume'][0]
    strCode = bidask['code']
    
    # 檢查是否為監控的期貨
    try:
        idxFuture = FutureList.index(strCode[0:2])
    except ValueError:
        return  # 非監控標的，跳過
           
    if strCode[2:5]== NEAR_MON: # 2026-01 (近月)
        intMonthIndex = 0
    elif strCode[2:5]== FAR_MON: # 2026-02 (遠月)
        intMonthIndex = 1
    else:
        intMonthIndex = -1    
        pprint('####Note :intMonthIndex = -1' )
 
    SetDfValue(dfBidAsk, idxFuture, 'bid_price', intMonthIndex, bid_price_0)
    SetDfValue(dfBidAsk, idxFuture, 'bid_volume', intMonthIndex, bid_volume_0)
    SetDfValue(dfBidAsk, idxFuture, 'ask_price', intMonthIndex, ask_price_0)
    SetDfValue(dfBidAsk, idxFuture, 'ask_volume', intMonthIndex, ask_volume_0)
    
    #pprint("@@@@@ Debug: " + strCode + " lstBid_price=" + str(lstBid_price[idxFuture][intMonthIndex]))

    bolPrintedLessOneMin = isinstance(lstMatchTime[idxFuture], datetime) and now < lstMatchTime[idxFuture] + timedelta(minutes=1) # Prevent transaction too fast,, change 1 transaction/min

    intBuyNear = GetDfValue(dfBidAsk, idxFuture, 'bid_price', 0)
    intBuyNear_vol = GetDfValue(dfBidAsk, idxFuture, 'bid_volume', 0)
    intBuyFar  = GetDfValue(dfBidAsk, idxFuture, 'bid_price', 1)
    intBuyFar_vol  = GetDfValue(dfBidAsk, idxFuture, 'bid_volume', 1)
    intSellNear = GetDfValue(dfBidAsk, idxFuture, 'ask_price', 0)
    intSellNear_vol = GetDfValue(dfBidAsk, idxFuture, 'ask_volume', 0)
    intSellFar = GetDfValue(dfBidAsk, idxFuture, 'ask_price', 1)
    intSellFar_vol = GetDfValue(dfBidAsk, idxFuture, 'ask_volume', 1)

    if (intBuyNear*intBuyFar*intSellNear*intSellFar)!=0 and (not bolPrintedLessOneMin): 
        if intBuyNear == intSellFar:
            pass
        elif intBuyNear > intSellFar:
            pprint(f'{now.strftime("%H:%M:%S")} {str(idxFuture+1).zfill(2)} . {FutureNameList[idxFuture].ljust(3)} $價差: \
                   {round(intBuyNear-intSellFar,2)} (1) {intBuyNear}/{intSellFar} @ {intBuyNear_vol}/{intSellFar_vol}  賣近 買遠 ' )
            lstMatchTime[idxFuture]=now

        elif intBuyFar >= intSellNear:
            # 計算價差
            price_diff = round(intBuyFar - intSellNear, 2)
            
            # 價差為0時不輸出也不下單
            if price_diff <= 0:
                return
            
            pprint(f'{now.strftime("%H:%M:%S")} {str(idxFuture+1).zfill(2)} . {FutureNameList[idxFuture].ljust(3)} $價差: \
                   {price_diff}   [2] {intBuyFar}/{intSellNear} @ {intBuyFar_vol}/{intSellNear_vol}  賣遠 買近 ' )
            lstMatchTime[idxFuture]=now

            # 檢查交易時段
            if not is_trading_time():
                pprint(f'{FutureNameList[idxFuture]} 非交易時段，暫停建倉')
                return
            
            # ========== 持倉限制檢查 ==========
            try:
                # 檢查總持倉
                current_positions = api.list_positions(api.futopt_account)
                total_position = sum(abs(pos.quantity) for pos in current_positions)
                
                if total_position >= MAX_TOTAL_POSITION:
                    logger.warning(f"{FutureNameList[idxFuture]} 已達總持倉上限 {MAX_TOTAL_POSITION} 口（當前: {total_position} 口）")
                    
                    # 通知節流：只在第一次達到上限時輸出和發送通知
                    limit_key = "總持倉上限"
                    if limit_key not in last_limit_notification:
                        pprint(f"{FutureNameList[idxFuture]} 已達總持倉上限 {MAX_TOTAL_POSITION} 口，不再建倉")
                        notifier.notify_position_limit_reached(
                            limit_type=limit_key,
                            current=total_position,
                            limit=MAX_TOTAL_POSITION
                        )
                        last_limit_notification[limit_key] = now
                    return
                
                # 檢查單一標的持倉
                contract_position = sum(
                    abs(pos.quantity) for pos in current_positions 
                    if pos.code.startswith(strCode[0:2])
                )
                
                if contract_position >= MAX_POSITION_PER_CONTRACT:
                    logger.warning(f"{FutureNameList[idxFuture]} 已達單一標的上限 {MAX_POSITION_PER_CONTRACT} 口（當前: {contract_position} 口）")
                    
                    # 通知節流：只在第一次達到上限時輸出和發送通知
                    limit_key = f"單一標的上限_{FutureNameList[idxFuture]}"
                    if limit_key not in last_limit_notification:
                        pprint(f"{FutureNameList[idxFuture]} 已達單一標的上限 {MAX_POSITION_PER_CONTRACT} 口，不再建倉")
                        notifier.notify_position_limit_reached(
                            limit_type=f"單一標的上限 ({FutureNameList[idxFuture]})",
                            current=contract_position,
                            limit=MAX_POSITION_PER_CONTRACT
                        )
                        last_limit_notification[limit_key] = now
                    return
                    
            except Exception as e:
                logger.error(f"持倉檢查失敗: {e}")
            
            # ========== Sell Far month, Buy near month
            intOnePairCost = (intSellNear + intBuyFar) * 2000 * 0.135 + objTrade.GetFutureCost(intSellNear + intBuyFar)
            
            # 除零保護
            if intOnePairCost <= 0:
                pprint(f'{FutureNameList[idxFuture]} 成本計算異常: {intOnePairCost}')
                return
            
            # 測試模式：跳過餘額檢查
            if g_bolTestMode:
                intHowManyPairCanBuy = 999  # 測試模式給予足夠的數量
                pprint(f'{FutureNameList[idxFuture]} [測試模式] 跳過餘額檢查')
            else:
                intHowManyPairCanBuy = objPos.balance_future // intOnePairCost
            
            if intHowManyPairCanBuy<1:
                pprint(f'{FutureNameList[idxFuture]} 餘額不足, 餘額: {objPos.balance_future} , 最少需要:{intOnePairCost}')
            else:
                # 限制單次下單數量
                intNewQty = min(intBuyFar_vol, intSellNear_vol, intHowManyPairCanBuy, MAX_SINGLE_ORDER)
                logger.info(f"ORDER - {FutureNameList[idxFuture]} 計算下單數量: 買量={intBuyFar_vol}, 賣量={intSellNear_vol}, 餘額可買={intHowManyPairCanBuy}, 限制={MAX_SINGLE_ORDER}, 最終={intNewQty}")   
                if  g_bolOrderOn and intNewQty>0 :
                    #當某個期貨有尚未成交的交易，就不再建倉
                    if objTrade.getTradeQty(strCode[0:2]+NEAR_MON)==0 and objTrade.getTradeQty(strCode[0:2]+FAR_MON)==0 : 
                        # 使用組合單建倉 - 確保兩邊同時成交
                        strStatus2, strStatus1, success = PlaceOrder_FutureCombo(
                            contract1=contract_2[idxFuture], action1=Action.Sell, price1=intBuyFar,
                            contract2=contract_1[idxFuture], action2=Action.Buy, price2=intSellNear,
                            intQty=intNewQty
                        )
                        
                        if not success:
                            pprint(f"  ⚠️  組合單建倉失敗，放棄此次建倉")
                            return  # 退出函數，等待下次機會
                        
                        pprint(f'[遠月] {contract_2[idxFuture].code} , {Action.Sell} , {intBuyFar} , {intNewQty}, {strStatus2}')
                        pprint(f'[近月] {contract_1[idxFuture].code} , {Action.Buy} , {intSellNear} , {intNewQty}, {strStatus1}')

                        #Update Balance
                        if strStatus2=='PendingSubmit' or strStatus2=='Submitted':
                            objPos.balance_future -= intNewQty * intBuyFar * 2000 * 0.135 + objTrade.GetFutureCost(intBuyFar)
                            objTrade.AddTrade(contract_2[idxFuture].code,Action.Sell, intBuyFar , intNewQty, strStatus2)
                        if strStatus1=='PendingSubmit' or strStatus1=='Submitted':
                            objPos.balance_future -= intNewQty * intSellNear * 2000 * 0.135 + objTrade.GetFutureCost(intSellNear)
                            objTrade.AddTrade(contract_1[idxFuture].code,Action.Buy, intSellNear , intNewQty, strStatus1)
    #---- end of def MyStrategy_New

@api.on_bidask_fop_v1()
def quote_callback(exchange:Exchange, bidask:BidAskFOPv1):
    #pprint(f"Exchange: {exchange}, BidAsk: {bidask}")
    MyStrategy_New(bidask)

#@api.on_tick_fop_v1()
#def quote_callback(exchange:Exchange, tick:TickFOPv1):
    #pprint(f"Exchange: {exchange}, Tick: {tick}")
    #pass

for j in range(0, len(FutureList)):
    # 只訂閱有效的合約
    if contract_1[j] and contract_2[j]:
        try:
            api.quote.subscribe(
                contract=contract_1[j], 
                quote_type = "bidask",
                version = sj.constant.QuoteVersion.v1
            )
            api.quote.subscribe(
                contract=contract_2[j], 
                quote_type = "bidask",
                version = sj.constant.QuoteVersion.v1
            )
            print(f"已訂閱: {contract_1[j].code}, {contract_2[j].code}")
        except Exception as e:
            print(f"訂閱 {FutureList[j]} 失敗: {e}")

print("\n✓ 所有訂閱已完成，開始監聽報價...")
print("停止方法:")
print("  1. 按 Ctrl+C")
print("  2. 關閉終端視窗")
print("  3. 執行 stop_program.ps1")
print()

# 全域停止標誌
running = True

# 信號處理函數
def signal_handler(sig, frame):
    global running
    print("\n\n⚠️  收到停止信號，正在關閉程式...")
    notifier.notify_program_stop("建倉機器人 (SinoPac-new)", "使用者手動停止")
    running = False
    try:
        api.logout()
        print("✓ 已登出")
    except:
        pass
    print("程式已停止")
    sys.exit(0)

# 註冊信號處理
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, signal_handler)

# ========== 斷線重連機制 ==========
def check_connection():
    """檢查API連線狀態"""
    try:
        # 嘗試獲取帳戶資訊來確認連線
        api.margin(api.futopt_account)
        return True
    except Exception as e:
        logger.error(f"連線檢查失敗: {e}")
        return False

def reconnect():
    """重新連線"""
    global running
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.warning(f"嘗試重新連線 ({attempt}/{max_retries})...")
            print(f"\n⚠️  嘗試重新連線 ({attempt}/{max_retries})...")
            
            # 重新登入
            api.login(
                api_key=API_KEY,
                secret_key=SECRET_KEY,
                contracts_cb=lambda security_type: None
            )
            
            # 重新啟動憑證
            api.activate_ca(ca_path=CA_PATH, ca_passwd=CA_PASSWORD)
            
            # 重新訂閱報價
            for j in range(0, len(FutureList)):
                if contract_1[j] and contract_2[j]:
                    api.quote.subscribe(contract=contract_1[j], quote_type="bidask", version=sj.constant.QuoteVersion.v1)
                    api.quote.subscribe(contract=contract_2[j], quote_type="bidask", version=sj.constant.QuoteVersion.v1)
            
            logger.info("✓ 重新連線成功")
            print("✓ 重新連線成功\n")
            notifier.notify_reconnect_success()
            return True
            
        except Exception as e:
            logger.error(f"重新連線失敗 ({attempt}/{max_retries}): {e}")
            print(f"✗ 重新連線失敗: {e}")
            if attempt < max_retries:
                import time
                time.sleep(5)  # 等待5秒後重試
    
    logger.critical("無法重新連線，程式將停止")
    print("\n❌ 無法重新連線，程式停止")
    notifier.notify_reconnect_failed()
    notifier.notify_program_stop("建倉機器人 (SinoPac-new)", "無法重新連線")
    running = False
    return False

# 保持程式運行，使用輪詢而非 Event().wait()
print("程式運行中，監聽報價...\n")
logger.info("開始監聽報價")

last_connection_check = datetime.now()
connection_check_interval = 60  # 每60秒檢查一次連線

try:
    import time
    while running:
        time.sleep(1)  # 每秒檢查一次
        
        # 定期檢查連線
        if (datetime.now() - last_connection_check).seconds >= connection_check_interval:
            if not check_connection():
                logger.warning("⚠️  偵測到連線中斷")
                print("\n⚠️  偵測到連線中斷，嘗試重新連線...")
                notifier.notify_connection_lost()
                reconnect()
            last_connection_check = datetime.now()
            
except KeyboardInterrupt:
    signal_handler(None, None)

#================================= Debuggin ========================
if(0):
    objPos.position
    objPos.AdjustQty('RAFL2', 1)
