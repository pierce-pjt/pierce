<template>
  <v-container class="py-10" style="max-width: 1600px;">
    
    <!-- 로딩 -->
    <div v-if="loading" class="d-flex justify-center my-10">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- 에러 -->
    <v-alert v-else-if="error" type="error" variant="tonal" class="mb-6">
      <div class="d-flex align-center justify-space-between">
        <span>{{ error }}</span>
        <v-btn color="error" variant="text" @click="loadUserData">다시 시도</v-btn>
      </div>
    </v-alert>

    <!-- 메인 컨텐츠 -->
    <div v-else>
      <!-- =================== 프로필 & 포트폴리오 요약 =================== -->
      <v-row class="mb-6">
        
        <!-- 프로필 카드 -->
        <v-col cols="12" md="4">
          <v-card class="custom-card pa-6 h-100" rounded="xl" variant="outlined">
            <div class="d-flex flex-column align-center">
              <v-avatar size="100" class="mb-4 border-subtle">
                <img 
                  :src="targetUser?.profile_image_url || targetUser?.profile_image || `https://ui-avatars.com/api/?name=${targetUser?.nickname || 'User'}&background=2563eb&color=fff&size=200`"
                  style="width: 100%; height: 100%; object-fit: cover;"
                  alt="프로필"
                />
              </v-avatar>
              
              <h2 class="text-h5 font-weight-bold text-white mb-1">
                {{ targetUser?.nickname || '사용자' }}
              </h2>
              <span class="text-grey mb-2">{{ targetUser?.email }}</span>
              
              <!-- 팔로우 정보 (클릭 가능) -->
              <div class="d-flex gap-4 mb-4">
                <button @click="loadFollowers" class="follow-stat-btn">
                  <span class="text-grey text-caption">팔로워</span>
                  <span class="text-white font-weight-bold">{{ targetUser?.followers_count || 0 }}</span>
                </button>
                <button @click="loadFollowing" class="follow-stat-btn">
                  <span class="text-grey text-caption">팔로잉</span>
                  <span class="text-white font-weight-bold">{{ targetUser?.following_count || 0 }}</span>
                </button>
              </div>
              
              <!-- 👇 본인이 아니면 팔로우 버튼, 본인이면 마이페이지로 이동 -->
              <v-btn 
                v-if="!isMyProfile"
                block
                :color="isFollowing ? 'grey' : 'primary'"
                :variant="isFollowing ? 'outlined' : 'flat'"
                rounded="lg"
                :prepend-icon="isFollowing ? 'mdi-account-check' : 'mdi-account-plus'"
                @click="toggleFollowUser"
              >
                {{ isFollowing ? '팔로잉' : '팔로우' }}
              </v-btn>
              
              <v-btn 
                v-else
                block
                variant="tonal" 
                color="primary" 
                rounded="lg" 
                prepend-icon="mdi-pencil"
                @click="$router.push('/my')"
              >
                내 프로필 수정
              </v-btn>
            </div>
          </v-card>
        </v-col>

        <!-- 포트폴리오 요약 카드 -->
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

      <!-- =================== 탭 컨텐츠 =================== -->
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
          <v-tab value="posts" class="text-body-1">💬 작성한 글</v-tab>
        </v-tabs>

        <v-divider class="border-opacity-25"></v-divider>

        <v-window v-model="activeTab" class="pa-4">
          
          <!-- ========== 보유 종목 ========== -->
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

          <!-- ========== 거래 내역 ========== -->
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

          <!-- ========== 작성한 글 ========== -->
          <v-window-item value="posts">
            <v-list bg-color="transparent">
              <v-list-item 
                v-for="post in userPosts" 
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
              
              <div v-if="userPosts.length === 0" class="text-center py-16 text-grey">
                <v-icon icon="mdi-pencil-off" size="48" class="mb-2"></v-icon>
                <div>작성한 게시글이 없습니다.</div>
              </div>
            </v-list>
          </v-window-item>

        </v-window>
      </v-card>
    </div>

    <!-- =================== 모달: 팔로워 목록 (MyPageView와 동일) =================== -->
    <v-dialog v-model="showFollowersModal" max-width="500">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4 d-flex justify-space-between align-center">
          <span>팔로워 {{ followers.length }}</span>
          <v-btn 
            icon="mdi-close" 
            variant="text" 
            size="small"
            @click="showFollowersModal = false"
          ></v-btn>
        </v-card-title>
        <v-divider class="border-opacity-25"></v-divider>
        <v-card-text class="pa-4" style="max-height: 400px; overflow-y: auto;">
          <div v-if="followers.length > 0">
            <div 
              v-for="follower in followers" 
              :key="follower.id"
              class="user-item"
              @click="goToUserProfile(follower.id)"
              style="cursor: pointer;"
            >
              <div class="d-flex align-center gap-3">
                <v-avatar size="40">
                  <img 
                    :src="follower.profile_image_url || follower.profile_image || `https://ui-avatars.com/api/?name=${follower.nickname}&background=2563eb&color=fff&size=80`"
                    style="width: 100%; height: 100%; object-fit: cover;"
                  />
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-white font-weight-medium">{{ follower.nickname }}</div>
                  <div class="text-grey text-caption">
                    수익률: 
                    <span :class="follower.total_return_rate > 0 ? 'text-red-accent-2' : 'text-blue-accent-2'">
                      {{ follower.total_return_rate > 0 ? '+' : '' }}{{ follower.total_return_rate }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-grey">
            아직 팔로워가 없습니다.
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- =================== 모달: 팔로잉 목록 (MyPageView와 동일) =================== -->
    <v-dialog v-model="showFollowingModal" max-width="500">
      <v-card class="custom-card" rounded="xl">
        <v-card-title class="text-white pa-4 d-flex justify-space-between align-center">
          <span>팔로잉 {{ following.length }}</span>
          <v-btn 
            icon="mdi-close" 
            variant="text" 
            size="small"
            @click="showFollowingModal = false"
          ></v-btn>
        </v-card-title>
        <v-divider class="border-opacity-25"></v-divider>
        <v-card-text class="pa-4" style="max-height: 400px; overflow-y: auto;">
          <div v-if="following.length > 0">
            <div 
              v-for="followingUser in following" 
              :key="followingUser.id"
              class="user-item"
              @click="goToUserProfile(followingUser.id)"
              style="cursor: pointer;"
            >
              <div class="d-flex align-center gap-3">
                <v-avatar size="40">
                  <img 
                    :src="followingUser.profile_image_url || followingUser.profile_image || `https://ui-avatars.com/api/?name=${followingUser.nickname}&background=2563eb&color=fff&size=80`"
                    style="width: 100%; height: 100%; object-fit: cover;"
                  />
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-white font-weight-medium">{{ followingUser.nickname }}</div>
                  <div class="text-grey text-caption">
                    수익률: 
                    <span :class="followingUser.total_return_rate > 0 ? 'text-red-accent-2' : 'text-blue-accent-2'">
                      {{ followingUser.total_return_rate > 0 ? '+' : '' }}{{ followingUser.total_return_rate }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-grey">
            아직 팔로우한 사용자가 없습니다.
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from '@/api/index'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

// =================== State ===================
const targetUser = ref(null)
const portfolio = ref(null)
const holdings = ref([])
const transactions = ref([])
const userPosts = ref([])
const followers = ref([])
const following = ref([])

const loading = ref(false)
const error = ref(null)

const showFollowersModal = ref(false)
const showFollowingModal = ref(false)
const showAllTransactions = ref(false)
const displayLimit = 10

const activeTab = ref('holdings')

const myUserId = ref(null) // 로그인한 사용자 ID
const isFollowing = ref(false)

// =================== Computed ===================
const userId = computed(() => route.params.id)

const isMyProfile = computed(() => {
  return myUserId.value && myUserId.value === parseInt(userId.value)
})

const portfolioStats = computed(() => {
  if (!portfolio.value) return null
  
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
  return showAllTransactions.value 
    ? transactions.value 
    : transactions.value.slice(0, displayLimit)
})

// =================== Methods ===================
const loadUserData = async () => {
  loading.value = true
  error.value = null
  
  try {
    // 로그인한 사용자 정보 가져오기
    try {
      const meRes = await axios.get('/users/me/', { withCredentials: true })
      myUserId.value = meRes.data.id
    } catch (e) {
      console.log('로그인 안 됨')
    }

    // 타겟 유저 정보
    const userRes = await axios.get(`/users/${userId.value}/`, { withCredentials: true })
    targetUser.value = userRes.data
    isFollowing.value = userRes.data.is_following || false

    // 포트폴리오 (공개된 경우)
    try {
      const portfolioRes = await axios.get(`/users/${userId.value}/portfolio-summary/`, { withCredentials: true })
      portfolio.value = portfolioRes.data
    } catch (e) {
      console.warn('포트폴리오 비공개')
    }

    // 보유종목
    try {
      const holdingsRes = await axios.get(`/users/${userId.value}/holdings/`, { withCredentials: true })
      holdings.value = holdingsRes.data
    } catch (e) {
      holdings.value = []
    }

    // 거래내역
    try {
      const txRes = await axios.get(`/users/${userId.value}/transactions/`, { withCredentials: true })
      transactions.value = txRes.data
    } catch (e) {
      transactions.value = []
    }

    // 작성한 글
    try {
      const postsRes = await axios.get(`/users/${userId.value}/posts/`, { withCredentials: true })
      userPosts.value = postsRes.data
    } catch (e) {
      userPosts.value = []
    }
    
  } catch (e) {
    console.error('유저 데이터 로드 실패:', e)
    error.value = '사용자 정보를 불러올 수 없습니다.'
  } finally {
    loading.value = false
  }
}

const loadFollowers = async () => {
  try {
    const res = await axios.get(`/users/${userId.value}/followers/`, { withCredentials: true })
    followers.value = res.data
    showFollowersModal.value = true
  } catch (e) {
    console.error('팔로워 로드 실패:', e)
  }
}

const loadFollowing = async () => {
  try {
    const res = await axios.get(`/users/${userId.value}/following/`, { withCredentials: true })
    following.value = res.data
    showFollowingModal.value = true
  } catch (e) {
    console.error('팔로잉 로드 실패:', e)
  }
}

const toggleFollowUser = async () => {
  try {
    const res = await fetch(`/api/users/${userId.value}/follow/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      }
    })
    
    if (res.ok) {
      const data = await res.json()
      isFollowing.value = data.is_following
      
      // 팔로워 수 업데이트
      if (data.is_following) {
        targetUser.value.followers_count++
      } else {
        targetUser.value.followers_count--
      }
    }
  } catch (e) {
    console.error('팔로우 처리 실패:', e)
    alert('팔로우 처리에 실패했습니다.')
  }
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

const goToStock = (ticker) => {
  router.push(`/stock/${ticker}`)
}

const goToPost = (postId) => {
  router.push(`/community/${postId}`)
}

const goToUserProfile = (userId) => {
  showFollowersModal.value = false
  showFollowingModal.value = false
  router.push(`/user/${userId}`)
}

// =================== Formatters ===================
const formatPrice = (value) => {
  return value?.toLocaleString() || '0'
}

const formatDate = (dateStr) => {
  return dayjs(dateStr).format('YYYY.MM.DD HH:mm')
}

const getColor = (val) => {
  if (val > 0) return 'red-accent-2'
  if (val < 0) return 'blue-accent-2'
  return 'grey-lighten-1'
}

// =================== Lifecycle ===================
onMounted(() => {
  loadUserData()
})

// URL 파라미터 변경 감지
watch(() => route.params.id, () => {
  if (route.name === 'user-profile') {
    loadUserData()
  }
})
</script>

<style scoped>
.custom-card {
  background-color: #141414 !important;
  border-color: #333 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}

.border-subtle {
  border: 2px solid #333;
}

.border-bottom {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.custom-table {
  background: transparent !important;
}

.custom-table th {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.custom-table td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  height: 60px !important;
}

.gap-4 {
  gap: 1rem;
}

.follow-stat-btn {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.follow-stat-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: background 0.2s;
}

.user-item:hover {
  background: rgba(255, 255, 255, 0.05);
}
</style>