
###                              平倉機器人
# Shioaji API: https://sinotrade.github.io

# ------- Dynamic Configuration
GROUP = 1

g_bolTestMode = True  # 測試模式：True=不檢查餘額, False=正常檢查餘額
g_bolOrderOn = True
g_bolLogOn = False

if GROUP == 1:
    # 成交量排行 group
    # '長榮航','宏達電','華新  ','台積電','友達  ','欣興  ','鴻海  ','元太  ','國泰金','長榮  ','聯電  '
    FutureList = ['HS','HC','CS','CD','CH','IR','DH','NV','CK','CZ','CC']
elif GROUP == 2:
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
MAX_CLOSE_QUANTITY = 10  # 單次平倉最多10口

print(f"\n⚙️  風險控制參數：")
print(f"  單次平倉上限: {MAX_CLOSE_QUANTITY} 口")
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
    print("\n請到 https://www.sinotrade.com.tw/newweb/PythonAPIKey/ 申請")
    raise ValueError("請先設定 API_KEY 和 SECRET_KEY")

# 驗證 Key 格式
invalid_chars_api = set(API_KEY) & {'0', 'O', 'I', 'l'}
invalid_chars_secret = set(SECRET_KEY) & {'0', 'O', 'I', 'l'}

if invalid_chars_api or invalid_chars_secret:
    print("❌ API Key 格式錯誤，包含無效字符（0, O, I, l）")
    raise ValueError("API Key 格式錯誤")

api = sj.Shioaji(simulation=g_bolTestMode)  # 根據測試模式自動切換

try:
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
    notifier.notify_program_start("平倉機器人 (SinoPac-close)")
except Exception as e:
    print(f"\n✗ 登入失敗: {e}")
    print("\n請確認：")
    print("1. API Key 和 Secret Key 是否正確")
    print("2. API Key 權限已啟用（Market/Data、Account、Trading）")
    print("3. 生產環境權限已開啟")
    raise

try:
    import os
    if not os.path.exists(CA_PATH):
        print(f"✗ 憑證檔案不存在: {CA_PATH}")
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
    if "Ca Password Incorrect" in error_msg:
        print("\n憑證密碼錯誤！")
        print(f"目前設定的密碼: '{CA_PASSWORD}'")
        print("請確認憑證密碼是否正確")
    print("\n⚠️  警告：憑證未啟動，部分功能可能無法使用\n")
except Exception as e:
    print(f"\n✗ 憑證啟動失敗: {e}")
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
    "logs/closing_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天午夜輪換
    retention="30 days",  # 保留30天
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    encoding="utf-8"
)

# 錯誤日誌（永久保存）
logger.add(
    "logs/errors.log",
    rotation="10 MB",
    retention=None,  # 永久保存
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {file}:{line} | {message}",
    encoding="utf-8"
)

# 平倉日誌（重要操作）
logger.add(
    "logs/closings_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",  # 保留90天
    level="INFO",
    filter=lambda record: "CLOSE" in record["message"] or "平倉" in record["message"],
    format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    encoding="utf-8"
)

# 保留舊日誌（兼容性）
logger.add("PerryLogs/Close_{time}.log", level="TRACE", rotation="200 MB")

print("✓ 日誌系統已配置")
print("  - 平倉日誌: logs/closing_YYYY-MM-DD.log (保留30天)")
print("  - 錯誤日誌: logs/errors.log (永久保存)")
print("  - 平倉記錄: logs/closings_YYYY-MM-DD.log (保留90天)\n")

logger.info("=" * 60)
logger.info("程式啟動 - 平倉機器人")
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
        #--- strFutureCode: 'HSFL2' -> ['HSFL2', 'HSFL2', 'HSFL2']
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
        order_type=sj.constant.FuturesOrderType.ROD, 
        octype=sj.constant.FuturesOCType.Auto,
        account=api.stock_account
    )

    trade = api.place_order(contract_stock, order1)
    

# Futures order
#   Return: status (ex: 'Submitted', 'PendingSubmit' ...)
def PlaceOrder_Future(contract_fut: sj.contracts.Future, objAction: Action, floPrice:float, intQty:int ): 
# =============================================================================
# PendingSubmit: 傳送中
# PreSubmitted: 預約單
# Submitted: 傳送成功
# Failed: 失敗
# Cancelled: 已刪除
# Filled: 完全成交
# Filling: 部分成交
# =============================================================================    '''
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
        order_type=sj.constant.FuturesOrderType.ROD, 
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
            action=f"{action_str}(平倉)",
            price=floPrice,
            quantity=intQty
        )
    elif strStatus == 'Failed':
        notifier.notify_order_failed(
            contract_code=contract_fut.code,
            action=f"{action_str}(平倉)",
            error=strStatus
        )
    
    return strStatus

# Cancel order
# api.cancel_order(trade)

# 修改order價格
# api.update_order(trade=trade, price=410)

# qty是指要減少的數量
# api.update_order(trade=trade, qty=1)

#==============================================================

# 建立 PositionAid
objPos = PositionAid(api) # 自動接手 SJ 主動回報 並處理 成交資訊
objPos.createFromServer()   # 從 api list_position 損益建立 Position 資訊

# 建立 TradeAid
objTrade = TradeAid(api)
objTrade.createFromServer()

# 取得目前持有的股票期貨列表
existing_positions = objPos.getStockList() #['HS', 'HC']

# 如果有持倉，只監控有持倉的期貨；如果沒有持倉，使用預設的 FutureList
if len(existing_positions) > 0:
    FutureList = existing_positions
    print(f"\n✓ 偵測到持倉，監控 {len(FutureList)} 檔期貨: {FutureList}")
else:
    print(f"\n⚠️  目前無持倉，使用預設監控列表 (GROUP={GROUP}): {FutureList}")

FutureNameList = ['']* len(FutureList)
contract_1 = ['']* len(FutureList)
contract_2 = ['']* len(FutureList)
lstBid_price =[0]* len(FutureList)
lstBid_volume =[0]* len(FutureList)
lstAsk_price =[0]* len(FutureList)
lstAsk_volume =[0]* len(FutureList)

lstMatchTime =['']* len(FutureList)

for i in range(0, len(FutureList)):   
    strCode = FutureList[i]
    FutureNameList[i]=GetFutureCode(strCode)
    
    contract_1[i] = api.Contracts.Futures[strCode+ NEAR_MON ] #2022-12
    contract_2[i] = api.Contracts.Futures[strCode+ FAR_MON] #2023-01

    lstBid_price[i]= [0,0]  #= [mon1, mon2]
    lstBid_volume[i]=[0,0]
    lstAsk_price[i]=[0,0]
    lstAsk_volume[i]=[0,0]

dictBidAsk = {'id': FutureList , 'name': FutureNameList, 'bid_price': lstBid_price , 'bid_volume': lstBid_volume , 'ask_price': lstAsk_price, 'ask_volume': lstAsk_volume}
dfBidAsk = pd.DataFrame(dictBidAsk)    


def MyStrategy_Close(bidask:BidAskFOPv1):
    #pprint('.', end='')
  
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

    #if isinstance(lstMatchTime[idxFuture], datetime) and now < lstMatchTime[idxFuture] + timedelta(minutes=1):
    #    return

    intBuyNear = GetDfValue(dfBidAsk, idxFuture, 'bid_price', 0)
    intBuyNear_vol = GetDfValue(dfBidAsk, idxFuture, 'bid_volume', 0)
    intBuyFar  = GetDfValue(dfBidAsk, idxFuture, 'bid_price', 1)
    intBuyFar_vol  = GetDfValue(dfBidAsk, idxFuture, 'bid_volume', 1)
    intSellNear = GetDfValue(dfBidAsk, idxFuture, 'ask_price', 0)
    intSellNear_vol = GetDfValue(dfBidAsk, idxFuture, 'ask_volume', 0)
    intSellFar = GetDfValue(dfBidAsk, idxFuture, 'ask_price', 1)
    intSellFar_vol = GetDfValue(dfBidAsk, idxFuture, 'ask_volume', 1)

    listPosition_OneFut = objPos.getPosition_OneFuture(strCode[0:2])
    cont1=None
    cont2=None
    
    # ========== 持倉異常檢測 ==========
    # 檢測單邊持倉（只有近月或只有遠月，但沒有配對）
    if len(listPosition_OneFut) == 1:
        pos = listPosition_OneFut[0]
        # 檢查是否有對應的交易記錄
        if objTrade.getTradeQty(pos.code) == 0:  # 沒有交易記錄表示可能是單邊持倉
            alert_msg = f"⚠️ 檢測到單邊持倉異常: {pos.code} {pos.action} x{pos.quantity} @ {pos.price}"
            logger.warning(alert_msg)
            notifier.notify_position_alert(alert_msg)
    
    # Case 1: 目前收到BidAsk資訊的這檔期貨，有兩個不同月份的庫存
    # Case 2: 目前收到BidAsk資訊的這檔期貨，只有一個月份的庫存
    if ((len(listPosition_OneFut)==1 or len(listPosition_OneFut)==2) and intBuyNear*intBuyFar !=0) : 
        #如果有賺錢，就將兩口期貨平倉 
        intCostGap=0
        intCloseQty= 888 

        for posOwned in listPosition_OneFut: # List[StockPosition]= [ StockPosition('HSFL2') StockPosition('HSFA3') ] 
            intTradeSubmit = objTrade.getTradeQty(posOwned.code) # + means Buy, - means Sell
            #pprint(f'intTradeSubmit= {intTradeSubmit}')
            
            if posOwned.code.find(NEAR_MON)>=0:                
                cont1 = contract_1[idxFuture]
                if posOwned.action==Action.Buy: # Need to sell
                    objAction1= Action.Sell
                    floPrice1= intBuyNear
                    intCostGap += (intBuyNear - posOwned.price) 
                    intCloseQty = min(intBuyNear_vol, max(posOwned.quantity-intTradeSubmit, 0), intCloseQty)   
                elif posOwned.action==Action.Sell: # Need to buy
                    objAction1=Action.Buy
                    floPrice1=intSellNear
                    intCostGap += (posOwned.price - intSellNear ) 
                    intCloseQty = min(intSellNear_vol, max(posOwned.quantity+intTradeSubmit, 0), intCloseQty) 
            elif posOwned.code.find(FAR_MON)>=0:
                cont2 = contract_2[idxFuture]
                objAction2=posOwned.action
                if posOwned.action==Action.Buy: # Need to sell
                    objAction2=Action.Sell
                    floPrice2=intBuyFar
                    intCostGap += (intBuyFar - posOwned.price) 
                    intCloseQty = min(intBuyFar_vol, max(posOwned.quantity-intTradeSubmit, 0), intCloseQty)
                elif posOwned.action==Action.Sell: # Need to buy
                    objAction2=Action.Buy
                    floPrice2=intSellFar
                    intCostGap += (posOwned.price - intSellFar ) 
                    intCloseQty = min(intSellFar_vol, max(posOwned.quantity+intTradeSubmit, 0), intCloseQty)   
        #==end for loop
        
        #pprint(f'=={strCode} , cost gap={round(intCostGap,2)} , CloseQty={intCloseQty}')
        #pprint(f'        cont1={objAction1},{floPrice1}')
        #pprint(f'          cont2={objAction2},{floPrice2} ')

        #if (intCostGap>= -2 and intCloseQty>0): //For testing only
        if (intCostGap>= 0.1 and intCloseQty>0):
            # 檢查交易時段
            if not is_trading_time():
                pprint(f'{strCode[0:2]} 非交易時段，暫停平倉')
                return
            
            # 限制單次平倉數量
            intCloseQty = min(intCloseQty, MAX_CLOSE_QUANTITY)
            logger.info(f"CLOSE - {strCode[0:2]} 計算平倉數量: 成本價差={intCostGap}, 數量={intCloseQty} (限制:{MAX_CLOSE_QUANTITY})")
            
            strStatus1='Perry'  
            strStatus2='Perry' 

            # Place Orders - 平倉時分別下單
            if g_bolOrderOn:
                if cont1 is not None and cont2 is not None:
                    # 兩個合約都存在，分別下單平倉
                    strStatus2 = PlaceOrder_Future(cont2, objAction2, floPrice2, intCloseQty)
                    strStatus1 = PlaceOrder_Future(cont1, objAction1, floPrice1, intCloseQty)
                    
                    if strStatus1 not in ['PendingSubmit', 'Submitted'] or strStatus2 not in ['PendingSubmit', 'Submitted']:
                        pprint(f"  ⚠️  平倉下單異常: {strStatus1}/{strStatus2}")
                        
                elif cont2 is not None:
                    # 只有遠月合約
                    strStatus2 = PlaceOrder_Future(cont2, objAction2, floPrice2, intCloseQty)
                    pprint(f"  ⚠️  只平遠月合約 (近月不存在)")
                    
                elif cont1 is not None:
                    # 只有近月合約
                    strStatus1 = PlaceOrder_Future(cont1, objAction1, floPrice1, intCloseQty)
                    pprint(f"  ⚠️  只平近月合約 (遠月不存在)")
                    
            else: # for OrderOn false testing purpose
                strStatus2='PendingSubmit'
                strStatus1='PendingSubmit'

            if(cont2 is not None):
                #objPos.AdjustQty(cont2.code, intCloseQty)
                objTrade.AddTrade(cont2.code,objAction2, floPrice2 , intCloseQty, strStatus2)
                pprint(f'[遠月] {cont2.code} , {objAction2} , {floPrice2} , {intCloseQty} , {strStatus2}')
            if(cont1 is not None):
                #objPos.AdjustQty(cont1.code, intCloseQty)
                objTrade.AddTrade(cont1.code,objAction1, floPrice1 , intCloseQty, strStatus1)
                pprint(f'[近月] {cont1.code} , {objAction1} , {floPrice1} , {intCloseQty} , {strStatus1}')

            intTotalQty=0
            floFee=0

            if(cont2 is not None):
                intTotalQty+=intCloseQty
                floFee += objTrade.GetFutureCost(floPrice2)*intCloseQty
            if(cont1 is not None):
                intTotalQty+=intCloseQty
                floFee += objTrade.GetFutureCost(floPrice1)*intCloseQty

            intProfit = intCostGap * 2000 * intCloseQty - floFee
            print(f'  === Profit: {intProfit}')

@api.on_bidask_fop_v1()
def quote_callback(exchange:Exchange, bidask:BidAskFOPv1):
    #pprint(f"Exchange: {exchange}, BidAsk: {bidask}")
    MyStrategy_Close(bidask)

#@api.on_tick_fop_v1()
#def quote_callback(exchange:Exchange, tick:TickFOPv1):
    #pprint(f"Exchange: {exchange}, Tick: {tick}")
    #  pass

print(f"\n開始訂閱 {len(FutureList)} 檔期貨的報價...")
for j in range(0, len(FutureList)):
    # 訂閱近月合約
    result1 = api.quote.subscribe(
        contract=contract_1[j], 
        quote_type = "bidask",
        version = sj.constant.QuoteVersion.v1 # or 'v1'
    )
    print(f"  訂閱 {contract_1[j].code} ({FutureNameList[j]}{NEAR_MON})")
    
    # 訂閱遠月合約
    result2 = api.quote.subscribe(
        contract=contract_2[j], 
        quote_type = "bidask",
        version = sj.constant.QuoteVersion.v1 # or 'v1'
    )
    print(f"  訂閱 {contract_2[j].code} ({FutureNameList[j]}{FAR_MON})")

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
    notifier.notify_program_stop("平倉機器人 (SinoPac-close)", "使用者手動停止")
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
    notifier.notify_program_stop("平倉機器人 (SinoPac-close)", "無法重新連線")
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
    testCode1='RAFL2'
    testCode2='RAFA3'
    
    objPos.position
    objPos.AdjustQty(testCode1, 1)

    objTrade.trades
    
    strStat= PlaceOrder_Future(contract_1[0], Action.Sell, 114, 1)
    objTrade.AddTrade(testCode1, Action.Sell, 114 , 1, strStat)
    print(objTrade.trades, '\n')
    objTrade.getTradeQty(testCode1)
    
    objTrade.getTradeQty(testCode1)
    objTrade.getTradeQty(testCode2)
    
    objTrade.createFromServer()
    
