from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import json

# 1. Django API 주소 (Docker 내부 통신용)
# 주의: localhost가 아니라 docker-compose의 'container_name'을 써야 합니다!
DJANGO_API_URL = "http://django:8000/api/vectors/"

def send_data_to_django(**context):
    # 예시 데이터 (나중에는 여기서 크롤링을 하거나 파일을 읽으면 됩니다)
    sample_data = [
        "Airflow는 워크플로우 자동화 도구입니다.",
        "RAG 시스템은 검색과 생성을 결합한 기술입니다.",
        "Docker Compose를 쓰면 컨테이너 관리가 쉽습니다."
    ]

    headers = {'Content-Type': 'application/json'}

    for text in sample_data:
        payload = {"content": text}
        
        try:
            # Django에게 POST 요청 보내기
            response = requests.post(DJANGO_API_URL, data=json.dumps(payload), headers=headers)
            
            if response.status_code == 201:
                print(f"✅ 성공: {text}")
            else:
                print(f"❌ 실패: {text} - 이유: {response.text}")
                
        except Exception as e:
            print(f"💥 에러 발생: {e}")

# 2. DAG 정의
with DAG(
    dag_id='rag_data_ingestion',  # Airflow UI에 뜰 이름
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,       # None: 수동 실행 (버튼 눌러야 실행)
    catchup=False,
    tags=['RAG', 'Django']
) as dag:

    # 3. Task 정의
    ingest_task = PythonOperator(
        task_id='send_text_to_django',
        python_callable=send_data_to_django
    )

    ingest_task