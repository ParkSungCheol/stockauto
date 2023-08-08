import backtrader as bt
from datetime import datetime
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr
 
 
class BOLLStrat(bt.Strategy):
        
 
    def __init__(self):
        global UpI
        UpI = []
        global DoI
        DoI = [] 
        global TR_l
        TR_l = []
        global i
        i = 0

        global Pos_score
        global Neg_score

        if self.data.high[0] == 0 :
            self.data.high[0] = self.data.close[0]
        if self.data.low[0] == 0 :
            self.data.low[0] = self.data.close[0]
        if self.data.high[0]%10 >= 5 :
            self.data.high[0] = round((self.data.high[0]+5)/10,0)*10
        if self.data.low[0]%10 >= 5 :
            self.data.low[0] = round((self.data.low[0]+5)/10,0)*10
        if self.data.close[0]%10 >= 5 :
            self.data.close[0] = round((self.data.close[0]+5)/10,0)*10
        
        global vol_diff_flag
        vol_diff_flag = 0
 
    def next(self):
        global i

        global Pos_score
        global Neg_score
        Pos_score = 0
        Neg_score = 0

        if self.data.high[0] == 0 :
            self.data.high[0] = self.data.close[0]
        if self.data.low[0] == 0 :
            self.data.low[0] = self.data.close[0]
        if self.data.high[0]%10 >= 5 :
            self.data.high[0] = round((self.data.high[0]+5)/10,0)*10
        if self.data.low[0]%10 >= 5 :
            self.data.low[0] = round((self.data.low[0]+5)/10,0)*10
        if self.data.close[0]%10 >= 5 :
            self.data.close[0] = round((self.data.close[0]+5)/10,0)*10

        global vol_diff_flag

        if self.data.volume[0] == 0 :
            vol_diff_flag = vol_diff_flag + 1

        if vol_diff_flag == 0 :
            self.data.volume[0] = self.data.volume[0] * 50

        if i == 0 :
            UpI.append(0)
            DoI.append(0)
        else :
            UpMove = self.datas[0].high[0] - self.datas[0].high[-1]
            DoMove = self.datas[0].low[-1] - self.datas[0].low[0]
            if UpMove > DoMove and UpMove > 0 : 
                UpD = UpMove 
            else : 
                UpD = 0 
            UpI.append(UpD) 
            if DoMove > UpMove and DoMove > 0 :
                DoD = DoMove 
            else : 
                DoD = 0
            DoI.append(DoD) 

        if i == 0 :
            TR_l.append(0)
        else :
            TR = max(self.data.high[0], self.data.close[-1]) - min(self.data.low[0], self.data.close[-1])
            #print(self.data.high[0], i, TR)
            TR_l.append(TR)
        

        TR_s = pd.Series(TR_l) 
        ATR = TR_s.ewm(com=12).mean() 
        UpI2 = pd.Series(UpI) 
        DoI2 = pd.Series(DoI) 
        PosDI = pd.Series(UpI2.ewm(com=12, min_periods=1).mean()*100 / ATR)
        NegDI = pd.Series(DoI2.ewm(com=12, min_periods=1).mean()*100 / ATR) 
        ADX = pd.Series((abs(PosDI - NegDI)*100 / (PosDI + NegDI)).ewm(com=12, min_periods=1).mean())

        
        
        if i == 0 :

            
            
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 1
                #print(i)
                #print(self.data.close[0])

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 35):
                Neg_score = Neg_score + 1
                #print(self.data.close[0])
            
        else :
            
            #print(NegDI.iloc[-1])
            
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 1
                #print(i)
                #print(self.data.close[0])

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 35):
                Neg_score = Neg_score + 1
                #print(self.data.close[0])

        orders = self.broker.get_orders_open()

        if orders:
            for order in orders:
                self.broker.cancel(order)
 
        if not self.position:
            if Pos_score >= 1 :
                self.buy()
                #print(self.data.close[0])

        else :
            if Pos_score >= 1 :
                self.buy()
                #print(self.data.close[0])

            elif Neg_score >= 1 :
                self.sell()
                #print(self.data.close[0])
            

        i = i + 1

class PercentReverter(bt.Sizer):

    params = (
        ('percents', 100),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = ((position.size * data.close[0] + cash) / data.close[0]) * (self.params.percents / 100)
            if (isbuy == True) & ((size + position.size) * data.close[0] > cash) :
                size = cash / data.close[0]
            if (isbuy==False) :
                size = size * 100
                if (size > position.size) :
                    size = position.size
        return math.floor(size)
 
cerebro = bt.Cerebro()
 
#data = bt.feeds.YahooFinanceData(dataname = '005930.KS', fromdate = datetime(2017,1,1), todate = datetime(2020,10,1))
data = bt.feeds.PandasData(dataname=fdr.DataReader(symbol='010140', start='2011-07-03', end='2021-07-03'))
cerebro.adddata(data)
cerebro.addstrategy(BOLLStrat)
cerebro.broker.setcash(100000000)
cerebro.addsizer(PercentReverter)
#cerebro.broker.setcommission(commission=0.005)
init_cash = cerebro.broker.getvalue()
cerebro.run()
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",round(float((final_cash-init_cash)/float(init_cash)*100),2), "%")
cerebro.plot()