from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json
import requests
import re

# 🔹 KOSPI 종목명 로딩용
import FinanceDataReader as fdr  # pip install finance-datareader 필요

# 네이버 API 설정
CLIENT_ID = "azhP2a68ejoD_N1Bwp55"
CLIENT_SECRET = "I9LYuloz92"

# Django API 주소 (LatestNews 테이블용)
DJANGO_API_URL = "http://django:8000/api/latest-news/"

def clean_html(text):
    """HTML 태그 제거"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', text)
    return cleantext

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

# 🔹 KOSPI 종목명 리스트 가져오는 함수
def get_kospi_stock_names(limit=None):
    """
    FinanceDataReader의 KRX 리스트에서
    Market == 'KOSPI' 인 종목명의 리스트를 반환
    """
    print(">>> KOSPI 종목 리스트를 불러오는 중입니다... (잠시 대기)")
    krx_stocks = fdr.StockListing('KRX')              # 전체 KRX
    kospi_stocks = krx_stocks[krx_stocks['Market'] == 'KOSPI']  # KOSPI만 필터
    names = kospi_stocks['Name'].dropna().tolist()

    if limit:
        names = names[:limit]

    print(f">>> 총 {len(names)}개의 KOSPI 종목명을 키워드로 사용합니다.")
    return names

def crawl_and_send_to_django(**context):
    """
    - 여러 키워드(현재는 KOSPI 종목명)에 대해 네이버 뉴스 크롤링
    - 🔸 오늘 날짜(KST 기준)의 기사만 Django로 저장
    """
    params = context.get("params", {})

    # 🔹 1순위: params에 keywords가 들어온 경우 그대로 사용 (기존 로직 유지)
    keywords = params.get("keywords")

    # "경제, 금리, 2차전지" 같은 문자열로 들어오는 경우 처리
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    # 🔹 params에 keywords가 없거나 비어 있으면 KOSPI 종목명을 키워드로 사용
    if not keywords:
        # limit 옵션이 있으면 일부만 사용 가능 (예: 100개만 테스트)
        limit = params.get("limit")  # 없으면 None → 전체
        keywords = get_kospi_stock_names(limit=limit)

    # ✅ 한국 시간(KST) 기준 '오늘 날짜' 계산
    now_kst = datetime.utcnow() + timedelta(hours=9)
    target_date = now_kst.strftime("%Y-%m-%d")

    print(f"📅 수집 대상 날짜(기사 날짜, KST 기준): {target_date}")
    print(f"🔍 검색 키워드 목록 ({len(keywords)}개):")
    for k in keywords:
        print(" -", k)

    display = 100
    start = 1

    total_success = 0
    total_fail = 0

    for keyword in keywords:
        print(f"\n====== 🔎 현재 키워드: {keyword} ======")
        json_data = get_naver_search(keyword, start, display)

        success_count = 0
        fail_count = 0

        if json_data and "items" in json_data:
            for item in json_data["items"]:
                # 1. 기사 날짜 파싱
                try:
                    raw_date = item["pubDate"]  # 예: 'Tue, 26 Nov 2024 09:00:00 +0900'
                    dt_obj = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S +0900")
                    article_date = dt_obj.strftime("%Y-%m-%d")
                except Exception as e:
                    print(f"📛 날짜 파싱 실패, 기사 스킵: {e} / raw={item.get('pubDate')}")
                    continue  # 날짜 모르면 오늘인지 아닌지 모르니 스킵

                # 2. 오늘 날짜가 아니면 스킵
                if article_date != target_date:
                    continue

                # 이 시점에서만 '오늘 날짜 기사'
                formatted_date = article_date

                # 3. 링크 처리
                news_link = item.get("originallink") or item.get("link")

                # 4. 페이로드 생성
                payload = {
                    "title": clean_html(item["title"]),
                    "body": clean_html(item["description"]),
                    "news_collection_date": formatted_date,
                    "url": news_link,
                    "views": 0,
                    # LatestNews에 종목명이나 코드 필드가 있으면 같이 보내도 좋음
                    # "keyword": keyword,
                }

                # 5. Django로 전송
                try:
                    response = requests.post(DJANGO_API_URL, json=payload)
                    if response.status_code == 201:
                        success_count += 1
                    else:
                        print(
                            f"❌ 저장 실패: {payload['title']} "
                            f"- {response.status_code} / {response.text}"
                        )
                        fail_count += 1
                except Exception as e:
                    print(f"💥 전송 에러 ({keyword}): {e}")
                    fail_count += 1

        print(f"➡ 키워드 '{keyword}' 결과: 성공 {success_count}건 / 실패 {fail_count}건")
        total_success += success_count
        total_fail += fail_count

    print(f"\n📊 전체 결과(오늘 기사만): 성공 {total_success}건 / 실패 {total_fail}건")


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

    # 🔹 이제 기본은 KOSPI 종목명 사용.
    #    필요하면 수동으로 keywords나 limit를 설정해서 override 가능.
    params={
        # "keywords": ["삼성전자", "LG에너지솔루션"],  # 수동 테스트용
        "limit": 100,  # 너무 많으면 부담되니 테스트 시에는 일부만 (None이면 전체 KOSPI)
    }

) as dag:

    task = PythonOperator(
        task_id="crawl_and_send_news",
        python_callable=crawl_and_send_to_django,
        provide_context=True,
    )
