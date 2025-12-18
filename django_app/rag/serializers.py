from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    User, Post, Follow, Comment, PostLike,
    Company, StockPrice, StockHolding, Transaction,
    HistoricalNews, LatestNews,
    WatchlistItem, StrategyNote,  
)

# ==========================================
# 1. User
# ==========================================
class UserReadSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile_image_url', 'followers_count', 'following_count', 'is_following', 'mileage', 'total_return_rate']

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request: return False
        current_user_id = request.session.get('user_id')
        if not current_user_id: return False
        return obj.followers.filter(follower_id=current_user_id).exists()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nickname", "password", "profile_image_url")
        extra_kwargs = {"password": {"write_only": True, "min_length": 4}}

    def create(self, validated_data):
        raw_password = validated_data.get("password")
        validated_data["password"] = make_password(raw_password)
        return super().create(validated_data)

class UserLoginSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    password = serializers.CharField(write_only=True)

# ==========================================
# 2. Feed & Community
# ==========================================
class CommentSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "created_at")
        read_only_fields = ("id", "post", "author", "created_at")

class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "ticker", "image", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

class PostReadSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField() # 이미지 URL 반환
    class Meta:
        model = Post
        fields = ("id", "title", "content", "image_url", "author", "ticker", "created_at", "updated_at", "comment_count", "like_count", "is_liked")

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request: return False
        user_id = request.session.get("user_id")
        if not user_id: return False
        return obj.likes.filter(user_id=user_id).exists()
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'

# ==========================================
# 3. Stocks & Assets
# ==========================================
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['code', 'name', 'market', 'is_active']

class StockPriceSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField(source='company.name')
    class Meta:
        model = StockPrice
        # record_time 필드 사용 확인
        fields = ['company', 'company_name', 'record_time', 'open', 'high', 'low', 'close', 'volume']

class StockHoldingSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField(source='company.name')
    company_code = serializers.ReadOnlyField(source='company.code')
    class Meta:
        model = StockHolding
        fields = ['company', 'company_code', 'company_name', 'quantity', 'average_price', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField(source='company.name')
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'company', 'company_name', 'type', 'price', 'quantity', 'amount', 'created_at']
        read_only_fields = ['user', 'amount', 'created_at']

# ==========================================
# 4. News & RAG & Etc
# ==========================================
class HistoricalNewsSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(read_only=True, required=False)
    class Meta:
        model = HistoricalNews
        fields = '__all__'
        read_only_fields = ('body_embedding_vector',)

class LatestNewsSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(read_only=True, required=False)
    class Meta:
        model = LatestNews
        fields = '__all__'
        read_only_fields = ('body_embedding_vector',)

class WatchlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistItem
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")

class StrategyNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyNote
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = ['record_time', 'open', 'high', 'low', 'close', 'volume']