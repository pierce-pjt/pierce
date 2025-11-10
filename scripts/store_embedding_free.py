# scripts/store_embedding_free.py
import os
import psycopg2
from sentence_transformers import SentenceTransformer

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ragdb")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")

# 무료 임베딩 모델 (384차원)
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    return model.encode(text).tolist()

def main():
    text = "Hello from local script to test embeddings"
    emb = get_embedding(text)
    
    conn = psycopg2.connect(
        host=DB_HOST, 
        port=DB_PORT, 
        dbname=DB_NAME, 
        user=DB_USER, 
        password=DB_PASS
    )
    cur = conn.cursor()
    
    # documents 테이블에 삽입
    cur.execute(
        "INSERT INTO documents (title, content) VALUES (%s, %s) RETURNING id", 
        ("local test", text)
    )
    doc_id = cur.fetchone()[0]
    
    # embeddings 테이블에 삽입
    emb_str = '[' + ','.join(map(str, emb)) + ']'
    cur.execute(
        "INSERT INTO embeddings (document_id, embedding, chunk_index) VALUES (%s, %s::vector, %s)", 
        (doc_id, emb_str, 0)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored embedding for doc_id: {doc_id}")

if __name__ == "__main__":
    main()