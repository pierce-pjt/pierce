from django.contrib import admin
from .models import (
    User, Post, Follow, 
    Company, StockPrice, StockHolding, Transaction,
    HistoricalNews, LatestNews,
    # 필요하다면 주석 해제
    # Comment, PostLike 
)

# 1. 유저 & 소셜
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'nickname')
    search_fields = ('nickname',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'created_at')
    search_fields = ('title', 'author__nickname')
    list_filter = ('created_at',)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__nickname', 'following__nickname')

# ========================================================
# 2. 주식 데이터 (리모델링 반영)
# ========================================================

# 2-1. 종목 마스터 (Company)
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'market', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('market', 'is_active')

# 2-2. 시세 데이터 (StockPrice) - 기존 StockDailyPrice 대체
@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    # record_time으로 변경됨
    list_display = ('company', 'record_time', 'close', 'volume')
    list_filter = ('company__market',) # 외래키 접근
    search_fields = ('company__name', 'company__code')
    date_hierarchy = 'record_time' # 날짜별로 보기 편하게 설정

# 2-3. 보유 잔고 (StockHolding)
@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    # ticker 대신 company 객체 사용
    list_display = ('user', 'company', 'quantity', 'average_price')
    search_fields = ('user__nickname', 'company__name')

# 2-4. 거래 내역 (Transaction) - 기존 TransactionHistory 대체
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'type', 'price', 'quantity', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__nickname', 'company__name')


# 3. 뉴스
@admin.register(HistoricalNews)
class HistoricalNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'news_collection_date', 'impacted_ticker')
    search_fields = ('title', 'impacted_ticker')
    readonly_fields = ('body_embedding_vector',)

@admin.register(LatestNews)
class LatestNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'news_collection_date', 'views')
    search_fields = ('title',)
    readonly_fields = ('body_embedding_vector',)