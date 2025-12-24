<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const posts = ref([])
const topInvestors = ref([])
const showWriteModal = ref(false)
const currentSort = ref('latest') // 정렬 상태 추가

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

const goToUserProfile = (userId) => {
  if (!userId) return;
  router.push(`/user/${userId}`);
}

// 📈 수익 상태에 따른 색상 결정
const getReturnColor = (val) => {
  const num = parseFloat(val)
  if (num > 0) return 'red'
  if (num < 0) return 'blue'
  return 'grey'
}

// 🔢 % 포맷 (기존 유지)
const formatReturnRate = (val) => {
  if (val === undefined || val === null) return '0'
  const num = parseFloat(val)
  return num > 0 ? `+${num}` : num.toString()
}

// 💰 금액 포맷 (천 단위 콤마)
const formatPrice = (val) => {
  if (!val) return '0'
  return Math.floor(val).toLocaleString()
}

// 🔄 정렬 기능 추가
const fetchData = async (sortType = currentSort.value) => {
  try {
    const feedRes = await fetch(`${API_BASE}/posts/feed/?sort=${sortType}`, {
      credentials: 'include'
    })
    if (feedRes.ok) {
      posts.value = await feedRes.json()
    } else if (feedRes.status === 401 && sortType === 'following') {
      alert('팔로잉 글 보기는 로그인이 필요합니다.')
      currentSort.value = 'latest'
      await fetchData('latest')
    }
    
    const rankRes = await fetch(`${API_BASE}/users/rank/top/`)
    if (rankRes.ok) topInvestors.value = await rankRes.json()
  } catch (e) { console.error(e) }
}

const changeSort = (sortType) => {
  if (sortType === 'following' && !authStore.isAuthenticated) {
    alert('팔로잉 글 보기는 로그인이 필요합니다.')
    return
  }
  currentSort.value = sortType
  fetchData(sortType)
}

const handleFileChange = (e) => {
  newPostImage.value = e.target.files[0]
}

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
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
      body: formData
    })
    if (res.ok) {
      showWriteModal.value = false
      newPostTitle.value = ''; newPostContent.value = ''; newPostTicker.value = ''; newPostImage.value = null;
      await fetchData()
    }
  } catch (e) { console.error(e) }
}

const openDetail = async (post) => {
  selectedPost.value = post
  newComment.value = ''
  try {
    const res = await fetch(`${API_BASE}/posts/${post.id}/comments/`)
    if (res.ok) comments.value = await res.json()
  } catch (e) { console.error(e) }
}

const addComment = async () => {
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  if (!newComment.value.trim()) return
  try {
    const res = await fetch(`${API_BASE}/posts/${selectedPost.value.id}/comments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
      body: JSON.stringify({ content: newComment.value })
    })
    if (res.ok) {
      const created = await res.json()
      comments.value.push(created)
      newComment.value = ''
      selectedPost.value.comment_count++
    }
  } catch (e) { console.error(e) }
}

const toggleLike = async (post, event) => {
  if (event) event.stopPropagation()
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  try {
    const res = await fetch(`${API_BASE}/posts/${post.id}/like/`, { 
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
    })
    if (res.ok) {
      const data = await res.json()
      post.is_liked = data.liked
      post.like_count = data.like_count
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

      <!-- 🆕 정렬 탭 추가 -->
      <div class="sort-tabs">
        <button 
          :class="['sort-tab', { active: currentSort === 'latest' }]"
          @click="changeSort('latest')"
        >
          ⏰ 최신글
        </button>
        <button 
          :class="['sort-tab', { active: currentSort === 'popular' }]"
          @click="changeSort('popular')"
        >
          🔥 인기글
        </button>
        <button 
          :class="['sort-tab', { active: currentSort === 'following' }]"
          @click="changeSort('following')"
        >
          👥 팔로잉
        </button>
      </div>

      <!-- 결과 없을 때 메시지 -->
      <div v-if="posts.length === 0" class="empty-state">
        <p v-if="currentSort === 'following'">팔로우한 사용자의 글이 없습니다.</p>
        <p v-else>아직 게시글이 없습니다.</p>
      </div>

      <div v-for="post in posts" :key="post.id" class="post-card" @click="openDetail(post)">
        <div class="post-header">
          <div class="user-info-group clickable-wrapper" @click.stop="goToUserProfile(post.author.id)">
            <img :src="post.author.profile_image_url || '/default-profile.png'" class="avatar" />
            <div class="user-detail">
              <div class="name-row">
                <span class="nickname">{{ post.author.nickname }}</span>
                <span class="profit-badge" :class="getReturnColor(post.author.realized_profit)">
                  실현 {{ post.author.realized_profit > 0 ? '+' : '' }}{{ formatPrice(post.author.realized_profit) }}원
                </span>
              </div>
              <span class="post-date">{{ new Date(post.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
          <span v-if="post.ticker" class="ticker-badge">{{ post.ticker }}</span>
        </div>
        
        <div class="post-body">
          <h3 class="post-title">{{ post.title }}</h3>
          <p class="post-excerpt">
            {{ post.content.length > 100 ? post.content.slice(0, 100) + '...' : post.content }}
            <span v-if="post.content.length > 100" class="more-link">더 보기</span>
          </p>
        </div>
        
        <div v-if="post.image_url" class="post-image-wrapper">
          <img :src="post.image_url" class="post-image" />
        </div>

        <div class="post-footer">
           <button class="action-btn" :class="{ active: post.is_liked }" @click.stop="toggleLike(post, $event)">
             {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
           </button>
           <span class="comment-icon">💬 {{ post.comment_count }}</span>
        </div>
      </div>
    </section>

    <aside class="sidebar">
      <div class="rank-card">
        <h3>🏆 수익 TOP 투자자</h3>
        <ul class="rank-list">
          <li v-for="(user, idx) in topInvestors" :key="user.id" class="rank-item">
            <div class="rank-user clickable-wrapper" @click="goToUserProfile(user.id)">
              <div class="rank-num">{{ idx + 1 }}</div>
              <img :src="user.profile_image_url || '/default-profile.png'" class="avatar-small" />
              <div class="rank-info">
                <span class="rank-name">{{ getRankBadge(idx) }} {{ user.nickname }}</span>
                <div class="rank-profit-group">
                  <span class="rank-rate" :class="getReturnColor(user.total_return_rate)">
                    {{ formatReturnRate(user.total_return_rate) }}%
                  </span>
                  <span class="rank-amount">{{ formatPrice(user.realized_profit) }}원</span>
                </div>
              </div>
            </div>
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
           <div class="user-info clickable-wrapper" @click.stop="goToUserProfile(selectedPost.author.id)">
            <img :src="selectedPost.author.profile_image_url || '/default-profile.png'" class="avatar" />
            <div class="user-detail">
              <div class="name-row">
                <span class="nickname">{{ selectedPost.author.nickname }}</span>
                <span class="profit-badge" :class="getReturnColor(selectedPost.author.realized_profit)">
                  {{ formatPrice(selectedPost.author.realized_profit) }}원
                </span>
              </div>
              <div class="post-date">{{ new Date(selectedPost.created_at).toLocaleString() }}</div>
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
              <span class="cmt-author clickable-text" @click.stop="goToUserProfile(cmt.author.id)">
                {{ cmt.author.nickname }}
              </span>
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
/* 🔴 레이아웃 및 공통 */
.community-layout { display: flex; gap: 40px; max-width: 1100px; margin: 0 auto; padding: 40px 20px; color: #f5f5f7; }
.feed-section { flex: 2; }
.sidebar { flex: 1; display: none; }
@media(min-width: 900px) { .sidebar { display: block; } }

/* 🟠 헤더 영역 */
.feed-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-text h2 { font-size: 28px; margin: 0 0 8px 0; font-weight: 800; }
.subtitle { color: #9ca3af; font-size: 15px; margin: 0; }
.write-btn { background: #2563eb; color: white; border: none; padding: 10px 24px; border-radius: 24px; font-weight: bold; cursor: pointer; transition: 0.2s; }
.write-btn:hover { background: #1d4ed8; transform: scale(1.05); }

/* 🆕 정렬 탭 스타일 */
.sort-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid #222;
  padding-bottom: 0;
}

.sort-tab {
  background: none;
  border: none;
  color: #9ca3af;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
  position: relative;
  bottom: -1px;
}

.sort-tab:hover {
  color: #d1d5db;
}

.sort-tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

/* 빈 상태 메시지 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #6b7280;
  font-size: 15px;
}

/* 🟡 게시글 카드 (개선) */
.post-card { background: #14141409; padding: 24px; border-radius: 20px; margin-bottom: 24px; border: 1px solid #222; cursor: pointer; transition: 0.2s; }
.post-card:hover { border-color: #3b82f6; background: #1a1a1a07; }

.post-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.user-info-group { display: flex; align-items: center; gap: 12px; }
.avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; background: #333333; }
.user-detail { display: flex; flex-direction: column; gap: 2px; }
.name-row { display: flex; align-items: center; gap: 8px; }
.nickname { font-weight: bold; font-size: 15px; }

/* 수익 뱃지 */
.profit-badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.05); }
.profit-badge.red { color: #ff4d4d; background: rgba(255, 77, 77, 0.1); }
.profit-badge.blue { color: #4d94ff; background: rgba(77, 148, 255, 0.1); }
.profit-badge.grey { color: #4a4a4aff; background: rgba(136, 136, 136, 0.1); }

.post-date { font-size: 12px; color: #6b7280; }
.ticker-badge { font-size: 11px; background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 4px 10px; border-radius: 8px; font-weight: 600; }

.post-title { font-size: 19px; font-weight: 700; margin: 0 0 10px 0; color: #f9fafb; }
.post-excerpt { font-size: 15px; color: #d1d5db; line-height: 1.6; margin-bottom: 12px; }
.more-link { color: #3b82f6; font-weight: 600; margin-left: 4px; }

.post-image-wrapper { margin: 16px 0; border-radius: 12px; overflow: hidden; border: 1px solid #222; }
.post-image { width: 100%; max-height: 450px; object-fit: cover; display: block; }

.post-footer { display: flex; align-items: center; gap: 20px; padding-top: 16px; border-top: 1px solid #222; color: #9ca3af; font-size: 14px; }
.action-btn { background: none; border: none; color: inherit; cursor: pointer; display: flex; align-items: center; gap: 6px; padding: 0; }
.action-btn.active { color: #ef4444; font-weight: bold; }

/* 🟢 사이드바 랭킹 */
.rank-card { background: #14141489; padding: 24px; border-radius: 20px; position: sticky; top: 100px; border: 1px solid #222; }
.rank-card h3 { margin: 0 0 20px 0; font-size: 18px; }
.rank-list { list-style: none; padding: 0; }
.rank-item { margin-bottom: 18px; }
.rank-user { display: flex; align-items: center; gap: 12px; }
.rank-num { width: 20px; font-weight: 800; color: #4b5563; font-style: italic; }
.avatar-small { width: 40px; height: 40px; border-radius: 50%; }
.rank-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.rank-profit-group { display: flex; align-items: center; gap: 8px; }
.rank-rate { font-size: 12px; font-weight: bold; }
.rank-amount { font-size: 12px; color: #9ca3af; }

/* 🔵 모달 및 기타 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; justify-content: center; align-items: center; z-index: 1000; backdrop-filter: blur(8px); }
.modal-content { background: #1c1c1e; padding: 32px; border-radius: 24px; color: #f5f5f7; border: 1px solid #333; max-height: 90vh; overflow-y: auto; }
.write-modal { width: 90%; max-width: 600px; }
.detail-modal { width: 90%; max-width: 700px; }

.input-full, .textarea-full { width: 100%; background: #000; border: 1px solid #333; color: white; padding: 14px; border-radius: 12px; margin-bottom: 12px; box-sizing: border-box; }
.textarea-full { height: 200px; resize: none; }

.submit-btn { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-weight: bold; cursor: pointer; }
.cancel-btn { background: #333; color: white; border: none; padding: 12px 24px; border-radius: 12px; cursor: pointer; margin-right: 8px; }

.clickable-wrapper { cursor: pointer; transition: opacity 0.2s; }
.clickable-wrapper:hover { opacity: 0.7; }
.red { color: #ff4d4d !important; } 
.blue { color: #4d94ff !important; }
.grey { color: #888 !important; }
</style>