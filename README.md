# 주식자동매매 프로그램
------------
### 왜 이런 프로젝트를 기획하였나요?
> **[ 주식 데이터 ]** 를 가지고<br/>
> **[ 기술적 분석방법별 구현, 수익률 백테스팅 및 자동매매 ]** 를 다뤄보고자<br/>
> **[ CREON API ]** 를 이용한 프로젝트<br/>
------------
### 어떤 기술을 사용하였나요?
> **[ 기술적 분석방법별 구현 ]**
+ **[ matplotlib.pyplot ]** 
  + CREON Plus에서 주식데이터를 가져온 후<br/>
    각 분석방법을 적용한 결과를 matplotlib.pyplot을 사용해 시각적으로 표현하여 검증
> **[ 수익률 백테스팅 ]**
+ **[ backtrader ]** 
  + FinanceDataReader(또는 YahooFinanceData)를 이용해 주식데이터를 가져온 후<br/>
    backtrader의 실행할 전략과 매수매도 단위를 설정하고<br/>
    백테스팅을 수행할 backtrader의 Cerebro에 시드머니와 거래당 수수료 등을 설정하고<br/>
    cerebro의 plot 메서드를 통해 백테스팅 과정을 시각적으로 표현하여 검증
> **[ 자동매매 ]**
+ **[ CREON API ]** 
  + CREON Plus에서 주식데이터를 가져온 후<br/>
    각 전략별 사용자가 입력한 비중조절을 실시한 후 해당 전략을 실행하고<br/>
    매수매도 시그널이 포착되면 CREON API를 이용해 매수매도를 실시하고<br/>
    결과를 Slack을 통해 사용자에게 알림
+ **[ PyQt5.QtWidgets ]** 
  + QApplication을 이용해 GUI 방식의 UI를 구현하고<br/>
    QMessageBox를 이용해 사용자에게 에러메시지 노출
------------
### 프로젝트는 어떤 서비스를 제공하나요?
+ 사용자가 **주식종목코드** 와 **예수금 중 매매비중**, **전략(하락장, 횡보장, 강세장 등)별 비중** 을 설정한 후 실행시키면 각 전략에 따라 매수와 매도를 자동으로 진행
+ **D+2예수금잔액, 총자산, 보유종목, 미체결수량** 등 정보를 제공
------------
### 추후 수정하거나 개발하고 싶은 부분이 있나요?
+ GUI방식의 EXE파일방식은 해당 파일을 가지고 있는 사람만 사용이 가능한 제약<br/>
  => **웹서비스나 앱서비스**로 변경해 불특정다수가 접근이 가능하도록 변경
+ 로직상 최근 10번의 매수시그널이 포착되어야 매수를 진행하는데 최소 10일간의 데이터를 저장할 DB를 운영하지 않기 때문에<br/>
  **파일시스템**을 이용하여 사용자의 로컬저장소에 저장해 사용중<br/>
  => 사용자가 삭제하거나 임의로 변경할 수 있어 취약<br/>
  => **별도의 DB**를 구축하여 웹이나 앱서비스 시 원활한 데이터 적재 가능하도록 구현
+ 불특정다수가 접근하는 서비스의 특성상 처음 접한 서비스라도 이해가능하도록 **직관적인 UI/UX**로 변경
------------
### 프로젝트 설치 및 실행방법은 어떻게 되나요?

------------
### 프로젝트 스크린샷을 첨부해주세요.
+ 스크린샷
  + Login<br/>
    <img width="522" alt="login" src="https://github.com/ParkSungCheol/MapleStoryCommunity/assets/93702296/5960616b-4ff8-4b98-8f84-9658045dad3f">
  + Main&nbsp;Map<br/>
    <img width="526" alt="mainMap" src="https://github.com/ParkSungCheol/MapleStoryCommunity/assets/93702296/5c0aa940-e678-4df6-b861-afb0f6d758e8"><br/>
    <img width="523" alt="mainMap2" src="https://github.com/ParkSungCheol/MapleStoryCommunity/assets/93702296/9fd1535d-bf9f-4610-aa1c-1efe6e235b53">
------------
