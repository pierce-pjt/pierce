from django.db import models
from pgvector.django import VectorField

# ==========================================
# 1. Users & Community (기존 코드 유지)
# ==========================================

class User(models.Model):
    nickname = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    profile_image_url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nickname

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    ticker = models.CharField(max_length=12, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.author.nickname}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.nickname} on {self.post.id}"

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="liked_posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"{self.user.nickname} likes {self.post.id}"

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow')
        ]
        
    def __str__(self):
        return f"{self.follower.nickname} follows {self.following.nickname}"


# ==========================================
# 2. Stocks (주식 데이터 - Airflow 연동 리모델링)
# ==========================================

# 2-1. 종목 마스터 (Airflow: update_stock_list가 채워줌)
class Company(models.Model):
    # Airflow SQL과 매칭: symbol -> code (db_column 사용)
    code = models.CharField(max_length=20, primary_key=True, db_column='symbol') 
    name = models.CharField(max_length=100)
    market = models.CharField(max_length=20) # KOSPI, KOSDAQ
    is_active = models.BooleanField(default=True)

    class Meta:
        # Airflow에서 INSERT INTO stock_list ... 하므로 테이블명 고정
        db_table = 'stock_list'
        verbose_name = '종목 정보'

    def __str__(self):
        return f"{self.name} ({self.code})"

# 2-2. 시세 데이터 (Airflow: kospi_hourly_collector가 채워줌)
# 기존 StockDailyPrice를 대체합니다.
class StockPrice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    
    # 1시간봉 차트를 위해 DateField -> DateTimeField로 변경
    record_time = models.DateTimeField(db_index=True) 
    
    open = models.DecimalField(max_digits=10, decimal_places=0)
    high = models.DecimalField(max_digits=10, decimal_places=0)
    low = models.DecimalField(max_digits=10, decimal_places=0)
    close = models.DecimalField(max_digits=10, decimal_places=0)
    volume = models.BigIntegerField()

    class Meta:
        # Airflow에서 사용하는 테이블 이름
        db_table = 'stock_price'
        ordering = ['-record_time']
        constraints = [
            models.UniqueConstraint(fields=['company', 'record_time'], name='unique_price_per_time')
        ]


# ==========================================
# 3. Portfolio & Transactions (자산 - Company 모델 연결)
# ==========================================

# 기존 TransactionHistory를 대체합니다.
class Transaction(models.Model):
    TRANSACTION_TYPES = (('BUY', '매수'), ('SELL', '매도'))
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    # ticker 문자열 대신 Company 모델과 연결 (데이터 무결성)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    
    type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=0) 
    quantity = models.IntegerField() 
    amount = models.DecimalField(max_digits=15, decimal_places=0) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_transaction'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.amount = self.price * self.quantity
        super().save(*args, **kwargs)

# 기존 StockHolding 리모델링
class StockHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holdings')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    
    quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_holding'
        unique_together = ('user', 'company')


# ==========================================
# 4. News (기존 코드 유지)
# ==========================================

class HistoricalNews(models.Model):
    news_collection_date = models.DateField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    url = models.URLField(max_length=2048, null=True, blank=True)
    body_embedding_vector = VectorField(dimensions=1536, null=True, blank=True)
    impacted_ticker = models.CharField(max_length=500, null=True, db_index=True)

class LatestNews(models.Model):
    news_collection_date = models.DateField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    url = models.URLField(max_length=2048, null=True, blank=True)
    body_embedding_vector = VectorField(dimensions=1536, null=True, blank=True)
    views = models.IntegerField(default=0)