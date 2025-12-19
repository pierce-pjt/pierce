<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const comments = ref([])
const newComment = ref('')
const loading = ref(true)

const API_BASE = '/api'

// 🍪 CSRF 토큰 가져오기
const getCookie = (name) => {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const postId = computed(() => route.params.id)

// 📥 게시글 상세 & 댓글 불러오기
const fetchPostDetail = async () => {
  loading.value = true
  try {
    // 게시글 상세 조회
    const postRes = await fetch(`${API_BASE}/posts/${postId.value}/`)
    if (postRes.ok) {
      post.value = await postRes.json()
    } else {
      alert('게시글을 찾을 수 없습니다.')
      router.push('/community')
      return
    }

    // 댓글 조회
    const commentsRes = await fetch(`${API_BASE}/posts/${postId.value}/comments/`)
    if (commentsRes.ok) {
      comments.value = await commentsRes.json()
    }
  } catch (e) {
    console.error('데이터 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

// 💬 댓글 작성
const addComment = async () => {
  if (!authStore.isAuthenticated) {
    alert('로그인이 필요합니다.')
    router.push('/login')
    return
  }
  
  if (!newComment.value.trim()) return

  try {
    const res = await fetch(`${API_BASE}/posts/${postId.value}/comments/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'include',
      body: JSON.stringify({ content: newComment.value })
    })

    if (res.ok) {
      const created = await res.json()
      comments.value.push(created)
      newComment.value = ''
      post.value.comment_count++
    } else {
      alert('댓글 등록에 실패했습니다.')
    }
  } catch (e) {
    console.error('댓글 등록 실패:', e)
  }
}

// ❤️ 좋아요 토글
const toggleLike = async () => {
  if (!authStore.isAuthenticated) {
    alert('로그인이 필요합니다.')
    router.push('/login')
    return
  }

  try {
    const res = await fetch(`${API_BASE}/posts/${postId.value}/like/`, { 
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'include',
    })
    
    if (res.ok) {
      const data = await res.json()
      post.value.is_liked = data.liked
      post.value.like_count = data.like_count
    }
  } catch (e) {
    console.error('좋아요 처리 실패:', e)
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchPostDetail()
})
</script>

<template>
  <div class="detail-page">
    <!-- 로딩 -->
    <div v-if="loading" class="loading-area">
      <p>게시글을 불러오는 중...</p>
    </div>

    <!-- 게시글 상세 -->
    <div v-else-if="post" class="detail-container">
      <button @click="goBack" class="back-btn">← 목록으로</button>

      <div class="detail-card">
        <!-- 헤더 -->
        <div class="detail-header">
          <div class="user-info">
            <img :src="post.author.profile_image_url || '/default-profile.png'" class="avatar" />
            <div>
              <div class="nickname">{{ post.author.nickname }}</div>
              <div class="meta-info">
                <span class="return-rate" :class="post.author.total_return_rate > 0 ? 'red' : 'blue'">
                  {{ post.author.total_return_rate > 0 ? '+' : '' }}{{ post.author.total_return_rate }}%
                </span>
                <span class="date">{{ new Date(post.created_at).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 제목 -->
        <h1 class="detail-title">
          <span v-if="post.ticker" class="ticker-badge">{{ post.ticker }}</span>
          {{ post.title }}
        </h1>

        <!-- 본문 -->
        <div class="detail-body">
          <p>{{ post.content }}</p>
          <img v-if="post.image_url" :src="post.image_url" class="detail-image" />
        </div>

        <!-- 좋아요 -->
        <div class="detail-actions">
          <button 
            class="action-btn" 
            :class="{ active: post.is_liked }" 
            @click="toggleLike"
          >
            {{ post.is_liked ? '❤️' : '🤍' }} 좋아요 {{ post.like_count }}
          </button>
        </div>

        <hr class="divider"/>

        <!-- 댓글 섹션 -->
        <div class="comments-section">
          <h3>댓글 {{ comments.length }}</h3>
          <div class="comment-list">
            <div v-for="cmt in comments" :key="cmt.id" class="comment-item">
              <span class="cmt-author">{{ cmt.author.nickname }}</span>
              <span class="cmt-content">{{ cmt.content }}</span>
            </div>
            <div v-if="comments.length === 0" class="no-comments">
              첫 댓글을 남겨보세요!
            </div>
          </div>
          <div class="comment-input-area">
            <input 
              v-model="newComment" 
              type="text" 
              placeholder="댓글을 남겨보세요..." 
              @keyup.enter="addComment"
            />
            <button @click="addComment">등록</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 에러 -->
    <div v-else class="error-area">
      <p>게시글을 불러올 수 없습니다.</p>
      <button @click="goBack" class="back-btn">목록으로</button>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  color: #f5f5f7;
}

.loading-area,
.error-area {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.back-btn {
  background: #374151;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 24px;
  transition: background 0.2s;
}

.back-btn:hover {
  background: #4b5563;
}

.detail-card {
  background: #141414;
  padding: 32px;
  border-radius: 16px;
  border: 1px solid #222;
}

.detail-header {
  margin-bottom: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.nickname {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 4px;
}

.meta-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #9ca3af;
}

.return-rate {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
}

.red {
  color: #ff4d4d;
}

.blue {
  color: #4d94ff;
}

.date {
  color: #6b7280;
}

.detail-title {
  font-size: 28px;
  font-weight: bold;
  margin: 0 0 24px 0;
  line-height: 1.4;
}

.ticker-badge {
  font-size: 14px;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  padding: 4px 10px;
  border-radius: 6px;
  margin-right: 8px;
  vertical-align: middle;
}

.detail-body {
  font-size: 16px;
  line-height: 1.8;
  color: #e5e7eb;
  white-space: pre-wrap;
  margin-bottom: 32px;
}

.detail-image {
  width: 100%;
  max-height: 500px;
  object-fit: cover;
  border-radius: 12px;
  margin-top: 24px;
}

.detail-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}

.action-btn {
  background: #1f2937;
  border: 1px solid #374151;
  color: #9ca3af;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #4b5563;
}

.action-btn.active {
  color: #ef4444;
  border-color: #ef4444;
}

.divider {
  border: 0;
  border-top: 1px solid #374151;
  margin: 32px 0;
}

.comments-section h3 {
  font-size: 18px;
  margin-bottom: 20px;
  color: #f5f5f7;
}

.comment-list {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.comment-item {
  background: #1f2937;
  padding: 14px;
  border-radius: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.cmt-author {
  font-weight: bold;
  color: #60a5fa;
  margin-right: 10px;
}

.cmt-content {
  color: #e5e7eb;
}

.no-comments {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  font-size: 14px;
}

.comment-input-area {
  display: flex;
  gap: 10px;
}

.comment-input-area input {
  flex: 1;
  background: #1f2937;
  border: 1px solid #374151;
  color: white;
  padding: 14px;
  border-radius: 8px;
  font-size: 14px;
}

.comment-input-area input:focus {
  outline: none;
  border-color: #3b82f6;
}

.comment-input-area button {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.2s;
}

.comment-input-area button:hover {
  background: #2563eb;
}

/* 스크롤바 스타일 */
.comment-list::-webkit-scrollbar {
  width: 6px;
}

.comment-list::-webkit-scrollbar-track {
  background: #1f2937;
  border-radius: 3px;
}

.comment-list::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}

.comment-list::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>