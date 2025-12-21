import os
import django
import pandas as pd
import time
import openai
import pytz  # 👈 추가
from datetime import datetime  # 👈 추가
from django.conf import settings

# 1. Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

from rag.models import HistoricalNews, StockPrice, Company

# 2. OpenAI 클라이언트 설정
client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE
)

# 👇 한국 시간대 설정
kst = pytz.timezone('Asia/Seoul')

def get_embedding(text):
    """OpenAI API로 임베딩 생성 (길이 제한 적용)"""
    try:
        if not text: return None
        text = text.replace("\n", " ")
        
        # OpenAI max token 안전 제한
        if len(text) > 5000:
            text = text[:5000]

        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"💥 임베딩 실패: {e}")
        return None

def import_news():
    print("📰 뉴스 데이터 적재 및 임베딩 생성 시작... (시간이 좀 걸립니다)")
    
    try:
        df = pd.read_csv('news_data_20251203_1625.csv')
    except FileNotFoundError:
        print("❌ 뉴스 CSV 파일을 찾을 수 없습니다.")
        return

    news_list = []
    total = len(df)

    for idx, row in df.iterrows():
        impacted_ticker = str(row['impacted_ticker'])
        if len(impacted_ticker) > 500:
            impacted_ticker = impacted_ticker[:500]

        vector = get_embedding(row['body'])
        
        # 👇 news_collection_date를 timezone-aware로 변환
        try:
            # CSV의 날짜 형식에 맞게 조정 (예: '2025-12-03' 또는 '2025-12-03 16:25:00')
            if isinstance(row['news_collection_date'], str):
                # 날짜만 있는 경우
                if ' ' not in row['news_collection_date']:
                    naive_dt = datetime.strptime(row['news_collection_date'], '%Y-%m-%d')
                else:
                    # 날짜 + 시간이 있는 경우
                    naive_dt = datetime.strptime(row['news_collection_date'], '%Y-%m-%d %H:%M:%S')
            else:
                # pandas Timestamp인 경우
                naive_dt = pd.to_datetime(row['news_collection_date']).to_pydatetime()
            
            # timezone-aware로 변환
            news_collection_date = kst.localize(naive_dt)
            
        except Exception as e:
            print(f"⚠️ 날짜 변환 실패 (row {idx}): {e}, 현재 시간 사용")
            news_collection_date = datetime.now(kst)
        
        news = HistoricalNews(
            news_collection_date=news_collection_date,  # 👈 수정
            title=row['title'],
            body=row['body'],
            url=row['url'],
            impacted_ticker=impacted_ticker,
            body_embedding_vector=vector
        )
        news_list.append(news)

        if (idx + 1) % 10 == 0:
            print(f"   ... {idx + 1}/{total} 처리 중")

    HistoricalNews.objects.bulk_create(news_list)
    print(f"✅ 뉴스 {len(news_list)}건 저장 및 임베딩 완료!")

def import_stock():
    print("\n📈 주식 데이터 적재 시작...")
    try:
        df = pd.read_csv('stock_data_20251203_1625.csv')
    except FileNotFoundError:
        print("❌ 주식 CSV 파일을 찾을 수 없습니다.")
        return

    # 티커 포맷팅 (6자리 맞춤)
    df['ticker'] = df['ticker'].astype(str).str.zfill(6)
    
    # 중복 제거 (티커 + 날짜 기준)
    df.drop_duplicates(subset=['ticker', 'date'], keep='first', inplace=True)

    # Company 객체 선행 생성
    print("🏢 종목 정보(Company) 확인 및 생성 중...")
    unique_tickers = df['ticker'].unique()
    
    for ticker in unique_tickers:
        Company.objects.get_or_create(
            code=ticker,
            defaults={'name': f"종목_{ticker}", 'market': 'KOSPI', 'is_active': True} 
        )
    
    # 빠른 조회를 위해 Company 객체들을 딕셔너리로 로딩
    company_map = {c.code: c for c in Company.objects.all()}

    stock_list = []
    print(f"📊 처리할 주식 데이터: {len(df)}건")
    
    for idx, row in df.iterrows():
        # 해당 티커의 Company 객체 가져오기
        company_obj = company_map.get(row['ticker'])
        
        if not company_obj:
            continue
        
        # 👇 record_time을 timezone-aware로 변환
        try:
            # CSV의 날짜 형식에 맞게 조정
            if isinstance(row['date'], str):
                # 날짜만 있는 경우 (예: '2025-12-03')
                if ' ' not in row['date']:
                    naive_dt = datetime.strptime(row['date'], '%Y-%m-%d')
                    # 장 마감 시간으로 설정 (15:30)
                    naive_dt = naive_dt.replace(hour=15, minute=30, second=0, microsecond=0)
                else:
                    # 날짜 + 시간이 있는 경우
                    naive_dt = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
            else:
                # pandas Timestamp인 경우
                naive_dt = pd.to_datetime(row['date']).to_pydatetime()
                if naive_dt.hour == 0 and naive_dt.minute == 0:
                    # 시간이 00:00이면 15:30으로 설정
                    naive_dt = naive_dt.replace(hour=15, minute=30)
            
            # timezone-aware로 변환
            record_time = kst.localize(naive_dt)
            
        except Exception as e:
            print(f"⚠️ 날짜 변환 실패 (row {idx}, ticker {row['ticker']}): {e}")
            continue

        stock = StockPrice(
            company=company_obj,
            record_time=record_time,  # 👈 수정
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume'])
        )
        stock_list.append(stock)
        
        # 진행 상황 표시
        if (idx + 1) % 500 == 0:
            print(f"   ... {idx + 1}/{len(df)} 처리 중")

    # ignore_conflicts=True: 이미 있는 날짜면 에러 안 내고 넘어감
    StockPrice.objects.bulk_create(stock_list, ignore_conflicts=True)
    print(f"✅ 주식 데이터 저장 완료!")

if __name__ == '__main__':
    print("🧹 기존 데이터를 초기화합니다...")
    HistoricalNews.objects.all().delete()
    StockPrice.objects.all().delete()
    # 주의: Company는 다른 데이터와 연결될 수 있어 필요시만 삭제
    # Company.objects.all().delete()
    
    import_news()
    import_stock()
    
    print("\n🎉 모든 데이터 적재 완료!")