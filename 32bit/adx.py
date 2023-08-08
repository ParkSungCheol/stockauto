import pandas as pd
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import win32com.client
import datetime
import sys
from PyQt5.QtWidgets import *
import win32com.client
import ctypes
import time
import yfinance as yf, pandas as pd, shutil, os, time, glob
import numpy as np
import requests
from get_all_tickers import get_tickers as gt
from statistics import mean
import plotly.graph_objects as go

# 연결 여부 체크
objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
bConnect = objCpCybos.IsConnect
if (bConnect == 0):
    print("PLUS가 정상적으로 연결되지 않음. ")
    exit()
 
# 차트 객체 구하기
objStockChart = win32com.client.Dispatch("CpSysDib.StockChart")
 
objStockChart.SetInputValue(0, 'A005930')   #종목 코드 - 삼성전자
objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
objStockChart.SetInputValue(4, 300) # 최근 100일 치
objStockChart.SetInputValue(5, [0,2,3,4,5,6,8]) #날짜,시가,고가,저가,종가,거래량
objStockChart.SetInputValue(6, ord('D')) # '차트 주가 - 일간 차트 요청
objStockChart.SetInputValue(9, ord('1')) # 수정주가 사용
objStockChart.BlockRequest()
 
length = objStockChart.GetHeaderValue(3)
count = 0
format= "%Y%m%d"

for i in range(length):
    day = objStockChart.GetDataValue(0, i)
    open = objStockChart.GetDataValue(1, i)
    high = objStockChart.GetDataValue(2, i)
    low = objStockChart.GetDataValue(3, i)
    close = objStockChart.GetDataValue(4, i)
    diff = objStockChart.GetDataValue(5, i)
    vol = objStockChart.GetDataValue(6, i)
    if(count==0):
        day = str(day)
        day = datetime.datetime.strptime(day, format)
        stock_list=[
            {'day': day, 'open': open, 'high': high,'low': low,'close': close,'diff' : diff,'vol': vol}
        ]
        df = pd.DataFrame(stock_list, columns=['day','open','high','low','close','diff','vol'])
    else :
        day = str(day)
        day = datetime.datetime.strptime(day, format)
        df = df.append({'day': day, 'open': open, 'high': high,'low': low,'close': close,'diff' : diff,'vol': vol},ignore_index=True)
    count=count+1

def reset_my_index(df):
  res = df[::-1].reset_index(drop=True)
  return(res)

df = reset_my_index(df)
pd.set_option('display.max_row', 500)

def cal_dmi(data, n, n_ADX) : 
    i = 0 
    UpI = [] 
    DoI = [] 
    TR_l = []
    while i <= data.index[-1] : 
        if i==0 :
            UpI.append(0)
            DoI.append(0)
        else :
            UpMove = data.loc[i, "high"] - data.loc[i-1, "high"] 
            DoMove = data.loc[i-1, "low"] - data.loc[i, "low"] 
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
        i = i + 1 

    i = 0 
    
    while i <= data.index[-1]:
        if i==0 :
            TR_l.append(0)
        else :
            TR = max(data.high.iloc[i], data.close.iloc[i-1]) - min(data.low.iloc[i], data.close.iloc[i-1])
            TR_l.append(TR)
            #print(data.high.iloc[i],i,TR)
        i = i + 1 
    TR_s = pd.Series(TR_l)
    ATR = pd.Series(TR_s.ewm(com=n, min_periods=1).mean()) 
    #ATR = pd.Series(TR_s.rolling(window=n, min_periods=1).mean())
    UpI = pd.Series(UpI) 
    DoI = pd.Series(DoI) 
    PosDI = pd.Series(UpI.ewm(com=n, min_periods=1).mean()*100 / ATR) 
    #PosDI = pd.Series(UpI.rolling(window=n, min_periods=1).mean() / ATR)
    NegDI = pd.Series(DoI.ewm(com=n, min_periods=1).mean()*100 / ATR) 
    #NegDI = pd.Series(DoI.rolling(window=n, min_periods=1).mean() / ATR)
    ADX = pd.Series((abs(PosDI - NegDI)*100 / (PosDI + NegDI)).ewm(com=n_ADX, min_periods=1).mean(), name='ADX_' + str(n) + '_' + str(n_ADX))
    #ADX = pd.Series((abs(PosDI - NegDI) / (PosDI + NegDI)).rolling(window=n_ADX, min_periods=1).mean(), name='ADX_' + str(n) + '_' + str(n_ADX))  
    return PosDI, NegDI, ADX

df["PDI"],df["MDI"],df["ADX"] = cal_dmi(df,12,12)
asset = 100000000
trade_flag = 0

def get_signal(data):
    buy_signal = [] #buy list
    sell_signal = [] #sell list
    global asset
    global trade_flag

    for i in range(len(data['close'])):
        Pos_score = 0
        Neg_score = 0

        print(df.ADX.iloc[-3])

        if i == 0 :
            
            if (df.MDI.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= 30) :
                Pos_score = Pos_score + 1
                #print(i)
            if (df.PDI.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= 35):
                Neg_score = Neg_score + 1
            
        else :

            #print(df.MDI.iloc[i])
            
            if (df.MDI.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= df.ADX.iloc[i-1]) & (df.ADX.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= 30) :
                Pos_score = Pos_score + 1
                #print(i)
            if (df.PDI.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= df.ADX.iloc[i-1]) & (df.ADX.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= 35):
                Neg_score = Neg_score + 1
 

        if (Pos_score >= 1) and (asset > data['close'][i]) : 
            buy_signal.append(data['close'][i])
            sell_signal.append(np.nan)
            trade_flag = trade_flag + 1
            asset = asset - data['close'][i]
            #print(data['close'][i])

        elif (Neg_score >= 1) and (trade_flag >= 1) :
            sell_signal.append(data['close'][i])
            buy_signal.append(np.nan)
            trade_flag = trade_flag - 1
            asset = asset + data['close'][i]
            print(data['close'][i])

        else:
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)

    return (buy_signal, sell_signal)

#Create new columns for the buy and sell signals
df['Buy'], df['Sell'] =  get_signal(df)

#Plot all of the data
#Get the figure and the figure size
fig = plt.figure(figsize=(12.2,6.4)) #width = 12.2 inches and height = 6.4 inches
#Add the subplot
ax = fig.add_subplot(1,1,1) #Number of rows, cols, & index
# Get the index values of the DataFrame
x_axis = df['day']
# Plot the Closing Price and Moving Average
ax.plot(x_axis, df['close'], color='black', lw=2, label = 'Close Price',alpha = 0.5)
#ax.plot(x_axis, new_df['SMA'], color='blue', lw=3, label = 'Moving Average',alpha = 0.5)
ax.scatter(x_axis, df['Buy'] , color='green', lw=1, label = 'Buy',marker = '^', alpha = 1)
ax.scatter(x_axis, df['Sell'] , color='red', lw=1, label = 'Sell',marker = 'v', alpha = 1)
# Set the Title & Show the Image
ax.set_title('samsung')
ax.set_xlabel('Date')
ax.set_ylabel('won Price')
plt.xticks(rotation = 45)
ax.legend()
#plt.show()