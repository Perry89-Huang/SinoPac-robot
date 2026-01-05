
###                              平倉機器人

# ------- Dynamic Configuration
GROUP= 1

g_bolOrderOn= True
g_bolLogOn=False

if GROUP==1:
    # 成交量排行 group
    # '長榮航','宏達電','華新  ','台積電','友達  ','欣興  ','鴻海  ','元太  ','國泰金','長榮  ','聯電  '
    FutureList = ['HS','HC','CS','CD','CH','IR','DH','NV','CK','CZ','CC']
elif GROUP==2:
    # Price 100~200 group
    # '景碩  ','南電  ','智原  ','智擎  ','技嘉  ','中美晶','可成  ', '奇鋐  ','穩懋  ','聯亞  ','臻鼎  ','微星  ','精材  '
    FutureList = ['IX','QS','IP','PC','GH','NO','GX', 'RA','NA','OT','LU','GI','QL']
    
import shioaji as sj

NEAR_MON = 'FL2'
FAR_MON = 'FA3'

FEE=25


# ---- Formal Login
api = sj.Shioaji(simulation=False)
accounts = api.login(
    "J120420374", 
    "celia5818"
)

api.activate_ca(
    ca_path="C:/ekey/551/J120420374/S/Sinopac.pfx",
    #ca_path="c:/eleader/ca/Sinopac.pfx",
    ca_passwd="celia5818",
    person_id="J120420374",
)


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

logger.add("PerryLogs\Close_{time}.log", level="TRACE", rotation="200 MB")

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


FutureList = objPos.getStockList() #['HS', 'HC']

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

    idxFuture = FutureList.index(strCode[0:2])

           
    if strCode[2:5]== NEAR_MON: #2022-12
        intMonthIndex = 0
    elif strCode[2:5]== FAR_MON: #2023-01
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
                    intCloseQty = min(intBuyNear_vol, min(posOwned.quantity-intTradeSubmit,0), intCloseQty)   
                elif posOwned.action==Action.Sell: # Need to buy
                    objAction1=Action.Buy
                    floPrice1=intSellNear
                    intCostGap += (posOwned.price - intSellNear ) 
                    intCloseQty = min(intSellNear_vol, min(posOwned.quantity+intTradeSubmit,0), intCloseQty) 
            elif posOwned.code.find(FAR_MON)>=0:
                cont2 = contract_2[idxFuture]
                objAction2=posOwned.action
                if posOwned.action==Action.Buy: # Need to sell
                    objAction2=Action.Sell
                    floPrice2=intBuyFar
                    intCostGap += (intBuyFar - posOwned.price) 
                    intCloseQty = min(intBuyFar_vol, min(posOwned.quantity-intTradeSubmit,0), intCloseQty)
                elif posOwned.action==Action.Sell: # Need to buy
                    objAction2=Action.Buy
                    floPrice2=intSellFar
                    intCostGap += (posOwned.price - intSellFar ) 
                    intCloseQty = min(intSellFar_vol, min(posOwned.quantity+intTradeSubmit,0), intCloseQty)   
        #==end for loop
        
        #pprint(f'=={strCode} , cost gap={round(intCostGap,2)} , CloseQty={intCloseQty}')
        #pprint(f'        cont1={objAction1},{floPrice1}')
        #pprint(f'          cont2={objAction2},{floPrice2} ')

        #if (intCostGap>= -2 and intCloseQty>0): //For testing only
        if (intCostGap>= 0.1 and intCloseQty>0):
            strStatus1='Perry'  
            strStatus2='Perry' 

            # Place Order
            if g_bolOrderOn:
                if(cont2 is not None):
                    strStatus2= PlaceOrder_Future(cont2,objAction2,floPrice2,intCloseQty) # Sell/Buy Far Month, 'PendingSubmit'
                #time.sleep(1.5)
                if(cont1 is not None):
                    strStatus1= PlaceOrder_Future(cont1,objAction1,floPrice1,intCloseQty) # Buy/Sell Near Month, 'PendingSubmit'
            else: # for OderOn false tseting purpose
                strStatus2='PendingSubmit'
                strStatus1='PendingSubmit'

            if(cont2 is not None):
                #objPos.AdjustQty(cont2.code, intCloseQty)
                objTrade.AddTrade(cont2.code,objAction2, floPrice2 , intCloseQty, strStatus2)
                pprint(f'PlaceOrder_Future {cont2.code} , {objAction2} , {floPrice2} , {intCloseQty} , {strStatus2}')
            if(cont1 is not None):
                #objPos.AdjustQty(cont1.code, intCloseQty)
                objTrade.AddTrade(cont1.code,objAction1, floPrice1 , intCloseQty, strStatus1)
                pprint(f'PlaceOrder_Future {cont1.code} , {objAction1} , {floPrice1} , {intCloseQty} , {strStatus1}')

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

for j in range(0, len(FutureList)):
    api.quote.subscribe(
        contract=contract_1[j], 
        quote_type = "bidask",
        version = sj.constant.QuoteVersion.v1 # or 'v1'
    )
    api.quote.subscribe(
        contract=contract_2[j], 
        quote_type = "bidask",
        version = sj.constant.QuoteVersion.v1 # or 'v1'
    )

#Event().wait()

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
    
