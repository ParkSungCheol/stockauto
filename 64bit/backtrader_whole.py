from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import yfinance as yf
import pandas as pd
import math
import FinanceDataReader as fdr

class IchimokuStrategy(bt.Strategy):
    def __init__(self):

        global i
        i = 0
        global Pos_score
        global Neg_score
        global trade_flag
        global max_price
        global high_price
        global low_price
        global final_flag

        trade_flag = 0
        max_price = 0
        high_price = 0
        low_price = self.data.close[0]
        final_flag = 0

        global close
        close = []

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

        global momentum_flag
        momentum_flag = []

        global flag
        flag = []

        global UpI
        UpI = []
        global DoI
        DoI = [] 
        global TR_l
        TR_l = []

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
        global max_price
        global high_price
        global low_price
        global final_flag
        global trade_flag
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
        SMA = close_1.rolling(window=20, min_periods=1).mean()
        STD = close_1.rolling(window=20, min_periods=1).std()
        Upper = SMA.iloc[-1] + (STD.iloc[-1] * 2)
        Lower = SMA.iloc[-1] - (STD.iloc[-1] * 2)
        sma_60 = close_1.rolling(window=60, min_periods=1).mean()

        if self.data.high[0] > sma_60.iloc[-1] :
            if self.data.close[0] < Lower :
                Pos_score = Pos_score + 0

            if self.data.close[0] > Upper :
                Neg_score = Neg_score + 3

        else :

            if self.data.close[0] < Lower :
                Pos_score = Pos_score + 0

            if self.data.close[0] > SMA.iloc[-1]:
                Neg_score = Neg_score + 3

        if self.data.close[0] < Lower:
            Pos_score = Pos_score + 3

        if self.data.close[0] > Upper:
            Neg_score = Neg_score + 3

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
                Pos_score = Pos_score + 3


            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) :
                Neg_score = Neg_score + 0


        else :
            #print(self.data.close[-26]) 

            if (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]) & (self.data.low[0] > self.data.high[-26]) & (self.data.close[0] > max(senkou_span_a[-26], senkou_span_b[-26])) :
                Pos_score = Pos_score + 3

            if (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]) & (self.data.high[0] < self.data.low[-26]) & (self.data.close[0] < min(senkou_span_a[-26], senkou_span_b[-26])) :
                Neg_score = Neg_score + 0

        if i < 10 :
            momentum_flag.append(100)
        else :
            momentum_flag.append((self.data.close[0]/self.data.close[-10])*100)
            
        momentum_flag_1 = pd.Series(momentum_flag)
        momentum_signal = momentum_flag_1.rolling(window=9, min_periods=1).mean()

        if (momentum_flag_1.iloc[-1] > momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] < 100):
            Pos_score = Pos_score + 0

        if (momentum_flag_1.iloc[-1] < momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] > 100):
            Neg_score = Neg_score + 0

        sma_20 = close_1.rolling(window=20, min_periods=1).mean()
        sma_60 = close_1.rolling(window=60, min_periods=1).mean()
        sma_120 = close_1.rolling(window=120, min_periods=1).mean()

        if sma_20.iloc[-1] > sma_60.iloc[-1] :
            Pos_score = Pos_score + 3
        
        if sma_20.iloc[-1] < sma_60.iloc[-1] :
            Neg_score = Neg_score + 0

        max_price = max(max_price, self.data.close[0])

        if ((sma_20.iloc[-1] >= sma_120.iloc[-1])):
            final_flag = 1
            Neg_score = Neg_score + 0

        elif (sma_20.iloc[-1] < sma_120.iloc[-1]) :
            final_flag = 0
            Pos_score = Pos_score + 0

        if i == 0 :
            flag.append(0)

        else :
            if (self.data.close[0] - self.data.close[-1]) > 0 :
                flag.append(1)

            else :
                flag.append(0)

        flag_1 = pd.Series(flag)
        psychological_line = flag_1.rolling(window=20, min_periods=1).mean()

        if psychological_line.iloc[-1] <= 0.3 :
            Pos_score = Pos_score + 0
        
        if psychological_line.iloc[-1] >= 0.7 :
            Neg_score = Neg_score + 0

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
                Pos_score = Pos_score + 0
                #print(i)
                #print(self.data.close[0])

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 35):
                Neg_score = Neg_score + 0
                #print(self.data.close[0])
            
        else :
            
            #print(NegDI.iloc[-1])
            
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 0
                #print(i)
                #print(self.data.close[0])

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 30):
                Neg_score = Neg_score + 0
                #print(self.data.close[0])

        high_price = close_1.rolling(window=1200, min_periods=1).max()
        low_price = min(low_price, self.data.close[0])

        print(round(((high_price.iloc[-1] - low_price) / low_price)*100, 2))

        orders = self.broker.get_orders_open()

         # Cancel open orders so we can track the median line
        if orders:
            for order in orders:
                self.broker.cancel(order)
 
        if not self.position:

            if (Pos_score >= 3) & (Neg_score < 6) :
                #trade_flag = trade_flag + 1
                #if trade_flag > 10 :
                #    trade_flag = 10
                #if trade_flag == 10 :
                    self.buy()
                #    final_flag = -1
                #    max_price = self.data.close[0]
                    #print(self.data.close[0])

        #elif self.data.close[0] < max_price * 0.8 :
        #    self.sell()
        #    max_price = 0
        #    trade_flag = 0

        else:

            if (Pos_score >= 3) & (Neg_score < 6) :
                #trade_flag = trade_flag + 1
                #if trade_flag > 10 :
                #    trade_flag = 10
                #if trade_flag == 10 :
                    self.buy()
                #    final_flag = -1
                    #print(self.data.close[0])

            elif (Neg_score >= 3) & (Pos_score < 6) :
                #trade_flag = trade_flag - 1
                #if trade_flag < 0 :
                #    trade_flag = 0
                #if (trade_flag < 4) :
                    self.sell()
                #    max_price = 0
                    #final_flag = 1
                    #trade_flag = 10
                    #print(self.data.close[0])
                
        
        i = i + 1
        

class PercentReverter(bt.Sizer):

    params = (
        ('percents', 33.3333),
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

    

data = bt.feeds.PandasData(dataname=fdr.DataReader(symbol='251270', start='2011-07-03', end='2021-07-03'))
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(IchimokuStrategy)
cerebro.broker.setcash(100000000)
cerebro.addsizer(PercentReverter)
#cerebro.addsizer(bt.sizers.SizerFix, stake=1)
#cerebro.broker.setcommission(commission=0.005)
init_cash = cerebro.broker.getvalue()
cerebro.run(runonce=True)
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",round(float((final_cash-init_cash)/float(init_cash)*100),2), "%")

cerebro.plot()