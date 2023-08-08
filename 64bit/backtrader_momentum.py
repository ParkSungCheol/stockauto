import backtrader as bt
from datetime import datetime
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr
 
 
class BOLLStrat(bt.Strategy):
 
    def __init__(self):

        global momentum_flag
        momentum_flag = []

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

        if i < 10 :
            momentum_flag.append(100)
        else :
            momentum_flag.append((self.data.close[0]/self.data.close[-10])*100)
            
        momentum_flag_1 = pd.Series(momentum_flag)
        momentum_signal = momentum_flag_1.rolling(window=9, min_periods=1).mean()

        if (momentum_flag_1.iloc[-1] >= momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] <= 95):
            Pos_score = Pos_score + 1

        if (momentum_flag_1.iloc[-1] < momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] > 105):
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

        i = i+1

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