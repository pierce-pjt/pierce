import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

from rag.models import LatestNews
from rag.utils import get_embedding

def fill_missing_vectors():
    # 벡터가 비어있는 뉴스만 찾기
    targets = LatestNews.objects.filter(body_embedding_vector__isnull=True)
    total = targets.count()
    
    print(f"📢 벡터가 없는 최신 뉴스 {total}개를 발견했습니다. 변환을 시작합니다...")

    success_count = 0
    for i, news in enumerate(targets):
        print(f"[{i+1}/{total}] '{news.title[:20]}...' 임베딩 생성 중...")
        
        # 벡터 생성
        vector = get_embedding(news.body)
        
        if vector:
            news.body_embedding_vector = vector
            news.save()
            success_count += 1
        else:
            print(f"❌ 실패: {news.title}")

    print(f"\n✅ 완료! 총 {success_count}/{total}개의 뉴스에 벡터가 주입되었습니다.")

if __name__ == '__main__':
    fill_missing_vectors()