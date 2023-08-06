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

        global flag
        flag = []

        global diff
        diff = []
        global RSI_U
        RSI_U = []
        global RSI_D
        RSI_D = []

        global close
        close = []

        global UpI
        UpI = []
        global DoI
        DoI = [] 
        global TR_l
        TR_l = []

        global macd
        macd = []

        global momentum_flag
        momentum_flag = []

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
            flag.append(0)

        else :
            if (self.data.close[0] - self.data.close[-1]) > 0 :
                flag.append(1)

            else :
                flag.append(0)

        flag_1 = pd.Series(flag)
        psychological_line = flag_1.rolling(window=20, min_periods=1).mean()

        if psychological_line.iloc[-1] <= 0.3 :
            Pos_score = Pos_score + 2

        if psychological_line.iloc[-1] >= 0.7 :
            Neg_score = Neg_score + 2

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


        if RSI.iloc[-1] < 30:
            Pos_score = Pos_score + 3

        if RSI.iloc[-1] > 70:
            Neg_score = Neg_score + 3

        close.append(self.data.close[0])
        close_1 = pd.Series(close)
        SMA = close_1.rolling(window=20, min_periods=1).mean()
        STD = close_1.rolling(window=20, min_periods=1).std()
        Upper = SMA.iloc[-1] + (STD.iloc[-1] * 2)
        Lower = SMA.iloc[-1] - (STD.iloc[-1] * 2)
        sma_60 = close_1.rolling(window=60, min_periods=1).mean()

        if self.data.high[0] > sma_60.iloc[-1] :
            if self.data.close[0] < Lower :
                Pos_score = Pos_score + 3

            if self.data.close[0] > Upper :
                Neg_score = Neg_score + 3

        else :

            if self.data.close[0] < Lower :
                Pos_score = Pos_score + 3

            if self.data.close[0] > SMA.iloc[-1]:
                Neg_score = Neg_score + 3

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


        if i == 0 :
            
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 2

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 30):
                Neg_score = Neg_score + 2
            
        else :
            
            
            if (NegDI.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= PosDI.iloc[-1]) & (ADX.iloc[-1] >= 30) :
                Pos_score = Pos_score + 2

            if (PosDI.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= ADX.iloc[-2]) & (ADX.iloc[-1] >= NegDI.iloc[-1]) & (ADX.iloc[-1] >= 30):
                Neg_score = Neg_score + 2


        ma_12 = close_1.ewm(span=12, adjust=False, min_periods=1).mean()
        ma_26 = close_1.ewm(span=26, adjust=False, min_periods=1).mean()


        macd.append(ma_12.iloc[-1] - ma_26.iloc[-1])
        macd_1 = pd.Series(macd)

        macd_signal = macd_1.ewm(span=9, adjust=False, min_periods=1).mean()


        if (macd_1.iloc[-1] > macd_signal.iloc[-1]) and (macd_1.iloc[-1] < 0):
            Pos_score = Pos_score + 2

        if (macd_1.iloc[-1] < macd_signal.iloc[-1]) and (macd_1.iloc[-1] > 0):
            Neg_score = Neg_score + 2

            
        if i < 10 :
            momentum_flag.append(100)
        else :
            momentum_flag.append((self.data.close[0]/self.data.close[-10])*100)
            
        momentum_flag_1 = pd.Series(momentum_flag)
        momentum_signal = momentum_flag_1.rolling(window=9, min_periods=1).mean()

        

        if (momentum_flag_1.iloc[-1] > momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] < 100):
            Pos_score = Pos_score + 2

        if (momentum_flag_1.iloc[-1] < momentum_signal.iloc[-1]) and (momentum_flag_1.iloc[-1] > 100):
            Neg_score = Neg_score + 2

        orders = self.broker.get_orders_open()
 
        # Cancel open orders so we can track the median line
        if orders:
            for order in orders:
                self.broker.cancel(order)
 
        if not self.position:

            if Pos_score >= 5 :
                self.buy()
                #print(self.data.close[0])

        else:

            if Pos_score >= 5 :
                self.buy()
                #print(self.data.close[0])

            elif Neg_score >= 4 :
                self.sell()
                #print(self.data.close[0])
        
        i = i + 1
        

class PercentReverter(bt.Sizer):
    params = (
        ('percents', 20),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = ((position.size * data.close[0] + cash) / data.close[0]) * (self.params.percents / 100)
            if (isbuy==False) and (size > position.size) :
                size = position.size
        return math.floor(size)

    

data = bt.feeds.PandasData(dataname=fdr.DataReader(symbol='005490', start='2017-07-10', end='2018-09-10'))
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(IchimokuStrategy)
cerebro.broker.setcash(100000000)
cerebro.addsizer(PercentReverter)
#cerebro.addsizer(bt.sizers.SizerFix, stake=1)
cerebro.broker.setcommission(commission=0.005)
init_cash = cerebro.broker.getvalue()
cerebro.run(runonce=True)
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",round(float((final_cash-init_cash)/float(init_cash)*100),2), "%")

cerebro.plot()