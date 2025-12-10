import os
import django
from datetime import datetime
import pandas as pd
from pykrx import stock  # pykrx 라이브러리 사용 (없으면 pip install pykrx)

# 1. Django 환경 설정 (manage.py가 있는 곳 기준)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings') # 프로젝트명 확인!
django.setup()

from rag.models import Company, StockPrice
from django.utils import timezone

def init_company_list():
    """
    1. 종목 마스터(Company) 데이터 초기화
    KRX에서 KOSPI, KOSDAQ 전 종목을 긁어와서 DB에 저장합니다.
    """
    print("🚀 종목 리스트 초기화 시작...")
    
    markets = [("KOSPI", "STK"), ("KOSDAQ", "KSQ")]
    total_created = 0
    total_updated = 0

    for market_name, _ in markets:
        try:
            # pykrx를 이용해 해당 시장의 종목 코드 리스트 가져오기
            tickers = stock.get_market_ticker_list(market=market_name)
            print(f"📡 {market_name} 종목 {len(tickers)}개 가져오는 중...")
            
            for ticker in tickers:
                name = stock.get_market_ticker_name(ticker)
                
                # DB 저장 (Insert or Update)
                obj, created = Company.objects.update_or_create(
                    code=ticker,
                    defaults={
                        'name': name,
                        'market': market_name,
                        'is_active': True
                    }
                )
                
                if created:
                    total_created += 1
                else:
                    total_updated += 1
                    
        except Exception as e:
            print(f"❌ {market_name} 수집 중 에러: {e}")

    print(f"✅ 종목 리스트 완료! (신규: {total_created}, 갱신: {total_updated})")


def init_latest_prices():
    """
    2. 시세 데이터(StockPrice) 초기화
    현재 시간 기준, 전 종목의 시세를 한 번에 긁어와서 저장합니다.
    """
    print("\n🚀 전 종목 현재가 수집 시작 (Snapshot)...")
    
    # 오늘 날짜 (장중이면 현재가, 장 마감이면 종가)
    today = datetime.now().strftime("%Y%m%d")
    current_time = timezone.now().replace(minute=0, second=0, microsecond=0) # 1시간 단위 끊기

    # KOSPI, KOSDAQ 전체 시세 한방에 가져오기 (API 호출 최소화)
    markets = ["KOSPI", "KOSDAQ"]
    
    for market in markets:
        print(f"📡 {market} 시세 가져오는 중...")
        try:
            # 해당 날짜의 전체 종목 시세 조회 (OHLCV)
            df = stock.get_market_ohlcv(today, market=market)
            
            # df.index가 '티커'임
            count = 0
            for ticker, row in df.iterrows():
                try:
                    # 해당 종목이 DB에 없으면 건너뜀 (Company 먼저 실행 필수)
                    if not Company.objects.filter(code=ticker).exists():
                        continue

                    # StockPrice 저장
                    StockPrice.objects.update_or_create(
                        company_id=ticker,
                        record_time=current_time,
                        defaults={
                            'open': row['시가'],
                            'high': row['고가'],
                            'low': row['저가'],
                            'close': row['종가'],
                            'volume': row['거래량']
                        }
                    )
                    count += 1
                except Exception as inner_e:
                    continue
            
            print(f"✅ {market} {count}개 종목 시세 저장 완료")
            
        except Exception as e:
            print(f"❌ {market} 시세 수집 실패: {e}")

if __name__ == '__main__':
    # 1. 종목 마스터부터 채우기
    init_company_list()
    
    # 2. 가격 데이터 채우기
    init_latest_prices()
    
    print("\n🎉 모든 데이터 초기화 완료! 이제 Django 서버를 켜서 확인해보세요.")