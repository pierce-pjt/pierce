from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# ==================================
# 1. User & Community (기존)
# ==================================
router.register(r'users', views.UserViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'follows', views.FollowViewSet)
# (댓글은 PostViewSet 안에서 처리하므로 별도 URL 불필요, 필요시 추가)

# ==================================
# 2. Stocks (리모델링 반영) 
# ==================================
# 👇 [수정] 새 ViewSet 이름으로 교체했습니다.
router.register(r'companies', views.CompanyViewSet)       # 종목 검색
router.register(r'stock-prices', views.StockPriceViewSet) # 차트 데이터
router.register(r'holdings', views.StockHoldingViewSet)   # 내 보유 주식
router.register(r'transactions', views.TransactionViewSet)# 내 거래 내역

# ==================================
# 3. News (기존)
# ==================================
router.register(r'historical-news', views.HistoricalNewsViewSet)
router.register(r'latest-news', views.LatestNewsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]