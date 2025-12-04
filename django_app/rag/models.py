from django.db import models
from pgvector.django import VectorField

# ==========================================
# 1. Users & Social
# ==========================================

class User(models.Model):
    # 닉네임은 한 번만 쓰이도록 unique 설정
    nickname = models.CharField(max_length=255, unique=True)
    # 해시된 비밀번호가 들어갈 칸
    password = models.CharField(max_length=255)
    profile_image_url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nickname

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)

class Follow(models.Model):
    following_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    follower_user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['following_user', 'follower_user'], name='unique_follow')
        ]

# ==========================================
# 2. Stocks
# ==========================================

class StockDailyPrice(models.Model):
    symbol = models.CharField(max_length=12, db_index=True) 
    trade_date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    high = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    low = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    close = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    volume = models.DecimalField(max_digits=20, decimal_places=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['symbol', 'trade_date'], name='unique_stock_price')
        ]

# ==========================================
# 3. Portfolio & Transactions
# ==========================================

class StockHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holdings')
    ticker = models.CharField(max_length=12, db_index=True)
    average_buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

class TransactionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    ticker = models.CharField(max_length=12, db_index=True)
    transaction_datetime = models.DateTimeField()
    transaction_type = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# ==========================================
# 4. News (RAG) - URL 필드 추가
# ==========================================

class HistoricalNews(models.Model):
    news_collection_date = models.DateField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    url = models.URLField(max_length=2048, null=True, blank=True)
    
    # 👇 [변경] OpenAI text-embedding-3-small 기준 1536차원
    body_embedding_vector = VectorField(dimensions=1536) 
    
    impacted_ticker = models.CharField(max_length=12, null=True, db_index=True)

class LatestNews(models.Model):
    news_collection_date = models.DateField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    url = models.URLField(max_length=2048, null=True, blank=True)
    
    # OpenAI용 1536 차원
    body_embedding_vector = VectorField(dimensions=1536)
    
    # 👇 [이 줄이 꼭 있어야 합니다!]
    views = models.IntegerField(default=0)