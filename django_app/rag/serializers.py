# rag/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    User, Post, Follow,
    StockDailyPrice, StockHolding, TransactionHistory,
    HistoricalNews, LatestNews,
    Comment, PostLike,
)

# ---- User 관련 ----

# 읽을 때 쓸 직렬화기 (비밀번호는 안 보여줌)
class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nickname", "profile_image_url")


# 회원가입/수정할 때 쓸 직렬화기
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nickname", "password", "profile_image_url")
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
        }

    def create(self, validated_data):
        # 비밀번호 해시
        raw_password = validated_data.get("password")
        validated_data["password"] = make_password(raw_password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 비밀번호를 수정하는 경우만 해시
        password = validated_data.get("password", None)
        if password:
            validated_data["password"] = make_password(password)
        return super().update(instance, validated_data)


# 로그인 요청용 (검증 용도)
class UserLoginSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    password = serializers.CharField(write_only=True)

# ---- Feed(피드) 관련 ----

class CommentSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "created_at")
        read_only_fields = ("id", "post", "author", "created_at")


class PostWriteSerializer(serializers.ModelSerializer):
    """글 작성/수정용 - author는 서버에서 세션 기준으로 채움"""

    class Meta:
        model = Post
        fields = ("id", "title", "content", "ticker", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class PostReadSerializer(serializers.ModelSerializer):
    """피드/상세 조회용"""
    author = UserReadSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "content",
            "author",
            "ticker",
            "created_at",
            "updated_at",
            "comment_count",
            "like_count",
            "is_liked",
        )

    def get_is_liked(self, obj):
        """현재 로그인한 유저가 이 글에 좋아요 눌렀는지 여부"""
        request = self.context.get("request")
        if not request:
            return False
        user_id = request.session.get("user_id")
        if not user_id:
            return False
        return obj.likes.filter(user_id=user_id).exists()

# ---- 이하 기존 serializer 유지 ----

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'

class StockDailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDailyPrice
        fields = '__all__'

class StockHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHolding
        fields = '__all__'

class TransactionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionHistory
        fields = '__all__'

class HistoricalNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalNews
        fields = '__all__'
        read_only_fields = ('body_embedding_vector',)

class LatestNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatestNews
        fields = '__all__'
        read_only_fields = ('body_embedding_vector',)
