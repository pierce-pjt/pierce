<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import VueApexCharts from 'vue3-apexcharts'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const code = route.params.code

const summary = ref(null)
const posts = ref([])
const loading = ref(true)
const activeTab = ref('chart') 
const tradeLogs = ref([])

// 📈 차트 데이터 상태
const fullChartData = ref([]) 
const chartSeries = ref([])   
const activeRange = ref('1M') 

// ✅ 등락에 따른 색상 클래스 (상승: red, 하락: blue)
const priceColorClass = computed(() => {
  const rate = summary.value?.change_rate || 0
  if (rate > 0) return 'red'
  if (rate < 0) return 'blue'
  return 'gray'
})

// ✅ 투자 경고 뱃지 (변동률 절대값 5% 이상일 때)
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
    // 💡 차트가 안 보이는 문제 해결 핵심: 데이터 최소/최대값에 맞춰 자동 확장
    min: 'dataMin',
    max: 'dataMax',
    forceNiceScale: true,
  },
  grid: { borderColor: '#1a1a1b', strokeDashArray: 2 },
  plotOptions: {
    candlestick: { 
      colors: { upward: '#f04452', downward: '#3182f6' },
      wick: { useFillColor: true }
    }
  },
  tooltip: { theme: 'dark' }
}))

const updateChartRange = (range) => {
  activeRange.value = range
  if (!fullChartData.value.length) return
  const now = new Date().getTime()
  let diff = 30 * 24 * 60 * 60 * 1000 
  if (range === '1W') diff = 7 * 24 * 60 * 60 * 1000
  else if (range === '1Y') diff = 365 * 24 * 60 * 60 * 1000
  
  const filtered = fullChartData.value.filter(d => d.x >= (now - diff))
  chartSeries.value = [{ name: '주가', data: filtered }]
}

const fetchData = async () => {
  try {
    const opt = { credentials: 'include' } // ⭐ 세션 유지 필수
    
    const [sumRes, feedRes, tradeRes] = await Promise.all([
      fetch(`/api/stock-prices/summary/?ticker=${code}`, opt),
      fetch(`/api/posts/feed/?ticker=${code}`, opt),
      fetch(`/api/transactions/`, opt)
    ])

    if (sumRes.ok) summary.value = await sumRes.json()
    if (feedRes.ok) posts.value = await feedRes.json()
    
    // ✅ 실시간 나의 거래 내역 필터링 및 최신순 정렬
    if (tradeRes.ok) {
      const allTrades = await tradeRes.json()
      tradeLogs.value = allTrades
        .filter(t => String(t.company) === String(code)) // 현재 종목만
        .reverse() // 최신순
        .slice(0, 10)
    }

    if (!fullChartData.value.length) {
      const chartRes = await fetch(`/api/stock-prices/chart/?ticker=${code}&days=365`, opt)
      if (chartRes.ok) {
        const json = await chartRes.json()
        fullChartData.value = json.map(row => ({
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
  } catch(e) { console.error("데이터 로드 실패:", e) } 
  finally { loading.value = false }
}

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
      body: JSON.stringify({ company: code, type: tradeType.value, price: summary.value.last_price, quantity: tradeQuantity.value })
    })
    if(res.ok) {
      alert('주문이 체결되었습니다!')
      await authStore.fetchUser() 
      showTradeModal.value = false
      fetchData() // 내역 즉시 갱신
    }
  } catch (e) { console.error("거래 실패:", e) }
}

let polling = null
onMounted(() => { fetchData(); polling = setInterval(fetchData, 5000); })
onUnmounted(() => { if (polling) clearInterval(polling) })
</script>

<template>
  <div class="dashboard-detail">
    <header class="detail-header">
      <div class="header-left">
        <button @click="router.back()" class="back-btn">〈</button>
        <div class="title-area">
          <h1 class="stock-title">{{ summary?.name }} <span class="stock-code">{{ code }}</span></h1>
          <div v-if="isHighVolatility" class="warning-badge">투자경고</div>
        </div>
      </div>
      <div class="header-right" v-if="authStore.isAuthenticated">
        <div class="mileage-badge">💎 {{ Number(authStore.user?.mileage || 0).toLocaleString() }} M</div>
        <div class="action-btns">
          <button @click="openTradeModal('BUY')" class="btn buy">매수</button>
          <button @click="openTradeModal('SELL')" class="btn sell">매도</button>
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
            <div class="chart-top">
              <div class="current-price-box" :class="priceColorClass">
                <span class="main-price">{{ Number(summary?.last_price).toLocaleString() }}원</span>
                <span class="main-rate">{{ summary?.change_rate > 0 ? '+' : '' }}{{ summary?.change_rate }}%</span>
              </div>
              <div class="range-tabs">
                <button v-for="r in ['1W', '1M', '1Y']" :key="r" @click="updateChartRange(r)" :class="{ active: activeRange === r }">{{ r }}</button>
              </div>
            </div>
            <VueApexCharts v-if="chartSeries.length && chartSeries[0].data.length" type="candlestick" height="400" :options="chartOptions" :series="chartSeries" />
            <div v-else class="chart-loading">차트 데이터를 불러오는 중...</div>
          </section>
        </div>

        <div v-if="activeTab === 'community'">
          <section class="feed-section shadow-card">
            <h3>종목 토론방</h3>
            <div v-if="posts.length === 0" class="empty">첫 게시글을 작성해보세요.</div>
            <div v-for="post in posts" :key="post.id" class="post-item">
              <div class="post-meta">
                <span class="user">{{ post.author.nickname || '익명' }}</span>
                <span class="time">{{ new Date(post.created_at).toLocaleDateString() }}</span>
              </div>
              <p class="post-text">{{ post.content }}</p>
            </div>
          </section>
        </div>
      </div>

      <aside class="content-right">
        <section class="log-section shadow-card">
          <div class="log-header">
            <h3>실시간 나의 거래</h3>
            <span class="live-dot"></span>
          </div>
          <div class="log-list">
            <div v-if="tradeLogs.length === 0" class="empty-log">거래 내역이 없습니다.</div>
            <div v-for="log in tradeLogs" :key="log.id" class="log-item">
              <div class="log-info">
                <span :class="log.type === 'BUY' ? 'tag-buy' : 'tag-sell'">{{ log.type === 'BUY' ? '매수' : '매도' }}</span>
                <span class="log-time">{{ new Date(log.created_at).toLocaleTimeString() }}</span>
              </div>
              <div class="log-details">
                <span class="log-amt">{{ log.quantity }}주</span>
                <span class="log-prc">{{ Number(log.price).toLocaleString() }}원</span>
              </div>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="showTradeModal" class="modal-overlay" @click.self="showTradeModal = false">
      <div class="modal-content">
        <h2 :class="tradeType === 'BUY' ? 'red' : 'blue'">{{ tradeType === 'BUY' ? '매수하기' : '매도하기' }}</h2>
        <div class="modal-body">
          <p class="modal-stock-name">{{ summary?.name }}</p>
          <p class="modal-price">현재가: <strong>{{ Number(summary?.last_price).toLocaleString() }}원</strong></p>
          <div class="input-row">
            <label>주문 수량</label>
            <input type="number" v-model.number="tradeQuantity" min="1" placeholder="0" />
          </div>
          <div class="total-row">
            <span>총 주문 금액</span>
            <strong :class="tradeType === 'BUY' ? 'red' : 'blue'">{{ Number(summary?.last_price * tradeQuantity).toLocaleString() }} M</strong>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showTradeModal = false" class="btn-cancel">취소</button>
          <button @click="executeTrade" :class="['btn-submit', tradeType === 'BUY' ? 'buy-bg' : 'sell-bg']">주문 확정</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 기존 스타일 유지 (생략) */
.dashboard-detail { background: #000; min-height: 100vh; color: #fff; padding: 0 20px 40px; }
.detail-header { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 25px 0; }
.header-left { display: flex; align-items: center; gap: 15px; }
.title-area { display: flex; align-items: baseline; gap: 10px; }
.warning-badge { background: #f0445222; color: #f04452; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #f0445244; }
.back-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; }
.stock-title { font-size: 24px; font-weight: bold; margin: 0; }
.stock-code { color: #666; font-size: 16px; font-weight: normal; }
.header-right { display: flex; align-items: center; gap: 20px; }
.mileage-badge { background: #1a1a1b; padding: 8px 15px; border-radius: 10px; color: #fbbf24; font-weight: bold; }
.action-btns { display: flex; gap: 10px; }
.btn { padding: 10px 25px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; color: #fff; }
.btn.buy { background: #f04452; } .btn.sell { background: #3182f6; }
.toss-nav { max-width: 1200px; margin: 0 auto 30px; display: flex; gap: 30px; border-bottom: 1px solid #1a1a1b; }
.toss-nav button { background: none; border: none; color: #666; font-size: 16px; font-weight: bold; padding: 10px 5px; cursor: pointer; border-bottom: 3px solid transparent; }
.toss-nav button.active { color: #fff; border-bottom-color: #fff; }
.main-grid { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 8fr 4fr; gap: 25px; }
.shadow-card { background: #1a1a1b; border-radius: 24px; padding: 25px; }
.red { color: #f04452; } .blue { color: #3182f6; }
.buy-bg { background: #f04452; } .sell-bg { background: #3182f6; }
.chart-top { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
.main-price { font-size: 32px; font-weight: bold; margin-right: 10px; }
.main-rate { font-size: 18px; font-weight: bold; }
.range-tabs { display: flex; background: #000; padding: 4px; border-radius: 10px; }
.range-tabs button { background: none; border: none; color: #666; padding: 6px 12px; border-radius: 8px; cursor: pointer; }
.range-tabs button.active { background: #1a1a1b; color: #fff; font-weight: bold; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: #1a1a1b; padding: 35px; border-radius: 30px; width: 400px; }
.modal-footer { display: grid; grid-template-columns: 1fr 2fr; gap: 15px; margin-top: 30px; }
.tag-buy { color: #f04452; font-weight: bold; font-size: 12px; }
.tag-sell { color: #3182f6; font-weight: bold; font-size: 12px; }
.live-dot { width: 8px; height: 8px; background: #00ff00; border-radius: 50%; box-shadow: 0 0 10px #00ff00; animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
@media (max-width: 1024px) { .main-grid { grid-template-columns: 1fr; } }
</style>