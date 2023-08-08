from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr

class IchimokuStrategy(bt.Strategy):
    def __init__(self):

        global ichimoku_high
        ichimoku_high = []
        global ichimoku_low
        ichimoku_low = []
        global senkou_span_a
        senkou_span_a = []
        global senkou_span_b
        senkou_span_b = []

        global i
        i = 0

        for k in range(26) :
            senkou_span_a.append(0)
            senkou_span_b.append(0)
        
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

        ichimoku_high.append(self.data.high[0])
        ichimoku_low.append(self.data.low[0])
        ichimoku_high_1 = pd.Series(ichimoku_high)
        ichimoku_low_1 = pd.Series(ichimoku_low)


        nine_period_high = ichimoku_high_1.rolling(window= 9, min_periods=1).max()
        nine_period_low = ichimoku_low_1.rolling(window= 9, min_periods=1).min()

        tenkan_sen = (nine_period_high + nine_period_low) / 2

        period26_high = ichimoku_high_1.rolling(window=26, min_periods=1).max()
        period26_low = ichimoku_low_1.rolling(window=26, min_periods=1).min()
        kijun_sen = (period26_high + period26_low) / 2

        senkou_span_a.append((tenkan_sen.iloc[-1] + kijun_sen.iloc[-1]) / 2)

        period52_high = ichimoku_high_1.rolling(window=52, min_periods=1).max()
        period52_low = ichimoku_low_1.rolling(window=52, min_periods=1).min()
        senkou_span_b.append((period52_high.iloc[-1] + period52_low.iloc[-1]) / 2)

        #print(senkou_span_a[-26])

        if i < 26 :
            if (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]) :
                Pos_score = Pos_score + 1


            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) :
                Neg_score = Neg_score + 1


        else :
            #print(self.data.close[-26]) 

            if (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]) & (self.data.low[0] > self.data.high[-26]) & (self.data.close[0] > max(senkou_span_a[-26], senkou_span_b[-26])) :
                Pos_score = Pos_score + 1

            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) & (self.data.high[0] < self.data.low[-26]) & (self.data.close[0] < min(senkou_span_a[-26], senkou_span_b[-26])) :
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
cerebro.addstrategy(IchimokuStrategy)
cerebro.broker.setcash(100000000)
cerebro.addsizer(PercentReverter)
#cerebro.broker.setcommission(commission=0.005)
init_cash = cerebro.broker.getvalue()
cerebro.run()
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",round(float((final_cash-init_cash)/float(init_cash)*100),2), "%")
cerebro.plot()