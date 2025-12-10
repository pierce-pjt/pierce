import requests
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 11, 20),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="update_stock_list",
    default_args=default_args,
    schedule_interval="0 8 * * 1-5",    # 평일 08:00 실행
    catchup=False, # 과거 데이터 실행 방지
)


def get_krx_list(market):
    """KRX에서 KOSPI(KRX:STK), KOSDAQ(KRX:KSQ) 전체 종목 리스트 가져오기"""
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    
    # 🚨 [핵심 수정] 헤더 추가 (봇 탐지 우회)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    
    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
        "locale": "ko_KR",
        "mktId": market,
        "share": "1",
        "csvxls_isNo": "false",
    }
    
    # headers 옵션 추가
    response = requests.post(url, data=data, headers=headers)
    
    # 응답 상태 코드 확인 (200이 아니면 에러 발생시키기)
    if response.status_code != 200:
        raise Exception(f"KRX API Error: {response.status_code}")

    js = response.json()
    df = pd.DataFrame(js["OutBlock_1"])
    return df


def update_stock_list():
    # Airflow Admin > Connections에 'stock_postgres'가 등록되어 있어야 함
    hook = PostgresHook(postgres_conn_id="stock_postgres")

    for market_id, market_name in [("STK", "KOSPI"), ("KSQ", "KOSDAQ")]:
        try:
            print(f"📡 Retrieving {market_name} list...")
            df = get_krx_list(market_id)
            print(f"✅ Fetched {len(df)} rows for {market_name}")

            # DB 연결 및 커서 획득
            conn = hook.get_conn()
            cursor = conn.cursor()

            for _, row in df.iterrows():
                sql = """
                INSERT INTO stock_list (symbol, name, market)
                VALUES (%s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET name = EXCLUDED.name,
                    market = EXCLUDED.market;
                """
                cursor.execute(
                    sql,
                    (
                        row["ISU_SRT_CD"],   # 종목코드 (symbol)
                        row["ISU_ABBRV"],    # 종목명 (name)
                        market_name          # 시장구분 (market)
                    ),
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error updating {market_name}: {e}")
            raise  # 에러 발생 시 Airflow Task를 실패 처리

    print("🎉 KOSPI/KOSDAQ 전체 종목 업데이트 완료.")


update_list_task = PythonOperator(
    task_id="update_stock_list",
    python_callable=update_stock_list,
    dag=dag,
)