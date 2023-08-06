import pandas as pd
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import datetime
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
objStockChart.SetInputValue(4, 400) # 최근 100일 치
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

# Commodity Channel Index 
def CCI(df, ndays): 
    df['TP'] = (df['high'] + df['low'] + df['close']) / 3 
    df['sma'] = df['TP'].rolling(ndays).mean()
    df['mad'] = df['TP'].rolling(ndays).apply(lambda x: pd.Series(x).mad())
    df['CCI'] = (df['TP'] - df['sma']) / (0.015 * df['mad']) 
    return df

# Compute the Commodity Channel Index(CCI) for NIFTY based on the 20-day Moving average
n = 20
df = CCI(df, n)
df["SIGNAL"] = df.CCI.rolling(9).mean()

def buy_sell(prices, cci, signal):
    buy_price = []
    sell_price = []
    flag = 0
    
    lower_band = (-100)
    upper_band = 100
    
    for i in range(len(prices)):
        if cci[i] < lower_band and cci[i] < signal[i] and flag != -1 :
            buy_price.append(np.nan)
            sell_price.append(prices[i])
            flag = -1
        
        elif cci[i] > lower_band and cci[i] > signal[i] and flag == -1 :
            buy_price.append(prices[i])
            sell_price.append(np.nan)
            flag = 0
                
        elif cci[i] > upper_band and cci[i] > signal[i] and flag != 1 :
            buy_price.append(prices[i])
            sell_price.append(np.nan)
            flag = 1

        elif cci[i] < upper_band and cci[i] < signal[i] and flag == 1 :
            buy_price.append(np.nan)
            sell_price.append(prices[i])
            flag = 0
                
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            
    return buy_price, sell_price

df['Buy'] = buy_sell(df['close'],df['CCI'],df['SIGNAL'])[0]
df['Sell'] = buy_sell(df['close'],df['CCI'],df['SIGNAL'])[1]

fig, (ax1,ax2) = plt.subplots(nrows=2, ncols=1)
# Get the index values of the DataFrame
#df1['day'] = df1['day'][:len(df1['close'])-33]
#df1['close'] = df1['close'][:len(df1['close'])-33]
x_axis = df['day']
# Plot the Closing Price and Moving Average
ax1.plot(x_axis, df['close'], color='black', lw=3, label = 'close',alpha = 0.5)
#ax1.plot(x_axis, df['trend'], color='yellow', lw=3,label = 'trend',alpha = 0.5)
ax2.plot(x_axis, df['CCI'], color='blue', lw=1, label = 'CCI',alpha = 0.5)
ax2.plot(x_axis, df['SIGNAL'], color='purple', lw=1, label = 'SIGNAL',alpha = 0.5)
#ax2.plot(x_axis, df['ADX'], color='black',lw=3, label = 'ADX')
ax2.axhline(y=100, color='b', linewidth=1)
ax2.axhline(y=0, color='b', linewidth=1)
ax2.axhline(y=-100, color='b', linewidth=1)
ax1.scatter(x_axis, df['Buy'] , color='green', lw=1, label = 'Buy',marker = '^', alpha = 1)
ax1.scatter(x_axis, df['Sell'] , color='red', lw=1, label = 'Sell',marker = 'v', alpha = 1)
# Set the Title & Show the Image
ax2.set_title('CCI For SamsungElectronics')
ax1.set_title('SamsungElectronics')
ax1.set_ylabel('Won Price')
plt.xticks(rotation = 45)
ax1.legend()
ax2.legend()
plt.show()