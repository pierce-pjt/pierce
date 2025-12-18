import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from config import DJANGO_DB

def save_to_db(data_list):
    """PostgreSQL에 직접 저장 (stock_price 테이블)"""
    if not data_list:
        return 0, 0
    
    conn = psycopg2.connect(**DJANGO_DB)
    cur = conn.cursor()
    
    saved = 0
    updated = 0
    
    try:
        for data in data_list:
            symbol = data['symbol']

            # ✅ 1) stock_list에 종목이 있는지 확인
            cur.execute("SELECT 1 FROM stock_list WHERE symbol = %s", (symbol,))
            exists = cur.fetchone()

            if not exists:
                print(f"⚠️ stock_list에 없는 심볼이라 스킵: {symbol}")
                # 👉 여기서 그냥 continue 해서 이 종목은 안 넣고 넘어감
                continue

            # ✅ 2) 기존 INSERT ... ON CONFLICT 로직
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
                data['record_time'],
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
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
        if data_list:
            print(f"   (Failed Data Sample: {data_list[0]})")
        raise
    finally:
        cur.close()
        conn.close()
    
    return saved, updated
