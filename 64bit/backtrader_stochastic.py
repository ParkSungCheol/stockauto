import backtrader as bt
from datetime import datetime
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr
 
 
class BOLLStrat(bt.Strategy):

        
 
    def __init__(self):

        global high
        high = []
        global low
        low = []
        global kdj_k
        kdj_k = []

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

        high.append(self.data.high[0])
        low.append(self.data.low[0])
        high_1 = pd.Series(high)
        low_1 = pd.Series(low)
        ndays_high = high_1.rolling(window=12, min_periods=1).max()
        ndays_low = low_1.rolling(window=12, min_periods=1).min()

        kdj_k.append(((self.data.close[0] - ndays_low.iloc[-1]) / (ndays_high.iloc[-1] - ndays_low.iloc[-1]))*100)
        kdj_k_1 = pd.Series(kdj_k)
        kdj_d = kdj_k_1.rolling(window=3, min_periods=1).mean()
        kdj_d_1 = pd.Series(kdj_d)
        kdj_j = kdj_d_1.rolling(window=3, min_periods=1).mean()
        kdj_j_1 = pd.Series(kdj_j)

        if (kdj_d_1.iloc[-1] < 15) and (kdj_d_1.iloc[-1] > kdj_j_1.iloc[-1]):
            Pos_score = Pos_score + 1

        if (kdj_d_1.iloc[-1] > 90) and (kdj_d_1.iloc[-1] < kdj_j_1.iloc[-1]):
            Neg_score = Neg_score + 1
        

        orders = self.broker.get_orders_open()

        if orders:
            for order in orders:
                self.broker.cancel(order)

        #print(self.data.close[0])
 
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