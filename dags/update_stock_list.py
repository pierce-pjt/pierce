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
}

dag = DAG(
    dag_id="update_stock_list",
    default_args=default_args,
    schedule_interval="0 8 * * 1-5",    # 평일 08:00 실행
)


def get_krx_list(market):
    """KRX에서 KOSPI(KRX:STK), KOSDAQ(KRX:KSQ) 전체 종목 리스트 가져오기"""
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
        "locale": "ko_KR",
        "mktId": market
    }
    js = requests.post(url, data=data).json()
    df = pd.DataFrame(js["OutBlock_1"])
    return df


def update_stock_list():
    hook = PostgresHook(postgres_conn_id="stock_postgres")

    for market_id, market_name in [("STK", "KOSPI"), ("KSQ", "KOSDAQ")]:
        df = get_krx_list(market_id)

        for _, row in df.iterrows():
            sql = """
            INSERT INTO stock_list (symbol, name, market)
            VALUES (%s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE
            SET name = EXCLUDED.name,
                market = EXCLUDED.market;
            """

            hook.run(
                sql,
                parameters=(
                    row["ISU_SRT_CD"],   # 종목코드
                    row["ISU_ABBRV"],    # 종목명
                    market_name
                ),
            )

    print("KOSPI/KOSDAQ 전체 종목 업데이트 완료.")


update_list_task = PythonOperator(
    task_id="update_stock_list",
    python_callable=update_stock_list,
    dag=dag,
)
