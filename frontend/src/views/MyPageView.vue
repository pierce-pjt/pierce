<template>
  <v-container class="py-10" style="max-width: 1200px;">
    
    <div v-if="loading" class="d-flex justify-center my-10">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <v-alert v-else-if="error" type="error" variant="tonal" class="mb-6">
      <div class="d-flex align-center justify-space-between">
        <span>{{ error }}</span>
        <v-btn color="error" variant="text" @click="loadAllData">다시 시도</v-btn>
      </div>
    </v-alert>

    <div v-else>
      <v-row class="mb-6">
        
        <v-col cols="12" md="4">
          <v-card class="custom-card pa-6 h-100" rounded="xl" variant="outlined">
            <div class="d-flex flex-column align-center">
              <v-avatar size="100" class="mb-4 border-subtle shadow-lg">
                <img 
                  :src="user?.profile_image_url || user?.profile_image || `https://ui-avatars.com/api/?name=${user?.nickname || 'User'}&background=2563eb&color=fff&size=200`"
                  style="width: 100%; height: 100%; object-fit: cover;"
                  alt="프로필"
                />
              </v-avatar>
              
              <h2 class="text-h5 font-weight-bold text-white mb-1">
                {{ user?.nickname || '사용자' }}
              </h2>
              <span class="text-grey mb-2">{{ user?.email }}</span>
              
              <div class="d-flex gap-4 mb-4">
                <button @click="loadFollowers" class="follow-stat-btn">
                  <span class="text-grey text-caption">팔로워</span>
                  <span class="text-white font-weight-bold">{{ user?.followers_count || 0 }}</span>
                </button>
                <button @click="loadFollowing" class="follow-stat-btn">
                  <span class="text-grey text-caption">팔로잉</span>
                  <span class="text-white font-weight-bold">{{ user?.following_count || 0 }}</span>
                </button>
              </div>
              
              <v-btn 
                block
                variant="tonal" 
                color="primary" 
                rounded="lg" 
                prepend-icon="mdi-pencil"
                @click="openEditDialog"
              >
                회원정보 수정
              </v-btn>
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" md="8">
          <v-card class="custom-card pa-8 h-100 d-flex flex-column justify-center" rounded="xl" variant="outlined">
            <div class="d-flex align-center justify-space-between mb-2">
              <h3 class="text-subtitle-1 text-grey font-weight-medium">💼 총 평가 자산</h3>
              <v-chip 
                v-if="portfolioStats"
                size="small" 
                :color="getColor(portfolioStats.returnRate)" 
                variant="tonal" 
                label
                class="font-weight-bold"
              >
                수익률 {{ portfolioStats.returnRate }}%
              </v-chip>
            </div>
            
            <div v-if="portfolioStats" class="d-flex align-end mb-6">
              <span class="text-h3 font-weight-bold text-white mr-2">
                {{ formatPrice(portfolioStats.totalEval) }}
              </span>
              <span class="text-h5 text-grey pb-1">원</span>
            </div>

            <v-divider class="mb-6 border-opacity-25"></v-divider>

            <v-row v-if="portfolioStats">
              <v-col cols="6">
                <div class="text-caption text-grey mb-1">총 투자금</div>
                <div class="text-h6 text-white">
                  {{ formatPrice(portfolioStats.totalInvested) }} 원
                </div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-grey mb-1">총 평가손익</div>
                <div 
                  :class="`text-h6 font-weight-bold text-${getColor(portfolioStats.totalProfit)}`"
                >
                  {{ portfolioStats.totalProfit > 0 ? '+' : '' }}{{ formatPrice(portfolioStats.totalProfit) }} 원
                </div>
              </v-col>
            </v-row>
          </v-card>
        </v-col>
      </v-row>

      <v-card class="custom-card mt-6" rounded="xl" variant="outlined" min-height="500">
        <v-tabs 
          v-model="activeTab" 
          bg-color="transparent" 
          color="primary" 
          grow 
          slider-color="primary"
        >
          <v-tab value="holdings" class="text-body-1">📊 보유 종목</v-tab>
          <v-tab value="transactions" class="text-body-1">📝 거래 내역</v-tab>
          <v-tab value="posts" class="text-body-1">💬 내가 쓴 글</v-tab>
          <v-tab value="watchlist" class="text-body-1">⭐ 관심 종목</v-tab>
          <v-tab value="notes" class="text-body-1">💡 투자 전략</v-tab>
        </v-tabs>

        <v-divider class="border-opacity-25"></v-divider>

        <v-window v-model="activeTab" class="pa-4">
          
          <v-window-item value="holdings">
            <v-table bg-color="transparent" hover class="text-white custom-table">
              <thead>
                <tr>
                  <th class="text-left text-grey">종목명</th>
                  <th class="text-right text-grey">수량</th>
                  <th class="text-right text-grey">평단가</th>
                  <th class="text-right text-grey">현재가</th>
                  <th class="text-right text-grey">평가손익</th>
                  <th class="text-right text-grey">수익률</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="item in holdings" 
                  :key="item.ticker"
                  @click="goToStock(item.ticker)"
                  style="cursor: pointer;"
                >
                  <td>
                    <div class="font-weight-bold">{{ item.company_name }}</div>
                    <div class="text-caption text-grey">{{ item.ticker }}</div>
                  </td>
                  <td class="text-right">{{ item.quantity }}주</td>
                  <td class="text-right">{{ formatPrice(item.average_buy_price) }}원</td>
                  <td class="text-right">{{ formatPrice(item.current_price) }}원</td>
                  <td 
                    class="text-right font-weight-bold" 
                    :class="`text-${getColor(item.profit)}`"
                  >
                    {{ formatPrice(item.profit) }}원
                  </td>
                  <td 
                    class="text-right font-weight-bold" 
                    :class="`text-${getColor(item.return_rate)}`"
                  >
                    {{ item.return_rate > 0 ? '+' : '' }}{{ item.return_rate }}%
                  </td>
                </tr>
                <tr v-if="holdings.length === 0">
                  <td colspan="6" class="text-center py-16 text-grey">
                    <v-icon icon="mdi-safe" size="48" class="mb-2"></v-icon>
                    <div>보유한 주식이 없습니다.</div>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-window-item>

          <v-window-item value="transactions">
            <div class="d-flex justify-space-between align-center mb-4">
              <h4 class="text-white">최근 {{ displayedTransactions.length }}건</h4>
              <v-btn 
                v-if="transactions.length > displayLimit"
                variant="text" 
                size="small"
                @click="showAllTransactions = !showAllTransactions"
              >
                {{ showAllTransactions ? '접기' : '전체보기' }}
              </v-btn>
            </div>

            <v-list bg-color="transparent" lines="two">
              <v-list-item 
                v-for="tx in displayedTransactions" 
                :key="tx.transaction_datetime" 
                class="px-4 py-3 border-bottom"
              >
                <template v-slot:prepend>
                  <v-avatar 
                    :color="tx.transaction_type === 'BUY' ? 'red-darken-4' : 'blue-darken-4'" 
                    rounded
                  >
                    <span class="text-caption font-weight-bold">
                      {{ tx.transaction_type === 'BUY' ? '매수' : '매도' }}
                    </span>
                  </v-avatar>
                </template>
                
                <v-list-item-title class="font-weight-bold text-white ml-4">
                  {{ tx.company_name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-grey ml-4 mt-1">
                  {{ formatPrice(tx.price) }}원 · {{ tx.quantity }}주
                </v-list-item-subtitle>
                
                <template v-slot:append>
                  <div class="text-right">
                    <div 
                      class="font-weight-bold"
                      :class="tx.transaction_type === 'BUY' ? 'text-red-accent-2' : 'text-blue-accent-2'"
                    >
                      {{ tx.transaction_type === 'BUY' ? '-' : '+' }}{{ formatPrice(tx.amount) }}원
                    </div>
                    <div class="text-caption text-grey mt-1">
                      {{ formatDate(tx.transaction_datetime) }}
                    </div>
                  </div>
                </template>
              </v-list-item>
              
              <div v-if="transactions.length === 0" class="text-center py-16 text-grey">
                <v-icon icon="mdi-history" size="48" class="mb-2"></v-icon>
                <div>거래 내역이 없습니다.</div>
              </div>
            </v-list>
          </v-window-item>

          <v-window-item value="posts">
            <v-list bg-color="transparent">
              <v-list-item 
                v-for="post in myPosts" 
                :key="post.id" 
                @click="goToPost(post.id)"
                class="px-4 py-3 border-bottom"
                style="cursor: pointer;"
              >
                <v-list-item-title class="text-white font-weight-medium mb-1">
                  {{ post.title }}
                </v-list-item-title>
                <v-list-item-subtitle class="d-flex align-center text-caption text-grey mt-2">
                  <v-icon icon="mdi-thumb-up-outline" size="14" class="mr-1"></v-icon> 
                  {{ post.like_count || 0 }}
                  <span class="mx-3">|</span>
                  <v-icon icon="mdi-comment-outline" size="14" class="mr-1"></v-icon> 
                  {{ post.comment_count || 0 }}
                  <span class="mx-3">|</span>
                  {{ formatDate(post.created_at) }}
                </v-list-item-subtitle>
              </v-list-item>
              
              <div v-if="myPosts.length === 0" class="text-center py-16 text-grey">
                <v-icon icon="mdi-pencil-off" size="48" class="mb-2"></v-icon>
                <div>작성한 게시글이 없습니다.</div>
              </div>
            </v-list>
          </v-window-item>

          <v-window-item value="watchlist">
            <v-row v-if="watchlist.length > 0" class="mt-2">
              <v-col 
                v-for="item in watchlist" 
                :key="item.ticker"
                cols="12" sm="6" md="4"
              >
                <v-card 
                  class="watchlist-card" 
                  rounded="xl" 
                  variant="flat"
                  @click="goToStock(item.ticker)"
                >
                  <div class="d-flex align-center pa-5">
                    <v-avatar size="52" class="mr-4 shadow-sm">
                      <v-img
                        :src="`https://static.toss.im/png-icons/securities/icn-sec-fill-${item.ticker}.png`"
                        alt="logo"
                        cover
                      >
                        <template v-slot:placeholder>
                          <v-icon color="grey-darken-2">mdi-finance</v-icon>
                        </template>
                      </v-img>
                    </v-avatar>

                    <div class="flex-grow-1">
                      <div class="d-flex justify-space-between align-start">
                        <div>
                          <div class="text-h6 font-weight-bold text-white mb-0 line-height-tight">
                            {{ item.ticker }}
                          </div>
                          <div class="text-caption text-grey-lighten-1">종목 상세 정보</div>
                        </div>
                        
                        <v-btn 
                          icon="mdi-close" 
                          variant="text" 
                          size="x-small"
                          color="grey-lighten-1"
                          class="remove-btn"
                          @click.stop="toggleWatchlistItem(item.ticker)"
                        ></v-btn>
                      </div>
                    </div>
                  </div>
                </v-card>
              </v-col>
            </v-row>
            
            <div v-else class="text-center py-16 text-grey">
              <v-icon icon="mdi-star-outline" size="64" color="grey-darken-3" class="mb-4"></v-icon>
              <div class="text-h6">관심 종목이 비어있습니다</div>
              <div class="text-body-2">별표를 눌러 나만의 리스트를 만들어보세요.</div>
            </div>
          </v-window-item>

          <v-window-item value="notes">
            <div class="d-flex justify-space-between align-center mb-4">
              <h4 class="text-white">내 투자 전략</h4>
              <v-btn 
                color="primary" 
                variant="tonal" 
                prepend-icon="mdi-plus"
                @click="openNoteDialog()"
              >
                메모 추가
              </v-btn>
            </div>

            <v-row v-if="strategyNotes.length > 0">
              <v-col 
                v-for="note in strategyNotes" 
                :key="note.id"
                cols="12"
              >
                <v-card class="custom-card pa-4" rounded="lg" variant="outlined">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <h4 class="text-white font-weight-bold">{{ note.title }}</h4>
                    <div>
                      <v-btn 
                        icon="mdi-pencil" 
                        variant="text" 
                        size="small"
                        @click="openNoteDialog(note)"
                      ></v-btn>
                      <v-btn 
                        icon="mdi-delete" 
                        variant="text" 
                        size="small"
                        color="error"
                        @click="deleteNote(note.id)"
                      ></v-btn>
                    </div>
                  </div>
                  <p class="text-grey mb-2">{{ note.content }}</p>
                  <span class="text-caption text-grey">
                    {{ formatDate(note.created_at) }}
                  </span>
                </v-card>
              </v-col>
            </v-row>

            <div v-else class="text-center py-16 text-grey">
              <v-icon icon="mdi-note-outline" size="48" class="mb-2"></v-icon>
              <div>작성한 메모가 없습니다.</div>
            </div>
          </v-window-item>

        </v-window>
      </v-card>
    </div>

    </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mypageAPI } from '@/api/mypage'
import dayjs from 'dayjs'

const router = useRouter()

// State
const user = ref(null)
const portfolio = ref(null)
const holdings = ref([])
const transactions = ref([])
const watchlist = ref([])
const strategyNotes = ref([])
const myPosts = ref([])
const followers = ref([])
const following = ref([])

const loading = ref(false)
const error = ref(null)
const showEditModal = ref(false)
const showNoteModal = ref(false)
const showAllTransactions = ref(false)
const showFollowersModal = ref(false)
const showFollowingModal = ref(false)
const displayLimit = 10
const activeTab = ref('holdings')

const editForm = ref({ nickname: '', email: '', password: '' })
const noteForm = ref({ title: '', content: '' })
const editingNote = ref(null)

// Computed
const portfolioStats = computed(() => {
  if (!portfolio.value) return null
  const { total_invested, total_eval, total_profit, total_return_rate } = portfolio.value.portfolio
  return {
    totalInvested: total_invested,
    totalEval: total_eval,
    totalProfit: total_profit,
    returnRate: total_return_rate
  }
})

const displayedTransactions = computed(() => {
  return showAllTransactions.value ? transactions.value : transactions.value.slice(0, displayLimit)
})

// Methods
const loadAllData = async () => {
  loading.value = true
  error.value = null
  try {
    const [userRes, portfolioRes, holdingsRes, txRes, postsRes] = await Promise.all([
      mypageAPI.getMyInfo(),
      mypageAPI.getPortfolioSummary(),
      mypageAPI.getHoldings(),
      mypageAPI.getTransactions(),
      mypageAPI.getMyPosts(),
    ])

    user.value = userRes.data
    portfolio.value = portfolioRes.data
    holdings.value = holdingsRes.data
    transactions.value = txRes.data
    myPosts.value = postsRes.data

    try {
      const watchlistRes = await mypageAPI.getWatchlist()
      const actualData = watchlistRes.data.results || watchlistRes.data
      watchlist.value = Array.isArray(actualData) ? actualData : []
    } catch (e) { watchlist.value = [] }
    
    try {
      const notesRes = await mypageAPI.getStrategyNotes()
      strategyNotes.value = notesRes.data
    } catch (e) { strategyNotes.value = [] }

  } catch (e) {
    error.value = '데이터를 불러오는 데 실패했습니다.'
  } finally {
    loading.value = false
  }
}

// ... 기타 메서드들 (loadFollowers, toggleFollow, updateProfile, saveNote 등 기존 로직 유지) ...
const loadFollowers = async () => {
  try {
    const res = await mypageAPI.getFollowers()
    followers.value = res.data
    showFollowersModal.value = true
  } catch (e) { console.error(e) }
}
const loadFollowing = async () => {
  try {
    const res = await mypageAPI.getFollowing()
    following.value = res.data
    showFollowingModal.value = true
  } catch (e) { console.error(e) }
}
const toggleFollow = async (targetUserId) => {
  try {
    const res = await fetch(`/api/users/${targetUserId}/follow/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    if (res.ok) {
      const data = await res.json()
      if (data.is_following) user.value.following_count++
      else user.value.following_count--
      loadAllData()
    }
  } catch (e) { alert('처리 실패') }
}
const getCookie = (name) => {
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}
const openEditDialog = () => {
  editForm.value = { nickname: user.value.nickname, email: user.value.email, password: '' }
  showEditModal.value = true
}
const updateProfile = async () => {
  try {
    await mypageAPI.updateProfile(user.value.id, editForm.value)
    alert('수정 완료')
    showEditModal.value = false
    loadAllData()
  } catch (e) { alert('수정 실패') }
}
const toggleWatchlistItem = async (ticker) => {
  try {
    const res = await mypageAPI.toggleWatchlist(ticker)
    if (!res.data.added) watchlist.value = watchlist.value.filter(item => item.ticker !== ticker)
  } catch (e) { console.error(e) }
}
const openNoteDialog = (note = null) => {
  if (note) {
    editingNote.value = note
    noteForm.value = { title: note.title, content: note.content }
  } else {
    editingNote.value = null
    noteForm.value = { title: '', content: '' }
  }
  showNoteModal.value = true
}
const saveNote = async () => {
  try {
    if (editingNote.value) await mypageAPI.updateStrategyNote(editingNote.value.id, noteForm.value)
    else await mypageAPI.createStrategyNote(noteForm.value)
    loadAllData()
    closeNoteModal()
  } catch (e) { alert('저장 실패') }
}
const deleteNote = async (id) => {
  if (!confirm('삭제하시겠습니까?')) return
  try {
    await mypageAPI.deleteStrategyNote(id)
    strategyNotes.value = strategyNotes.value.filter(n => n.id !== id)
  } catch (e) { alert('삭제 실패') }
}
const closeNoteModal = () => { showNoteModal.value = false }
const goToStock = (ticker) => router.push(`/stock/${ticker}`)
const goToPost = (postId) => router.push(`/community/${postId}`)

const formatPrice = (v) => v?.toLocaleString() || '0'
const formatDate = (d) => dayjs(d).format('YYYY.MM.DD HH:mm')
const getColor = (v) => {
  if (v > 0) return 'red-accent-2'
  if (v < 0) return 'blue-accent-2'
  return 'grey-lighten-1'
}

onMounted(loadAllData)
</script>

<style scoped>
.custom-card {
  background-color: #141414 !important;
  border-color: #333 !important;
}

.watchlist-card {
  background: linear-gradient(145deg, #1e1e1e, #141414) !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  cursor: pointer;
}

.watchlist-card:hover {
  transform: translateY(-5px);
  background: linear-gradient(145deg, #252525, #1a1a1a) !important;
  border-color: rgba(49, 130, 246, 0.5) !important;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4) !important;
}

.line-height-tight { line-height: 1.2; }

.remove-btn {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 1 !important;
  background-color: rgba(255, 255, 255, 0.1);
}

.follow-stat-btn {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
}

.follow-stat-btn:hover { background: rgba(255, 255, 255, 0.05); }

.user-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.user-item:hover { background: rgba(255, 255, 255, 0.05); }

.border-subtle { border: 2px solid #333; }
.border-bottom { border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.custom-table { background: transparent !important; }
.custom-table td { height: 60px !important; }
.gap-4 { gap: 1rem; }
.gap-3 { gap: 0.75rem; }
</style>