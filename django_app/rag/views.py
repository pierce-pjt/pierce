from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.db.models import Count
from pgvector.django import CosineDistance

import openai

# 👇 [수정] 모델 Import 변경 (StockDailyPrice -> StockPrice 등)
from .models import (
    User, Post, Follow, Comment, PostLike,
    Company, StockPrice, StockHolding, Transaction,
    HistoricalNews, LatestNews,
)

# 👇 [수정] Serializer Import 변경
from .serializers import (
    UserSerializer, UserReadSerializer, UserLoginSerializer,
    PostWriteSerializer, PostReadSerializer, CommentSerializer,
    FollowSerializer,
    CompanySerializer, StockPriceSerializer, StockHoldingSerializer, TransactionSerializer,
    HistoricalNewsSerializer, LatestNewsSerializer
)

# --- OpenAI 클라이언트 지연 로딩 (기존 코드 유지) ---
def get_openai_client():
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    api_base = getattr(settings, 'OPENAI_API_BASE', None) 
    if not api_key:
        print("❌ [CRITICAL] OPENAI_API_KEY가 없습니다!")
        return None
    if not api_base:
        print("⚠️ [Warning] OPENAI_API_BASE가 없습니다. 공식 서버로 접속합니다.")
    return openai.OpenAI(api_key=api_key, base_url=api_base)

def get_embedding(text):
    client = get_openai_client()
    try:
        text = text.replace("\n", " ")
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"💥 OpenAI 임베딩 생성 실패: {e}")
        return None

# =================================================
# 1. User & Social ViewSets (기존 코드 100% 유지)
# =================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["register", "login", "create", "list", "retrieve", "followers", "following"]:
            return [AllowAny()]
        return super().get_permissions()

    def _get_current_user(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            return None
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = qs.annotate(
            followers_count=Count('followers', distinct=True),
            following_count=Count('following', distinct=True)
        )
        serializer = UserReadSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        target_user = self.get_object()
        serializer = UserReadSerializer(target_user)
        data = serializer.data
        
        current_user = self._get_current_user(request)
        if current_user:
            is_following = Follow.objects.filter(follower=current_user, following=target_user).exists()
            data['is_following'] = is_following
        else:
            data['is_following'] = False
            
        data['followers_count'] = target_user.followers.count()
        data['following_count'] = target_user.following.count()
        return Response(data)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            read_data = UserReadSerializer(user).data
            return Response(read_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        login_serializer = UserLoginSerializer(data=request.data)
        if not login_serializer.is_valid():
            return Response(login_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nickname = login_serializer.validated_data["nickname"]
        password = login_serializer.validated_data["password"]

        try:
            user = User.objects.get(nickname=nickname)
        except User.DoesNotExist:
            return Response({"detail": "존재하지 않는 닉네임입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({"detail": "비밀번호가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        request.session["user_id"] = user.id
        return Response({
            "message": "로그인 성공",
            "user": UserReadSerializer(user).data,
        })

    @action(detail=False, methods=["post"])
    def logout(self, request):
        request.session.flush()
        return Response({"message": "로그아웃 되었습니다."})

    @action(detail=False, methods=["get"])
    def me(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "유저를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserReadSerializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def follow(self, request, pk=None):
        target_user = self.get_object()
        current_user = self._get_current_user(request)
        if not current_user:
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        if current_user.id == target_user.id:
            return Response({"detail": "자기 자신은 팔로우할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        follow_obj, created = Follow.objects.get_or_create(follower=current_user, following=target_user)
        if not created:
            follow_obj.delete()
            is_following = False
            message = "언팔로우 했습니다."
        else:
            is_following = True
            message = "팔로우 했습니다."
        return Response({
            "message": message,
            "is_following": is_following,
            "followers_count": target_user.followers.count()
        })

    @action(detail=True, methods=["get"])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers_qs = user.followers.select_related('follower').all()
        follower_users = [f.follower for f in followers_qs]
        serializer = UserReadSerializer(follower_users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def following(self, request, pk=None):
        user = self.get_object()
        following_qs = user.following.select_related('following').all()
        following_users = [f.following for f in following_qs]
        serializer = UserReadSerializer(following_users, many=True)
        return Response(serializer.data)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related("author")
    serializer_class = PostWriteSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "feed"]:
            return PostReadSerializer
        return PostWriteSerializer

    def get_queryset(self):
        qs = Post.objects.all().select_related("author")
        qs = qs.annotate(comment_count=Count("comments"), like_count=Count("likes"))
        return qs

    def _get_current_user(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDenied("로그인이 필요합니다.")
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise PermissionDenied("유저 정보를 찾을 수 없습니다.")

    def perform_create(self, serializer):
        user = self._get_current_user(self.request)
        serializer.save(author=user)

    def perform_update(self, serializer):
        user = self._get_current_user(self.request)
        post = self.get_object()
        if post.author_id != user.id:
            raise PermissionDenied("본인이 작성한 글만 수정할 수 있습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self._get_current_user(self.request)
        if instance.author_id != user.id:
            raise PermissionDenied("본인이 작성한 글만 삭제할 수 있습니다.")
        instance.delete()

    @action(detail=False, methods=["get"])
    def feed(self, request):
        ticker = request.query_params.get("ticker")
        qs = self.get_queryset().order_by("-created_at")
        if ticker:
            qs = qs.filter(ticker=ticker)
        serializer = self.get_serializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        user = self._get_current_user(request)
        post = self.get_object()
        like_obj, created = PostLike.objects.get_or_create(post=post, user=user)
        if not created:
            like_obj.delete()
            liked = False
        else:
            liked = True
        like_count = post.likes.count()
        return Response({"liked": liked, "like_count": like_count})

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "GET":
            comments = post.comments.select_related("author").order_by("created_at")
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        user = self._get_current_user(request)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, author=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer


# ========================================================
# 2. Stock ViewSets (리모델링 반영 및 Company 추가)
# ========================================================

# 2-0. 종목 마스터 조회 (검색용)
class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """종목 검색 및 리스트 조회"""
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']

# 2-1. 시세 차트 데이터
class StockPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """차트 그리기용 시세 데이터 조회"""
    queryset = StockPrice.objects.all().order_by('record_time')
    serializer_class = StockPriceSerializer
    
    # 쿼리 파라미터 필터링 (예: /api/prices/?code=005930)
    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.query_params.get('code')
        if code:
            qs = qs.filter(company_id=code)
        return qs

# 2-2. 내 보유 주식 (Portfolio)
class StockHoldingViewSet(viewsets.ModelViewSet):
    queryset = StockHolding.objects.all()
    serializer_class = StockHoldingSerializer
    
    # 내꺼만 조회
    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id:
            return StockHolding.objects.none()
        return StockHolding.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        user_id = self.request.session.get("user_id")
        user = User.objects.get(id=user_id)
        serializer.save(user=user)

# 2-3. 거래 내역 (Transaction)
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    # 내 거래내역만 조회
    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id:
            return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id).order_by('-created_at')

    def perform_create(self, serializer):
        # 거래 기록 생성 시 자동으로 유저 할당
        user_id = self.request.session.get("user_id")
        user = User.objects.get(id=user_id)
        serializer.save(user=user)


# ========================================================
# 3. News ViewSets (기존 코드 100% 유지)
# ========================================================

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
            return Response({"error": "임베딩 생성 실패"}, status=500)
        
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

    @action(detail=True, methods=['get'], url_path='similar_latest')
    def similar_latest_news(self, request, pk=None):
        news_item = self.get_object() 
        query_vector = news_item.body_embedding_vector
        if not query_vector:
             return Response({"error": "임베딩 벡터가 없습니다."}, status=400)

        results = LatestNews.objects.exclude(pk=pk).annotate(
            distance=CosineDistance('body_embedding_vector', query_vector)
        ).order_by('distance')[:5]

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='similar_historical')
    def similar_historical_news(self, request, pk=None):
        latest_news = self.get_object()
        query_vector = latest_news.body_embedding_vector
        if query_vector is None:
            return Response({"message": "아직 AI 분석이 완료되지 않았습니다."}, status=200)

        similar_docs = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', query_vector)
        ).order_by('distance')[:3]

        serializer = HistoricalNewsSerializer(similar_docs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def search(self, request):
        query_text = request.data.get('query')
        if not query_text:
            return Response({"error": "query 필드가 필요합니다."}, status=400)
        
        try:
            query_vector = get_embedding(query_text)
            if not query_vector:
                return Response({"error": "임베딩 생성 실패"}, status=500)

            results = LatestNews.objects.annotate(
                distance=CosineDistance('body_embedding_vector', query_vector)
            ).order_by('distance')[:5]

            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)