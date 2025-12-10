import mojito
from pykrx import stock
from datetime import datetime
import time
import requests
import urllib3
from config import *

# 로그 지저분해지는 것 방지 (InsecureRequestWarning 숨기기)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_broker():
    return mojito.KoreaInvestment(
        api_key=MOJITO_API_KEY,
        api_secret=MOJITO_API_SECRET,
        acc_no=MOJITO_ACC_NO,
        mock=True 
    )

def get_kospi_tickers():
    """코스피 전체 종목"""
    today = datetime.now().strftime("%Y%m%d")
    try:
        tickers = stock.get_market_ticker_list(today, market="KOSPI")
    except:
        tickers = stock.get_market_ticker_list(market="KOSPI")
    
    ticker_names = {}
    for ticker in tickers:
        try:
            ticker_names[ticker] = stock.get_market_ticker_name(ticker)
        except:
            ticker_names[ticker] = "Unknown"
    
    return ticker_names

def fetch_latest_bar(broker, ticker, name):
    """최신 1시간봉 조회 (좀비 모드: 차단되면 60초 대기)"""
    
    max_retries = 5  # 재시도 횟수 증가
    
    for attempt in range(max_retries):
        # 1. 기본 대기 시간 (안전하게 1.1초)
        time.sleep(1.1) 

        try:
            resp = broker.fetch_ohlcv(
                symbol=ticker,
                timeframe=TIMEFRAME, 
                adj_price=True
            )
            
            # [응답 검증]
            if not isinstance(resp, dict):
                print(f"⚠️ 이상한 응답 [{ticker}]: {resp} -> 재시도")
                time.sleep(2.0)
                continue

            # [API 제한 체크] EGW00201 = 초당 건수 초과
            msg_cd = resp.get('msg_cd', '')
            if msg_cd == 'EGW00201':
                print(f"🔥 과부하 감지 [{ticker}]: 5초간 대기 후 재시도 ({attempt+1}/{max_retries})...")
                time.sleep(5.0) 
                continue

            # [정상 데이터 처리]
            if 'output2' in resp:
                data_list = resp['output2']
                if data_list and len(data_list) > 0:
                    latest = data_list[0] 
                    current_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
                    
                    return {
                        'symbol': ticker,
                        'record_time': current_dt,
                        'open': float(latest.get('stck_oprc', 0)),
                        'high': float(latest.get('stck_hgpr', 0)),
                        'low': float(latest.get('stck_lwpr', 0)),
                        'close': float(latest.get('stck_prpr', 0)),
                        'volume': int(latest.get('cntg_vol', 0))
                    }
                else:
                    return None 
            
            # [그 외 API 에러]
            msg1 = resp.get('msg1')
            if msg1:
                print(f"⚠️ API 메시지 [{ticker}]: {msg1}")
                time.sleep(1.0)

        # 🚨 [핵심] 연결 거부(Connection Refused) 발생 시 대처
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ce:
            print(f"🚨 [서버 차단 감지] 1분간 대기합니다... (Zombie Mode On)")
            time.sleep(60.0) # 1분 대기 (차단 풀릴 때까지)
            
        except Exception as e:
            print(f"⚠️ 예외 발생 [{ticker}]: {e}")
            time.sleep(1.0)
    
    print(f"❌ 최종 실패 [{ticker}/{name}] - 건너뜁니다.")
    return None

def collect_data():
    """수집 메인 함수"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now()}] 1시간봉 수집 시작 (좀비 모드)")
    print(f"{'='*60}\n")
    
    broker = get_broker()
    ticker_names = get_kospi_tickers()
    
    print(f"총 {len(ticker_names)}개 종목 수집 시작...")
    
    results = []
    
    for idx, (ticker, name) in enumerate(ticker_names.items(), 1):
        result = fetch_latest_bar(broker, ticker, name)
        
        if result:
            results.append(result)
        
        if idx % 50 == 0:
            print(f"  진행중: {idx}/{len(ticker_names)} (성공: {len(results)}건)")

    print(f"\n✅ 수집 완료: 총 {len(results)}개 데이터 준비됨")
    
    return results