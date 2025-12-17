<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const posts = ref([])
const topInvestors = ref([]) // 👑 랭킹 데이터
const showWriteModal = ref(false)

// 📝 글쓰기 데이터
const newPostTitle = ref('')
const newPostContent = ref('')
const newPostTicker = ref('')
const newPostImage = ref(null) // 파일 객체

const API_BASE = '/api'

// 🔄 데이터 로드
const fetchData = async () => {
  // 1. 피드 조회
  const feedRes = await fetch(`${API_BASE}/posts/feed/`)
  if (feedRes.ok) posts.value = await feedRes.json()
  
  // 2. 랭킹 조회
  const rankRes = await fetch(`${API_BASE}/users/rank/top/`)
  if (rankRes.ok) topInvestors.value = await rankRes.json()
}

// 📸 이미지 선택 핸들러
const handleFileChange = (e) => {
  newPostImage.value = e.target.files[0]
}

// ✨ 글 작성 (FormData 사용)
const createPost = async () => {
  if (!authStore.isAuthenticated) return alert('로그인 필요')
  
  const formData = new FormData()
  formData.append('title', newPostTitle.value)
  formData.append('content', newPostContent.value)
  if (newPostTicker.value) formData.append('ticker', newPostTicker.value)
  if (newPostImage.value) formData.append('image', newPostImage.value)

  const res = await fetch(`${API_BASE}/posts/`, {
    method: 'POST',
    body: formData // JSON 대신 FormData 전송
  })
  
  if (res.ok) {
    showWriteModal.value = false
    newPostTitle.value = ''; newPostContent.value = ''; newPostImage.value = null;
    await fetchData()
    // 글 작성 보상 마일리지 지급 로직은 백엔드 Signal로 처리 권장 (여기선 생략)
    alert('글이 등록되었습니다! (+50 백마일)')
  }
}

// 👑 랭킹 뱃지 (1~3등)
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
        <h2>투자의 발견</h2>
        <button class="write-btn" @click="showWriteModal = true">글쓰기</button>
      </div>

      <div v-for="post in posts" :key="post.id" class="post-card">
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
        
        <h3>{{ post.title }}</h3>
        <p>{{ post.content }}</p>
        
        <div v-if="post.image_url" class="post-image-wrapper">
          <img :src="post.image_url" class="post-image" />
        </div>

        <div class="post-actions">
           <span>❤️ {{ post.like_count }}</span>
           <span>💬 {{ post.comment_count }}</span>
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
      <div class="modal-content">
        <h3>글 쓰기</h3>
        <input v-model="newPostTitle" placeholder="제목" class="input-full" />
        <textarea v-model="newPostContent" placeholder="내용" class="textarea-full"></textarea>
        <input v-model="newPostTicker" placeholder="관련 종목코드 (선택)" class="input-full" />
        <input type="file" @change="handleFileChange" accept="image/*" class="input-full" />
        <button @click="createPost" class="submit-btn">등록</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.community-layout { display: flex; gap: 30px; max-width: 1100px; margin: 0 auto; padding-top: 20px; color: #f5f5f7; }
.feed-section { flex: 2; }
.sidebar { flex: 1; display: none; } /* 모바일 숨김 */
@media(min-width: 768px) { .sidebar { display: block; } }

.post-card { background: #141414; padding: 20px; border-radius: 16px; margin-bottom: 16px; border: 1px solid #222; }
.user-info { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.avatar { width: 36px; height: 36px; border-radius: 50%; }
.nickname { font-weight: bold; }
.return-rate { font-size: 12px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1); margin-left: 6px;}
.red { color: #ff4d4d; } .blue { color: #4d94ff; }

.post-image-wrapper { margin: 12px 0; border-radius: 12px; overflow: hidden; }
.post-image { width: 100%; object-fit: cover; max-height: 400px; }

/* 사이드바 랭킹 스타일 */
.rank-card { background: #1a1a1a; padding: 20px; border-radius: 16px; position: sticky; top: 80px; }
.rank-list { list-style: none; padding: 0; margin-top: 16px; }
.rank-item { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.rank-user { display: flex; align-items: center; gap: 10px; flex: 1; }
.avatar-small { width: 30px; height: 30px; border-radius: 50%; }
.rank-info { display: flex; flex-direction: column; font-size: 13px; }
.rank-name { font-weight: bold; }
.follow-btn { background: #333; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; }

/* 모달 및 기타 버튼 스타일은 기존 유지 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 100;}
.modal-content { background: #222; padding: 20px; border-radius: 12px; width: 400px; display: flex; flex-direction: column; gap: 10px; }
.input-full, .textarea-full { background: #333; border: 1px solid #444; color: white; padding: 10px; border-radius: 8px; width: 100%; box-sizing: border-box; }
.submit-btn { background: #2563eb; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; }
.write-btn { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; float: right; }
</style>