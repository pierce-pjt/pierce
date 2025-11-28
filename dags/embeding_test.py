import openai
import requests
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime, timedelta

# 네이버 API 설정
CLIENT_ID = "azhP2a68ejoD_N1Bwp55"
CLIENT_SECRET = "I9LYuloz92"

# Django API 주소 (LatestNews 테이블용)
DJANGO_API_URL = "http://django:8000/api/latest-news/"

# GPT-4 임베딩을 생성하는 함수
def get_gpt_embeddings(text):
    try:
        response = openai.embeddings.create(
            model="gpt-4",  # GPT-4 모델을 사용
            input=text
        )
        embeddings = response['data'][0]['embedding']
        return embeddings
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []

# HTML 태그 제거 함수
def clean_html(text):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', text)
    return cleantext

# 네이버 뉴스 검색 API 호출 함수
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

# 네이버 뉴스 검색 함수
def get_naver_search(keyword, start, display):
    base = "https://openapi.naver.com/v1/search/news.json"
    params = f"?query={urllib.parse.quote(keyword)}&start={start}&display={display}&sort=date"
    url = base + params
    
    result = get_request_url(url)
    return json.loads(result) if result else None

# 뉴스 크롤링 및 Django에 전송하는 함수
def crawl_and_send_to_django(keywords, limit=100):
    # 한국 시간(KST) 기준 '오늘 날짜' 계산
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
    processed_count = 0  # 임베딩 처리 개수 제한을 위한 변수

    for keyword in keywords:
        print(f"\n====== 🔎 현재 키워드: {keyword} ======")
        json_data = get_naver_search(keyword, start, display)

        success_count = 0
        fail_count = 0

        if json_data and "items" in json_data:
            for item in json_data["items"]:
                if processed_count >= limit:
                    break  # 설정된 개수만큼 처리 후 종료

                # 기사 날짜 파싱
                try:
                    raw_date = item["pubDate"]
                    dt_obj = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S +0900")
                    article_date = dt_obj.strftime("%Y-%m-%d")
                except Exception as e:
                    print(f"📛 날짜 파싱 실패, 기사 스킵: {e} / raw={item.get('pubDate')}")
                    continue

                # 오늘 날짜가 아니면 스킵
                if article_date != target_date:
                    continue

                # 임베딩 생성
                body = clean_html(item["description"])
                embedding = get_gpt_embeddings(body)

                # 페이로드 생성
                payload = {
                    "title": clean_html(item["title"]),
                    "body": body,
                    "news_collection_date": article_date,
                    "url": item.get("originallink") or item.get("link"),
                    "views": 0,
                    "embedding_vector": embedding,  # 임베딩 값 추가
                }

                # Django로 전송
                try:
                    response = requests.post(DJANGO_API_URL, json=payload)
                    if response.status_code == 201:
                        success_count += 1
                    else:
                        print(f"❌ 저장 실패: {payload['title']} - {response.status_code} / {response.text}")
                        fail_count += 1
                except Exception as e:
                    print(f"💥 전송 에러 ({keyword}): {e}")
                    fail_count += 1

                processed_count += 1  # 처리된 기사 카운트 증가

        print(f"➡ 키워드 '{keyword}' 결과: 성공 {success_count}건 / 실패 {fail_count}건")
        total_success += success_count
        total_fail += fail_count

    print(f"\n📊 전체 결과(오늘 기사만): 성공 {total_success}건 / 실패 {total_fail}건")

# 테스트용 키워드 설정
keywords = ["삼성전자", "LG에너지솔루션"]  # 예시로 두 개의 키워드만 사용
crawl_and_send_to_django(keywords, limit=100)  # 100개 기사로 제한하여 테스트
