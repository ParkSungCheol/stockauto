from matplotlib.pyplot import tricontour
from pandas.core.frame import DataFrame
import backtrader as bt
from datetime import datetime
import yfinance as yf
import pandas as pd
 
 
class BOLLStrat(bt.Strategy):

    params = (
        ("period", 20),
        ("devfactor", 2),
        ("size", 20),
        ("debug", False)
        )
        
 
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavol = self.datas[0].volume
        global tr0
        tr0 = []
        global tr1
        tr1 = [] 
        global tr2
        tr2 = [] 
        global tr
        global atr
        global signal
 
    def next(self):
        a=abs(self.datas[0].high[0] - self.datas[0].low[0])
        tr0.append(a)
        b=abs(self.datas[0].high[0] - self.datas[0].close[-1])
        tr1.append(b)
        c=abs(self.datas[0].low[0] - self.datas[0].close[-1])
        tr2.append(c)
        tr=pd.Series(max(a,b,c))
        atr=pd.Series(tr.ewm(alpha=1/14, adjust=False).mean())
        signal=pd.Series(atr.rolling(9, min_periods=1).mean())
        print(signal.iloc[-1])



cerebro = bt.Cerebro()
 
#data = bt.feeds.YahooFinanceData(dataname = '005930.KS', fromdate = datetime(2017,1,1), todate = datetime(2020,10,1))
data = bt.feeds.PandasData(dataname=yf.download('005930.KS', '2017-01-01', '2021-04-01'))
cerebro.adddata(data)
cerebro.addstrategy(BOLLStrat)
cerebro.broker.setcash(100000000)
cerebro.addsizer(bt.sizers.SizerFix, stake=30)
cerebro.broker.setcommission(commission=0.005)
init_cash = cerebro.broker.getvalue()
cerebro.run()
final_cash = cerebro.broker.getvalue()
print("최종금액 : ",final_cash,"원")
print("수익률 : ",float((final_cash-init_cash)/float(init_cash)*100), "%")
cerebro.plot()