from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.db.models import F, OuterRef, Subquery, DecimalField, BigIntegerField, Value, FloatField, Count, Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal, InvalidOperation
from pgvector.django import CosineDistance
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models.functions import Coalesce, Cast
from rag.models import Follow 

import yfinance as yf
from django.db import transaction
from datetime import timedelta
import openai
import pandas as pd
import numpy as np



from .utils import get_embedding, update_similarity_score


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

from django.db.models import F, OuterRef, Subquery, DecimalField, BigIntegerField, FloatField
from rest_framework import viewsets, filters
from .models import Company, StockPrice
from .serializers import CompanySerializer

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
# =================================================@method_decorator(csrf_exempt, name='dispatch')
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
            return Response(
                UserReadSerializer(user, context={'request': request}).data, 
                status=status.HTTP_201_CREATED
            )
        
        print("❌ 회원가입 실패 에러:", serializer.errors) 
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

    @action(detail=False, methods=["get"], url_path="me/portfolio-summary")
    def portfolio_summary(self, request):
        user = get_current_user(request)
        # 🆕 수량이 0보다 큰 것만 조회
        holdings = StockHolding.objects.filter(user=user, quantity__gt=0)
        
        if not holdings.exists():
            return Response({
                "user": UserReadSerializer(user).data,
                "portfolio": {
                    "total_invested": 0, "total_eval": 0,
                    "total_profit": 0, "total_return_rate": 0.0,
                },
                "holdings_count": 0,
            })

        company_codes = [h.company_id for h in holdings]
        latest_prices = StockPrice.objects.filter(
            company_id__in=company_codes
        ).order_by('company', '-record_time').distinct('company')

        price_map = {p.company_id: p.close for p in latest_prices}

        total_invested = Decimal("0")
        total_eval = Decimal("0")

        for h in holdings:
            invested = h.average_price * h.quantity
            total_invested += invested
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

    @action(detail=False, methods=["get"], url_path="me/holdings")
    def holdings(self, request):
        user = get_current_user(request)
        # 🆕 수량이 0보다 큰 것만 조회
        holdings = StockHolding.objects.filter(
            user=user, 
            quantity__gt=0
        ).select_related('company')

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
                "ticker": h.company_id,
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

    @action(detail=False, methods=["get"], url_path="me/transactions")
    def transactions(self, request):
        user = get_current_user(request)
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

    @action(detail=True, methods=["get"], url_path="test")
    def test_action(self, request, pk=None):
        return Response({"message": "테스트 성공", "user_id": pk})

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

    @action(detail=False, methods=["get"], url_path="me/followers")
    def followers(self, request, pk=None):
        user = get_current_user(request)
        users = [r.follower for r in user.followers.select_related('follower')]
        return Response(UserReadSerializer(users, many=True).data)

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
    
    @action(detail=False, methods=["get"], url_path="rank/top")
    def top_investors(self, request):
        top_users = User.objects.all().order_by('-total_return_rate')[:5]
        return Response(UserReadSerializer(top_users, many=True).data)
    
    # =================== 특정 유저의 포트폴리오 ===================

    @action(detail=True, methods=["get"], url_path="portfolio-summary")
    def user_portfolio_summary(self, request, pk=None):
        target_user = self.get_object()
        # 🆕 수량이 0보다 큰 것만 조회
        holdings = StockHolding.objects.filter(user=target_user, quantity__gt=0)
        
        if not holdings.exists():
            return Response({
                "user": UserReadSerializer(target_user, context={'request': request}).data,
                "portfolio": {
                    "total_invested": 0,
                    "total_eval": 0,
                    "total_profit": 0,
                    "total_return_rate": 0.0,
                },
                "holdings_count": 0,
            })
        
        company_codes = [h.company_id for h in holdings]
        latest_prices = StockPrice.objects.filter(
            company_id__in=company_codes
        ).order_by('company', '-record_time').distinct('company')
        price_map = {p.company_id: p.close for p in latest_prices}
        
        total_invested = Decimal("0")
        total_eval = Decimal("0")
        for h in holdings:
            invested = h.average_price * h.quantity
            total_invested += invested
            current_price = price_map.get(h.company_id, h.average_price)
            total_eval += current_price * h.quantity
        
        total_profit = total_eval - total_invested
        total_return_rate = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        return Response({
            "user": UserReadSerializer(target_user, context={'request': request}).data,
            "portfolio": {
                "total_invested": float(total_invested),
                "total_eval": float(total_eval),
                "total_profit": float(total_profit),
                "total_return_rate": float(round(total_return_rate, 2)),
            },
            "holdings_count": holdings.count(),
        })
    
    @action(detail=True, methods=["get"], url_path="holdings")
    def user_holdings(self, request, pk=None):
        target_user = self.get_object()
        # 🆕 수량이 0보다 큰 것만 조회
        holdings = StockHolding.objects.filter(
            user=target_user,
            quantity__gt=0
        ).select_related('company')
        
        if not holdings.exists():
            return Response([])
        
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
                "ticker": h.company_id,
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

    @action(detail=True, methods=["get"], url_path="transactions")
    def user_transactions(self, request, pk=None):
        target_user = self.get_object()
        qs = Transaction.objects.filter(user=target_user).select_related('company').order_by("-created_at")
        
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

    @action(detail=True, methods=["get"], url_path="followers")
    def user_followers(self, request, pk=None):
        target_user = self.get_object()
        users = [r.follower for r in target_user.followers.select_related('follower')]
        return Response(UserReadSerializer(users, many=True, context={'request': request}).data)
    
    @action(detail=True, methods=["get"], url_path="following")
    def user_following(self, request, pk=None):
        target_user = self.get_object()
        users = [r.following for r in target_user.following.select_related('following')]
        return Response(UserReadSerializer(users, many=True, context={'request': request}).data)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related("author").annotate(
        comment_count=Count("comments", distinct=True),
        like_count=Count("likes", distinct=True)
    )
    serializer_class = PostWriteSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
        """
        게시글 피드 조회 (정렬 기능 포함)
        GET /api/posts/feed/?sort=latest|popular|following&ticker=종목코드
        """
        sort_by = request.query_params.get("sort", "latest")
        ticker = request.query_params.get("ticker")
        
        # 기본 쿼리셋
        qs = self.get_queryset()
        
        # 정렬 방식에 따라 처리
        if sort_by == "popular":
            # 좋아요 + 댓글 수 기준 정렬
            qs = qs.annotate(
                engagement=Count("likes", distinct=True) + Count("comments", distinct=True)
            ).order_by("-engagement", "-created_at")
            
        elif sort_by == "following":
            # 팔로우한 사용자의 글만
            try:
                user = get_current_user(request)
            except PermissionDenied:
                # 비로그인 사용자
                return Response(
                    {"detail": "로그인이 필요합니다."}, 
                    status=401
                )
            
            # 디버깅: 현재 유저 확인
            print(f"현재 유저: {user}, 유저 ID: {user.id}")
            
            # Follow 모델을 통해 팔로잉한 유저 ID 목록 가져오기
            following_user_ids = Follow.objects.filter(
                follower=user
            ).values_list('following_id', flat=True)
            
            # 디버깅: 팔로잉 유저 ID 확인
            print(f"팔로잉 유저 IDs: {list(following_user_ids)}")
            
            qs = qs.filter(author_id__in=following_user_ids).order_by("-created_at")
            
            # 디버깅: 필터링된 게시글 수
            print(f"필터링된 게시글 수: {qs.count()}")
            
        else:  # "latest" (기본값)
            qs = qs.order_by("-created_at")
        
        # 종목 필터링 (기존 기능 유지)
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
    
    # 🆕 댓글 삭제 기능
    @action(detail=False, methods=["delete"], url_path="comments/(?P<comment_id>[^/.]+)")
    def delete_comment(self, request, comment_id=None, pk=None):
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({"error": "댓글을 찾을 수 없습니다."}, status=404)
        
        if comment.author != get_current_user(request):
            return Response({"error": "본인 댓글만 삭제 가능합니다."}, status=403)
        
        comment.delete()
        return Response({"message": "삭제되었습니다."}, status=204)
    
    
class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer


# ========================================================
# 2. Stock ViewSets
# ========================================================

class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    # 중요: 이전에 추가했던 queryset = Company.objects.none() 줄이 있다면 반드시 삭제하세요!
    serializer_class = CompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']

    def get_queryset(self):
        # 1. 서브쿼리: 각 회사별 최신 가격 데이터 1건 추출
        latest_prices = StockPrice.objects.filter(
            company_id=OuterRef('pk') # company 대신 pk로 직접 매칭
        ).order_by('-record_time')

        # 2. 쿼리셋 정의
        return Company.objects.annotate(
            # 현재가 가져오기 (없으면 0.0)
            curr_price=Coalesce(
                Subquery(latest_prices.values('close')[:1], output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            # 거래량 가져오기 (없으면 0)
            curr_volume=Coalesce(
                Subquery(latest_prices.values('volume')[:1], output_field=BigIntegerField()),
                Value(0, output_field=BigIntegerField())
            )
        ).annotate(
            # 거래대금 계산: 두 필드를 모두 Float로 형변환 후 곱셈 (Postgres 호환성 최적화)
            trading_value=Cast(F('curr_price'), FloatField()) * Cast(F('curr_volume'), FloatField())
        ).order_by('-trading_value', 'name')
class StockPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockPrice.objects.all().order_by('-record_time')
    serializer_class = StockPriceSerializer

    def get_queryset(self):
        queryset = StockPrice.objects.all().order_by('-record_time')
        ticker = self.request.query_params.get('ticker')
        if ticker:
            queryset = queryset.filter(company_id=ticker)
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        ticker = request.query_params.get('ticker')
        if not ticker:
            return Response({"error": "Ticker is required"}, status=400)

        prices = StockPrice.objects.filter(company_id=ticker).order_by('-record_time')[:2]

        if not prices.exists():
            return Response({"error": "No data found"}, status=404)

        latest = prices[0]
        prev = prices[1] if len(prices) > 1 else None

        change = 0
        change_rate = 0
        if prev:
            change = latest.close - prev.close
            if prev.close > 0:
                change_rate = (change / prev.close) * 100

        return Response({
            "name": latest.company.name if latest.company else ticker,
            "code": latest.company_id,
            "last_price": latest.close,
            "volume": latest.volume,
            "change": change,
            "change_rate": round(change_rate, 2),
        })

    @action(detail=False, methods=['get'])
    def chart(self, request):
        ticker = request.query_params.get('ticker')
        days = int(request.query_params.get('days', 30))
        
        data = StockPrice.objects.filter(company_id=ticker).order_by('-record_time')[:days]
        
        results = [
            {
                "date": d.record_time.strftime("%Y-%m-%d"),
                "open": d.open,
                "high": d.high,
                "low": d.low,
                "close": d.close,
                "volume": d.volume
            } 
            for d in reversed(data)
        ]
        return Response(results)

    # 🆕 이동평균선 계산 API
    @action(detail=False, methods=['get'], url_path='moving-averages')
    def moving_averages(self, request):
        ticker = request.query_params.get('ticker')
        days = int(request.query_params.get('days', 365))
        
        if not ticker:
            return Response({"error": "Ticker is required"}, status=400)
        
        # 1. DB 조회 최적화 (필요한 필드만 가져오기)
        prices = StockPrice.objects.filter(
            company_id=ticker
        ).order_by('record_time')[:days]
        
        if not prices.exists():
            return Response({"error": "No data found"}, status=404)
        
        # 2. DataFrame 변환
        df = pd.DataFrame(list(prices.values('record_time', 'open', 'high', 'low', 'close', 'volume')))
        df['date'] = df['record_time'].dt.strftime('%Y-%m-%d')
        
        # 3. 이동평균선 계산 (벡터화 연산)
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()
        
        # 4. 🔥 핵심 최적화: iterrows 삭제 및 NaN 처리
        # JSON은 NaN을 인식하지 못하므로 None(null)으로 변환합니다.
        df = df.replace({np.nan: None})
        results = df.to_dict('records')
        
        return Response(results)

    @action(detail=False, methods=['get'], url_path='bollinger-bands')
    def bollinger_bands(self, request):
        ticker = request.query_params.get('ticker')
        days = int(request.query_params.get('days', 365))
        period = int(request.query_params.get('period', 20))
        std_dev = float(request.query_params.get('std_dev', 2))
        
        if not ticker:
            return Response({"error": "Ticker is required"}, status=400)
        
        prices = StockPrice.objects.filter(
            company_id=ticker
        ).order_by('record_time')[:days]
        
        if not prices.exists():
            return Response({"error": "No data found"}, status=404)
        
        df = pd.DataFrame(list(prices.values('record_time', 'open', 'high', 'low', 'close', 'volume')))
        df['date'] = df['record_time'].dt.strftime('%Y-%m-%d')
        
        # 볼린저 밴드 계산
        df['sma'] = df['close'].rolling(window=period, min_periods=1).mean()
        df['std'] = df['close'].rolling(window=period, min_periods=1).std()
        df['upper_band'] = df['sma'] + (df['std'] * std_dev)
        df['lower_band'] = df['sma'] - (df['std'] * std_dev)
        
        # 🔥 핵심 최적화: iterrows 삭제 및 NaN 처리
        df = df.replace({np.nan: None})
        results = df.to_dict('records')
        
        return Response(results)

class StockHoldingViewSet(viewsets.ModelViewSet):
    queryset = StockHolding.objects.all()
    serializer_class = StockHoldingSerializer
    
    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id: return StockHolding.objects.none()
        return StockHolding.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        user = get_current_user(self.request)
        serializer.save(user=user)

from django.db.models import F
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id: 
            return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id).order_by('-created_at')

    def perform_create(self, serializer):
        user = get_current_user(self.request)
        trade_type = serializer.validated_data.get('type')
        # 데이터 타입을 Decimal로 강제 변환하여 계산 오류 방지
        price = Decimal(str(serializer.validated_data.get('price')))
        quantity = Decimal(str(serializer.validated_data.get('quantity')))
        company = serializer.validated_data.get('company')
        amount = price * quantity

        # 모든 DB 작업은 하나의 원자적 트랜잭션으로 처리
        with transaction.atomic():
            if trade_type == 'BUY':
                # [매수 로직]
                if user.mileage < amount:
                    raise PermissionDenied("마일리지가 부족합니다.")
                
                user.mileage -= amount
                user.save()

                holding, created = StockHolding.objects.get_or_create(
                    user=user, company=company,
                    defaults={'average_price': Decimal('0'), 'quantity': 0}
                )
                
                if created:
                    holding.quantity = int(quantity)
                    holding.average_price = price
                else:
                    # 새로운 평단가 계산
                    total_cost = (holding.average_price * Decimal(holding.quantity)) + amount
                    holding.quantity += int(quantity)
                    holding.average_price = total_cost / Decimal(holding.quantity)
                holding.save()

            elif trade_type == 'SELL':
                # [매도 로직]
                holding = StockHolding.objects.filter(user=user, company=company).first()
                if not holding or holding.quantity < int(quantity):
                    raise PermissionDenied("보유 수량이 부족합니다.")

                # 🎯 실현손익 계산: (현재 매도가 - 내가 샀던 평단가) * 수량
                # holding.average_price는 Decimal이므로 정상 계산됨
                pnl = (price - holding.average_price) * quantity

                # 유저 테이블에 누적 수익금 저장
                current_profit = user.realized_profit or Decimal('0')
                user.realized_profit = current_realized_profit = current_profit + pnl
                
                # 실현 수익률 계산 (초기 자산 10,000,000원 기준)
                initial_capital = Decimal('10000000')
                # ZeroDivisionError 방지 및 float 변환
                if initial_capital > 0:
                    user.total_return_rate = float((user.realized_profit / initial_capital) * 100)
                
                user.mileage += amount  # 판매 대금 추가
                user.save()

                # 잔고 업데이트
                holding.quantity -= int(quantity)
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.save()

            # 최종적으로 거래 내역(Transaction) 저장
            serializer.save(user=user, amount=amount)

# ========================================================
# 2-1. Market Index ViewSet (KOSPI, KOSDAQ 전용)
# ========================================================


class MarketIndexViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        # KOSPI: ^KS11, KOSDAQ: ^KQ11 (yfinance 티커 기준)
        indices = {
            'KOSPI': '^KS11',
            'KOSDAQ': '^KQ11'
        }
        result = []

        for name, ticker_symbol in indices.items():
            try:
                # 1. 지수 데이터 가져오기 (최근 5일치 일봉 데이터)
                ticker = yf.Ticker(ticker_symbol)
                # '1d' 간격으로 최근 5일 데이터를 가져와서 차트와 변동률 계산
                hist = ticker.history(period="5d", interval="1d")

                if hist.empty:
                    continue

                # 2. 실시간 정보 및 변동률 계산
                latest_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_rate = ((latest_close - prev_close) / prev_close) * 100

                # 3. 차트용 데이터 (최근 10~20개 포인트 - sparkline용)
                # interval을 '15m' 등으로 설정하면 더 세밀한 차트가 가능하지만, 
                # 여기서는 간단히 일별 종가 리스트를 보냅니다.
                chart_data = hist['Close'].tolist()

                result.append({
                    "name": name,
                    "value": round(float(latest_close), 2),
                    "change_rate": round(float(change_rate), 2),
                    "series": [{"data": [round(float(x), 2) for x in chart_data]}]
                })
            except Exception as e:
                print(f"❌ {name} 지수 수집 에러: {e}")
                result.append({
                    "name": name, "value": 0, "change_rate": 0, "series": [{"data": []}]
                })

        return Response(result)

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
    permission_classes = [AllowAny] 

    def create(self, request, *args, **kwargs):
        url = request.data.get('url')
        
        if url and LatestNews.objects.filter(url=url).exists():
            print(f"✋ 중복 뉴스 스킵 (URL): {url}")
            return Response(
                {"message": "Skipped (Duplicate)", "url": url}, 
                status=status.HTTP_201_CREATED
            )
        
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # 🆕 이미지가 있는 뉴스만 필터링
        queryset = self.queryset.exclude(image_url__isnull=True).exclude(image_url='')
        
        sort_by = request.query_params.get('sort', 'latest')
        search_query = request.query_params.get('search', '')

        if sort_by == 'similarity':
            if search_query:
                vector = get_embedding(search_query)
                if vector:
                    queryset = queryset.annotate(
                        distance=CosineDistance('body_embedding_vector', vector)
                    ).order_by('distance')
                else:
                    queryset = queryset.order_by('-news_collection_date')
            else:
                queryset = queryset.order_by('-max_similarity_score')

        elif sort_by == 'popular':
            queryset = queryset.order_by('-view_count')

        else:
            queryset = queryset.order_by('-news_collection_date')

        if search_query and sort_by != 'similarity':
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(body__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        # 🆕 기본 쿼리셋에도 이미지 필터 적용
        return LatestNews.objects.exclude(
            image_url__isnull=True
        ).exclude(
            image_url=''
        ).order_by('-news_collection_date')

    @action(detail=True, methods=['post'], url_path='increment-view')
    def increment_view(self, request, pk=None):
        """뉴스 조회수 증가"""
        news = self.get_object()
        news.view_count = F('view_count') + 1
        news.save(update_fields=['view_count'])
        news.refresh_from_db()
        return Response({'view_count': news.view_count}, status=200)

    @action(detail=True, methods=['get'], url_path='similar_historical')
    def similar_historical_news(self, request, pk=None):
        current_news = self.get_object()
        
        if current_news.body_embedding_vector is None:
            return Response({"message": "분석 중 (임베딩 없음)"}, status=200)

        similar_news = HistoricalNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', current_news.body_embedding_vector)
        ).order_by('distance').first()

        if not similar_news:
            return Response({"message": "유사한 과거 데이터가 없습니다."}, status=200)

        raw_ticker = similar_news.impacted_ticker
        target_tickers = []
        if raw_ticker:
            split_tickers = raw_ticker.split("|")
            target_tickers = [t.strip() for t in split_tickers if t.strip()][:3]

        related_stocks_data = []
        target_date = similar_news.news_collection_date
        start_date = target_date - timedelta(days=5)
        end_date = target_date + timedelta(days=10)

        for code in target_tickers:
            company_obj = Company.objects.filter(code=code).first()
            company_name = company_obj.name if company_obj else code
            
            stock_prices = StockPrice.objects.filter(
                company__code=code,
                record_time__range=(start_date, end_date)
            ).order_by('record_time')
            
            related_stocks_data.append({
                "name": company_name,
                "ticker": code,
                "chart_data": StockPriceSerializer(stock_prices, many=True).data
            })

        similar_news_data = HistoricalNewsSerializer(similar_news).data
        
        return Response({
            "similar_news": similar_news_data,
            "similarity_score": 1 - similar_news.distance,
            "related_stocks": related_stocks_data 
        })  

    @action(detail=False, methods=['post'])
    def search(self, request):
        query_text = request.data.get('query')
        if not query_text: return Response({"error": "query 필요"}, status=400)
        vec = get_embedding(query_text)
        if not vec: return Response({"error": "임베딩 실패"}, status=500)
        
        # 🆕 검색 결과에도 이미지 필터 적용
        results = LatestNews.objects.exclude(
            image_url__isnull=True
        ).exclude(
            image_url=''
        ).annotate(
            distance=CosineDistance('body_embedding_vector', vec)
        ).order_by('distance')[:5]
        
        return Response(self.get_serializer(results, many=True).data)

    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        
        if text:
            vector = get_embedding(text)
            if vector:
                instance = serializer.save(body_embedding_vector=vector)
                update_similarity_score(instance)
            else:
                serializer.save()
        else:
            serializer.save()
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
        
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        user = get_current_user(request)
        ticker = request.data.get('ticker')
        if not ticker: 
            return Response(status=400)
        
        item = WatchlistItem.objects.filter(user=user, ticker=ticker).first()
        if item:
            item.delete()
            return Response({'added': False})
        else:
            try:
                company = Company.objects.get(code=ticker)
                WatchlistItem.objects.create(user=user, ticker=ticker, company=company)
            except Company.DoesNotExist:
                WatchlistItem.objects.create(user=user, ticker=ticker)
            return Response({'added': True})

class StrategyNoteViewSet(viewsets.ModelViewSet):
    queryset = StrategyNote.objects.all()
    serializer_class = StrategyNoteSerializer

    def get_queryset(self):
        user = get_current_user(self.request)
        return StrategyNote.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=get_current_user(self.request))


