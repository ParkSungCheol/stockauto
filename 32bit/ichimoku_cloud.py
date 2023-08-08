import pandas as pd
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
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
objStockChart.SetInputValue(4, 2375) # 최근 100일 치
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

def ichimoku_cloud(df) :

    nine_period_high = df['high'].rolling(window= 9, min_periods=1).max()
    nine_period_low = df['low'].rolling(window= 9, min_periods=1).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = df['high'].rolling(window=26, min_periods=1).max()
    period26_low = df['low'].rolling(window=26, min_periods=1).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(25)
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = df['high'].rolling(window=52, min_periods=1).max()
    period52_low = df['low'].rolling(window=52, min_periods=1).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(25)

    return df['senkou_span_a'],df['senkou_span_b']

df['senkou_span_a'],df['senkou_span_b']= ichimoku_cloud(df)

asset = 100000000
trade_flag = 0

# Create a function to get the buy and sell signals
def get_signal(data):
    buy_signal = [] #buy list
    sell_signal = [] #sell list
    global asset
    global trade_flag
    for i in range(len(data['close'])):
        Pos_score = 0
        Neg_score = 0

        #print(df.senkou_span_a.iloc[i])
        

        if i < 26 :
            if (df.senkou_span_a.iloc[i] > df.senkou_span_b.iloc[i]) and (df.close.iloc[i] < df.senkou_span_a.iloc[i]) :
                Pos_score = Pos_score + 1

            if ((df.senkou_span_a.iloc[i] < df.senkou_span_b.iloc[i]) and (df.close.iloc[i] > df.senkou_span_a.iloc[i])) :
                Neg_score = Neg_score + 1

        else :
            #print(df.close.iloc[i-26])
            if (df.senkou_span_a.iloc[i] > df.senkou_span_b.iloc[i]) and (df.close.iloc[i] < df.senkou_span_a.iloc[i]) and (df.close.iloc[i] > df.close.iloc[i-26]) :
                Pos_score = Pos_score + 1

            if ((df.senkou_span_a.iloc[i] < df.senkou_span_b.iloc[i]) and (df.close.iloc[i] > df.senkou_span_a.iloc[i])) and (df.close.iloc[i] < df.close.iloc[i-26]) :
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