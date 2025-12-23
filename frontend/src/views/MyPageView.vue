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
              <v-avatar size="100" class="mb-4 border-subtle">
                <img 
                  :src="user?.profile_image_url || user?.profile_image || '/default-profile.png'" 
                  class="avatar"
                  style="width: 100%; height: 100%; object-fit: cover;"
                />
              </v-avatar>
              
              <h2 class="text-h5 font-weight-bold text-white mb-1">
                {{ user?.nickname || '사용자' }}
              </h2>
              <span class="text-grey mb-4">{{ user?.email }}</span>
              
              <div class="d-flex gap-4 mb-6">
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
            <v-row v-if="watchlist.length > 0">
              <v-col 
                v-for="item in watchlist" 
                :key="item.ticker"
                cols="12" sm="6" md="4"
              >
                <v-card 
                  class="custom-card watchlist-card pa-4" 
                  rounded="lg" 
                  variant="outlined"
                  @click="goToStock(item.ticker)"
                >
                  <div class="d-flex align-center pa-2">
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
                            {{ item.company_name || item.ticker }}
                          </div>
                          <div class="text-caption text-grey-lighten-1">{{ item.ticker }}</div>
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
              <v-icon icon="mdi-star-outline" size="48" class="mb-2"></v-icon>
              <div>관심 종목이 없습니다.</div>
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
              <v-col v-for="note in strategyNotes" :key="note.id" cols="12">
                <v-card class="custom-card pa-4" rounded="lg" variant="outlined">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <h4 class="text-white font-weight-bold">{{ note.title }}</h4>
                    <div>
                      <v-btn icon="mdi-pencil" variant="text" size="small" @click="openNoteDialog(note)"></v-btn>
                      <v-btn icon="mdi-delete" variant="text" size="small" color="error" @click="deleteNote(note.id)"></v-btn>
                    </div>
                  </div>
                  <p class="text-grey mb-2">{{ note.content }}</p>
                  <span class="text-caption text-grey">{{ formatDate(note.created_at) }}</span>
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

    <v-dialog v-model="showEditModal" max-width="400">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4">회원정보 수정</v-card-title>
        <v-card-text class="pa-4">
          <v-text-field v-model="editForm.nickname" label="닉네임" variant="outlined" bg-color="#1E1E1E" color="primary" class="mb-3"></v-text-field>
          <v-text-field v-model="editForm.email" label="이메일" variant="outlined" bg-color="#1E1E1E" color="primary" class="mb-3"></v-text-field>
          <v-text-field v-model="editForm.password" label="비밀번호 (변경 시에만)" type="password" variant="outlined" bg-color="#1E1E1E" color="primary" hint="변경하지 않으려면 비워두세요"></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showEditModal = false">취소</v-btn>
          <v-btn color="primary" variant="flat" @click="updateProfile">저장</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showNoteModal" max-width="500">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4">{{ editingNote ? '메모 수정' : '새 메모 작성' }}</v-card-title>
        <v-card-text class="pa-4">
          <v-text-field v-model="noteForm.title" label="제목" variant="outlined" bg-color="#1E1E1E" color="primary" class="mb-3"></v-text-field>
          <v-textarea v-model="noteForm.content" label="내용" variant="outlined" bg-color="#1E1E1E" color="primary" rows="5"></v-textarea>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeNoteModal">취소</v-btn>
          <v-btn color="primary" variant="flat" @click="saveNote">저장</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFollowersModal" max-width="500">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4 d-flex justify-space-between align-center">
          <span>팔로워 {{ followers.length }}</span>
          <v-btn icon="mdi-close" variant="text" size="small" @click="showFollowersModal = false"></v-btn>
        </v-card-title>
        <v-divider class="border-opacity-25"></v-divider>
        <v-card-text class="pa-4" style="max-height: 400px; overflow-y: auto;">
          <div v-if="followers.length > 0">
            <div v-for="follower in followers" :key="follower.id" class="user-item">
              <div class="d-flex align-center gap-3">
                <v-avatar size="40">
                  <img :src="follower.profile_image_url || follower.profile_image || `https://ui-avatars.com/api/?name=${follower.nickname}&background=2563eb&color=fff`" style="width: 100%; height: 100%; object-fit: cover;" />
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-white font-weight-medium">{{ follower.nickname }}</div>
                  <div class="text-grey text-caption">수익률: <span :class="follower.total_return_rate > 0 ? 'text-red-accent-2' : 'text-blue-accent-2'">{{ follower.total_return_rate > 0 ? '+' : '' }}{{ follower.total_return_rate }}%</span></div>
                </div>
                <v-btn v-if="follower.id !== user?.id" :color="follower.is_following ? 'grey' : 'primary'" :variant="follower.is_following ? 'outlined' : 'flat'" size="small" @click="toggleFollow(follower.id)">
                  {{ follower.is_following ? '팔로잉' : '팔로우' }}
                </v-btn>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-grey">아직 팔로워가 없습니다.</div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFollowingModal" max-width="500">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4 d-flex justify-space-between align-center">
          <span>팔로잉 {{ following.length }}</span>
          <v-btn icon="mdi-close" variant="text" size="small" @click="showFollowingModal = false"></v-btn>
        </v-card-title>
        <v-divider class="border-opacity-25"></v-divider>
        <v-card-text class="pa-4" style="max-height: 400px; overflow-y: auto;">
          <div v-if="following.length > 0">
            <div v-for="fUser in following" :key="fUser.id" class="user-item">
              <div class="d-flex align-center gap-3">
                <v-avatar size="40">
                  <img :src="fUser.profile_image_url || fUser.profile_image || `https://ui-avatars.com/api/?name=${fUser.nickname}&background=2563eb&color=fff`" style="width: 100%; height: 100%; object-fit: cover;" />
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-white font-weight-medium">{{ fUser.nickname }}</div>
                  <div class="text-grey text-caption">수익률: <span :class="fUser.total_return_rate > 0 ? 'text-red-accent-2' : 'text-blue-accent-2'">{{ fUser.total_return_rate > 0 ? '+' : '' }}{{ fUser.total_return_rate }}%</span></div>
                </div>
                <v-btn color="grey" variant="outlined" size="small" @click="toggleFollow(fUser.id)">팔로잉</v-btn>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-grey">아직 팔로우한 사용자가 없습니다.</div>
        </v-card-text>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mypageAPI } from '@/api/mypage'
import dayjs from 'dayjs'

const router = useRouter()

// =================== State (병합) ===================
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
const showFollowersModal = ref(false)
const showFollowingModal = ref(false)
const showAllTransactions = ref(false)
const displayLimit = 10
const activeTab = ref('holdings')

const editForm = ref({ nickname: '', email: '', password: '' })
const noteForm = ref({ title: '', content: '' })
const editingNote = ref(null)

// =================== Computed ===================
const portfolioStats = computed(() => {
  if (!portfolio.value?.portfolio) return null
  const { total_invested, total_eval, total_profit, total_return_rate } = portfolio.value.portfolio
  return {
    totalInvested: total_invested,
    totalEval: total_eval,
    totalProfit: total_profit,
    returnRate: total_return_rate,
    isProfitable: total_profit >= 0
  }
})

const displayedTransactions = computed(() => {
  return showAllTransactions.value ? transactions.value : transactions.value.slice(0, displayLimit)
})

// =================== Methods ===================

// [데이터 로드] Code 2의 로깅 + Code 1의 Pagination 대응 병합
const loadAllData = async () => {
  loading.value = true
  error.value = null
  console.log('🔄 마이페이지 데이터 동기화 시작...')
  
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
    
    // 닉네임 폼 초기화
    editForm.value = { nickname: user.value.nickname, email: user.value.email, password: '' }

    // [선택적 데이터 로드] Pagination 대응 (results || data)
    try {
      const watchlistRes = await mypageAPI.getWatchlist()
      watchlist.value = watchlistRes.data.results || watchlistRes.data
    } catch (e) { console.warn('⚠️ 관심종목 로드 실패') }

    try {
      const notesRes = await mypageAPI.getStrategyNotes()
      strategyNotes.value = notesRes.data.results || notesRes.data
    } catch (e) { console.warn('⚠️ 전략메모 로드 실패') }

    console.log('✅ 모든 데이터 로드 완료')
  } catch (e) {
    console.error('❌ 필수 데이터 로딩 실패:', e)
    error.value = e.response ? `${e.response.status} 에러: 데이터 호출 실패` : '서버에 연결할 수 없습니다.'
  } finally {
    loading.value = false
  }
}

// [팔로우 로직] Code 1의 기능 유지
const loadFollowers = async () => {
  try {
    const res = await mypageAPI.getFollowers()
    followers.value = res.data
    showFollowersModal.value = true
  } catch (e) { console.error('팔로워 로드 실패', e) }
}

const loadFollowing = async () => {
  try {
    const res = await mypageAPI.getFollowing()
    following.value = res.data
    showFollowingModal.value = true
  } catch (e) { console.error('팔로잉 로드 실패', e) }
}

const toggleFollow = async (targetUserId) => {
  try {
    // API 명세에 따라 mypageAPI.toggleFollow()가 있다면 그것을 사용하고, 없다면 fetch 사용
    const res = await fetch(`/api/users/${targetUserId}/follow/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
    })
    
    if (res.ok) {
      const data = await res.json()
      // UI 즉시 반영 로직
      if (showFollowingModal.value && !data.is_following) {
        following.value = following.value.filter(u => u.id !== targetUserId)
      }
      if (showFollowersModal.value) {
        const fUser = followers.value.find(u => u.id === targetUserId)
        if (fUser) fUser.is_following = data.is_following
      }
      data.is_following ? user.value.following_count++ : user.value.following_count--
    }
  } catch (e) { alert('처리 실패') }
}

// [공통 유틸리티]
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

// [회원정보/메모/이동 로직]
const openEditDialog = () => { showEditModal.value = true }
const updateProfile = async () => {
  try {
    const payload = { nickname: editForm.value.nickname, email: editForm.value.email }
    if (editForm.value.password) payload.password = editForm.value.password
    await mypageAPI.updateProfile(user.value.id, payload)
    alert('수정되었습니다.')
    showEditModal.value = false
    await loadAllData()
  } catch (e) { alert(e.response?.data?.detail || '수정 실패') }
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
    const res = await mypageAPI.getStrategyNotes()
    strategyNotes.value = res.data.results || res.data
    closeNoteModal()
  } catch (e) { alert('저장 실패') }
}

const deleteNote = async (id) => {
  if (confirm('삭제하시겠습니까?')) {
    await mypageAPI.deleteStrategyNote(id)
    strategyNotes.value = strategyNotes.value.filter(n => n.id !== id)
  }
}

const closeNoteModal = () => { showNoteModal.value = false; editingNote.value = null }
const goToStock = (ticker) => router.push(`/stock/${ticker}`)
const goToPost = (postId) => router.push({ name: 'community-detail', params: { id: postId } })

// [포맷터]
const formatPrice = (val) => val?.toLocaleString() || '0'
const formatDate = (date) => dayjs(date).format('YYYY.MM.DD HH:mm')
const getColor = (val) => {
  if (val > 0) return 'red-accent-2'
  if (val < 0) return 'blue-accent-2'
  return 'grey-lighten-1'
}

onMounted(loadAllData)
</script>

<style scoped>
.custom-card {
  background-color: #141414 !important;
  border-color: #333 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}
.border-subtle { border: 2px solid #333; }
.border-bottom { border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.custom-table { background: transparent !important; }
.custom-table th { border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; }
.custom-table td { border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important; height: 60px !important; }
.gap-4 { gap: 1rem; }
.gap-3 { gap: 0.75rem; }

/* 팔로우 버튼 디자인 */
.follow-stat-btn {
  background: none; border: none; cursor: pointer; display: flex;
  flex-direction: column; align-items: center; gap: 4px; padding: 8px 12px;
  border-radius: 8px; transition: background 0.2s;
}
.follow-stat-btn:hover { background: rgba(255, 255, 255, 0.05); }

/* 관심종목 카드 디자인 */
.watchlist-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.watchlist-card:hover {
  transform: translateY(-5px);
  background: #1e1e1e !important;
  border-color: #2563eb !important;
}
.user-item { padding: 12px; border-radius: 8px; transition: background 0.2s; }
.user-item:hover { background: rgba(255, 255, 255, 0.05); }
.line-height-tight { line-height: 1.2; }
</style>