<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const posts = ref([])
const loading = ref(false)

// 📝 글쓰기 모달 상태
const showWriteModal = ref(false)
const newPost = ref({ title: '', content: '', ticker: '' })

// 💬 상세(댓글) 모달 상태
const selectedPost = ref(null)
const comments = ref([])
const newComment = ref('')

// 🔄 데이터 불러오기 (피드)
const fetchFeed = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/posts/feed/')
    if (res.ok) {
      posts.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ✨ 글 작성하기
const createPost = async () => {
  if (!authStore.isAuthenticated) {
    alert('로그인이 필요합니다.')
    return
  }
  if (!newPost.value.title || !newPost.value.content) {
    alert('제목과 내용을 입력해주세요.')
    return
  }

  try {
    const res = await fetch('/api/posts/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        // Django CSRF 토큰 처리가 필요할 수 있음 (일단 쿠키 자동 포함)
      },
      body: JSON.stringify(newPost.value)
    })
    
    if (res.ok) {
      // 성공 시 목록 갱신 및 모달 닫기
      await fetchFeed()
      showWriteModal.value = false
      newPost.value = { title: '', content: '', ticker: '' }
    } else {
      alert('글 작성에 실패했습니다.')
    }
  } catch (e) {
    console.error(e)
  }
}

// ❤️ 좋아요 토글
const toggleLike = async (post, event) => {
  event.stopPropagation() // 상세 모달 열림 방지
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')

  try {
    const res = await fetch(`/api/posts/${post.id}/like/`, { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      // 화면 즉시 갱신 (낙관적 업데이트 or 응답값 사용)
      post.is_liked = data.liked
      post.like_count = data.like_count
      
      // 상세 모달이 열려있다면 그쪽 데이터도 동기화
      if (selectedPost.value && selectedPost.value.id === post.id) {
        selectedPost.value.is_liked = data.liked
        selectedPost.value.like_count = data.like_count
      }
    }
  } catch (e) {
    console.error(e)
  }
}

// 🔍 게시글 상세 열기 (댓글 조회)
const openDetail = async (post) => {
  selectedPost.value = post
  newComment.value = ''
  try {
    const res = await fetch(`/api/posts/${post.id}/comments/`)
    if (res.ok) comments.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

// 💬 댓글 작성
const addComment = async () => {
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  if (!newComment.value.trim()) return

  try {
    const res = await fetch(`/api/posts/${selectedPost.value.id}/comments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newComment.value })
    })
    if (res.ok) {
      // 댓글 목록 갱신
      const created = await res.json()
      comments.value.push(created)
      newComment.value = ''
      // 게시글의 댓글 수도 +1
      selectedPost.value.comment_count++
    }
  } catch (e) {
    console.error(e)
  }
}

// 🗑️ 글 삭제 (본인인 경우)
const deletePost = async (id) => {
  if (!confirm('정말 삭제하시겠습니까?')) return
  try {
    const res = await fetch(`/api/posts/${id}/`, { method: 'DELETE' })
    if (res.ok) {
      selectedPost.value = null // 모달 닫기
      await fetchFeed() // 목록 갱신
    } else {
      alert('삭제 권한이 없거나 오류가 발생했습니다.')
    }
  } catch(e) { console.error(e) }
}

onMounted(() => {
  fetchFeed()
})
</script>

<template>
  <div class="community-page">
    
    <header class="page-header">
      <div class="header-content">
        <h1>투자자들의 이야기</h1>
        <p>인사이트를 공유하고 함께 성장하세요.</p>
      </div>
      <button class="write-btn" @click="showWriteModal = true">
        ✍️ 글쓰기
      </button>
    </header>

    <div class="feed-container">
      <div v-if="loading" class="loading">로딩 중...</div>
      
      <div v-else-if="posts.length === 0" class="empty-state">
        아직 게시글이 없습니다. 첫 글을 남겨보세요!
      </div>

      <div 
        v-else 
        v-for="post in posts" 
        :key="post.id" 
        class="post-card"
        @click="openDetail(post)"
      >
        <div class="post-header">
          <div class="author-info">
            <img :src="post.author.profile_image_url || '/default-profile.png'" class="avatar-small" />
            <span class="nickname">{{ post.author.nickname }}</span>
          </div>
          <span class="date">{{ new Date(post.created_at).toLocaleDateString() }}</span>
        </div>

        <h3 class="post-title">
          <span v-if="post.ticker" class="ticker-badge">{{ post.ticker }}</span>
          {{ post.title }}
        </h3>
        <p class="post-preview">{{ post.content }}</p>

        <div class="post-footer">
          <button 
            class="action-btn" 
            :class="{ active: post.is_liked }"
            @click="toggleLike(post, $event)"
          >
            {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
          </button>
          <span class="comment-cnt">💬 {{ post.comment_count }}</span>
        </div>
      </div>
    </div>

    <div v-if="showWriteModal" class="modal-overlay" @click.self="showWriteModal = false">
      <div class="modal-content write-modal">
        <h2>새 글 작성</h2>
        <input v-model="newPost.title" type="text" placeholder="제목을 입력하세요" class="input-field" />
        <input v-model="newPost.ticker" type="text" placeholder="종목코드 (선택사항, 예: 005930)" class="input-field" />
        <textarea v-model="newPost.content" placeholder="내용을 자유롭게 적어주세요" class="textarea-field"></textarea>
        
        <div class="modal-actions">
          <button class="cancel-btn" @click="showWriteModal = false">취소</button>
          <button class="submit-btn" @click="createPost">등록하기</button>
        </div>
      </div>
    </div>

    <div v-if="selectedPost" class="modal-overlay" @click.self="selectedPost = null">
      <div class="modal-content detail-modal">
        <div class="detail-header">
          <div class="author-info">
            <img :src="selectedPost.author.profile_image_url || '/default-profile.png'" class="avatar-medium" />
            <div>
              <div class="nickname">{{ selectedPost.author.nickname }}</div>
              <div class="date">{{ new Date(selectedPost.created_at).toLocaleString() }}</div>
            </div>
          </div>
          <button 
            v-if="authStore.user && authStore.user.id === selectedPost.author.id" 
            class="delete-btn"
            @click="deletePost(selectedPost.id)"
          >
            삭제
          </button>
        </div>

        <h2 class="detail-title">
          <span v-if="selectedPost.ticker" class="ticker-badge large">{{ selectedPost.ticker }}</span>
          {{ selectedPost.title }}
        </h2>
        <div class="detail-body">{{ selectedPost.content }}</div>

        <div class="detail-actions">
          <button 
            class="action-btn" 
            :class="{ active: selectedPost.is_liked }"
            @click="toggleLike(selectedPost, $event)"
          >
            {{ selectedPost.is_liked ? '❤️' : '🤍' }} 좋아요 {{ selectedPost.like_count }}
          </button>
        </div>

        <hr class="divider" />

        <div class="comments-section">
          <h3>댓글 {{ comments.length }}</h3>
          <div class="comment-list">
            <div v-for="cmt in comments" :key="cmt.id" class="comment-item">
              <span class="cmt-author">{{ cmt.author.nickname }}</span>
              <span class="cmt-content">{{ cmt.content }}</span>
              <span class="cmt-date">{{ new Date(cmt.created_at).toLocaleDateString() }}</span>
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

  </div>
</template>

<style scoped>
.community-page { max-width: 800px; margin: 0 auto; color: #f5f5f7; padding-bottom: 80px; }

/* 헤더 */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #1f2937; padding-bottom: 20px; }
.page-header h1 { font-size: 28px; margin: 0 0 8px 0; }
.page-header p { color: #9ca3af; margin: 0; }
.write-btn { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: background 0.2s; }
.write-btn:hover { background: #1d4ed8; }

/* 피드 리스트 */
.feed-container { display: flex; flex-direction: column; gap: 16px; }
.post-card { background: #141414; border: 1px solid #1f2937; border-radius: 16px; padding: 20px; cursor: pointer; transition: transform 0.2s, border-color 0.2s; }
.post-card:hover { transform: translateY(-2px); border-color: #3b82f6; }

.post-header { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; color: #9ca3af; }
.author-info { display: flex; align-items: center; gap: 8px; }
.avatar-small { width: 24px; height: 24px; border-radius: 50%; background: #333; }
.nickname { color: #fff; font-weight: 600; }

.post-title { margin: 0 0 10px 0; font-size: 18px; display: flex; align-items: center; gap: 8px; }
.ticker-badge { font-size: 12px; background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 2px 6px; border-radius: 4px; font-weight: normal; }
.post-preview { color: #d1d5db; font-size: 15px; line-height: 1.5; margin-bottom: 16px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.post-footer { display: flex; gap: 16px; font-size: 14px; color: #9ca3af; }
.action-btn { background: none; border: none; color: inherit; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 14px; padding: 0; }
.action-btn.active { color: #ef4444; }

/* 모달 공통 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 100; backdrop-filter: blur(4px); }
.modal-content { background: #1f2937; padding: 24px; border-radius: 16px; width: 90%; max-width: 600px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.5); color: #f5f5f7; }

/* 글쓰기 모달 */
.input-field, .textarea-field { width: 100%; background: #111827; border: 1px solid #374151; color: white; padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 15px; box-sizing: border-box;}
.textarea-field { height: 200px; resize: none; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
.cancel-btn { background: #374151; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; }
.submit-btn { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; }

/* 상세 모달 */
.detail-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
.avatar-medium { width: 40px; height: 40px; border-radius: 50%; background: #333; }
.delete-btn { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.detail-title { font-size: 24px; margin-bottom: 20px; line-height: 1.3; }
.detail-body { font-size: 16px; line-height: 1.6; color: #e5e7eb; white-space: pre-wrap; margin-bottom: 30px; }
.divider { border: 0; border-top: 1px solid #374151; margin: 20px 0; }

/* 댓글 영역 */
.comment-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; max-height: 300px; overflow-y: auto; }
.comment-item { background: #111827; padding: 12px; border-radius: 8px; font-size: 14px; }
.cmt-author { font-weight: 700; color: #60a5fa; margin-right: 8px; }
.cmt-date { font-size: 12px; color: #6b7280; float: right; }
.comment-input-area { display: flex; gap: 10px; }
.comment-input-area input { flex: 1; background: #111827; border: 1px solid #374151; color: white; padding: 10px; border-radius: 8px; }
.comment-input-area button { background: #3b82f6; color: white; border: none; padding: 0 20px; border-radius: 8px; cursor: pointer; }
</style>