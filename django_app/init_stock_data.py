import os
import django
from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock
import pytz  # 👈 추가

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

from rag.models import Company, StockPrice
from django.utils import timezone


def init_company_list():
    """종목 마스터(Company) 데이터 초기화"""
    print("🚀 종목 리스트 초기화 시작...")
    
    markets = [("KOSPI", "STK"), ("KOSDAQ", "KSQ")]
    total_created = 0
    total_updated = 0

    for market_name, _ in markets:
        try:
            tickers = stock.get_market_ticker_list(market=market_name)
            print(f"📡 {market_name} 종목 {len(tickers)}개 가져오는 중...")
            
            for ticker in tickers:
                name = stock.get_market_ticker_name(ticker)
                
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


def init_historical_prices(days=365):
    """최근 N일간의 전 종목 일봉 데이터 수집"""
    print(f"\n🚀 최근 {days}일간 전 종목 일봉 데이터 수집 시작...")
    
    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')
    
    # 날짜 범위 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 주말 제외
    while end_date.weekday() >= 5:
        end_date -= timedelta(days=1)
    
    end_str = end_date.strftime("%Y%m%d")
    start_str = start_date.strftime("%Y%m%d")
    
    print(f"📅 수집 기간: {start_str} ~ {end_str}")
    
    # 전체 종목 리스트
    all_companies = Company.objects.filter(is_active=True)
    total_companies = all_companies.count()
    
    print(f"📊 총 {total_companies}개 종목 처리 시작...\n")
    
    total_saved = 0
    success_count = 0
    fail_count = 0
    
    for idx, company in enumerate(all_companies, 1):
        ticker = company.code
        name = company.name
        
        try:
            # 해당 종목의 기간별 OHLCV 데이터 조회
            df = stock.get_market_ohlcv_by_date(start_str, end_str, ticker)
            
            if df.empty:
                print(f"⚠️ [{idx}/{total_companies}] {ticker} ({name}): 데이터 없음")
                fail_count += 1
                continue
            
            saved_count = 0
            for date_idx, row in df.iterrows():
                try:
                    # ✅ timezone-aware datetime으로 변환
                    naive_dt = pd.to_datetime(date_idx).replace(
                        hour=15, 
                        minute=30, 
                        second=0, 
                        microsecond=0
                    )
                    record_time = kst.localize(naive_dt)
                    
                    # DB 저장
                    StockPrice.objects.update_or_create(
                        company=company,
                        record_time=record_time,
                        defaults={
                            'open': float(row['시가']),
                            'high': float(row['고가']),
                            'low': float(row['저가']),
                            'close': float(row['종가']),
                            'volume': int(row['거래량'])
                        }
                    )
                    saved_count += 1
                    
                except Exception as inner_e:
                    print(f"   ❌ {ticker} {date_idx} 저장 실패: {inner_e}")
                    continue
            
            total_saved += saved_count
            success_count += 1
            
            # 진행 상황 출력 (10개마다)
            if idx % 10 == 0:
                print(f"✅ [{idx}/{total_companies}] {ticker} ({name}): {saved_count}일 저장 완료 (누적: {total_saved:,}건)")
            
        except Exception as e:
            print(f"❌ [{idx}/{total_companies}] {ticker} ({name}) 실패: {e}")
            fail_count += 1
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ 데이터 수집 완료!")
    print(f"   - 성공: {success_count}개 종목")
    print(f"   - 실패: {fail_count}개 종목")
    print(f"   - 총 저장: {total_saved:,}건")
    print(f"{'='*60}\n")


def init_latest_prices():
    """당일 최신 시세만 수집"""
    print("\n🚀 당일 최신 시세 수집 시작...")
    
    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')
    
    today = datetime.now()
    while today.weekday() >= 5:
        today -= timedelta(days=1)
    today_str = today.strftime("%Y%m%d")
    
    print(f"📅 수집 날짜: {today_str}")
    
    # ✅ timezone-aware datetime
    current_time = timezone.now().astimezone(kst).replace(
        hour=15, 
        minute=30, 
        second=0, 
        microsecond=0
    )
    
    markets = ["KOSPI", "KOSDAQ"]
    total_saved = 0
    
    for market in markets:
        print(f"\n📡 {market} 시세 가져오는 중...")
        try:
            df = stock.get_market_ohlcv(today_str, market=market)
            print(f"✅ DataFrame 조회 성공: {len(df)}행")
            
            if len(df) == 0:
                print("⚠️ 데이터가 비어있습니다.")
                continue
            
            count = 0
            for ticker, row in df.iterrows():
                try:
                    company = Company.objects.filter(code=ticker).first()
                    if not company:
                        continue
                    
                    StockPrice.objects.update_or_create(
                        company=company,
                        record_time=current_time,
                        defaults={
                            'open': float(row['시가']),
                            'high': float(row['고가']),
                            'low': float(row['저가']),
                            'close': float(row['종가']),
                            'volume': int(row['거래량'])
                        }
                    )
                    count += 1
                    
                    if count % 100 == 0:
                        print(f"   ... {count}개 처리 중")
                        
                except Exception as e:
                    continue
            
            total_saved += count
            print(f"✅ {market} 총 {count}개 저장 완료")
            
        except Exception as e:
            print(f"❌ {market} 시세 수집 실패: {e}")
    
    print(f"\n✅ 당일 시세 총 {total_saved}개 저장 완료")


if __name__ == '__main__':
    import sys
    
    print(f"\n{'='*60}")
    print(f"📊 주식 데이터 수집 프로그램")
    print(f"{'='*60}\n")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    
    if mode == 'full':
        print("🔄 모드: 전체 초기화 (1년치 데이터)")
        init_company_list()
        init_historical_prices(days=365)
        
    elif mode == 'historical':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        print(f"🔄 모드: 히스토리 수집 ({days}일)")
        init_historical_prices(days=days)
        
    elif mode == 'daily':
        print("🔄 모드: 일일 업데이트 (당일만)")
        init_latest_prices()
        
    elif mode == 'company':
        print("🔄 모드: 종목 리스트 업데이트")
        init_company_list()
        
    else:
        print("❌ 알 수 없는 모드입니다.")
        print("사용법:")
        print("  python init_stock_data.py full          # 전체")
        print("  python init_stock_data.py historical    # 1년치")
        print("  python init_stock_data.py historical 30 # 최근 30일")
        print("  python init_stock_data.py daily         # 당일만")
        print("  python init_stock_data.py company       # 종목 리스트만")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🎉 작업 완료!")
    print(f"{'='*60}\n")