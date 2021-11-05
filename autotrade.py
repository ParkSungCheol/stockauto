import sys
from sys import exit
from PyQt5.QtWidgets import *
import win32com.client
import ctypes
import pandas as pd
import requests
from pandas.core.window.rolling import Window
from pandas_datareader import data, wb
import matplotlib as mpl
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import datetime
import win32com.client
import yfinance as yf, pandas as pd, shutil, os, time, glob
import numpy as np
from statistics import mean
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox


def post_message(message) :
    payload = '{"text" : "%s"}' % message
    response = requests.post('https://hooks.slack.com/services/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',
        data=payload.encode('utf-8'))
    print(response.text)
 
g_objCodeMgr = win32com.client.Dispatch('CpUtil.CpCodeMgr')
g_objCpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
cpCash = win32com.client.Dispatch('CpTrade.CpTd6033')
objStockChart = win32com.client.Dispatch("CpSysDib.StockChart")
objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")
objStockOrder = win32com.client.Dispatch("CpTrade.CpTd0311")
 
def InitPlusCheck():
    # 프로세스가 관리자 권한으로 실행 여부
    if ctypes.windll.shell32.IsUserAnAdmin():
        print('정상: 관리자권한으로 실행된 프로세스입니다.')
    else:
        print('오류: 일반권한으로 실행됨. 관리자 권한으로 실행해 주세요')
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("오류: 일반권한으로 실행됨. 관리자 권한으로 실행해 주세요      ")
        result = msgBox.exec_()
        return False
 
    # 연결 여부 체크
    if (g_objCpStatus.IsConnect == 0):
        print("PLUS가 정상적으로 연결되지 않음. ")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("PLUS가 정상적으로 연결되지 않음.      ")
        result = msgBox.exec_()
        return False
 
    # 주문 관련 초기화
    if (cpTradeUtil.TradeInit(0) != 0):
        print("주문 초기화 실패")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문 초기화 실패      ")
        result = msgBox.exec_()
        return False
 
    return True

def buy(past, cash, cash2, present_close, code, percent, segment_percent, trade_vol = -1) :

    # 주문 초기화
    initCheck = cpTradeUtil.TradeInit(0)

    trade_vol = int(trade_vol)

    if (initCheck != 0):
        print("주문 초기화 실패")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문 초기화 실패      ")
        result = msgBox.exec_()
        exit()


    # 주식 매수 주문
    acc = cpTradeUtil.AccountNumber[0] #계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)  # 주식상품 구분
    objStockOrder.SetInputValue(0, "2")   # 2: 매수
    objStockOrder.SetInputValue(1, acc )   #  계좌번호
    objStockOrder.SetInputValue(2, accFlag[0])   # 상품구분 - 주식 상품 중 첫번째
    print(code)
    objStockOrder.SetInputValue(3, code)   # 종목코드 - 필요한 종목으로 변경 필요 
    if trade_vol != -1 :
        print(trade_vol)
        if trade_vol <= 0 :
            post_message("매수가능수량이 0보다 작아 해당 전략 하 매수를 종료합니다.")
            return past, cash2
        objStockOrder.SetInputValue(4, trade_vol)   # 매수수량 - 요청 수량으로 변경 필요
    
    else :
        volume = int(cash/present_close*percent*segment_percent)
        if volume > cash/present_close*segment_percent - past :
            volume = int(cash/present_close*segment_percent - past)
            post_message("잔여예수금이 부족하여 해당 전략에 배정된 예수금을 모두 소진하였습니다.")
            if volume <= 0 :
                post_message("매수가능수량이 0보다 작아 해당 전략 하 매수를 종료합니다.")
                return past, cash2
        print(volume)
        objStockOrder.SetInputValue(4, volume)   # 매수수량 - 요청 수량으로 변경 필요 
    print(present_close)
    objStockOrder.SetInputValue(5, present_close)   # 주문단가 - 필요한 가격으로 변경 필요 
    objStockOrder.SetInputValue(7, "0")   # 주문 조건 구분 코드, 0: 기본 1: IOC 2:FOK
    objStockOrder.SetInputValue(8, "01")   # 주문호가 구분코드 - 01: 보통

    # 매수 주문 요청
    nRet = objStockOrder.BlockRequest()
    if (nRet != 0) :
        print("주문요청 오류", nRet)    
        # 0: 정상,  그 외 오류, 4: 주문요청제한 개수 초과 
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문요청 오류(4: 주문요청제한 개수 초과) : " + str(nRet) + "      ")
        result = msgBox.exec_()
        exit()

    rqStatus = objStockOrder.GetDibStatus()
    errMsg = objStockOrder.GetDibMsg1()
    if rqStatus != 0:
        print("주문 실패: ", rqStatus, errMsg)
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문 실패 : " + str(rqStatus) + str(errMsg) + "      ")
        result = msgBox.exec_()
        exit()

    if trade_vol != -1 :
        cash2 = cash2 - trade_vol*present_close
        past = past + trade_vol

        post_message("매수대상 : " + str(code) + ",매수가 : " +  str(present_close)+ ",매수수량 : " +  str(trade_vol) + ",총수량 : " +  str(past) + ",잔여예수금 : " + str(cash2))

    else :
        cash2 = cash2 - volume*present_close
        past = past + volume

        post_message("매수대상 : " + str(code) + ",매수가 : " +  str(present_close) + ",매수수량 : " +  str(volume) + ",총수량 : " +  str(past) + ",잔여예수금 : " + str(cash2))

    return past, cash2


def sell(past, cash, cash2, present_close, code, percent, segment_percent, trade_vol = -1) :


    # 주문 초기화
    initCheck = cpTradeUtil.TradeInit(0)

    trade_vol = int(trade_vol)

    if (initCheck != 0):
        print("주문 초기화 실패")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문 초기화 실패      ")
        result = msgBox.exec_()
        exit()

    # 주식 매도 주문
    acc = cpTradeUtil.AccountNumber[0] #계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)  # 주식상품 구분
    objStockOrder.SetInputValue(0, "1")   # 1 : 매도
    objStockOrder.SetInputValue(1, acc )   #  계좌번호
    objStockOrder.SetInputValue(2, accFlag[0])   # 상품구분 - 주식 상품 중 첫번째
    print(code)
    objStockOrder.SetInputValue(3, code)   # 종목코드 - 필요한 종목으로 변경 필요 
    if trade_vol != -1 :
        print(trade_vol)
        if trade_vol <= 0 :
            post_message("매도가능수량이 0보다 작아 해당 전략 하 매도를 종료합니다.")
            return past, cash2
        objStockOrder.SetInputValue(4, trade_vol)   # 매도수량 - 요청 수량으로 변경 필요 
    
    else :
        volume = int(cash/present_close*percent*segment_percent)
        if volume > past :
            volume = past
            post_message("매도대상 : " + str(code) + " 전량 매도했습니다.")
            if volume <= 0 :
                post_message("매도가능수량이 0보다 작아 해당 전략 하 매도를 종료합니다.")
                return past, cash2
        print(volume)
        objStockOrder.SetInputValue(4, volume)   # 매도수량 - 요청 수량으로 변경 필요 
    print(present_close)
    objStockOrder.SetInputValue(5, present_close)   # 주문단가 - 필요한 가격으로 변경 필요 
    objStockOrder.SetInputValue(7, "0")   # 주문 조건 구분 코드, 0: 기본 1: IOC 2:FOK
    objStockOrder.SetInputValue(8, "01")   # 주문호가 구분코드 - 01: 보통

    # 매도 주문 요청
    nRet = objStockOrder.BlockRequest()
    if (nRet != 0) :
        print("주문요청 오류", nRet)    
        # 0: 정상,  그 외 오류, 4: 주문요청제한 개수 초과 
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문요청 오류(4: 주문요청제한 개수 초과) : " + str(nRet) + "      ")
        result = msgBox.exec_()
        exit()

    rqStatus = objStockOrder.GetDibStatus()
    errMsg = objStockOrder.GetDibMsg1()
    if rqStatus != 0:
        print("주문 실패: ", rqStatus, errMsg)
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("에러메시지")
        msgBox.setText("주문 실패 : " + str(rqStatus) + str(errMsg) + "      ")
        result = msgBox.exec_()
        exit()

    if trade_vol != -1 :
        cash2 = cash2 + trade_vol*present_close
        past = past - trade_vol

        post_message("매도대상 : " + str(code) + ",매도가 : " +  str(present_close) + ",매도수량 : " +  str(trade_vol) + ",총수량 : " +  str(past) + ",잔여예수금 : " + str(cash2))

    else :
        cash2 = cash2 + volume*present_close
        past = past - volume

        post_message("매도대상 : " + str(code) + ",매도가 : " +  str(present_close) + ",매도수량 : " +  str(volume) + ",총수량 : " +  str(past) + ",잔여예수금 : " + str(cash2))

    return past, cash2

def lower(past, cash, cash2, present_close, code, percent, segment_percent) :
 
    objStockChart.SetInputValue(0, code)   #종목 코드 - 삼성전자
    objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
    objStockChart.SetInputValue(4, 300) # 최근 1000일 치
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
    df["flag"] = psychological_line(df)
    df["psychological_line"] = df.flag.rolling(window=20, min_periods=1).mean()
    df["diff"][0] = 0
    df["RSI"] = rsi(df, 14)

    Pos_score = 0
    Neg_score = 0

    if df.psychological_line.iloc[-1] <= 0.3 :
        Pos_score = Pos_score + 1

    #print(df.psychological_line.iloc[-2])

    if df.psychological_line.iloc[-1] >= 0.7 :
        Neg_score = Neg_score + 1

    if df.RSI.iloc[-1] < 30:
        Pos_score = Pos_score + 2
    
    #print(df.RSI.iloc[-2])

    if df.RSI.iloc[-1] > 70:
        Neg_score = Neg_score + 2

        
    if (df.kdj_d.iloc[-1] < 15) and (df.kdj_d.iloc[-1] > df.kdj_j.iloc[-1]):
        Pos_score = Pos_score + 1

    #print(df.kdj_j.iloc[-2])

    if (df.kdj_d.iloc[-1] > 85) and (df.kdj_d.iloc[-1] < df.kdj_j.iloc[-1]):
        Neg_score = Neg_score + 1


    post_message("lower전략을 실행합니다.")
    if Pos_score >= 4:
        past, cash2 = buy(past, cash, cash2, present_close, code, percent, segment_percent)
            
    elif (Neg_score >= 4) and (past >= 1):
        past, cash2 = sell(past, cash, cash2, present_close, code, percent, segment_percent)

    else :
        post_message("lower전략에서는 금일 매수,매도가 이뤄지지 않았습니다")
    
    return past, cash2

def mix(past, cash, cash2, present_close, code, percent, segment_percent) :
 
    objStockChart.SetInputValue(0, code)   #종목 코드 - 삼성전자
    objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
    objStockChart.SetInputValue(4, 300) # 최근 1000일 치
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

    def get_macd(df) :

        ma_12 = df['close'].ewm(span=12, adjust=False).mean()


        ma_26 = df['close'].ewm(span=26, adjust=False).mean()

        df["MACD"] = ma_12 - ma_26

        df["SIGNAL"]=df.MACD.ewm(span=9, min_periods=1, adjust=False).mean()

        #print(ma_26)

        return df


    def momentum(df) :
        flag = []

        for i in range(len(df["close"])) :
            if i < 10 :
                flag.append(100)
            else :
                flag.append(df.close[i]/df.close[i-10]*100)

        return flag

    df["kdj_k"],df["kdj_d"],df["kdj_j"] = get_stochastic(df, 12, 3, 3)
    df["flag"] = psychological_line(df)
    df["psychological_line"] = df.flag.rolling(window=20, min_periods=1).mean()
    df["momentum"] = momentum(df)
    df["signal"] = df.momentum.rolling(window=9, min_periods=1).mean()
    df["PDI"],df["MDI"],df["ADX"] = cal_dmi(df,12,12)
    df = get_macd(df)
    df["diff"][0] = 0
    df["RSI"] = rsi(df, 14)

    Pos_score = 0
    Neg_score = 0

    if df.psychological_line.iloc[-1] <= 0.3 :
        Pos_score = Pos_score + 2

    #print(df.psychological_line.iloc[-2])

    if df.psychological_line.iloc[-1] >= 0.7 :
        Neg_score = Neg_score + 2

    if df.RSI.iloc[-1] < 30:
        Pos_score = Pos_score + 3

    #print(df.RSI.iloc[-2])

    if df.RSI.iloc[-1] > 70:
        Neg_score = Neg_score + 3

        
    if (df.kdj_d.iloc[-1] < 15) and (df.kdj_d.iloc[-1] > df.kdj_j.iloc[-1]):
        Pos_score = Pos_score + 2

    #print(df.kdj_j.iloc[-2])

    if (df.kdj_d.iloc[-1] > 85) and (df.kdj_d.iloc[-1] < df.kdj_j.iloc[-1]):
        Neg_score = Neg_score + 2

            
    if (df.MDI.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30) :
        Pos_score = Pos_score + 1
    
    #print(df.ADX.iloc[-3])

    if (df.PDI.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30):
        Neg_score = Neg_score + 1



    if (df.MACD.iloc[-1] > df.SIGNAL.iloc[-1]) and (df.MACD.iloc[-1] < 0):
        Pos_score = Pos_score + 2

    #print(df.SIGNAL.iloc[-2])

    if (df.MACD.iloc[-1] < df.SIGNAL.iloc[-1]) and (df.MACD.iloc[-1] > 0):
        Neg_score = Neg_score + 2

        

    if (df.momentum.iloc[-1] > df.signal.iloc[-1]) and (df.momentum.iloc[-1] < 100):
        Pos_score = Pos_score + 2

    #print(df.signal.iloc[-2])

    if (df.momentum.iloc[-1] < df.signal.iloc[-1]) and (df.momentum.iloc[-1] > 100):
        Neg_score = Neg_score + 2

    post_message("mix전략을 실행합니다.")
    if Pos_score >= 5: 
        past, cash2 = buy(past, cash, cash2, present_close, code, percent, segment_percent)
            
    elif (Neg_score >= 4) and (past >= 1):
        past, cash2 = sell(past, cash, cash2, present_close, code, percent, segment_percent)

    else :
        post_message("mix전략에서는 금일 매수,매도가 이뤄지지 않았습니다")

    return past, cash2

def neutral(past, cash, cash2, present_close, code, percent, segment_percent) :
 
    objStockChart.SetInputValue(0, code)   #종목 코드 - 삼성전자
    objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
    objStockChart.SetInputValue(4, 300) # 최근 1000일 치
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

    def get_macd(df) :

        ma_12 = df['close'].ewm(span=12, adjust=False).mean()


        ma_26 = df['close'].ewm(span=26, adjust=False).mean()

        df["MACD"] = ma_12 - ma_26

        df["SIGNAL"]=df.MACD.ewm(span=9, min_periods=1, adjust=False).mean()

        #print(ma_26)

        return df


    def momentum(df) :
        flag = []

        for i in range(len(df["close"])) :
            if i < 10 :
                flag.append(100)
            else :
                flag.append(df.close[i]/df.close[i-10]*100)

        return flag
        

    df["momentum"] = momentum(df)
    df["signal"] = df.momentum.rolling(window=9, min_periods=1).mean()
    df["PDI"],df["MDI"],df["ADX"] = cal_dmi(df,12,12)
    df = get_macd(df)

    Pos_score = 0
    Neg_score = 0

    if (df.MDI.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30) :
        Pos_score = Pos_score + 1

    #print(df.ADX.iloc[-3])

    if (df.PDI.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30):
        Neg_score = Neg_score + 1



    if (df.MACD.iloc[-1] > df.SIGNAL.iloc[-1]) and (df.MACD.iloc[-1] < 0):
        Pos_score = Pos_score + 2

    #print(df.SIGNAL.iloc[-2])

    if (df.MACD.iloc[-1] < df.SIGNAL.iloc[-1]) and (df.MACD.iloc[-1] > 0):
        Neg_score = Neg_score + 2

        

    if (df.momentum.iloc[-1] > df.signal.iloc[-1]) and (df.momentum.iloc[-1] < 100):
        Pos_score = Pos_score + 2

    #print(df.signal.iloc[-2])

    if (df.momentum.iloc[-1] < df.signal.iloc[-1]) and (df.momentum.iloc[-1] > 100):
        Neg_score = Neg_score + 2
       
        
    post_message("neutral전략을 실행합니다.")
    if Pos_score >= 3: 
        past, cash2 = buy(past, cash, cash2, present_close, code, percent, segment_percent)
            
    elif (Neg_score >= 3) and (past >= 1):
        past, cash2 = sell(past, cash, cash2, present_close, code, percent, segment_percent)

    else :
        post_message("neutral전략에서는 금일 매수,매도가 이뤄지지 않았습니다")

    return past, cash2

def upper(past, cash, cash2, present_close, code, percent, segment_percent, trade_flag, final_flag) :
 
    objStockChart.SetInputValue(0, code)   #종목 코드 - 삼성전자
    objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
    objStockChart.SetInputValue(4, 300) # 최근 1000일 치
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

    Pos_score = 0
    Neg_score = 0

    if df.ma20.iloc[-1] > df.ma60.iloc[-1] :
        Pos_score = Pos_score + 3

    #print(df.ma60.iloc[-2])

    if df.ma20.iloc[-1] < df.ma60.iloc[-1] :
        Neg_score = Neg_score + 3

    if (df.close.iloc[-1] < df.CLOSE_SIGNAL.iloc[-1]) and (df.OBV.iloc[-1] > df.OBV_SIGNAL.iloc[-1]):
        Pos_score = Pos_score + 2

    #print(df.OBV_SIGNAL.iloc[-2])
    
    if (df.close.iloc[-1] >= df.CLOSE_SIGNAL.iloc[-1]) and (df.OBV.iloc[-1] <= df.OBV_SIGNAL.iloc[-1]):
        Neg_score = Neg_score + 2

    if df.psychological_line.iloc[-1] <= 0.3 :
        Pos_score = Pos_score + 1

    #print(df.psychological_line.iloc[-2])

    if df.psychological_line.iloc[-1] >= 0.75 :
        Neg_score = Neg_score + 1

    if df.RSI.iloc[-1] < 30:
        Pos_score = Pos_score + 2

    #print(df.RSI.iloc[-2])

    if df.RSI.iloc[-1] > 75:
        Neg_score = Neg_score + 2

            
    if (df.MDI.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30) :
        Pos_score = Pos_score + 2

    #print(df.ADX.iloc[-3])        

    if (df.PDI.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= 35):
        Neg_score = Neg_score + 2

    post_message("upper전략을 실행합니다.")
    if Pos_score >= 5: 
        past, cash2 = buy(past, cash, cash2, present_close, code, percent, segment_percent)
            
    elif (Neg_score >= 6) and (past >= 1):
        past, cash2 = sell(past, cash, cash2, present_close, code, percent, segment_percent)

    else :
        post_message("upper전략에서는 금일 매수,매도가 이뤄지지 않았습니다")

    return past, cash2

def whole(past, cash, cash2, present_close, code, percent, segment_percent) :

    objStockChart.SetInputValue(0, code)   #종목 코드 - 삼성전자
    objStockChart.SetInputValue(1, ord('2')) # 개수로 조회
    objStockChart.SetInputValue(4, 300) # 최근 1000일 치
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
    df["PDI"],df["MDI"],df["ADX"] = cal_dmi(df,12,12)
    df["diff"][0] = 0
    df["RSI"] = rsi(df, 14)

    Pos_score = 0
    Neg_score = 0

    if (df.close.iloc[-1] < df.CLOSE_SIGNAL.iloc[-1]) and (df.OBV.iloc[-1] > df.OBV_SIGNAL.iloc[-1]):
        Pos_score = Pos_score + 2

    #print(df.OBV_SIGNAL.iloc[-2])
    
    if (df.close.iloc[-1] >= df.CLOSE_SIGNAL.iloc[-1]) and (df.OBV.iloc[-1] <= df.OBV_SIGNAL.iloc[-1]):
        Neg_score = Neg_score + 2

    if df.RSI.iloc[-1] < 30:
        Pos_score = Pos_score + 3

    #print(df.RSI.iloc[-2])

    if df.RSI.iloc[-1] > 75:
        Neg_score = Neg_score + 3
            
    if (df.MDI.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.PDI.iloc[-1]) & (df.ADX.iloc[-1] >= 30) :
        Pos_score = Pos_score + 1

    #print(df.ADX.iloc[-3])

    if (df.PDI.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= df.ADX.iloc[-2]) & (df.ADX.iloc[-1] >= df.MDI.iloc[-1]) & (df.ADX.iloc[-1] >= 35):
        Neg_score = Neg_score + 1

        
    if (df.kdj_d.iloc[-1] < 15) and (df.kdj_d.iloc[-1] > df.kdj_j.iloc[-1]):
        Pos_score = Pos_score + 1

    #print(df.kdj_j.iloc[-2])

    if (df.kdj_d.iloc[-1] > 90) and (df.kdj_d.iloc[-1] < df.kdj_j.iloc[-1]):
        Neg_score = Neg_score + 1

    post_message("whole전략을 실행합니다.")
    if Pos_score >= 3: 
        past, cash2 = buy(past, cash, cash2, present_close, code, percent, segment_percent)
            
    elif (Neg_score >= 3) and (past >= 1):
        past, cash2 = sell(past, cash, cash2, present_close, code, percent, segment_percent)

    else :
        post_message("whole전략에서는 금일 매수,매도가 이뤄지지 않았습니다")

    return past, cash2

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
 
        # plus 상태 체크
        if InitPlusCheck() == False:
            exit()
 
        self.setWindowTitle("autotrade UI")
        self.setGeometry(500, 200, 600, 500)
        
        nH = 50
        nm = 50

        self.code = QLabel("비중변경", self)
        self.code.move(20 + 6 * nm, nH-50)

        self.code = QLabel("주식코드", self)
        self.code.move(20,nH)
        self.code = QLineEdit("", self)
        self.code.move(20 + 3 * nm, nH)

        btnExit8 = QPushButton('D+2예수금출력', self)
        btnExit8.move(20 + 9 * nm, nH)
        btnExit8.clicked.connect(self.cash)


        nH += 50

        self.percent = QLabel("매수매도비중%", self)
        self.percent.move(20,nH)
        self.percent = QLineEdit("10", self)
        self.percent.move(20 + 3 * nm, nH)

        btnExit8 = QPushButton('총자산출력', self)
        btnExit8.move(20 + 9 * nm, nH)
        btnExit8.clicked.connect(self.asset)


        nH += 50

        self.lower = QLabel("lower전략비중%", self)
        self.lower.move(20,nH)
        self.lower = QLineEdit("", self)
        self.lower.move(20 + 3 * nm, nH)

        self.lower_diff = QLineEdit("0", self)
        self.lower_diff.move(20 + 6 * nm, nH)

        btnExit8 = QPushButton('보유자산출력', self)
        btnExit8.move(20 + 9 * nm, nH)
        btnExit8.clicked.connect(self.stock)


        nH += 50

        self.mix = QLabel("mix전략비중%", self)
        self.mix.move(20,nH)
        self.mix = QLineEdit("", self)
        self.mix.move(20 + 3 * nm, nH)

        self.mix_diff = QLineEdit("0", self)
        self.mix_diff.move(20 + 6 * nm, nH)

        btnExit8 = QPushButton('미체결잔량출력', self)
        btnExit8.move(20 + 9 * nm, nH)
        btnExit8.clicked.connect(self.lost)


        nH += 50

        self.neutral = QLabel("neutral전략비중%", self)
        self.neutral.move(20,nH)
        self.neutral = QLineEdit("", self)
        self.neutral.move(20 + 3 * nm, nH)

        self.neutral_diff = QLineEdit("0", self)
        self.neutral_diff.move(20 + 6 * nm, nH)


        nH += 50

        self.upper = QLabel("upper전략비중%", self)
        self.upper.move(20,nH)
        self.upper = QLineEdit("", self)
        self.upper.move(20 + 3 * nm, nH)

        self.upper_diff = QLineEdit("0", self)
        self.upper_diff.move(20 + 6 * nm, nH)


        nH += 50

        self.whole = QLabel("whole전략비중%", self)
        self.whole.move(20,nH)
        self.whole = QLineEdit("", self)
        self.whole.move(20 + 3 * nm, nH)

        self.whole_diff = QLineEdit("0", self)
        self.whole_diff.move(20 + 6 * nm, nH)

        nH += 50

        self.buy = QLabel("buy전략비중%", self)
        self.buy.move(20,nH)
        self.buy = QLineEdit("", self)
        self.buy.move(20 + 3 * nm, nH)

        self.buy_diff = QLineEdit("0", self)
        self.buy_diff.move(20 + 6 * nm, nH)

        nH += 50

        btnExit8 = QPushButton('실행', self)
        btnExit8.move(20 + 3 * nm, nH)
        btnExit8.clicked.connect(self.messageBox)

        btnExit8 = QPushButton('종료', self)
        btnExit8.move(20 + 6 * nm, nH)
        btnExit8.clicked.connect(self.exit)
        nH += 50

    def exit(self):
        exit()

    def activate(self) :
        global code # 종목코드
        global percent # 매수매도비중
        global lower_percent
        global mix_percent
        global neutral_percent
        global upper_percent
        global whole_percent
        global buy_percent
        global lower_diff
        global mix_diff
        global neutral_diff
        global upper_diff
        global whole_diff
        global buy_diff

        f1 = open(str(code) + ".txt", "r")
        lines = f1.readlines()
        lines = lines[0].split(',')
        lower_past = int(lines[0])
        mix_past = int(lines[1])
        neutral_past = int(lines[2])
        upper_past = int(lines[3])
        whole_past = int(lines[4])
        buy_past = int(lines[5])
        trade_flag = int(lines[6])
        final_flag = int(lines[7])
        f1.close()


        # 현재가 객체 구하기
        objStockMst.SetInputValue(0, code)   #종목 코드
        objStockMst.BlockRequest()
 
        # 현재가 통신 및 통신 에러 처리 
        rqStatus = objStockMst.GetDibStatus()
        rqRet = objStockMst.GetDibMsg1()
        print("통신상태", rqStatus, rqRet)
        if rqStatus != 0:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setWindowTitle("에러메시지")
            msgBox.setText("통신상태 : " + str(rqStatus) + str(rqRet) + "      ")
            result = msgBox.exec_()
            exit()

        # 현재가 정보 조회

        name= objStockMst.GetHeaderValue(1)  # 종목명
        time= objStockMst.GetHeaderValue(4)  # 시간
        present_close= objStockMst.GetHeaderValue(11) # 종가
        diff= objStockMst.GetHeaderValue(12)  # 대비
        open_value= objStockMst.GetHeaderValue(13)  # 시가
        high= objStockMst.GetHeaderValue(14)  # 고가
        low= objStockMst.GetHeaderValue(15)   # 저가
        offer = objStockMst.GetHeaderValue(16)  #매도호가
        bid = objStockMst.GetHeaderValue(17)   #매수호가
        vol= objStockMst.GetHeaderValue(18)   #거래량
        vol_value= objStockMst.GetHeaderValue(19)  #거래대금
 
        # 예상 체결관련 정보
        exFlag = objStockMst.GetHeaderValue(58) #예상체결가 구분 플래그
        exPrice = objStockMst.GetHeaderValue(55) #예상체결가
        exDiff = objStockMst.GetHeaderValue(56) #예상체결가 전일대비
        exVol = objStockMst.GetHeaderValue(57) #예상체결수량

        value1 = 1 # 기본 1 예외 2

        if value1 == 1 :
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
            cpCash.SetInputValue(0, acc) # 계좌번호
            cpCash.SetInputValue(1, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            cpCash.BlockRequest()
            cash1 = cpCash.GetHeaderValue(3) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash2 = cpCash.GetHeaderValue(9) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash3 = cpCash.GetHeaderValue(11) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
    
        if value1 == 2 :
            CpTd0732 = win32com.client.Dispatch('CpTrade.CpTd0732')
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            CpTd0732.SetInputValue(0, acc) #계좌번호
            CpTd0732.SetInputValue(1, "10") #구분코드 국내주식은 10
            CpTd0732.BlockRequest()
            cash = CpTd0732.GetHeaderValue(3)
        

        cash = cash2 + cash3
        #print(cash)

        cnt = cpCash.GetHeaderValue(7)

        for i in range(cnt):
            code2 = cpCash.GetDataValue(12, i)  # 종목코드
            volume = cpCash.GetDataValue(15, i) # 매도가능수량
            if i == 0 :
                item=[{'code': code2, 'volume': volume}]
                item = pd.DataFrame(item, columns=['code','volume'])
            else :
                item = item.append({'code': code2, 'volume': volume},ignore_index=True)

        #print(cnt)

        post_message("<" + str(code) + "종목 전략을 실행합니다." + ">")

        if lower_diff > 0 :
            trade_vol = (lower_past/(lower_percent - lower_diff)) * lower_diff
            if trade_vol > 0 :
                post_message("lower전략 비중조정을 실행합니다.")
                lower_past, cash2 = buy(lower_past, cash, cash2, present_close, code, percent, lower_percent, trade_vol)
        elif (lower_past >= 1) & (lower_diff < 0) :
            trade_vol = abs((lower_past/(lower_percent - lower_diff)) * (lower_diff))
            if trade_vol > 0 :
                post_message("lower전략 비중조정을 실행합니다.")
                lower_past, cash2 = sell(lower_past, cash, cash2, present_close, code, percent, lower_percent, trade_vol)
        if mix_diff > 0 :
            trade_vol = (mix_past/(mix_percent - mix_diff)) * mix_diff
            if trade_vol > 0 :
                post_message("mix전략 비중조정을 실행합니다.")
                mix_past, cash2 = buy(mix_past, cash, cash2, present_close, code, percent, mix_percent, trade_vol)
        elif (mix_past >= 1) & (mix_diff < 0) :
            trade_vol = abs((mix_past/(mix_percent - mix_diff)) * (mix_diff))
            if trade_vol > 0 :
                post_message("mix전략 비중조정을 실행합니다.")
                mix_past, cash2 = sell(mix_past, cash, cash2, present_close, code, percent, mix_percent, trade_vol)
        if neutral_diff > 0 :
            trade_vol = (neutral_past/(neutral_percent - neutral_diff)) * neutral_diff
            if trade_vol > 0 :
                post_message("neutral전략 비중조정을 실행합니다.")
                neutral_past, cash2 = buy(neutral_past, cash, cash2, present_close, code, percent, neutral_percent, trade_vol)
        elif (neutral_past >= 1) & (neutral_diff < 0) :
            trade_vol = abs((neutral_past/(neutral_percent - neutral_diff)) * (neutral_diff))
            if trade_vol > 0 :
                post_message("neutral전략 비중조정을 실행합니다.")
                neutral_past, cash2 = sell(neutral_past, cash, cash2, present_close, code, percent, neutral_percent, trade_vol)
        if upper_diff > 0 :
            trade_vol = (upper_past/(upper_percent - upper_diff)) * upper_diff
            if trade_vol > 0 :
                post_message("upper전략 비중조정을 실행합니다.")
                upper_past, cash2 = buy(upper_past, cash, cash2, present_close, code, percent, upper_percent, trade_vol)
        elif (upper_past >= 1) & (upper_diff < 0) :
            trade_vol = abs((upper_past/(upper_percent - upper_diff)) * (upper_diff))
            if trade_vol > 0 :
                post_message("upper전략 비중조정을 실행합니다.")
                upper_past, cash2 = sell(upper_past, cash, cash2, present_close, code, percent, upper_percent, trade_vol)
        if whole_diff > 0 :
            trade_vol = (whole_past/(whole_percent - whole_diff)) * whole_diff
            if trade_vol > 0 :
                post_message("whole전략 비중조정을 실행합니다.")
                whole_past, cash2 = buy(whole_past, cash, cash2, present_close, code, percent, whole_percent, trade_vol)
        elif (whole_past >= 1) & (whole_diff < 0) :
            trade_vol = abs((whole_past/(whole_percent - whole_diff)) * (whole_diff))
            if trade_vol > 0 :
                post_message("whole전략 비중조정을 실행합니다.")
                whole_past, cash2 = sell(whole_past, cash, cash2, present_close, code, percent, whole_percent, trade_vol)
        if buy_diff > 0 :
            trade_vol = (buy_past/(buy_percent - buy_diff)) * buy_diff
            if trade_vol > 0 :
                post_message("buy전략 비중조정을 실행합니다.")
                buy_past, cash2 = buy(buy_past, cash, cash2, present_close, code, percent, buy_percent, trade_vol)
        elif (buy_past >= 1) & (buy_diff < 0) :
            trade_vol = abs((buy_past/(buy_percent - buy_diff)) * (buy_diff))
            if trade_vol > 0 :
                post_message("buy전략 비중조정을 실행합니다.")
                buy_past, cash2 = sell(buy_past, cash, cash2, present_close, code, percent, buy_percent, trade_vol)
        
        if lower_percent != 0 :
            lower_past, cash2 = lower(lower_past, cash, cash2, present_close, code, percent, lower_percent)
        if mix_percent != 0 :
            mix_past, cash2 = mix(mix_past, cash, cash2, present_close, code, percent, mix_percent)
        if neutral_percent != 0 :
            neutral_past, cash2 = neutral(neutral_past, cash, cash2, present_close, code, percent, neutral_percent)
        if upper_percent != 0 :
            upper_past, cash2 = upper(upper_past, cash, cash2, present_close, code, percent, upper_percent, trade_flag, final_flag)
        if whole_percent != 0 :
            whole_past, cash2 = whole(whole_past, cash, cash2, present_close, code, percent, whole_percent)
        if buy_percent != 0 :
            post_message("buy전략을 실행합니다.")
            buy_past, cash2 = buy(buy_past, cash, cash2, present_close, code, 1, buy_percent)

        f2 = open(str(code) + ".txt", "w")
        f2.write(str(int(lower_past)) + "," +str(int(mix_past)) + "," +str(int(neutral_past)) + "," +str(int(upper_past)) + "," +str(int(whole_past)) + "," +str(int(buy_past)) + "," +str(int(trade_flag)) + "," +str(int(final_flag)))
        f2.close()

    def messageBox(self):
        global code
        global percent
        global lower_percent
        global mix_percent
        global neutral_percent
        global upper_percent
        global whole_percent
        global buy_percent
        global lower_diff
        global mix_diff
        global neutral_diff
        global upper_diff
        global whole_diff
        global buy_diff

        code = self.code.text()
        percent = round(float(self.percent.text()),2)
        lower_percent = round(float(self.lower.text()),2)
        mix_percent = round(float(self.mix.text()),2)
        neutral_percent = round(float(self.neutral.text()),2)
        upper_percent = round(float(self.upper.text()),2)
        whole_percent = round(float(self.whole.text()),2)
        buy_percent = round(float(self.buy.text()),2)
        cash_percent = 100 - (lower_percent + mix_percent + neutral_percent + upper_percent + whole_percent + buy_percent)
        lower_diff = round(float(self.lower_diff.text()),2)
        mix_diff = round(float(self.mix_diff.text()),2)
        neutral_diff = round(float(self.neutral_diff.text()),2)
        upper_diff = round(float(self.upper_diff.text()),2)
        whole_diff = round(float(self.whole_diff.text()),2)
        buy_diff = round(float(self.buy_diff.text()),2)

        if cash_percent < 0 :
            msgBox = QMessageBox()
            msgBox.setWindowTitle("에러메시지")
            msgBox.setText("설정비중이 100%를 초과합니다.       ")
            result = msgBox.exec_()
            self.exit()

        msgBox = QMessageBox()

        msgBox.setWindowTitle("입력정보확인")

        msgBox.setIcon(QMessageBox.NoIcon)

        msgBox.setText("< 입력하신 정보를 보여드립니다. 맞으면 Yes버튼을 눌러주세요. >      ")

        msgBox.setInformativeText("입력하신 주식코드는 " + str(code) + " 입니다.\n\n입력하신 매수매도비중은 " + str(percent) + "% 입니다.\n\n입력하신 lower전략비중은 " + str(lower_percent) + "% 입니다.\n입력하신 lower비중변경은 " + str(lower_diff) + "% 입니다.\n\n입력하신 mix전략비중은 " + str(mix_percent) + "% 입니다.\n입력하신 mix비중변경은 " + str(mix_diff) + "% 입니다.\n\n입력하신 neutral전략비중은 " + str(neutral_percent) + "% 입니다.\n입력하신 neutral비중변경은 " + str(neutral_diff) + "% 입니다.\n\n입력하신 upper전략비중은 " + str(upper_percent) + "% 입니다.\n입력하신 upper비중변경은 " + str(upper_diff) + "% 입니다.\n\n입력하신 whole전략비중은 " + str(whole_percent) + "% 입니다.\n입력하신 whole비중변경은 " + str(whole_diff) + "% 입니다.\n\n입력하신 buy전략비중은 " + str(buy_percent) + "% 입니다\n입력하신 buy비중변경은 " + str(buy_diff) + "% 입니다\n\n잔여현금비중은 " + str(cash_percent) + "% 입니다.")

        msgBox.setStandardButtons(QMessageBox.RestoreDefaults | QMessageBox.Yes | QMessageBox.No)

        msgBox.setDefaultButton(QMessageBox.No)

        result = msgBox.exec_()

        if result == QMessageBox.Yes:

            percent = round(float(percent)/100,2)
            lower_percent = round(float(lower_percent)/100,2)
            mix_percent = round(float(mix_percent)/100,2)
            neutral_percent = round(float(neutral_percent)/100,2)
            upper_percent = round(float(upper_percent)/100,2)
            whole_percent = round(float(whole_percent)/100,2)
            buy_percent = round(float(buy_percent)/100,2)
            lower_diff = round(float(lower_diff)/100,2)
            mix_diff = round(float(mix_diff)/100,2)
            neutral_diff = round(float(neutral_diff)/100,2)
            upper_diff = round(float(upper_diff)/100,2)
            whole_diff = round(float(whole_diff)/100,2)
            buy_diff = round(float(buy_diff)/100,2)

            self.activate()

        if result == QMessageBox.RestoreDefaults :
            f3 = open(str(code) + ".txt", "w")
            f3.write("0,0,0,0,0,0,0,1")
            f3.close()

    def cash(self) :
        value1 = 1 # 기본 1 예외 2

        if value1 == 1 :
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
            cpCash.SetInputValue(0, acc) # 계좌번호
            cpCash.SetInputValue(1, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            cpCash.BlockRequest()
            cash1 = cpCash.GetHeaderValue(3) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash2 = cpCash.GetHeaderValue(9) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash3 = cpCash.GetHeaderValue(11) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
    
        if value1 == 2 :
            CpTd0732 = win32com.client.Dispatch('CpTrade.CpTd0732')
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            CpTd0732.SetInputValue(0, acc) #계좌번호
            CpTd0732.SetInputValue(1, "10") #구분코드 국내주식은 10
            CpTd0732.BlockRequest()
            cash = CpTd0732.GetHeaderValue(3)
        
        cash = cash2 + cash3
        #print(cash2)
        #print(cash3)

        msgBox = QMessageBox()

        msgBox.setWindowTitle("D+2예수금출력")

        msgBox.setIcon(QMessageBox.NoIcon)

        msgBox.setText("< 귀하의 D+2 예수금을 알려드립니다. >      ")

        msgBox.setInformativeText("D+2 예수금은 " + str(format(cash2, ',')) + "원 입니다.")

        result = msgBox.exec_()

    def asset(self) :
        value1 = 1 # 기본 1 예외 2

        if value1 == 1 :
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
            cpCash.SetInputValue(0, acc) # 계좌번호
            cpCash.SetInputValue(1, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            cpCash.BlockRequest()
            cash1 = cpCash.GetHeaderValue(3) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash2 = cpCash.GetHeaderValue(9) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
            cash3 = cpCash.GetHeaderValue(11) # 3 - (longlong) 평가금액(단위:원) 4 - (longlong) 평가손익(단위:원) 8 – (double) 수익율 9 – (longlong) D+2 예상 예수금 11 – (longlong) 잔고평가금액
    
        if value1 == 2 :
            CpTd0732 = win32com.client.Dispatch('CpTrade.CpTd0732')
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            CpTd0732.SetInputValue(0, acc) #계좌번호
            CpTd0732.SetInputValue(1, "10") #구분코드 국내주식은 10
            CpTd0732.BlockRequest()
            cash = CpTd0732.GetHeaderValue(3)
        
        cash = cash2 + cash3

        msgBox = QMessageBox()

        msgBox.setWindowTitle("총자산출력")

        msgBox.setIcon(QMessageBox.NoIcon)

        msgBox.setText("< 귀하의 총자산을 알려드립니다. >      ")

        msgBox.setInformativeText("총자산은 " + str(format(cash, ',')) + "원 입니다.")

        result = msgBox.exec_()

    def stock(self) :
        value1 = 1 # 기본 1 예외 2

        if value1 == 1 :
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
            cpCash.SetInputValue(0, acc) # 계좌번호
            cpCash.SetInputValue(1, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            cpCash.BlockRequest()
    
        if value1 == 2 :
            CpTd0732 = win32com.client.Dispatch('CpTrade.CpTd0732')
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0] # 계좌번호
            CpTd0732.SetInputValue(0, acc) #계좌번호
            CpTd0732.SetInputValue(1, "10") #구분코드 국내주식은 10
            CpTd0732.BlockRequest()
            cash = CpTd0732.GetHeaderValue(3)

        cnt = cpCash.GetHeaderValue(7)

        for i in range(cnt):
            code1 = cpCash.GetDataValue(12, i)  # 종목코드
            volume_1 = cpCash.GetDataValue(7, i) # 체결잔고수량
            volume_2 = cpCash.GetDataValue(15, i) # 매도가능수량
            book = cpCash.GetDataValue(4, i) # 체결장부단가
            rate = cpCash.GetDataValue(11, i) # 수익률
            earning = cpCash.GetDataValue(10, i) # 평가손익
            if i == 0 :
                item=[{'code': code1, 'volume_1': volume_1,'volume_2': volume_2, 'book': book, 'rate': rate, 'earning' : earning}]
                item = pd.DataFrame(item, columns=['code','volume_1','volume_2','book','rate','earning'])
            else :
                item = item.append({'code': code1, 'volume_1': volume_1,'volume_2': volume_2, 'book': book, 'rate': rate, 'earning' : earning},ignore_index=True)

        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("보유자산출력")

        msgBox.setText("< 귀하의 보유자산을 알려드립니다. >      ")
        //안뇽

        if cnt == 0 :

            msgBox.setInformativeText("보유자산은 없습니다.")


        else :

            for i in range(cnt):
                sub_code = item.code[i]
                objStockMst.SetInputValue(0, sub_code)   #종목 코드
                objStockMst.BlockRequest()
 
                # 현재가 통신 및 통신 에러 처리 
                rqStatus = objStockMst.GetDibStatus()
                rqRet = objStockMst.GetDibMsg1()
                print("통신상태", rqStatus, rqRet)
                if rqStatus != 0:
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.NoIcon)
                    msgBox.setWindowTitle("에러메시지")
                    msgBox.setText("통신상태 : " + str(rqStatus) + str(rqRet) + "      ")
                    result = msgBox.exec_()
                    exit()

                # 현재가 정보 조회
                present_close= objStockMst.GetHeaderValue(11) # 종가

                if i == 0:
                    text = "보유주식코드 : " + str(item.code[i]) + ", 보유주식수 : " + str(item.volume_2[i]) + ", 체결잔고수량 : " + str(item.volume_1[i]) + ", 매수가 : " + str(item.book[i]) + ", 현재가 : " + str(present_close) + ", 평가손익 : " + str(item.earning[i]) + ", 수익률 : " + str(round(item.rate[i],2)) + "%"

                else :

                    text = text + "\n보유주식코드 : " + str(item.code[i]) + ", 보유주식수 : " + str(item.volume_2[i]) + ", 체결잔고수량 : " + str(item.volume_1[i]) + ", 매수가 : " + str(item.book[i]) + ", 현재가 : " + str(present_close) + ", 평가손익 : " + str(item.earning[i]) + ", 수익률 : " + str(round(item.rate[i],2)) + "%"

                if i == cnt - 1 :

                    msgBox.setInformativeText(text)

        result = msgBox.exec_()

    def lost(self) :
        CpTd5339 = win32com.client.Dispatch('CpTrade.CpTd5339')
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0] # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # 주식상품 구분
        CpTd5339.SetInputValue(0, acc) #계좌번호
        CpTd5339.SetInputValue(1, accFlag[0])
        CpTd5339.SetInputValue(4, "0") # 전체
        CpTd5339.SetInputValue(5, "1") # 정렬 기준 - 역순
        CpTd5339.SetInputValue(6, "0") # 전체
        CpTd5339.SetInputValue(7, 20) # 요청 개수 - 최대 20개
            
        ret = CpTd5339.BlockRequest()
        if CpTd5339.GetDibStatus() != 0:
            print("통신상태", CpTd5339.GetDibStatus(), CpTd5339.GetDibMsg1())
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setWindowTitle("에러메시지")
            msgBox.setText("통신상태 : " + str(CpTd5339.GetDibStatus()) + str(CpTd5339.GetDibMsg1()) + "      ")
            result = msgBox.exec_()
            exit()

 
        if (ret == 2 or ret == 3):
            print("통신 오류", ret)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setWindowTitle("에러메시지")
            msgBox.setText("통신 오류 : " + str(ret) + "      ")
            result = msgBox.exec_()
            exit()
 
        # 통신 초과 요청 방지에 의한 요류 인 경우
        while (ret == 4) : # 연속 주문 오류 임. 이 경우는 남은 시간동안 반드시 대기해야 함.
            remainTime = g_objCpStatus.LimitRequestRemainTime
            print("연속 통신 초과에 의해 재 통신처리 : ",remainTime/1000, "초 대기" )
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setWindowTitle("에러메시지")
            msgBox.setText("연속 통신 초과에 의해 재 통신처리 : " + str(remainTime/1000) + "초 대기" + "      ")
            result = msgBox.exec_()
            time.sleep(remainTime / 1000)
            ret = CpTd5339.BlockRequest()
            
        cnt1 = CpTd5339.GetHeaderValue(5)    
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.NoIcon)
        msgBox.setWindowTitle("미체결잔량출력")

        msgBox.setText("< 귀하의 미체결잔량을 알려드립니다. >      ")

        if cnt1 == 0 :

            msgBox.setInformativeText("미체결잔량은 없습니다.")


        else :  

            for i in range(cnt1):
                code2 = CpTd5339.GetDataValue(3, i)  # 종목코드
                amount = CpTd5339.GetDataValue(6, i)  # 주문수량
                price2 = CpTd5339.GetDataValue(7, i)  # 주문단가
                ContAmount = CpTd5339.GetDataValue(8, i)  # 체결수량
                if i == 0 :
                    item1=[{'code': code2, 'amount': amount,'price': price2, 'ContAmount': ContAmount}]
                    item1 = pd.DataFrame(item1, columns=['code','amount','price','ContAmount'])
                else :
                    item1 = item1.append({'code': code2, 'amount': amount,'price': price2, 'ContAmount': ContAmount},ignore_index=True)

            for i in range(cnt1):

                if i == 0:
                    text = "보유주식코드 : " + str(item1.code[i]) + ", 원주문수량 : " + str(item1.amount[i]) + ", 주문단가 : " + str(item1.price[i]) + ", 체결수량 : " + str(item1.ContAmount[i]) + ", 미체결수량 : " + str(item1.amount[i] - item1.ContAmount[i])

                else :

                    text = text + "\n보유주식코드 : " + str(item1.code[i]) + ", 원주문수량 : " + str(item1.amount[i]) + ", 주문단가 : " + str(item1.price[i]) + ", 체결수량 : " + str(item1.ContAmount[i]) + ", 미체결수량 : " + str(item1.amount[i] - item1.ContAmount[i])

                if i == cnt1 - 1 :

                    msgBox.setInformativeText(text)

        result = msgBox.exec_()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()

