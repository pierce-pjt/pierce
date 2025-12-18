<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const posts = ref([])
const topInvestors = ref([])
const showWriteModal = ref(false)

// 📝 글쓰기 데이터
const newPostTitle = ref('')
const newPostContent = ref('')
const newPostTicker = ref('')
const newPostImage = ref(null)

// 💬 상세 모달 상태
const selectedPost = ref(null)
const comments = ref([])
const newComment = ref('')

const API_BASE = '/api'

// 🍪 쿠키에서 CSRF 토큰 가져오는 함수
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

// 🔄 데이터 로드 (GET 요청은 credentials 불필요하지만 넣어도 무방)
const fetchData = async () => {
  try {
    const feedRes = await fetch(`${API_BASE}/posts/feed/`)
    if (feedRes.ok) posts.value = await feedRes.json()
    
    const rankRes = await fetch(`${API_BASE}/users/rank/top/`)
    if (rankRes.ok) topInvestors.value = await rankRes.json()
  } catch (e) { console.error(e) }
}

const handleFileChange = (e) => {
  newPostImage.value = e.target.files[0]
}

// ✨ 글 작성 (FormData)
const createPost = async () => {
  if (!authStore.isAuthenticated) return alert('로그인 필요')
  
  const formData = new FormData()
  formData.append('title', newPostTitle.value)
  formData.append('content', newPostContent.value)
  if (newPostTicker.value) formData.append('ticker', newPostTicker.value)
  if (newPostImage.value) formData.append('image', newPostImage.value)

  try {
    const res = await fetch(`${API_BASE}/posts/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'), // 🛡️ CSRF 토큰 추가
      },
      credentials: 'include', // 🔑 세션 쿠키 전송 필수
      body: formData
    })
    
    if (res.ok) {
      showWriteModal.value = false
      newPostTitle.value = ''; newPostContent.value = ''; newPostTicker.value = ''; newPostImage.value = null;
      await fetchData()
    } else {
      alert('글 작성 실패: ' + res.status)
    }
  } catch (e) { console.error(e) }
}

// 🔍 상세 열기 & 댓글 조회
const openDetail = async (post) => {
  selectedPost.value = post
  newComment.value = ''
  try {
    const res = await fetch(`${API_BASE}/posts/${post.id}/comments/`)
    if (res.ok) comments.value = await res.json()
  } catch (e) { console.error(e) }
}

// 💬 댓글 작성 (JSON)
const addComment = async () => {
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  if (!newComment.value.trim()) return

  try {
    const res = await fetch(`${API_BASE}/posts/${selectedPost.value.id}/comments/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'), // 🛡️ CSRF 토큰 추가
      },
      credentials: 'include', // 🔑 세션 쿠키 전송 필수
      body: JSON.stringify({ content: newComment.value })
    })

    if (res.ok) {
      const created = await res.json()
      comments.value.push(created)
      newComment.value = ''
      selectedPost.value.comment_count++
    } else {
      console.error('댓글 작성 실패:', res.status)
      alert('댓글을 등록할 수 없습니다.')
    }
  } catch (e) { console.error(e) }
}

// ❤️ 좋아요 토글
const toggleLike = async (post, event) => {
  if (event) event.stopPropagation()
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')

  try {
    const res = await fetch(`${API_BASE}/posts/${post.id}/like/`, { 
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'), // 🛡️ CSRF 토큰 추가
      },
      credentials: 'include', // 🔑 세션 쿠키 전송 필수
    })
    
    if (res.ok) {
      const data = await res.json()
      post.is_liked = data.liked
      post.like_count = data.like_count
      // 상세 모달이 열려있다면 동기화
      if (selectedPost.value && selectedPost.value.id === post.id) {
        selectedPost.value.is_liked = data.liked
        selectedPost.value.like_count = data.like_count
      }
    }
  } catch (e) { console.error(e) }
}

const getRankBadge = (index) => {
  if (index === 0) return '🥇'
  if (index === 1) return '🥈'
  if (index === 2) return '🥉'
  return ''
}

onMounted(fetchData)
</script>

<template>
  <div class="community-layout">
    <section class="feed-section">
      <div class="feed-header">
        <div class="header-text">
          <h2>투자의 발견</h2>
          <p class="subtitle">노하우를 공유하고 나만의 투자멘토를 찾아보세요.</p>
        </div>
        <button class="write-btn" @click="showWriteModal = true">글쓰기</button>
      </div>

      <div v-for="post in posts" :key="post.id" class="post-card" @click="openDetail(post)">
        <div class="post-meta">
          <div class="user-info">
            <img :src="post.author.profile_image_url || '/default-profile.png'" class="avatar" />
            <div>
              <span class="nickname">{{ post.author.nickname }}</span>
              <span class="return-rate" :class="post.author.total_return_rate > 0 ? 'red' : 'blue'">
                {{ post.author.total_return_rate > 0 ? '+' : '' }}{{ post.author.total_return_rate }}%
              </span>
            </div>
          </div>
          <span class="date">{{ new Date(post.created_at).toLocaleDateString() }}</span>
        </div>
        
        <h3>
           <span v-if="post.ticker" class="ticker-badge">{{ post.ticker }}</span>
           {{ post.title }}
        </h3>
        
        <div class="post-content">
          <p>
            {{ post.content.length > 100 ? post.content.slice(0, 100) + '...' : post.content }}
            <span v-if="post.content.length > 100" class="more-link">더 보기</span>
          </p>
        </div>
        
        <div v-if="post.image_url" class="post-image-wrapper">
          <img :src="post.image_url" class="post-image" />
        </div>

        <div class="post-actions">
           <button class="action-btn" :class="{ active: post.is_liked }" @click.stop="toggleLike(post, $event)">
             {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
           </button>
           <span class="comment-icon">💬 {{ post.comment_count }}</span>
        </div>
      </div>
    </section>

    <aside class="sidebar">
      <div class="rank-card">
        <h3>🏆 수익금 상위 투자자 TOP 5</h3>
        <ul class="rank-list">
          <li v-for="(user, idx) in topInvestors" :key="user.id" class="rank-item">
            <span class="rank-num">{{ idx + 1 }}</span>
            <div class="rank-user">
              <img :src="user.profile_image_url || '/default-profile.png'" class="avatar-small" />
              <div class="rank-info">
                <span class="rank-name">
                  {{ getRankBadge(idx) }} {{ user.nickname }}
                </span>
                <span class="rank-rate red">+{{ user.total_return_rate }}%</span>
              </div>
            </div>
            <button class="follow-btn">팔로우</button>
          </li>
        </ul>
      </div>
    </aside>
    
    <div v-if="showWriteModal" class="modal-overlay" @click.self="showWriteModal = false">
      <div class="modal-content write-modal">
        <h3>글 쓰기</h3>
        <div class="form-group">
           <input v-model="newPostTitle" placeholder="제목을 입력하세요" class="input-full title-input" />
        </div>
        <div class="form-group">
           <input v-model="newPostTicker" placeholder="관련 종목코드 (선택, 예: 005930)" class="input-full" />
        </div>
        <div class="form-group">
           <textarea v-model="newPostContent" placeholder="자유롭게 투자 이야기를 나누어보세요" class="textarea-full"></textarea>
        </div>
        <div class="form-group file-group">
           <input type="file" @change="handleFileChange" accept="image/*" class="file-input" />
        </div>
        <div class="modal-actions">
           <button @click="showWriteModal = false" class="cancel-btn">취소</button>
           <button @click="createPost" class="submit-btn">등록하기</button>
        </div>
      </div>
    </div>

    <div v-if="selectedPost" class="modal-overlay" @click.self="selectedPost = null">
      <div class="modal-content detail-modal">
        <div class="detail-header">
           <div class="user-info">
            <img :src="selectedPost.author.profile_image_url || '/default-profile.png'" class="avatar" />
            <div>
              <div class="nickname">{{ selectedPost.author.nickname }}</div>
              <div class="date">{{ new Date(selectedPost.created_at).toLocaleString() }}</div>
            </div>
          </div>
        </div>
        <h2 class="detail-title">{{ selectedPost.title }}</h2>
        <div class="detail-body">
           <p>{{ selectedPost.content }}</p>
           <img v-if="selectedPost.image_url" :src="selectedPost.image_url" class="detail-image" />
        </div>
        <div class="detail-actions">
           <button class="action-btn" :class="{ active: selectedPost.is_liked }" @click="toggleLike(selectedPost)">
             {{ selectedPost.is_liked ? '❤️' : '🤍' }} 좋아요 {{ selectedPost.like_count }}
           </button>
        </div>
        <hr class="divider"/>
        <div class="comments-section">
          <h3>댓글 {{ comments.length }}</h3>
          <div class="comment-list">
            <div v-for="cmt in comments" :key="cmt.id" class="comment-item">
              <span class="cmt-author">{{ cmt.author.nickname }}</span>
              <span class="cmt-content">{{ cmt.content }}</span>
            </div>
          </div>
          <div class="comment-input-area">
            <input v-model="newComment" type="text" placeholder="댓글을 남겨보세요..." @keyup.enter="addComment"/>
            <button @click="addComment">등록</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.community-layout { display: flex; gap: 40px; max-width: 1100px; margin: 0 auto; padding-top: 40px; color: #f5f5f7; }
.feed-section { flex: 2; }
.sidebar { flex: 1; display: none; }
@media(min-width: 900px) { .sidebar { display: block; } }

/* 헤더 스타일 개선 */
.feed-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; }
.header-text h2 { font-size: 28px; margin: 0 0 8px 0; }
.subtitle { color: #9ca3af; font-size: 15px; margin: 0; }
.write-btn { background: #2563eb; color: white; border: none; padding: 10px 24px; border-radius: 20px; font-weight: bold; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
.write-btn:hover { background: #1d4ed8; }

/* 게시글 카드 */
.post-card { background: #141414; padding: 24px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #222; cursor: pointer; transition: transform 0.2s; }
.post-card:hover { transform: translateY(-2px); border-color: #3b82f6; }

.user-info { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.avatar { width: 40px; height: 40px; border-radius: 50%; }
.nickname { font-weight: bold; font-size: 15px; }
.return-rate { font-size: 12px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1); margin-left: 6px; }
.red { color: #ff4d4d; } .blue { color: #4d94ff; }
.post-meta { display: flex; justify-content: space-between; color: #888; font-size: 13px; }

.post-content p { color: #d1d5db; line-height: 1.6; margin: 12px 0; }
.more-link { color: #60a5fa; font-weight: bold; margin-left: 8px; font-size: 14px; }
.ticker-badge { font-size: 12px; background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 2px 6px; border-radius: 4px; vertical-align: middle; margin-right: 6px; }

.post-image-wrapper { margin-top: 12px; border-radius: 12px; overflow: hidden; }
.post-image { width: 100%; max-height: 400px; object-fit: cover; display: block; }

.post-actions { display: flex; gap: 16px; margin-top: 16px; color: #9ca3af; font-size: 14px; }
.action-btn { background: none; border: none; color: inherit; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 4px; }
.action-btn.active { color: #ef4444; }

/* 사이드바 */
.rank-card { background: #1a1a1a; padding: 24px; border-radius: 16px; position: sticky; top: 100px; }
.rank-list { list-style: none; padding: 0; margin-top: 20px; }
.rank-item { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.rank-user { display: flex; align-items: center; gap: 12px; flex: 1; }
.avatar-small { width: 32px; height: 32px; border-radius: 50%; }
.rank-info { display: flex; flex-direction: column; font-size: 14px; }
.rank-name { font-weight: bold; }
.follow-btn { background: #333; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }

/* 모달 공통 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 100; backdrop-filter: blur(4px); }
.modal-content { background: #1f2937; padding: 32px; border-radius: 20px; color: #f5f5f7; box-shadow: 0 20px 50px rgba(0,0,0,0.5); display: flex; flex-direction: column; }

/* ✨ 글쓰기 모달 확장 스타일 */
.write-modal { width: 90%; max-width: 800px; height: auto; max-height: 90vh; }
.form-group { margin-bottom: 16px; }
.input-full { width: 100%; background: #111827; border: 1px solid #374151; color: white; padding: 14px; border-radius: 12px; box-sizing: border-box; font-size: 16px; }
.title-input { font-size: 20px; font-weight: bold; }
.textarea-full { width: 100%; height: 300px; background: #111827; border: 1px solid #374151; color: white; padding: 14px; border-radius: 12px; resize: none; box-sizing: border-box; font-size: 16px; line-height: 1.6; }
.file-input { margin-top: 8px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; }
.cancel-btn { background: #374151; color: white; border: none; padding: 12px 24px; border-radius: 12px; cursor: pointer; font-size: 16px; }
.submit-btn { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; }

/* 상세 모달 */
.detail-modal { width: 90%; max-width: 700px; max-height: 90vh; overflow-y: auto; }
.detail-title { font-size: 24px; margin: 20px 0; }
.detail-body { font-size: 16px; line-height: 1.7; color: #e5e7eb; white-space: pre-wrap; margin-bottom: 30px; }
.detail-image { max-width: 100%; border-radius: 12px; margin-top: 20px; }
.divider { border: 0; border-top: 1px solid #374151; margin: 30px 0; }
.comment-list { max-height: 300px; overflow-y: auto; margin-bottom: 20px; }
.comment-item { background: #111827; padding: 12px; border-radius: 8px; margin-bottom: 10px; font-size: 14px; }
.cmt-author { font-weight: bold; color: #60a5fa; margin-right: 8px; }
.comment-input-area { display: flex; gap: 10px; }
.comment-input-area input { flex: 1; background: #111827; border: 1px solid #374151; color: white; padding: 12px; border-radius: 8px; }
.comment-input-area button { background: #3b82f6; color: white; border: none; padding: 0 20px; border-radius: 8px; cursor: pointer; }
</style>