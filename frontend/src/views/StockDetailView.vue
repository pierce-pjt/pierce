<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { mypageAPI } from '@/api/mypage' 
import VueApexCharts from 'vue3-apexcharts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const code = route.params.code 

// --- 상태 관리 ---
const summary = ref(null)
const posts = ref([])
const loading = ref(true)
const activeTab = ref('chart') 
const tradeLogs = ref([])      
const watchlist = ref([]) // 관심종목 ticker 배열

// 📈 차트 데이터 상태
const fullChartData = ref([]) 
const chartSeries = ref([])   
const activeRange = ref('1M') 

// --- Computed ---

// 관심종목 여부 확인
const isWatched = computed(() => watchlist.value.includes(code))

const priceColorClass = computed(() => {
  const rate = summary.value?.change_rate || 0
  if (rate > 0) return 'text-red'
  if (rate < 0) return 'text-blue'
  return 'text-gray'
})

const isHighVolatility = computed(() => {
  return Math.abs(summary.value?.change_rate || 0) >= 5.0
})

const chartOptions = computed(() => ({
  chart: {
    type: 'candlestick',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: false }
  },
  theme: { mode: 'dark' },
  xaxis: { 
    type: 'datetime', 
    labels: { style: { colors: '#666', fontSize: '10px' } },
    axisBorder: { show: false }
  },
  yaxis: {
    opposite: true,
    labels: { 
      style: { colors: '#999' },
      formatter: (val) => val?.toLocaleString() 
    },
    min: undefined,
    max: undefined,
    forceNiceScale: true,
  },
  grid: { 
    borderColor: '#1a1a1b', 
    strokeDashArray: 2 
  },
  plotOptions: {
    candlestick: { 
      colors: { upward: '#f04452', downward: '#3182f6' },
      wick: { useFillColor: true }
    }
  }
}))

// --- 데이터 로직 ---

// 관심종목 불러오기
const fetchWatchlist = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await fetch('/api/watchlist/', { credentials: 'include' })
    if (res.ok) {
      const data = await res.json()
      const items = data.results || data 
      if (Array.isArray(items)) {
        watchlist.value = items.map(item => item.ticker)
      }
    }
  } catch (e) {
    console.error("관심종목 로드 실패", e)
  }
}

// 관심종목 토글
const toggleWatchlist = async () => {
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  try {
    const res = await fetch('/api/watchlist/toggle/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ ticker: code })
    })
    
    if (res.ok) {
      const result = await res.json()
      if (result.added) {
        if (!watchlist.value.includes(code)) watchlist.value.push(code)
      } else {
        watchlist.value = watchlist.value.filter(c => c !== code)
      }
    }
  } catch (e) {
    console.error("관심종목 토글 실패", e)
  }
}

const updateChartRange = (range) => {
  activeRange.value = range
  if (!fullChartData.value || fullChartData.value.length === 0) return
  
  const lastDate = Math.max(...fullChartData.value.map(d => d.x))
  let diff = 30 * 24 * 60 * 60 * 1000 
  if (range === '1W') diff = 7 * 24 * 60 * 60 * 1000
  else if (range === '1Y') diff = 365 * 24 * 60 * 60 * 1000
  
  const filtered = fullChartData.value.filter(d => d.x >= (lastDate - diff))
  chartSeries.value = [{ name: '주가', data: filtered }]
}

const fetchMyTransactions = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await mypageAPI.getTransactions()
    const allTrades = Array.isArray(res.data) ? res.data : []
    
    tradeLogs.value = allTrades
      .filter(tx => tx.ticker === code || tx.company_code === code)
      .sort((a, b) => new Date(b.transaction_datetime) - new Date(a.transaction_datetime))
      .slice(0, 15)
  } catch (e) {
    console.error("거래 내역 로드 실패:", e)
  }
}

const fetchData = async () => {
  try {
    const opt = { credentials: 'include' }
    
    const [sumRes, feedRes] = await Promise.all([
      fetch(`/api/stock-prices/summary/?ticker=${code}`, opt),
      fetch(`/api/posts/feed/?ticker=${code}`, opt)
    ])

    if (sumRes.ok) summary.value = await sumRes.json()
    if (feedRes.ok) posts.value = await feedRes.json()

    const chartRes = await fetch(`/api/stock-prices/chart/?ticker=${code}&days=365`, opt)
    if (chartRes.ok) {
      const json = await chartRes.json()
      const rawData = Array.isArray(json) ? json : (json.results || [])
      
      if (rawData.length > 0) {
        fullChartData.value = rawData.map(row => ({
          x: new Date(row.date).getTime(),
          y: [
            parseFloat(row.open), 
            parseFloat(row.high), 
            parseFloat(row.low), 
            parseFloat(row.close)
          ]
        }))
        updateChartRange(activeRange.value)
      }
    }
    await fetchMyTransactions()
  } catch(e) { 
    console.error("데이터 패칭 에러:", e) 
  } finally { 
    loading.value = false 
  }
}

// --- 거래 로직 ---
const showTradeModal = ref(false)
const tradeType = ref('BUY')
const tradeQuantity = ref(0)

const openTradeModal = (type) => {
  if(!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  tradeType.value = type
  tradeQuantity.value = 0
  showTradeModal.value = true
}

const executeTrade = async () => {
  if (tradeQuantity.value <= 0) return alert('수량을 입력해주세요.')
  
  try {
    const res = await fetch('/api/transactions/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', 
      body: JSON.stringify({ 
        company: code, 
        type: tradeType.value, 
        price: summary.value.last_price, 
        quantity: tradeQuantity.value 
      })
    })

    // ✅ 성공했을 때 (200~299)
    if (res.ok) {
      alert(`${tradeType.value === 'BUY' ? '매수' : '매도'} 주문이 체결되었습니다!`)
      await authStore.fetchUser() 
      showTradeModal.value = false
      await fetchData() 
    } 
    // ❌ 에러가 발생했을 때 (400, 403 등)
    else {
      const errorData = await res.json()
      // 백엔드의 raise PermissionDenied("메시지") 내용이 errorData.detail에 담깁니다.
      alert(errorData.detail || '거래 처리 중 오류가 발생했습니다.')
    }

  } catch (e) { 
    console.error("거래 통신 에러:", e)
    alert('서버와 통신하는 중 문제가 발생했습니다.')
  }
}

const formatPrice = (value) => value?.toLocaleString() || '0'
const formatDate = (dateStr) => dayjs(dateStr).format('MM.DD HH:mm')

let polling = null

// 인증 상태 변화 감시
watch(() => authStore.isAuthenticated, (newVal) => {
  if (newVal) fetchWatchlist()
}, { immediate: true })

onMounted(() => { 
  fetchData()
  if (authStore.isAuthenticated) fetchWatchlist()
  polling = setInterval(fetchData, 10000) 
})
onUnmounted(() => { 
  if (polling) clearInterval(polling) 
})
</script>

<template>
  <div class="dashboard-detail">
    <header class="detail-header">
      <div class="header-left">
        <button @click="router.back()" class="back-btn">〈</button>
        <div class="title-area">
          <div class="name-row">
            <button class="star-btn" @click="toggleWatchlist">
              {{ isWatched ? '★' : '☆' }}
            </button>
            <h1 class="stock-title">{{ summary?.name || '로딩 중...' }}</h1>
            <span class="stock-code">{{ code }}</span>
            <div v-if="isHighVolatility" class="warning-badge">투자경고</div>
          </div>
          <div class="price-info" :class="priceColorClass">
            <span class="main-price">{{ formatPrice(summary?.last_price) }}원</span>
            <span class="main-rate">{{ (summary?.change_rate || 0) > 0 ? '+' : '' }}{{ summary?.change_rate }}%</span>
          </div>
        </div>
      </div>
      
      <div class="header-right" v-if="authStore.isAuthenticated">
        <div class="mileage-badge">💎 {{ formatPrice(authStore.user?.mileage) }} M</div>
        <div class="action-btns">
          <button @click="openTradeModal('BUY')" class="btn buy-bg">매수</button>
          <button @click="openTradeModal('SELL')" class="btn sell-bg">매도</button>
        </div>
      </div>
    </header>

    <nav class="toss-nav">
      <button @click="activeTab = 'chart'" :class="{ active: activeTab === 'chart' }">차트·호가</button>
      <button @click="activeTab = 'community'" :class="{ active: activeTab === 'community' }">커뮤니티</button>
    </nav>

    <div class="main-grid">
      <div class="content-left">
        <div v-if="activeTab === 'chart'">
          <section class="chart-section shadow-card">
            <div class="chart-header">
              <span class="text-subtitle-2 text-grey">주가 흐름</span>
              <div class="range-tabs">
                <button v-for="r in ['1W', '1M', '1Y']" :key="r" @click="updateChartRange(r)" :class="{ active: activeRange === r }">{{ r }}</button>
              </div>
            </div>
            <div class="chart-wrapper">
              <VueApexCharts 
                v-if="chartSeries.length > 0 && chartSeries[0].data.length > 0" 
                type="candlestick" 
                height="400" 
                :options="chartOptions" 
                :series="chartSeries" 
              />
              <div v-else class="empty-chart">차트 데이터를 불러오는 중입니다...</div>
            </div>
          </section>
        </div>

        <div v-if="activeTab === 'community'">
          <section class="feed-section shadow-card">
            <h3 class="mb-4">종목 토론방</h3>
            <div v-if="posts.length === 0" class="empty">첫 게시글을 작성해보세요.</div>
            <div v-for="post in posts" :key="post.id" class="post-item">
              <div class="post-meta">
                <span class="user">{{ post.author?.nickname || '익명' }}</span>
                <span class="time">{{ formatDate(post.created_at) }}</span>
              </div>
              <p class="post-text">{{ post.content }}</p>
            </div>
          </section>
        </div>
      </div>

      <aside class="content-right">
        <section class="log-section shadow-card">
          <div class="log-header">
            <h3>나의 거래 내역</h3>
            <span v-if="authStore.isAuthenticated" class="live-dot"></span>
          </div>
          <div class="log-list custom-scrollbar">
            <div v-if="!authStore.isAuthenticated" class="empty-log">로그인 후 확인 가능합니다.</div>
            <div v-else-if="tradeLogs.length === 0" class="empty-log">거래 내역이 없습니다.</div>
            <div v-else v-for="log in tradeLogs" :key="log.id" class="log-item-v2">
              <div class="item-top">
                <span class="type-tag" :class="log.transaction_type === 'BUY' ? 'buy' : 'sell'">
                  {{ log.transaction_type === 'BUY' ? '매수' : '매도' }}
                </span>
                <span class="time">{{ formatDate(log.transaction_datetime) }}</span>
              </div>
              <div class="item-bottom">
                <span class="quantity">{{ log.quantity }}주 · {{ formatPrice(log.price) }}원</span>
                <span class="total-amount" :class="log.transaction_type === 'BUY' ? 'text-red' : 'text-blue'">
                  {{ log.transaction_type === 'BUY' ? '-' : '+' }}{{ formatPrice(log.amount) }}원
                </span>
              </div>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="showTradeModal" class="modal-overlay" @click.self="showTradeModal = false">
      <div class="modal-content">
        <div class="modal-header-text">
          <h2 :class="tradeType === 'BUY' ? 'text-red' : 'text-blue'">
            {{ summary?.name }} {{ tradeType === 'BUY' ? '매수하기' : '매도하기' }}
          </h2>
          <p class="current-price-label">현재가: {{ formatPrice(summary?.last_price) }}원</p>
        </div>

        <div class="input-group">
          <label>주문 수량</label>
          <input 
            v-model.number="tradeQuantity" 
            type="number" 
            placeholder="0" 
            min="1"
            class="trade-input"
          />
        </div>

        <div class="modal-footer">
          <button @click="showTradeModal = false" class="btn-cancel">취소</button>
          <button 
            @click="executeTrade" 
            class="btn-submit" 
            :class="tradeType === 'BUY' ? 'buy-bg' : 'sell-bg'"
          >
            {{ tradeType === 'BUY' ? '매수 확인' : '매도 확인' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-detail { background: #000; min-height: 100vh; color: #fff; padding: 0 20px 60px; font-family: sans-serif; }
.detail-header { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 30px 0; }

/* 헤더 & 타이틀 */
.header-left { display: flex; align-items: flex-start; gap: 20px; }
.back-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; padding-top: 5px; }
.name-row { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
.stock-title { font-size: 28px; font-weight: bold; margin: 0; }
.stock-code { color: #666; font-size: 16px; }
.warning-badge { background: rgba(240, 68, 82, 0.15); color: #f04452; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid rgba(240, 68, 82, 0.3); }

/* 별 아이콘 스타일 */
.star-btn { background: none; border: none; color: #ff9d00; font-size: 24px; cursor: pointer; padding: 0; transition: transform 0.2s; line-height: 1; }
.star-btn:hover { transform: scale(1.2); }

/* 가격 정보 */
.price-info { display: flex; align-items: baseline; gap: 12px; }
.main-price { font-size: 32px; font-weight: 800; }
.main-rate { font-size: 20px; font-weight: bold; }

/* 상단 우측 */
.header-right { display: flex; align-items: center; gap: 20px; }
.mileage-badge { background: #1a1a1b; padding: 10px 18px; border-radius: 12px; color: #fbbf24; font-weight: bold; border: 1px solid #333; }
.btn { padding: 12px 30px; border-radius: 14px; border: none; font-weight: bold; cursor: pointer; color: #fff; font-size: 16px; }

/* 네비게이션 */
.toss-nav { max-width: 1200px; margin: 0 auto 30px; display: flex; gap: 30px; border-bottom: 1px solid #1a1a1b; }
.toss-nav button { background: none; border: none; color: #666; font-size: 17px; font-weight: bold; padding: 12px 5px; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.toss-nav button.active { color: #fff; border-bottom-color: #fff; }

/* 그리드 레이아웃 */
.main-grid { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 8fr 4fr; gap: 30px; }
.shadow-card { background: #1a1a1b; border-radius: 24px; padding: 25px; border: 1px solid #222; }

/* 차트 섹션 */
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.range-tabs { display: flex; background: #000; padding: 4px; border-radius: 10px; }
.range-tabs button { background: none; border: none; color: #666; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: bold; }
.range-tabs button.active { background: #1a1a1b; color: #fff; }

/* 우측 거래 내역 */
.log-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.log-list { max-height: 600px; overflow-y: auto; }
.log-item-v2 { padding: 15px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.log-item-v2:last-child { border-bottom: none; }
.item-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.type-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fff; }
.type-tag.buy { background: #f04452; }
.type-tag.sell { background: #3182f6; }
.item-bottom { display: flex; justify-content: space-between; font-size: 14px; }
.total-amount { font-weight: bold; }

/* 커뮤니티 */
.post-item { padding: 15px 0; border-bottom: 1px solid #333; }
.post-meta { display: flex; gap: 10px; font-size: 13px; color: #999; margin-bottom: 5px; }
.post-text { font-size: 15px; line-height: 1.5; margin: 0; }

/* 모달 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.modal-content { background: #1a1a1b; padding: 40px; border-radius: 32px; width: 420px; border: 1px solid #333; }
.input-group { display: flex; flex-direction: column; gap: 10px; margin: 20px 0; }
.input-group input { background: #000; border: 1px solid #333; padding: 16px; border-radius: 16px; color: #fff; font-size: 22px; text-align: right; }
.modal-footer { display: grid; grid-template-columns: 1fr 2fr; gap: 15px; margin-top: 20px; }
.btn-cancel { background: #333; border: none; color: #fff; padding: 16px; border-radius: 16px; cursor: pointer; font-weight: bold; }
.btn-submit { border: none; color: #fff; font-weight: bold; border-radius: 16px; cursor: pointer; }

/* 공통 유틸리티 */
.text-red { color: #f04452; }
.text-blue { color: #3182f6; }
.text-grey { color: #919193; }
.buy-bg { background: #f04452; }
.sell-bg { background: #3182f6; }
.live-dot { width: 8px; height: 8px; background: #4caf50; border-radius: 50%; box-shadow: 0 0 10px #4caf50; animation: pulse 2s infinite; }

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
@media (max-width: 1024px) { .main-grid { grid-template-columns: 1fr; } }
</style>