from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

def insert_dummy(**context):
    pg = PostgresHook(postgres_conn_id='postgres_default')
    # 더미 문서와 더미 임베딩 삽입 (실 서비스에서는 OpenAI 등에서 임베딩 생성)
    pg.run("INSERT INTO users (username, email) VALUES (%s, %s) ON CONFLICT DO NOTHING", parameters=["testuser","test@example.com"])
    res = pg.get_records("SELECT id FROM users WHERE username=%s", parameters=["testuser"])
    user_id = res[0][0]
    pg.run("INSERT INTO documents (title, content, owner_id) VALUES (%s,%s,%s)", parameters=["hello","this is content", user_id])
    doc_id = pg.get_records("SELECT id FROM documents WHERE owner_id=%s ORDER BY created_at DESC LIMIT 1", parameters=[user_id])[0][0]
    # 임베딩은 더미 배열을 텍스트로 전달 (psycopg2가 vector 형식으로 처리해줌)
    dummy_embedding = [0.01] * 1536
    pg.run("INSERT INTO embeddings (document_id, embedding, chunk_index) VALUES (%s, %s, %s)", parameters=[doc_id, dummy_embedding, 0])

with DAG('example_rag_pipeline', start_date=datetime(2024,1,1), schedule_interval=None, catchup=False) as dag:
    t1 = PythonOperator(task_id='insert_dummy', python_callable=insert_dummy)
