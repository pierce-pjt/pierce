from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied

from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.db.models import Count, Sum
from decimal import Decimal, InvalidOperation
from pgvector.django import CosineDistance

import openai

# 모델 및 시리얼라이저 Import
from .models import (
    User, Post, Follow, Comment, PostLike,
    Company, StockPrice, StockHolding, Transaction,
    HistoricalNews, LatestNews,
    WatchlistItem, StrategyNote, 
)
from .serializers import (
    UserSerializer, UserReadSerializer, UserLoginSerializer,
    PostWriteSerializer, PostReadSerializer, CommentSerializer, FollowSerializer,
    CompanySerializer, StockPriceSerializer, StockHoldingSerializer, TransactionSerializer,
    HistoricalNewsSerializer, LatestNewsSerializer,
    WatchlistItemSerializer, StrategyNoteSerializer
)

# --- OpenAI 설정 ---
def get_openai_client():
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    api_base = getattr(settings, 'OPENAI_API_BASE', None) 
    if not api_key: return None
    return openai.OpenAI(api_key=api_key, base_url=api_base)

def get_embedding(text):
    client = get_openai_client()
    try:
        text = text.replace("\n", " ")
        response = client.embeddings.create(input=[text], model="text-embedding-3-small")
        return response.data[0].embedding
    except Exception as e:
        print(f"💥 OpenAI Error: {e}")
        return None

# --- Helper Function ---
def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise PermissionDenied("로그인이 필요합니다.")
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise PermissionDenied("유저 정보를 찾을 수 없습니다.")


# =================================================
# 1. User & Social ViewSets
# =================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["register", "login", "create", "list", "retrieve", "followers", "following"]:
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().annotate(
            followers_count=Count('followers', distinct=True),
            following_count=Count('following', distinct=True)
        )
        serializer = UserReadSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        target_user = self.get_object()
        serializer = UserReadSerializer(target_user)
        data = serializer.data
        
        user_id = request.session.get("user_id")
        if user_id:
            is_following = Follow.objects.filter(follower_id=user_id, following=target_user).exists()
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
            return Response(UserReadSerializer(user).data, status=status.HTTP_201_CREATED)
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
        return Response({"message": "로그인 성공", "user": UserReadSerializer(user).data})

    @action(detail=False, methods=["post"])
    def logout(self, request):
        request.session.flush()
        return Response({"message": "로그아웃 되었습니다."})

    @action(detail=False, methods=["get"])
    def me(self, request):
        user = get_current_user(request)
        return Response(UserReadSerializer(user).data)

    # --- [수정] url_path 추가하여 /api/users/me/portfolio-summary/ 경로 생성 ---
    @action(detail=False, methods=["get"], url_path="me/portfolio-summary")
    def portfolio_summary(self, request):
        user = get_current_user(request)
        holdings = StockHolding.objects.filter(user=user)
        
        if not holdings.exists():
            return Response({
                "user": UserReadSerializer(user).data,
                "portfolio": {
                    "total_invested": 0, "total_eval": 0,
                    "total_profit": 0, "total_return_rate": 0.0,
                },
                "holdings_count": 0,
            })

        # 보유 종목들의 최신가 조회
        company_codes = [h.company_id for h in holdings]
        
        # Postgres Distinct 활용하여 각 종목별 최신 record_time 데이터 1개씩만 가져오기
        latest_prices = StockPrice.objects.filter(
            company_id__in=company_codes
        ).order_by('company', '-record_time').distinct('company')

        price_map = {p.company_id: p.close for p in latest_prices}

        total_invested = Decimal("0")
        total_eval = Decimal("0")

        for h in holdings:
            invested = h.average_price * h.quantity
            total_invested += invested
            
            # 현재가 없으면 평단가로 계산
            current_price = price_map.get(h.company_id, h.average_price)
            total_eval += current_price * h.quantity

        total_profit = total_eval - total_invested
        total_return_rate = (total_profit / total_invested * 100) if total_invested > 0 else 0

        return Response({
            "user": UserReadSerializer(user).data,
            "portfolio": {
                "total_invested": float(total_invested),
                "total_eval": float(total_eval),
                "total_profit": float(total_profit),
                "total_return_rate": float(round(total_return_rate, 2)),
            },
            "holdings_count": holdings.count(),
        })

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/holdings")
    def holdings(self, request):
        user = get_current_user(request)
        holdings = StockHolding.objects.filter(user=user).select_related('company')

        company_codes = [h.company_id for h in holdings]
        latest_prices = StockPrice.objects.filter(
            company_id__in=company_codes
        ).order_by('company', '-record_time').distinct('company')
        
        price_map = {p.company_id: p.close for p in latest_prices}

        result = []
        for h in holdings:
            invested_amount = h.average_price * h.quantity
            current_price = price_map.get(h.company_id, h.average_price)
            eval_amount = current_price * h.quantity
            profit = eval_amount - invested_amount
            return_rate = (profit / invested_amount * 100) if invested_amount > 0 else 0.0

            result.append({
                "ticker": h.company_id, # 프론트 호환성을 위해 company_id를 ticker 키에 담음
                "company_name": h.company.name,
                "quantity": h.quantity,
                "average_buy_price": float(h.average_price),
                "invested_amount": float(invested_amount),
                "current_price": float(current_price),
                "eval_amount": float(eval_amount),
                "profit": float(profit),
                "return_rate": round(float(return_rate), 2),
                "last_updated": h.updated_at,
            })
        return Response(result)

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/transactions")
    def transactions(self, request):
        user = get_current_user(request)
        # TransactionHistory -> Transaction 모델 사용
        qs = Transaction.objects.filter(user=user).select_related('company').order_by("-created_at")
        limit = request.query_params.get("limit")
        if limit:
            qs = qs[:int(limit)]

        data = []
        for t in qs:
            data.append({
                "ticker": t.company_id,
                "company_name": t.company.name,
                "transaction_datetime": t.created_at,
                "transaction_type": t.type,
                "price": float(t.price),
                "quantity": t.quantity,
                "amount": float(t.amount)
            })
        return Response(data)

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/posts")
    def posts(self, request):
        user = get_current_user(request)
        posts = (
            Post.objects.filter(author=user)
            .select_related("author")
            .annotate(
                comment_count=Count("comments"),
                like_count=Count("likes"),
            )
            .order_by("-created_at")
        )
        serializer = PostReadSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data)

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/liked-posts")
    def liked_posts(self, request):
        user = get_current_user(request)
        posts = (
            Post.objects.filter(likes__user=user)
            .select_related("author")
            .annotate(
                comment_count=Count("comments"),
                like_count=Count("likes"),
            )
            .order_by("-created_at")
            .distinct()
        )
        serializer = PostReadSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data)

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/followers")
    def followers(self, request, pk=None):
        user = get_current_user(request)
        users = [r.follower for r in user.followers.select_related('follower')]
        return Response(UserReadSerializer(users, many=True).data)

    # --- [수정] url_path 추가 ---
    @action(detail=False, methods=["get"], url_path="me/following")
    def following(self, request, pk=None):
        user = get_current_user(request)
        users = [r.following for r in user.following.select_related('following')]
        return Response(UserReadSerializer(users, many=True).data)
    
    @action(detail=True, methods=["post"])
    def follow(self, request, pk=None):
        target_user = self.get_object()
        current_user = get_current_user(request)
        if current_user.id == target_user.id:
            return Response({"detail": "본인은 팔로우할 수 없습니다."}, status=400)
        
        obj, created = Follow.objects.get_or_create(follower=current_user, following=target_user)
        if not created:
            obj.delete()
            return Response({"message": "언팔로우", "is_following": False, "followers_count": target_user.followers.count()})
        return Response({"message": "팔로우", "is_following": True, "followers_count": target_user.followers.count()})


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related("author").annotate(
        comment_count=Count("comments"), like_count=Count("likes")
    )
    serializer_class = PostWriteSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "feed"]:
            return PostReadSerializer
        return PostWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=get_current_user(self.request))

    def perform_update(self, serializer):
        post = self.get_object()
        if post.author != get_current_user(self.request):
            raise PermissionDenied("본인 글만 수정 가능")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != get_current_user(self.request):
            raise PermissionDenied("본인 글만 삭제 가능")
        instance.delete()

    @action(detail=False, methods=["get"])
    def feed(self, request):
        ticker = request.query_params.get("ticker")
        qs = self.get_queryset().order_by("-created_at")
        if ticker:
            qs = qs.filter(ticker=ticker)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        user = get_current_user(request)
        post = self.get_object()
        obj, created = PostLike.objects.get_or_create(post=post, user=user)
        if not created:
            obj.delete()
            liked = False
        else:
            liked = True
        return Response({"liked": liked, "like_count": post.likes.count()})

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "GET":
            qs = post.comments.select_related("author").order_by("created_at")
            return Response(CommentSerializer(qs, many=True).data)
        
        user = get_current_user(request)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, author=user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer


# ========================================================
# 2. Stock ViewSets
# ========================================================

class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']

class StockPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockPrice.objects.all().order_by('record_time')
    serializer_class = StockPriceSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.query_params.get('code')
        if code:
            qs = qs.filter(company_id=code)
        return qs

class StockHoldingViewSet(viewsets.ModelViewSet):
    # 👇 [필수] 라우터 Basename 에러 방지용
    queryset = StockHolding.objects.all()
    serializer_class = StockHoldingSerializer
    
    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id: return StockHolding.objects.none()
        return StockHolding.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        user = get_current_user(self.request)
        serializer.save(user=user)

class TransactionViewSet(viewsets.ModelViewSet):
    # 👇 [필수] 라우터 Basename 에러 방지용
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id: return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id).order_by('-created_at')

    def perform_create(self, serializer):
        user = get_current_user(self.request)
        serializer.save(user=user)


# ========================================================
# 3. News ViewSets
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
        if not query_text: return Response({"error": "query 필요"}, status=400)
        
        vec = get_embedding(query_text)
        if not vec: return Response({"error": "임베딩 실패"}, status=500)
        
        results = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', vec)
        ).order_by('distance')[:5]
        return Response(self.get_serializer(results, many=True).data)

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
        item = self.get_object()
        if not item.body_embedding_vector:
             return Response({"error": "벡터 없음"}, status=400)
        results = LatestNews.objects.exclude(pk=pk).annotate(
            distance=CosineDistance('body_embedding_vector', item.body_embedding_vector)
        ).order_by('distance')[:5]
        return Response(self.get_serializer(results, many=True).data)

    @action(detail=True, methods=['get'], url_path='similar_historical')
    def similar_historical_news(self, request, pk=None):
        item = self.get_object()
        if not item.body_embedding_vector:
            return Response({"message": "분석 중"}, status=200)
        results = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', item.body_embedding_vector)
        ).order_by('distance')[:3]
        return Response(HistoricalNewsSerializer(results, many=True).data)

    @action(detail=False, methods=['post'])
    def search(self, request):
        query_text = request.data.get('query')
        if not query_text: return Response({"error": "query 필요"}, status=400)
        vec = get_embedding(query_text)
        if not vec: return Response({"error": "임베딩 실패"}, status=500)
        results = LatestNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', vec)
        ).order_by('distance')[:5]
        return Response(self.get_serializer(results, many=True).data)


# ========================================================
# 4. MyPage ViewSets
# ========================================================

class WatchlistItemViewSet(viewsets.ModelViewSet):
    queryset = WatchlistItem.objects.all()
    serializer_class = WatchlistItemSerializer

    def get_queryset(self):
        user = get_current_user(self.request)
        return WatchlistItem.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=get_current_user(self.request))

class StrategyNoteViewSet(viewsets.ModelViewSet):
    queryset = StrategyNote.objects.all()
    serializer_class = StrategyNoteSerializer

    def get_queryset(self):
        user = get_current_user(self.request)
        return StrategyNote.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=get_current_user(self.request))