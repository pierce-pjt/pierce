# rag/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password
from django.conf import settings
from pgvector.django import CosineDistance
import openai

from .models import (
    User, Post, Follow,
    StockDailyPrice, StockHolding, TransactionHistory,
    HistoricalNews, LatestNews
)
from .serializers import (
    UserSerializer, UserReadSerializer, UserLoginSerializer,
    PostSerializer, FollowSerializer,
    StockDailyPriceSerializer, StockHoldingSerializer, TransactionHistorySerializer,
    HistoricalNewsSerializer, LatestNewsSerializer
)

# --- OpenAI 클라이언트 지연 로딩 ---
openai_client = None

def get_openai_client():
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    # 👇 .env에서 주소 가져오기
    api_base = getattr(settings, 'OPENAI_API_BASE', None) 

    if not api_key:
        print("❌ [CRITICAL] OPENAI_API_KEY가 없습니다!")
        return None
        
    if not api_base:
        print("⚠️ [Warning] OPENAI_API_BASE가 없습니다. 공식 서버로 접속합니다.")
        # 배포된 키라면 base_url이 필수일 확률이 높습니다.

    return openai.OpenAI(
        api_key=api_key,
        base_url=api_base  # 👈 여기가 핵심! 주소를 바꿔치기 합니다.
    )
def get_embedding(text):
    """OpenAI API를 사용하여 텍스트를 벡터(1536차원)로 변환"""
    client = get_openai_client()
    try:
        # 공백 제거 및 줄바꿈 처리 (임베딩 품질 향상)
        text = text.replace("\n", " ")
        
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small" # 가성비 & 성능 최적 모델
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"💥 OpenAI 임베딩 생성 실패: {e}")
        return None
# --------------------------------------

# 1. User ViewSet -----------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer  # 기본은 생성/수정용

    def get_permissions(self):
        # 회원가입, 로그인은 누구나 접근 가능
        if self.action in ["register", "login", "create"]:
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        # 유저 목록 조회 시 비밀번호가 안 보이도록 ReadSerializer 사용
        users = self.get_queryset()
        serializer = UserReadSerializer(users, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserReadSerializer(user)
        return Response(serializer.data)

    # POST /api/users/register/
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """
        회원가입: nickname, password, profile_image_url(optional)
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            read_data = UserReadSerializer(user).data
            return Response(read_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # POST /api/users/login/
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """
        로그인: nickname, password
        - 성공 시 세션에 user_id 저장
        """
        login_serializer = UserLoginSerializer(data=request.data)
        if not login_serializer.is_valid():
            return Response(login_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nickname = login_serializer.validated_data["nickname"]
        password = login_serializer.validated_data["password"]

        try:
            user = User.objects.get(nickname=nickname)
        except User.DoesNotExist:
            return Response({"detail": "존재하지 않는 닉네임입니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({"detail": "비밀번호가 올바르지 않습니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 세션 로그인 (request.session 사용)
        request.session["user_id"] = user.id

        return Response({
            "message": "로그인 성공",
            "user": UserReadSerializer(user).data,
        })

    # POST /api/users/logout/
    @action(detail=False, methods=["post"])
    def logout(self, request):
        """
        로그아웃: 세션 제거
        """
        request.session.flush()
        return Response({"message": "로그아웃 되었습니다."})

    # GET /api/users/me/
    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        현재 로그인한 유저 정보 반환 (세션 기반)
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return Response({"detail": "로그인이 필요합니다."},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "유저를 찾을 수 없습니다."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = UserReadSerializer(user)
        return Response(serializer.data)


# ---------------------------------------------
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




# 2. RAG (뉴스) ViewSets - OpenAI 적용 --------
class HistoricalNewsViewSet(viewsets.ModelViewSet):
    queryset = HistoricalNews.objects.all()
    serializer_class = HistoricalNewsSerializer

    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        if text:
            vector = get_embedding(text)
            if vector:
                serializer.save(body_embedding_vector=vector)
            else:
                # 임베딩 실패 시 저장할지 말지 결정 (여기선 일단 그냥 저장)
                serializer.save()
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def search(self, request):
        query_text = request.data.get('query')
        if not query_text:
            return Response({"error": "query 필드가 필요합니다."}, status=400)
        
        query_vector = get_embedding(query_text)
        if not query_vector:
            return Response({"error": "임베딩 생성에 실패했습니다."}, status=500)
        
        # 코사인 유사도로 상위 5개 검색
        results = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', query_vector)
        ).order_by('distance')[:5]

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

class LatestNewsViewSet(viewsets.ModelViewSet):
    queryset = LatestNews.objects.all()
    serializer_class = LatestNewsSerializer

    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        if text:
            vector = get_embedding(text)
            if vector:
                serializer.save(body_embedding_vector=vector)
            else:
                serializer.save()
        else:
            serializer.save()