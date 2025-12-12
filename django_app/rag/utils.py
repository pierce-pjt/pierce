import openai
from django.conf import settings

# Django settings에서 API 키 가져오기
client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE
)

def get_embedding(text):
    """텍스트를 벡터로 변환하는 함수"""
    try:
        if not text: 
            return None
        
        # 텍스트 전처리
        text = text.replace("\n", " ")
        if len(text) > 5000:
            text = text[:5000]

        # OpenAI API 호출
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
        
    except Exception as e:
        print(f"💥 임베딩 생성 실패: {e}")
        return None