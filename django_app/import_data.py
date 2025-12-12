import os
import django
import pandas as pd
import time
import openai
from django.conf import settings

# 1. Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

# 👇 [수정] 모델명 변경 (StockDailyPrice -> StockPrice, Company 추가)
from rag.models import HistoricalNews, StockPrice, Company

# 2. OpenAI 클라이언트 설정
client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE
)

def get_embedding(text):
    """OpenAI API로 임베딩 생성 (길이 제한 적용) - 기존 로직 유지"""
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
        # 파일명은 그대로 유지
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
        
        # HistoricalNews 모델 필드명은 기존과 동일하므로 그대로 유지
        news = HistoricalNews(
            news_collection_date=row['news_collection_date'],
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

    # 👇 [추가] Company 객체 선행 생성 (ForeignKey 연결을 위해 필수)
    print("🏢 종목 정보(Company) 확인 및 생성 중...")
    unique_tickers = df['ticker'].unique()
    
    # CSV에 종목명이 없으면 티커를 이름으로 사용, 있으면 name 컬럼 사용 권장
    # 여기서는 CSV 구조를 모르니 티커를 이름으로 임시 사용하거나 'Unknown' 처리
    for ticker in unique_tickers:
        Company.objects.get_or_create(
            code=ticker,
            defaults={'name': f"종목_{ticker}", 'market': 'KOSPI'} 
        )
    
    # 빠른 조회를 위해 Company 객체들을 딕셔너리로 로딩
    company_map = {c.code: c for c in Company.objects.all()}

    stock_list = []
    print(f"📊 처리할 주식 데이터: {len(df)}건")
    
    for _, row in df.iterrows():
        # 해당 티커의 Company 객체 가져오기
        company_obj = company_map.get(row['ticker'])
        
        if not company_obj:
            continue # 만약 Company가 없으면 스킵

        # 👇 [수정] StockPrice 모델 필드명에 맞춰 변경
        stock = StockPrice(
            company=company_obj,       # ForeignKey 객체 할당
            record_time=row['date'],   # date -> record_time
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume']
        )
        stock_list.append(stock)

    # ignore_conflicts=True: 이미 있는 날짜면 에러 안 내고 넘어감
    StockPrice.objects.bulk_create(stock_list, ignore_conflicts=True)
    print(f"✅ 주식 데이터 저장 완료!")

if __name__ == '__main__':
    print("🧹 기존 데이터를 초기화합니다...")
    # 모델명 변경 반영
    HistoricalNews.objects.all().delete()
    StockPrice.objects.all().delete()
    # 주의: Company는 다른 데이터(포트폴리오 등)와 연결될 수 있어 삭제 시 주의 필요
    # 테스트 단계라면 Company도 초기화해도 됨: Company.objects.all().delete()
    
    import_news()
    import_stock()