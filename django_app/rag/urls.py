from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import MarketIndexViewSet

router = DefaultRouter()

# User & Community
router.register(r'users', views.UserViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'follows', views.FollowViewSet)

# Stocks
router.register(r'companies', views.CompanyViewSet)
router.register(r'stock-prices', views.StockPriceViewSet)
router.register(r'holdings', views.StockHoldingViewSet)
router.register(r'transactions', views.TransactionViewSet)

# News
router.register(r'historical-news', views.HistoricalNewsViewSet)
router.register(r'latest-news', views.LatestNewsViewSet)

# MyPage
router.register(r'watchlist', views.WatchlistItemViewSet)
router.register(r'strategy-notes', views.StrategyNoteViewSet)

router.register(r'market-indices', MarketIndexViewSet, basename='market-indices')

urlpatterns = [
    path('', include(router.urls)),
]