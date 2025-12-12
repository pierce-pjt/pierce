from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json
import requests
import re
import html 
import FinanceDataReader as fdr

# 네이버 API 설정
CLIENT_ID = "azhP2a68ejoD_N1Bwp55"
CLIENT_SECRET = "I9LYuloz92"

# Django API 주소
DJANGO_API_URL = "http://django:8000/api/latest-news/"

def clean_html(text):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', text)
    
    return html.unescape(cleantext)

def analyze_sentiment_basic(text):
    """간단 감성 분석"""
    positive_keywords = ['급등', '강세', '상승', '호재', '대박', '성장', '최고', '수주', '흑자', '돌파', '기대']
    negative_keywords = ['급락', '약세', '하락', '악재', '적자', '우려', '바닥', '손실', '둔화', '위기', '불안']
    text = text.replace(" ", "")
    if any(keyword in text for keyword in positive_keywords): return 'positive'
    elif any(keyword in text for keyword in negative_keywords): return 'negative'
    else: return 'neutral'

def extract_source_from_url(url):
    """URL에서 언론사 도메인 추출"""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return "Internet News"

# 👇 [추가] 뉴스 페이지에 직접 접속해서 og:image (대표 이미지) 추출
def extract_og_image(url):
    try:
        # 1초 안에 응답 없으면 포기 (속도 저하 방지)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=1.5)
        
        if response.status_code == 200:
            html = response.text
            # <meta property="og:image" content="..."> 패턴 찾기
            match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if match:
                return match.group(1) # 이미지 URL 반환
    except Exception:
        pass # 이미지 없거나 접속 실패하면 쿨하게 패스
    return None

def get_request_url(url):
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"[ERROR] API Request Failed: {e}")
        return None

def get_naver_search(keyword, start, display):
    base = "https://openapi.naver.com/v1/search/news.json"
    params = f"?query={urllib.parse.quote(keyword)}&start={start}&display={display}&sort=date"
    url = base + params
    result = get_request_url(url)
    return json.loads(result) if result else None

def get_kospi_stock_names(limit=None):
    print(">>> KOSPI 종목 리스트 로딩...")
    krx_stocks = fdr.StockListing('KRX')              
    kospi_stocks = krx_stocks[krx_stocks['Market'] == 'KOSPI']  
    names = kospi_stocks['Name'].dropna().tolist()
    if limit: names = names[:limit]
    print(f">>> 총 {len(names)}개의 종목 키워드 사용")
    return names

def crawl_and_send_to_django(**context):
    params = context.get("params", {})
    keywords = params.get("keywords")

    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    if not keywords:
        limit = params.get("limit")  
        keywords = get_kospi_stock_names(limit=limit)

    now_kst = datetime.utcnow() + timedelta(hours=9)
    target_date = now_kst.strftime("%Y-%m-%d")
    print(f"📅 수집 대상 날짜: {target_date}")
    
    display = 3
    start = 1
    total_success = 0
    total_fail = 0

    for keyword in keywords:
        print(f"\n====== 🔎 키워드: {keyword} ======")
        json_data = get_naver_search(keyword, start, display)

        success_count = 0
        fail_count = 0

        if json_data and "items" in json_data:
            for item in json_data["items"]:
                # 1. 날짜 파싱 및 필터링
                try:
                    raw_date = item["pubDate"]
                    dt_obj = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S +0900")
                    article_date = dt_obj.strftime("%Y-%m-%d")
                    
                    # ⭐ [수정] ISO 포맷으로 변환 (YYYY-MM-DDTHH:MM:SS)
                    full_date_time = dt_obj.isoformat()
                except:
                    continue

                if article_date != target_date:
                    continue

                # 2. 데이터 정제
                title_clean = clean_html(item["title"])
                description_clean = clean_html(item["description"])
                news_link = item.get("originallink") or item.get("link")
                
                # ⭐ [안전장치] 빈 문자열이면 에러날 수 있으므로 기본값 처리
                if not title_clean: title_clean = "제목 없음"
                if not description_clean: description_clean = "내용 없음"

                # 3. 데이터 전송 준비
                image_url = extract_og_image(news_link)

                payload = {
                    "title": title_clean[:255], # 길이 제한
                    "body": description_clean,
                    "news_collection_date": full_date_time,
                    "url": news_link,
                    "views": 0,
                    "company_name": keyword,
                    "source": extract_source_from_url(news_link)[:50],
                    "sentiment": analyze_sentiment_basic(title_clean),
                    "image_url": image_url
                }
                
                # ⭐ [핵심] JSON으로 에러 메시지를 받기 위한 헤더
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }

                try:
                    response = requests.post(DJANGO_API_URL, json=payload, headers=headers)
                    if response.status_code == 201:
                        success_count += 1
                    else:
                        # 이제 로그에 HTML이 아니라 {"title": ["This field is required"]} 처럼 나옵니다!
                        print(f"❌ 실패 ({response.status_code}): {response.text}")
                        fail_count += 1
                except Exception as e:
                    print(f"💥 전송 에러: {e}")
                    fail_count += 1

        print(f"➡ '{keyword}' 결과: 성공 {success_count} / 실패 {fail_count}")
        total_success += success_count
        total_fail += fail_count

    print(f"\n📊 전체 결과: 성공 {total_success} / 실패 {total_fail}")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="naver_news_to_postgres",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    params={"limit": 100}
) as dag:
    task = PythonOperator(
        task_id="crawl_and_send_news",
        python_callable=crawl_and_send_to_django,
        provide_context=True,
    )