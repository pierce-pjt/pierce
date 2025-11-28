from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from pgvector.django import CosineDistance
import openai  # Assuming OpenAI GPT is used

from .models import (
    User, Post, Follow, 
    StockDailyPrice, StockHolding, TransactionHistory,
    HistoricalNews, LatestNews
)
from .serializers import (
    UserSerializer, PostSerializer, FollowSerializer,
    StockDailyPriceSerializer, StockHoldingSerializer, TransactionHistorySerializer,
    HistoricalNewsSerializer, LatestNewsSerializer
)

# --- AI 모델 지연 로딩 (메모리 최적화) ---
gpt_embedding_model = None

def get_gpt_embedding_model():
    global gpt_embedding_model
    if gpt_embedding_model is None:
        print("⏳ GPT 모델 로딩 시작...")
        openai.api_key = 'S14P02BB05-24ba2286-b737-41bb-83cf-bdb39d3ee31e'  # Make sure you set your API key
        gpt_embedding_model = 'gpt-4'  # Example of GPT-3 embedding model
        print("✅ GPT 모델 로딩 완료!")
    return gpt_embedding_model

# --------------------------------------

# 1. 일반 CRUD ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

class StockDailyPriceViewSet(viewsets.ModelViewSet):
    queryset = StockDailyPrice.objects.all()
    serializer_class = StockDailyPriceSerializer

class StockHoldingViewSet(viewsets.ModelViewSet):
    queryset = StockHolding.objects.all()
    serializer_class = StockHoldingSerializer

class TransactionHistoryViewSet(viewsets.ModelViewSet):
    queryset = TransactionHistory.objects.all()
    serializer_class = TransactionHistorySerializer

# 2. RAG (뉴스) ViewSets - 자동 임베딩 및 검색 기능
class HistoricalNewsViewSet(viewsets.ModelViewSet):
    queryset = HistoricalNews.objects.all()
    serializer_class = HistoricalNewsSerializer

    # 저장 시 자동 임베딩 (GPT를 사용하여 임베딩 생성)
    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        if text:
            model = get_gpt_embedding_model()
            embedding = self.get_gpt_embeddings(text)  # Generate embedding from GPT model
            serializer.save(body_embedding_vector=embedding)
        else:
            serializer.save()

    # GPT 기반 유사도 검색 기능 (POST /api/historical-news/search/)
    @action(detail=False, methods=['post'])
    def search(self, request):
        query_text = request.data.get('query')
        if not query_text:
            return Response({"error": "query 필드가 필요합니다."}, status=400)
        
        model = get_gpt_embedding_model()
        query_embedding = self.get_gpt_embeddings(query_text)
        
        # 코사인 유사도로 상위 5개 검색
        results = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', query_embedding)
        ).order_by('distance')[:5]

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    # GPT API를 호출하여 임베딩을 생성
    def get_gpt_embeddings(self, text):
        try:
            response = openai.Embedding.create(
                model="gpt-4",  # Example model
                input=text
            )
            embeddings = response['data'][0]['embedding']
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

class LatestNewsViewSet(viewsets.ModelViewSet):
    queryset = LatestNews.objects.all()
    serializer_class = LatestNewsSerializer

    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        if text:
            model = get_gpt_embedding_model()
            embedding = self.get_gpt_embeddings(text)
            serializer.save(body_embedding_vector=embedding)
        else:
            serializer.save()

    # GPT API를 호출하여 임베딩을 생성
    def get_gpt_embeddings(self, text):
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",  # Example model
                input=text
            )
            embeddings = response['data'][0]['embedding']
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
