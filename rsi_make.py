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
objStockChart.SetInputValue(4, 200) # 최근 100일 치
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

# 상승, 하락분을 알기위해 현재 종가에서 전일 종가를 빼서 데이터프레임에 추가하겠습니다.

#def fnRSI(m_Df, m_N):
   
#    U = np.where(m_Df.diff(1)['close'] > 0, m_Df.diff(1)['close'], 0)
#    D = np.where(m_Df.diff(1)['close'] < 0, m_Df.diff(1)['close'] *(-1), 0)

    #df["AU"] = pd.DataFrame(U).rolling( window=m_N).mean()
#    df["AU"] = pd.DataFrame(U).ewm(span=m_N, adjust=False).mean()

    #df["AD"] = pd.DataFrame(D).rolling( window=m_N).mean()
#    df["AD"] = pd.DataFrame(D).ewm(span=m_N, adjust=False).mean()

#    df["RSI"] = df.AU/(df.AD+df.AU) *100

#    return df

#df = fnRSI(df, 14)

df["U"]=0
df["D"]=0
df["AU"]=0
df["AD"]=0
theta = 14

for i in range(df.shape[0]) :
    if i == 0 :
        pass
    else :
        delta = df["close"].iloc[i] - df["close"].iloc[i-1]
        if delta >= 0 :
            df["U"].iloc[i] = delta
        else :
            df["D"].iloc[i] = -delta
 
df["AU"].iloc[theta-1] = df["U"].iloc[:theta].mean()
df["AD"].iloc[theta-1] = df["D"].iloc[:theta].mean()

for i in range(theta, df.shape[0]) :
    df["AU"].iloc[i] = (df["AU"].iloc[i-1]*13 + df["U"].iloc[i])/14
    df["AD"].iloc[i] = (df["AD"].iloc[i-1]*13 + df["D"].iloc[i])/14

df["RS"]=0
df["RSI"]=0

for i in range(df.shape[0]) :
    df["RS"].iloc[i] = df["AU"].iloc[i] / df["AD"].iloc[i]
    df["RSI"].iloc[i] = df["RS"].iloc[i] / (1 + df["RS"].iloc[i]) * 100

df["SIGNAL"] = df["RSI"].rolling(window=9).mean()
#df["SIGNAL"] = df["RSI"].ewm(span=9, adjust=False).mean()
 
# RSI값이 30 이하일 때 매수, 80 이상일 때 매도하도록 설정해보겠습니다. 

# Create a function to get the buy and sell signals
def get_signal(data):
  buy_signal = [] #buy list
  sell_signal = [] #sell list
  for i in range(len(data['close'])):
    if data['RSI'][i] > 80 : #Then you should sell 
      #print('SELL')
      buy_signal.append(np.nan)
      sell_signal.append(data['RSI'][i])
    elif data['RSI'][i] < 30 : #Then you should buy
      #print('BUY')
      sell_signal.append(np.nan)
      buy_signal.append(data['RSI'][i])
    else:
      buy_signal.append(np.nan)
      sell_signal.append(np.nan)
  return (buy_signal, sell_signal)

#Create new columns for the buy and sell signals
df['Buy'] =  get_signal(df)[0]
df['Sell'] =  get_signal(df)[1]

#Plot all of the data
#Get the figure and the figure size
fig, (ax1,ax2) = plt.subplots(nrows=2, ncols=1)
# Get the index values of the DataFrame
#df1['day'] = df1['day'][:len(df1['close'])-33]
#df1['close'] = df1['close'][:len(df1['close'])-33]
x_axis = df['day']
# Plot the Closing Price and Moving Average
ax1.plot(x_axis, df['close'], color='purple', lw=3, label = 'close',alpha = 0.5)
ax2.plot(x_axis, df['RSI'], color='blue', lw=1, label = 'RSI',alpha = 0.5)
ax2.plot(x_axis, df['SIGNAL'], color='red', lw=1, label = 'SIGNAL',alpha = 0.5)
#ax2.scatter(x_axis, df1['Buy'] , color='green', lw=3, label = 'Buy',marker = '^', alpha = 1)
#ax2.scatter(x_axis, df1['Sell'] , color='red', lw=3, label = 'Sell',marker = 'v', alpha = 1)
# Set the Title & Show the Image
ax2.set_title('RSI For samsung')
ax1.set_title('samsung')
ax1.set_ylabel('won Price')
plt.xticks(rotation = 45)
ax1.legend()
ax2.legend()
plt.show()