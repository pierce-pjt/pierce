import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from config import DJANGO_DB

def save_to_db(data_list):
    """PostgreSQL에 직접 저장 (Django stock_price 테이블)"""
    if not data_list:
        return 0, 0
    
    conn = psycopg2.connect(**DJANGO_DB)
    cur = conn.cursor()
    
    saved = 0
    updated = 0
    
    try:
        for data in data_list:
            # 1. 테이블명 변경: rag_stockdailyprice -> stock_price
            # 2. 컬럼명 변경: trade_date -> record_time
            # 3. 딕셔너리 키 변경: data['trade_date'] -> data['record_time']
            cur.execute("""
                INSERT INTO stock_price 
                    (symbol, record_time, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, record_time) 
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
                RETURNING (xmax = 0) AS inserted
            """, (
                data['symbol'],
                data['record_time'],  # <-- 여기가 핵심 (시간 정보 포함)
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume']
                # created_at은 Django 모델에서 auto_now_add=True이므로 
                # DB가 알아서 넣게 하거나, 필요시 수동 추가해도 됩니다.
                # 여기선 SQL에서 뺐습니다 (DB Default값 사용)
            ))
            
            result = cur.fetchone()
            if result and result[0]:
                saved += 1
            else:
                updated += 1
        
        conn.commit()
        print(f"✅ DB 저장 완료: 신규 {saved}개, 업데이트 {updated}개")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ DB 저장 실패: {e}")
        # 어떤 데이터에서 에러 났는지 디버깅용 로그
        if data_list:
            print(f"   (Failed Data Sample: {data_list[0]})")
        raise
    finally:
        cur.close()
        conn.close()
    
    return saved, updated