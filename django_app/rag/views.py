from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.db.models import Count, Sum, Q
from decimal import Decimal, InvalidOperation
from pgvector.django import CosineDistance
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from datetime import timedelta
import openai

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
@method_decorator(csrf_exempt, name='dispatch')
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
        
        # 💥 [디버깅 추가] 서버 터미널에 정확한 에러 원인을 찍어줍니다.
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

        company_codes = [h.company_id for h in holdings]
        # record_time 기준 최신 데이터 조회
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
        # 수익률 상위 5명 조회
        top_users = User.objects.all().order_by('-total_return_rate')[:5]
        return Response(UserReadSerializer(top_users, many=True).data)

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
    # 기본 쿼리셋 (record_time 역순)
    queryset = StockPrice.objects.all().order_by('-record_time')
    serializer_class = StockPriceSerializer
    
    # 💥💥💥 [핵심 수정] summary, chart 액션 추가 💥💥💥
    @action(detail=False, methods=['get'])
    def summary(self, request):
        ticker = request.query_params.get('ticker')
        if not ticker:
            return Response({"error": "Ticker is required"}, status=400)

        # company_id(=symbol)로 필터링, 최신 날짜순 2개
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

        data = {
            "name": latest.company.name if latest.company else ticker,
            "code": latest.company_id,
            "last_price": latest.close,
            "volume": latest.volume,
            "change": change,
            "change_rate": round(change_rate, 2),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def chart(self, request):
        ticker = request.query_params.get('ticker')
        days = int(request.query_params.get('days', 30))
        
        # 최신 n일치 데이터
        data = StockPrice.objects.filter(company_id=ticker).order_by('-record_time')[:days]
        
        # 차트용 오름차순 정렬
        results = [
            {
                "date": d.record_time.strftime("%Y-%m-%d"),
                "close": d.close
            } 
            for d in reversed(data)
        ]
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

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user_id = self.request.session.get("user_id")
        if not user_id: return Transaction.objects.none()
        return Transaction.objects.filter(user_id=user_id).order_by('-created_at')

    def perform_create(self, serializer):
        user = get_current_user(self.request)
        # 매수/매도 요청 데이터
        trade_type = serializer.validated_data.get('type')
        price = serializer.validated_data.get('price')
        quantity = serializer.validated_data.get('quantity')
        amount = price * quantity

        if trade_type == 'BUY':
            if user.mileage < amount:
                raise PermissionDenied("마일리지가 부족합니다.")
            user.mileage -= amount
        elif trade_type == 'SELL':
            # (보유 수량 체크 로직은 생략되었으나 실제론 필요함)
            user.mileage += amount
            
        user.save() # 마일리지 업데이트 저장
        serializer.save(user=user, amount=amount)


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
        # 1. 요청 데이터에서 '제목' 꺼내기
        title = request.data.get('title')
        
        # 2. DB에 같은 제목의 뉴스가 있는지 확인
        # (필요하다면 company_name이나 date도 같이 비교 가능)
        if title and LatestNews.objects.filter(title=title).exists():
            print(f"✋ 중복 뉴스 스킵: {title}")
            # 저장을 안 하고 바로 200 OK 리턴 (Airflow가 실패로 인식하지 않게)
            return Response({"message": "Skipped (Duplicate)", "title": title}, status=200)

        # 3. 중복이 아니면 원래대로 저장 진행 (perform_create -> 임베딩 생성 등)
        return super().create(request, *args, **kwargs)
    # 👇 [수정] list 메서드에서 정렬 및 검색 로직을 통합 처리

    def list(self, request, *args, **kwargs):
        # 1. 기본 쿼리셋
        queryset = self.queryset.all()
        
        # 2. 파라미터 받기
        sort_by = request.query_params.get('sort', 'latest')
        search_query = request.query_params.get('search', '')

        # 3. 정렬 로직 분기
        if sort_by == 'similarity':
            if search_query:
                # [CASE A] 검색어 있음 -> '의미'가 비슷한 뉴스 찾기 (Semantic Search)
                vector = get_embedding(search_query)
                if vector:
                    queryset = queryset.annotate(
                        distance=CosineDistance('body_embedding_vector', vector)
                    ).order_by('distance')
                else:
                    # 임베딩 실패 시 최신순으로 Fallback
                    queryset = queryset.order_by('-news_collection_date')
            else:
                # [CASE B] 검색어 없음 -> '역사가 반복되는' 뉴스 찾기 (Pattern Matching)
                # (모델에 max_similarity_score 필드가 있어야 함)
                queryset = queryset.order_by('-max_similarity_score')

        elif sort_by == 'popular':
            # [CASE C] 인기순 (조회수)
            # (모델에 view_count 필드가 있어야 함)
            queryset = queryset.order_by('-view_count')

        else:
            # [CASE D] 최신순 (기본값)
            queryset = queryset.order_by('-news_collection_date')

        # 4. 키워드 필터링 (유사도 정렬이 아닐 때만 적용)
        # 유사도 정렬은 이미 의미 기반으로 찾았으므로 제외, 인기/최신순일 때만 텍스트 포함 여부 확인
        if search_query and sort_by != 'similarity':
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(body__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )

        # 5. 페이지네이션 처리
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # 🔎 Retrieve(상세 조회)를 위해 get_queryset은 기본 상태 유지 (혹은 필요 시 삭제 가능)
    def get_queryset(self):
        return LatestNews.objects.all().order_by('-news_collection_date')

    # (기존 similar_historical_news, search 액션 유지)
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
        results = LatestNews.objects.annotate(
            distance=CosineDistance('body_embedding_vector', vec)
        ).order_by('distance')[:5]
        return Response(self.get_serializer(results, many=True).data)

    def perform_create(self, serializer):
        text = serializer.validated_data.get('body')
        
        # 1. 임베딩 생성 및 저장
        if text:
            vector = get_embedding(text)
            if vector:
                # save()는 저장된 객체(instance)를 반환함
                instance = serializer.save(body_embedding_vector=vector)
                
                # 2. 👇 [핵심] 저장 직후 유사도 점수 계산 함수 호출!
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
        if not ticker: return Response(status=400)
        
        # 이미 있으면 삭제, 없으면 생성
        item = WatchlistItem.objects.filter(user=user, ticker=ticker).first()
        if item:
            item.delete()
            return Response({'added': False})
        else:
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