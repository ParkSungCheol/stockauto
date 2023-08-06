from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from typing_extensions import final

import backtrader as bt
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr

class IchimokuStrategy(bt.Strategy):
    def __init__(self):

        global close
        close = []

        global i
        i = 0
        global Pos_score
        global Neg_score
        global trade_flag
        global max_price
        global high_price
        global low_price
        global final_flag
        global buy_price
        trade_flag = 0
        max_price = 0
        high_price = 0
        low_price = self.data.close[0]
        buy_price = 0
        final_flag = 1

        global obv
        obv = []
        obv.append(0)

        global flag
        flag = []

        global diff
        diff = []
        global RSI_U
        RSI_U = []
        global RSI_D
        RSI_D = []

        global UpI
        UpI = []
        global DoI
        DoI = [] 
        global TR_l
        TR_l = []

        global ichimoku_high
        ichimoku_high = []
        global ichimoku_low
        ichimoku_low = []
        global senkou_span_a
        senkou_span_a = []
        global senkou_span_b
        senkou_span_b = []

        for k in range(26) :
            senkou_span_a.append(0)
            senkou_span_b.append(0)

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

        global high
        high = []
        global low
        low = []
        global kdj_k
        kdj_k = []

        global macd
        macd = []

        global f2
        f2 = open("A011170.txt", "w")
 
    def next(self):
        global i
        global Pos_score
        global Neg_score
        global trade_flag
        global flag
        global max_price
        global high_price
        global low_price
        global final_flag
        global buy_price
        global f2
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

        close.append(self.data.close[0])
        close_1 = pd.Series(close)

        c = self.data.close 
        v = self.data.volume 
 
        if (i >= 1) and (c[0] > c[-1]):
            obv.append(obv[-1] + v[0])
        elif (i >= 1) and (c[0] < c[-1]):
            obv.append(obv[-1] - v[0])
        elif (i >= 1):
            obv.append(obv[-1])
        
        obv_1 = pd.Series(obv)
        signal = obv_1.ewm(com=20, min_periods=1).mean()

        signal_1 = close_1.ewm(com=20, min_periods=1).mean()

        if (i >= 20) & (self.data.close[0] < signal_1.iloc[-1]) and (obv_1.iloc[-1] > signal.iloc[-1]):
            Pos_score = Pos_score + 4

        if (i >= 20) & (self.data.close[0] >= signal_1.iloc[-1]) and (obv_1.iloc[-1] <= signal.iloc[-1]):
            Neg_score = Neg_score + 4
            

        if i == 0 :
            flag.append(0)

        else :
            if (self.data.close[0] - self.data.close[-1]) > 0 :
                flag.append(1)

            else :
                flag.append(0)

        flag_1 = pd.Series(flag)
        psychological_line = flag_1.rolling(window=20, min_periods=1).mean()

        if (i >= 20) & (psychological_line.iloc[-1] <= 0.3) :
            Pos_score = Pos_score + 0

        if (i >= 20) & (psychological_line.iloc[-1] >= 0.7) :
            Neg_score = Neg_score + 0

        if i == 0 :
            diff.append(0)

        else :
            diff.append(self.data.close[0] - self.data.close[-1])

        if diff[-1] >= 0 :
            RSI_U.append(diff[-1])
            RSI_D.append(0)

        else :
            RSI_U.append(0)
            RSI_D.append(-diff[-1])
        
        RSI_U_1 = pd.Series(RSI_U)
        RSI_D_1 = pd.Series(RSI_D)
        RSI_AU = RSI_U_1.ewm(com=14, min_periods=1).mean()
        RSI_AD = RSI_D_1.ewm(com=14, min_periods=1).mean()
        RS = RSI_AU / RSI_AD
        RSI = (RS / (1+RS)) * 100


        if (i >= 14) & (RSI.iloc[-1] < 30):
            Pos_score = Pos_score + 4

        if (i >= 14) & (RSI.iloc[-1] > 75):
            Neg_score = Neg_score + 4
            

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
            TR = max(self.datas[0].high[0], self.datas[0].close[-1]) - min(self.datas[0].low[0], self.datas[0].close[-1])
            TR_l.append(TR)
        

        TR_s = pd.Series(TR_l) 
        ATR = TR_s.ewm(com=12).mean() 
        UpI2 = pd.Series(UpI) 
        DoI2 = pd.Series(DoI) 
        PosDI = pd.Series(UpI2.ewm(com=12, min_periods=1).mean()*100 / ATR)
        NegDI = pd.Series(DoI2.ewm(com=12, min_periods=1).mean()*100 / ATR) 
        ADX = pd.Series((abs(PosDI - NegDI)*100 / (PosDI + NegDI)).ewm(com=12, min_periods=1).mean())

 

        if i  >= 24 :
                   
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 0

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 30):
                Neg_score = Neg_score + 4
                

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

        if (9 <= i) & (i < 26) :
            if (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]) :
                Pos_score = Pos_score + 6


            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) :
                Neg_score = Neg_score + 4


        elif i >= 26 :
            #print(self.data.close[-26]) 

            if (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]) & (self.data.low[0] > self.data.high[-26]) & (self.data.close[0] > max(senkou_span_a[-26], senkou_span_b[-26])) :
                Pos_score = Pos_score + 6

            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) & (self.data.high[0] < self.data.low[-26]) & (self.data.close[0] < min(senkou_span_a[-26], senkou_span_b[-26])) :
                Neg_score = Neg_score + 4
                #f2.write(str(senkou_span_b[-26]) + "\n")

        ma_12 = close_1.ewm(span=12, adjust=False, min_periods=1).mean()
        ma_26 = close_1.ewm(span=26, adjust=False, min_periods=1).mean()

        #print(ma_26.iloc[-1])

        macd.append(ma_12.iloc[-1] - ma_26.iloc[-1])
        macd_1 = pd.Series(macd)

        macd_signal = macd_1.ewm(span=9, adjust=False, min_periods=1).mean()

        #print(macd_signal.iloc[-1])

        if (i >= 21) & (macd_1.iloc[-1] > macd_signal.iloc[-1]) & (macd_1.iloc[-1] < 0):
            Pos_score = Pos_score + 4

        if (i >= 21) & (macd_1.iloc[-1] < macd_signal.iloc[-1]) & (macd_1.iloc[-1] > 0):
            Neg_score = Neg_score + 4

        sma_20 = close_1.rolling(window=20, min_periods=1).mean()
        sma_60 = close_1.rolling(window=60, min_periods=1).mean()
        sma_120 = close_1.rolling(window=120, min_periods=1).mean()

        if (i >= 60) & (sma_60.iloc[-1] > sma_120.iloc[-1]) :
            Pos_score = Pos_score + 4
        
        if (i >= 60) & (sma_60.iloc[-1] < sma_120.iloc[-1]) :
            Neg_score = Neg_score + 2

        max_price = max(max_price, self.data.close[0])

        if (i >= 20) & ((sma_20.iloc[-1] > sma_120.iloc[-1]*1.1) | (self.data.close[0] < max_price * 0.8)):
            final_flag = -1
            Neg_score = Neg_score + 0
            

        elif (i >= 20) & (sma_20.iloc[-1] <= sma_120.iloc[-1]) :
            final_flag = 1
            Pos_score = Pos_score + 4
            #print(sma_20.iloc[-1])
            #f2.write(str(sma_120.iloc[-1]) + "\n")

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


        if (i >= 18) & (kdj_d_1.iloc[-1] < 15) and (kdj_d_1.iloc[-1] > kdj_j_1.iloc[-1]):
            Pos_score = Pos_score + 2

        if (i >= 18) & (kdj_d_1.iloc[-1] > 85) and (kdj_d_1.iloc[-1] < kdj_j_1.iloc[-1]):
            Neg_score = Neg_score + 2
            #print(kdj_d_1.iloc[-1])
            #f2.write(str(kdj_d_1.iloc[-1]) + "\n")

        high_price = close_1.rolling(window=240, min_periods=1).max()
        low_price = min(low_price, self.data.close[0])

        #print(round(((high_price.iloc[-1] - low_price) / low_price)*100, 2))
        #print(i)
        #f2.write(str(max_price) + "\n")

        orders = self.broker.get_orders_open()
        

 
        # Cancel open orders so we can track the median line
        if orders:
            for order in orders:
                self.broker.cancel(order)
 
        if not self.position:

            if (Pos_score >= 4) & (Neg_score < 6) :
                trade_flag = trade_flag + 1
                if trade_flag > 10 :
                    trade_flag = 10
                if trade_flag == 10 :
                    self.buy()
                    buy_price = self.data.close[0]
                    final_flag = -1
                    max_price = self.data.close[0]
                    #print(self.data.close[0])
                    f2.write(str(self.data.close[0]) + "\n")

        #elif self.data.close[0] < max_price * 0.8 :
        #    self.sell()
        #    max_price = 0
        #    trade_flag = 0

        else:

            if (final_flag == 1) & (Pos_score >= 4) & (Neg_score < 6) :
                trade_flag = trade_flag + 1
                if trade_flag > 10 :
                    trade_flag = 10
                if trade_flag == 10 :
                    self.buy()
                    buy_price = self.data.close[0]
                    final_flag = -1
                    #print(self.data.close[0])
                    f2.write(str(self.data.close[0]) + "\n")

            elif (final_flag == -1) & (Neg_score >= 4) & (Pos_score < 6) :
                trade_flag = trade_flag - 1
                if trade_flag < 0 :
                    trade_flag = 0
                if (trade_flag < 4) :
                    self.sell()
                    max_price = 0
                    buy_price = 0
                    #f2.write(str(self.data.close[0]) + "\n")
                    #final_flag = 1
                    #trade_flag = 10
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
                size = size*100
                if (size > position.size) :
                    size = position.size
        return math.floor(size)


data = bt.feeds.PandasData(dataname=fdr.DataReader(symbol='051910', start='2014-12-08', end='2017-11-10'))
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(IchimokuStrategy)
cerebro.broker.setcash(100000000)
cerebro.addsizer(PercentReverter)
#cerebro.addsizer(bt.sizers.SizerFix, stake=1)
#cerebro.broker.setcommission(commission=0.001)
init_cash = cerebro.broker.getvalue()
cerebro.run(runonce=True)
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",round(float((final_cash-init_cash)/float(init_cash)*100),2), "%")
f2.close()

cerebro.plot()