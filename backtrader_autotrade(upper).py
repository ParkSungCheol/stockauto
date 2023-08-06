from pandas.core.window.rolling import Window
import win32com.client
import pandas as pd
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import win32com.client
import datetime
from PyQt5.QtWidgets import *
import win32com.client
import yfinance as yf, pandas as pd, shutil, os, time, glob
import numpy as np
from statistics import mean

# 연결 여부 체크
objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
bConnect = objCpCybos.IsConnect
if (bConnect == 0):
    print("PLUS가 정상적으로 연결되지 않음. ")
    exit()
 
# 차트 객체 구하기
objStockChart = win32com.client.Dispatch("CpSysDib.StockChart")
 
objStockChart.SetInputValue(0, 'A000660')   #종목 코드 - 삼성전자
objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
objStockChart.SetInputValue(4, 2375) # 최근 1000일 치
objStockChart.SetInputValue(5, [0,2,3,4,5,6,8]) #날짜,시가,고가,저가,종가,거래량
objStockChart.SetInputValue(6, ord('D')) # '차트 주가 - 일간 차트 요청
objStockChart.SetInputValue(9, ord('1')) # 수정주가 사용
objStockChart.BlockRequest()
 
length = objStockChart.GetHeaderValue(3)
count = 0
format= "%Y%m%d"

for i in range(length):
    day = objStockChart.GetDataValue(0, i)
    open1 = objStockChart.GetDataValue(1, i)
    high = objStockChart.GetDataValue(2, i)
    low = objStockChart.GetDataValue(3, i)
    close = objStockChart.GetDataValue(4, i)
    diff = objStockChart.GetDataValue(5, i)
    vol = objStockChart.GetDataValue(6, i)
    if(count==0):
        day = str(day)
        day = datetime.datetime.strptime(day, format)
        stock_list=[
            {'day': day, 'open1': open1, 'high': high,'low': low,'close': close,'diff' : diff,'vol': vol}
        ]
        df = pd.DataFrame(stock_list, columns=['day','open1','high','low','close','diff','vol'])
    else :
        day = str(day)
        day = datetime.datetime.strptime(day, format)
        df = df.append({'day': day, 'open1': open1, 'high': high,'low': low,'close': close,'diff' : diff,'vol': vol},ignore_index=True)
    count=count+1

def reset_my_index(df):
  res = df[::-1].reset_index(drop=True)
  return(res)

df = reset_my_index(df)
pd.set_option('display.max_row', 500)

def moving_average(df) :

    df["ma5"] = df['close'].rolling(window=5, min_periods=1).mean()

    df["ma20"] = df['close'].rolling(window=20, min_periods=1).mean()

    df["ma60"] = df['close'].rolling(window=60, min_periods=1).mean()

    df["ma120"] = df['close'].rolling(window=120, min_periods=1).mean()

    return df

def obv(df) :
    OBV=[]
    close=[]
    OBV.append(0)
    close.append(df.close[0])
    for i in range(1, len(df.close)) :
        close.append(df.close[i])
        if df.close[i] > df.close[i-1] :
            OBV.append(OBV[i-1]+df.vol[i])
        elif df.close[i] < df.close[i-1] :
            OBV.append(OBV[i-1]-df.vol[i])
        else :
            OBV.append(OBV[i-1])

    return OBV, close

def psychological_line(df) :

    flag = []

    for i in range(len(df["close"])) :
        if i==0 :
            flag.append(0)
        else :
            if df["diff"][i] > 0 :
                flag.append(1)
            else :
                flag.append(0)
    
    return flag

def rsi(df, RSI_n) :
 
    # U(up): n일 동안의 종가 상승 분
    df["RSI_U"]=df["diff"].apply(lambda x: x if x>0 else 0)
 
    # D(down): n일 동안의 종가 하락 분 --> 음수를 양수로 바꿔줌
    df["RSI_D"]=df["diff"].apply(lambda x: x * (-1) if x<0 else 0)
 
    # AU(average ups): U값의 평균
    df["RSI_AU"]=df["RSI_U"].ewm(com=RSI_n, min_periods=1).mean()
 
    # DU(average downs): D값의 평균
    df["RSI_AD"]=df["RSI_D"].ewm(com=RSI_n, min_periods=1).mean()

    df.RSI_AU.iloc[0] = 1
 
    RSI = df.apply(lambda x:x["RSI_AU"]/(x["RSI_AU"]+ x["RSI_AD"]) * 100,1)

    return RSI

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

    return df['tenkan_sen'], df['kijun_sen'], df['senkou_span_a'],df['senkou_span_b']

def get_macd(df) :

  ma_12 = df['close'].ewm(span=12, adjust=False).mean()


  ma_26 = df['close'].ewm(span=26, adjust=False).mean()

  df["MACD"] = ma_12 - ma_26

  df["SIGNAL"]=df.MACD.ewm(span=9, min_periods=1, adjust=False).mean()

  #print(ma_26)

  return df

def get_stochastic(df, n, m, t):
    
    # n일중 최고가
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    # n일중 최저가
    ndays_low = df.low.rolling(window=n, min_periods=1).min()

    # Fast%K 계산
    kdj_k = ((df.close - ndays_low) / (ndays_high - ndays_low))*100
    # Fast%D (=Slow%K) 계산
    kdj_d = kdj_k.rolling(window=m, min_periods=1).mean()
    # Slow%D 계산
    kdj_j = kdj_d.rolling(window=t, min_periods=1).mean()
    
    return kdj_k, kdj_d, kdj_j

df["kdj_k"],df["kdj_d"],df["kdj_j"] = get_stochastic(df, 12, 3, 3)
df['OBV'], df['close_list'] = obv(df)
df['OBV_SIGNAL'] = df['OBV'].ewm(com=20, min_periods=1).mean()
df['CLOSE_SIGNAL'] = df['close_list'].ewm(com=20, min_periods=1).mean()
df["flag"] = psychological_line(df)
df["psychological_line"] = df.flag.rolling(window=20, min_periods=1).mean()
df["PDI"],df["MDI"],df["ADX"] = cal_dmi(df,12,12)
df['tenkan_sen'], df['kijun_sen'], df['senkou_span_a'], df['senkou_span_b'] = ichimoku_cloud(df)
df = get_macd(df)
df = moving_average(df)
df["diff"][0] = 0
df["RSI"] = rsi(df, 14)

asset = 100000000
trade_flag = 0
max_price = 0
final_flag = 1
position = 0
f2 = open("A005930.txt", "w")

# Create a function to get the buy and sell signals
def get_signal(data, f2):
    buy_signal = [] #buy list
    sell_signal = [] #sell list
    global asset
    global trade_flag
    global max_price
    global final_flag
    global position

    for i in range(len(data['close'])):
        Pos_score = 0
        Neg_score = 0

        if (i >= 60) & (df.ma60.iloc[i] > df.ma120.iloc[i]) :
            Pos_score = Pos_score + 4

        if (i >= 60) & (df.ma60.iloc[i] < df.ma120.iloc[i]) :
            Neg_score = Neg_score + 2

        max_price = max(max_price, df.close.iloc[i])

        if (i >= 20) & ((df.ma20.iloc[i] > df.ma120.iloc[i]*1.1) | (df.close.iloc[i] < max_price * 0.8)):
            final_flag = -1
            Neg_score = Neg_score + 0
            

        elif (i >= 20) & (df.ma20.iloc[i] <= df.ma120.iloc[i]) :
            final_flag = 1
            Pos_score = Pos_score + 4
            #print(df.ma20.iloc[i])
            #f2.write(str(df.ma120.iloc[i]) + "\n")

        if (i >= 20) & (df.close.iloc[i] < df.CLOSE_SIGNAL.iloc[i]) and (df.OBV.iloc[i] > df.OBV_SIGNAL.iloc[i]):
            Pos_score = Pos_score + 4
    
        if (i >= 20) & (df.close.iloc[i] >= df.CLOSE_SIGNAL.iloc[i]) and (df.OBV.iloc[i] <= df.OBV_SIGNAL.iloc[i]):
            Neg_score = Neg_score + 4
            

        if df.psychological_line.iloc[i] <= 0.3 :
            Pos_score = Pos_score + 0

        if df.psychological_line.iloc[i] >= 0.75 :
            Neg_score = Neg_score + 0

        if (i >= 14) & (df.RSI.iloc[i] < 30):
            Pos_score = Pos_score + 4

        if (i >= 14) & (df.RSI.iloc[i] > 75):
            Neg_score = Neg_score + 4
            

        if i  >= 24 :
           
            if (df.MDI.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= df.ADX.iloc[i-1]) & (df.ADX.iloc[i] >= df.PDI.iloc[i]) & (df.ADX.iloc[i] >= 30) :
                Pos_score = Pos_score + 0

            if (df.PDI.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= df.ADX.iloc[i-1]) & (df.ADX.iloc[i] >= df.MDI.iloc[i]) & (df.ADX.iloc[i] >= 30):
                Neg_score = Neg_score + 4
                

        if (9 <= i) & (i < 26) :

            if (df.tenkan_sen.iloc[i] > df.kijun_sen.iloc[i]) :
                Pos_score = Pos_score + 6


            if (df.tenkan_sen.iloc[i] < df.kijun_sen.iloc[i]) :
                Neg_score = Neg_score + 4


        elif i >= 26 :
            #print(self.data.close[-26]) 

            if (df.tenkan_sen.iloc[i] > df.kijun_sen.iloc[i]) & (df.low.iloc[i] > df.high.iloc[i-26]) & (df.close.iloc[i] > max(df.senkou_span_a.iloc[i], df.senkou_span_b.iloc[i])) :
                Pos_score = Pos_score + 6

            if (df.tenkan_sen.iloc[i] < df.kijun_sen.iloc[i]) & (df.high.iloc[i] < df.low.iloc[i-26]) & (df.close.iloc[i] < min(df.senkou_span_a.iloc[i], df.senkou_span_b.iloc[i])) :
                Neg_score = Neg_score + 4
                #f2.write(str(df.senkou_span_b.iloc[i]) + "\n")

        if (i >= 21) & (df.MACD.iloc[i] > df.SIGNAL.iloc[i]) and (df.MACD.iloc[i] < 0):
            Pos_score = Pos_score + 4

        if (i >= 21) & (df.MACD.iloc[i] < df.SIGNAL.iloc[i]) and (df.MACD.iloc[i] > 0):
            Neg_score = Neg_score + 4

        if (i >= 18) & (df.kdj_d.iloc[i] < 15) and (df.kdj_d.iloc[i] > df.kdj_j.iloc[i]):
            Pos_score = Pos_score + 2

        if (i >= 18) & (df.kdj_d.iloc[i] > 85) and (df.kdj_d.iloc[i] < df.kdj_j.iloc[i]):
            Neg_score = Neg_score + 2
            #print(df.kdj_d.iloc[i])
            #f2.write(str(df.kdj_d.iloc[i]) + "\n")
        
        #print(i)
        #f2.write(str(max_price) + "\n")
        

        if (position == 0) and (Pos_score >= 4)  and (Neg_score < 6) and (asset > data['close'][i]): 
            trade_flag = trade_flag + 1
            if trade_flag > 10 :
                trade_flag = 10
            if trade_flag == 10 :
                buy_signal.append(data['close'][i])
                sell_signal.append(np.nan)
                position = position + 1
                final_flag = -1
                asset = asset - data['close'][i]
                max_price = df.close.iloc[i]
                #print(data['close'][i])
                f2.write(str(data['close'][i]) + "\n")
            else :
                buy_signal.append(np.nan)
                sell_signal.append(np.nan)

        elif (final_flag == 1) and (Pos_score >= 4) and (Neg_score < 6) and (asset > data['close'][i]):
            trade_flag = trade_flag + 1
            if trade_flag > 10 :
                trade_flag = 10
            if trade_flag == 10 :
                buy_signal.append(data['close'][i])
                sell_signal.append(np.nan)
                position = position + 1
                asset = asset - data['close'][i]
                final_flag = -1
                #print(data['close'][i])
                f2.write(str(data['close'][i]) + "\n")
            else :
                buy_signal.append(np.nan)
                sell_signal.append(np.nan)

        elif (final_flag == -1) and (Neg_score >= 4) and (Pos_score < 6) and (position >= 1) :
            trade_flag = trade_flag - 1
            if trade_flag < 0 :
                trade_flag = 0
            if (trade_flag < 4) :
                buy_signal.append(np.nan)
                sell_signal.append(data['close'][i])
                position = position - 1
                asset = asset + data['close'][i]
                max_price = 0
                #print(data['close'][i])
                #f2.write(str(data['close'][i]) + "\n")
            else :
                buy_signal.append(np.nan)
                sell_signal.append(np.nan)

        else:
            buy_signal.append(np.nan)
            sell_signal.append(np.nan)

    return (buy_signal, sell_signal)

#Create new columns for the buy and sell signals
df['Buy'],df['Sell'] =  get_signal(df, f2)
f2.close()

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