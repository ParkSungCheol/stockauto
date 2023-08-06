from pickle import FALSE
import pandas_datareader as pdr
import datetime as dt
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import datetime
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
objStockChart.SetInputValue(4, 1000) # 최근 100일 치
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

def wwma(values, n):
    return values.ewm(alpha=1/n, adjust=FALSE).mean()
    #return values.rolling(14).sum()/14

def atr(df, n):
    df['tr0'] = abs(df["high"] - df["low"])
    df['tr1'] = abs(df["high"] - df["close"].shift(1))
    df['tr2'] = abs(df["low"] - df["close"].shift())
    df["tr"] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(df.tr, n)
    #print(df.tr1)
    #trs = np.array(df.tr)
    #atrs = np.zeros(len(trs))
    #atrs[n-1] = np.mean(trs[:n])

    #for i in range(n, len(trs)):
        #atrs[i] = ((n-1) * atrs[i-1] + trs[i])/n

    #atrs = atrs.round(3)
    return atr

df["ATR"]=atr(df,14)
#df["SIGNAL"]=df["ATR"].ewm(span=9, adjust=FALSE).mean()
df["SIGNAL"]=df["ATR"].rolling(9).mean()

fig, (ax1,ax2) = plt.subplots(nrows=2, ncols=1)
# Get the index values of the DataFrame
#df1['day'] = df1['day'][:len(df1['close'])-33]
#df1['close'] = df1['close'][:len(df1['close'])-33]
x_axis = df['day']
# Plot the Closing Price and Moving Average
ax1.plot(x_axis, df['close'], color='purple', lw=3, label = 'close',alpha = 0.5)
#ax1.plot(x_axis, df['trend'], color='yellow', lw=3,label = 'trend',alpha = 0.5)
ax2.plot(x_axis, df['ATR'], color='blue', lw=1, label = 'ATR',alpha = 0.5)
ax2.plot(x_axis, df['SIGNAL'], color='purple', lw=1, label = 'SIGNAL',alpha = 0.5)
#ax2.plot(x_axis, df['ADX'], color='black',lw=3, label = 'ADX')
#ax2.axhline(y=20, color='r', linewidth=1)
#ax2.scatter(x_axis, df1['Buy'] , color='green', lw=3, label = 'Buy',marker = '^', alpha = 1)
#ax2.scatter(x_axis, df1['Sell'] , color='red', lw=3, label = 'Sell',marker = 'v', alpha = 1)
# Set the Title & Show the Image
ax2.set_title('ATR For samsung')
ax1.set_title('samsung')
ax1.set_ylabel('won Price')
plt.xticks(rotation = 45)
ax1.legend()
ax2.legend()
plt.show()